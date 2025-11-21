import logging
import traceback
import os
import openai
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, current_app
from langdetect import detect, LangDetectException
from src.app.main.forms import (
    EmptyForm,
    QuestionForm,
    SearchForm,
)

# from src.app.translate import translate
from src.app.main import bp
from src.app.main.query_parser import parse_query
from src.app.main.async_activity_service import AsyncActivityService
from src.app.client.async_github import AsyncGitHubClient
from src.app.client.async_jira import AsyncJiraClient
from src.utils.references import MONITOR_LOG_BACKEND, openai_models

monitor_logger = logging.getLogger(MONITOR_LOG_BACKEND)
messages = []


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
def index():
    """Home page with async API calls"""
    form = EmptyForm()
    error = None

    if request.method == "POST":
        user_message = request.form.get("message", "")
        messages.append({"is_user": True, "q": user_message})

        try:
            parsed_query = parse_query(user_message)
            if not parsed_query:
                response = "I couldn't identify a team member in your question."
            else:
                # RUNNING ASYNC CODE IN FLASK: We need to create an event loop
                # Flask is synchronous, so we need to bridge to async code

                # Create a new event loop for this request
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                try:

                    # Create async clients
                    github_client = AsyncGitHubClient(
                        current_app.config["GITHUB_API_KEY"]
                    )
                    jira_client = AsyncJiraClient(
                        base_url=current_app.config["JIRA_BASE_URL"],
                        email=current_app.config.get("JIRA_EMAIL"),
                        api_token=current_app.config["JIRA_API_KEY"],
                    )

                    # Create async service
                    activity_service = AsyncActivityService(jira_client, github_client)

                    # RUN THE ASYNC COROUTINE: loop.run_until_complete() runs the async function
                    # This blocks until the async function finishes
                    activity_data = loop.run_until_complete(
                        activity_service.handle_intent(parsed_query)
                    )

                    response = f"Here's what I found for {parsed_query.member_name}: {activity_data}"

                finally:
                    # Always clean up the event loop
                    loop.close()

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}"
            messages.append({"is_user": False, "a": error_msg})
            monitor_logger.error(f"Error processing query: {str(e)}")

        messages.append({"is_user": False, "a": response})

    return render_template(
        "index.html",
        title="Team Activity Monitor",
        messages=messages,
        error=error,
        config=current_app.config,
    )


@bp.route("/reset", methods=["POST"])
def reset():
    flash("Chat history cleared")
    return redirect(url_for("main.index"))


def get_openai_response(message):
    """Handle OpenAI communication"""
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
