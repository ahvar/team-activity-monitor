import os
from pathlib import Path
from dotenv import load_dotenv

basedir = Path(__file__).resolve().parent.parent
envfile = basedir / ".env"
load_dotenv(str(envfile))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "you-will-never-guess"
    GITHUB_API_KEY = os.environ.get("GITHUB_API_KEY")
    JIRA_API_KEY = os.environ.get("JIRA_API_KEY")
    JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    ADMINS = ["arthurvargasdev@gmail.com"]
    ITEMS_PER_PAGE = 10
    LANGUAGES = ["en", "es"]
