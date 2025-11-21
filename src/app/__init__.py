import os
import logging
from flask import Flask, request, current_app
from src.config import Config
from src.utils.references import set_team_members


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    set_team_members(app.config["TEAM_MEMBERS"])

    from src.app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)

    from src.app.main import bp as main_bp

    app.register_blueprint(main_bp)

    return app
