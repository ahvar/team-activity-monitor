from src.config import Config


class TestConfig(Config):
    TESTING = True
    # SQLALCHEMY_DATABASE_URI = "sqlite://"
    SECRET_KEY = "test-secret-key"
    WTF_CSRF_ENABLED = False
    GITHUB_API_KEY = "fake-github-key"
    JIRA_API_KEY = "fake-jira-key"
    JIRA_BASE_URL = "https://fakeactivitymonitor.com"
    OPENAI_API_KEY = "fake-openai-api-key"
    ADMINS = []

    # Set small page sizes to test pagination with fewer records
    ITEMS_PER_PAGE = 3
