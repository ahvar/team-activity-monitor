import logging
import traceback
import os
import openai
from pathlib import Path
from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, current_app
from flask_babel import _, get_locale
from langdetect import detect, LangDetectException
from src.app.main.forms import (
    EmptyForm,
    QuestionForm,
    SearchForm,
)

# from src.app.translate import translate
from src.app.main import bp
from src.utils.references import MONITOR_LOG_BACKEND, openai_models

monitor_logger = logging.getLogger(MONITOR_LOG_BACKEND)
messages = []


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
def index():
    """Home page"""
    form = EmptyForm()
    error = None
    if request.method == "POST":
        user_message = request.form.get("message", "")
        # TODO: process with JIRA/Github integration
        messages.append({"is_user": True, "q": user_message})
        messages.append(
            {
                "is_user": False,
                "a": f"I received your query: '{user_message}'. Integration coming soon",
            }
        )

        if not openai.api_key:
            flash(_("OpenAI API key is not set!"))
            return render_template(
                "index.html", messages=messages, error="OpenAI API key is not set!"
            )

    return render_template("index.html", title="Home", messages=messages, error=error)


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
