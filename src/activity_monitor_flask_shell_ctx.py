from src.app import create_app

app = create_app()
from src.app.main.async_activity_service import AsyncActivityService


@app.shell_context_processor
def make_shell_context():
    return {
        "AsyncActivityService": AsyncActivityService,
    }
