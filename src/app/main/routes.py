import logging
import traceback
import os
import openai
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    g,
    current_app,
    jsonify,
)
from langdetect import detect, LangDetectException
from src.app.main.forms import (
    EmptyForm,
)

from src.app.main import bp
from src.app.main.query_parser import parse_query
from src.app.main.async_activity_service import AsyncActivityService
from src.app.main.response_templates import (
    format_jira_only_response,
    format_commits_only_response,
    format_prs_only_response,
    format_activity_summary_response,
)
from src.app.client.async_github import AsyncGitHubClient
from src.app.client.async_jira import AsyncJiraClient
from src.utils.references import MONITOR_LOG_BACKEND, openai_models, TEAM_MEMBERS

monitor_logger = logging.getLogger(MONITOR_LOG_BACKEND)
messages = []


def create_async_clients():
    """Create and return async GitHub and Jira clients."""
    github_client = AsyncGitHubClient(current_app.config["GITHUB_API_KEY"])
    jira_client = AsyncJiraClient(
        base_url=current_app.config["JIRA_BASE_URL"],
        email=current_app.config.get("JIRA_EMAIL"),
        api_token=current_app.config["JIRA_API_KEY"],
    )
    return github_client, jira_client


def process_user_query(user_message: str) -> str:
    """Process user query and return response string with better error handling."""

    # Handle empty/whitespace queries
    if not user_message or not user_message.strip():
        return "Please ask me something! Try: 'What is Arthur working on?'"

    parsed_query = parse_query(user_message)

    if not parsed_query:
        # More helpful error message with actual team members
        team_list = (
            ", ".join(TEAM_MEMBERS[:-1]) + f" or {TEAM_MEMBERS[-1]}"
            if len(TEAM_MEMBERS) > 1
            else TEAM_MEMBERS[0]
        )
        return f"I couldn't identify a team member in your question. I can help with information about: {team_list}"

    # Create event loop and run async code
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        github_client, jira_client = create_async_clients()
        activity_service = AsyncActivityService(jira_client, github_client)

        activity_data = loop.run_until_complete(
            activity_service.handle_intent(parsed_query)
        )

        return format_activity_response(activity_data)

    except Exception as e:
        monitor_logger.error(f"Error processing query '{user_message}': {str(e)}")
        return f"Sorry, I encountered an error while fetching {parsed_query.member_name}'s information. Please try again later."

    finally:
        loop.close()


def format_activity_response(activity_data: dict) -> str:
    """Format activity data using appropriate template based on intent."""
    member_name = activity_data.get("member_name", "Unknown")
    intent = activity_data.get("intent", "")

    # Extract data
    jira_issues = activity_data.get("jira", {}).get("issues", [])
    github_commits = activity_data.get("github", {}).get("commits", [])
    github_prs = activity_data.get("github", {}).get("pull_requests", [])

    # Extract errors
    jira_error = activity_data.get("jira", {}).get("error")
    github_error = activity_data.get("github", {}).get("error")

    if intent == "JIRA_ISSUES":
        return format_jira_only_response(member_name, jira_issues, jira_error)

    elif intent == "GITHUB_COMMITS":
        return format_commits_only_response(member_name, github_commits, github_error)

    elif intent == "GITHUB_PULL_REQUESTS":
        return format_prs_only_response(member_name, github_prs, github_error)

    else:  # MEMBER_ACTIVITY_SUMMARY
        return format_activity_summary_response(
            member_name,
            jira_issues,
            github_commits,
            github_prs,
            jira_error,
            github_error,
        )


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
def index():
    """Home page with async API calls"""
    form = EmptyForm()  # CREATE FORM FOR CSRF
    error = None

    if request.method == "POST":
        if not form.validate_on_submit():
            error_msg = "Security validation failed. Please refresh and try again."
            return jsonify({"success": False, "error": error_msg})

        user_message = request.form.get("message", "")

        # Handle requests
        try:
            response = process_user_query(user_message)
            return jsonify({"success": True, "response": response})
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            monitor_logger.error(f"Error processing query: {str(e)}")
            return jsonify({"success": False, "error": error_msg})

    return render_template(
        "index.html",
        title="Team Activity Monitor",
        messages=messages,
        error=error,
        form=form,
        config=current_app.config,
    )


@bp.route("/reset", methods=["POST"])
def reset():
    """Clear chat history"""
    global messages
    messages = []
    flash("Chat history cleared")
    return redirect(url_for("main.index"))


def get_openai_response(message):
    """Handle OpenAI communication - for future enhancement"""
    if not openai.api_key:
        raise ValueError("API key is not set!")

    try:
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model=openai_models[0],
            messages=[{"role": "user", "content": message}],
            stream=False,
        )
        if not response or not response.choices:
            raise ValueError("No response received from API")
        return response.choices[0].message.content
    except openai.AuthenticationError:
        raise ValueError("Invalid API key")
    except Exception as e:
        raise ValueError(f"Error communicating with OpenAI: {str(e)}")
