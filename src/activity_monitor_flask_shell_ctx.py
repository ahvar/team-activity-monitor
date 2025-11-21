from src.app import create_app

app = create_app()
from src.app.main.async_activity_service import AsyncActivityService


@app.shell_context_processor
def make_shell_context():
    return {
        "AsyncActivityService": AsyncActivityService,
    }


def main():
    """Console script entry point for 'team-monitor' command"""
    import os

    # Set default host and port
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"

    print(f"Starting Team Activity Monitor on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
