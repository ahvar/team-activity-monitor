from src.config import Config


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret-key"
    WTF_CSRF_ENABLED = False
    ADMINS = []
    ITEMS_PER_PAGE = 3
