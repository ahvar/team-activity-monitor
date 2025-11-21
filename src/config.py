import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent.parent
envfile = basedir / ".env"
load_dotenv(str(envfile))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    GITHUB_API_KEY = os.environ.get("GITHUB_API_KEY")
    GITHUB_BASE_URL = os.environ.get("GITHUB_BASE_URL")
    JIRA_API_KEY = os.environ.get("JIRA_API_KEY")
    JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL")
    JIRA_EMAIL = os.environ.get("JIRA_EMAIL")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    ITEMS_PER_PAGE = 10
    LANGUAGES = ["en", "es"]

    TEAM_MEMBERS = [
        name.strip()
        for name in os.environ.get("TEAM_MEMBERS", "").split(",")
        if name.strip()
    ]

    if not TEAM_MEMBERS:
        raise ValueError("TEAM_MEMBERS environment variable is required")
