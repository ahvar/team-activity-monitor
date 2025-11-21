import os
import logging
from flask import Flask, request, current_app
from src.config import Config
from src.utils.references import set_team_members

# from src.app.cli import init_frontend_logger

# app_logger = init_frontend_logger(logging.INFO)


# def get_locale():
#    return request.accept_languages.best_match(current_app.config["LANGUAGES"])


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    set_team_members(app.config["TEAM_MEMBERS"])

    from src.app.errors import bp as errors_bp

    app.register_blueprint(errors_bp)
    # from src.app.auth import bp as auth_bp

    # app.register_blueprint(auth_bp, url_prefix="/auth")
    from src.app.main import bp as main_bp

    app.register_blueprint(main_bp)

    # from src.app.cli import bp as cli_bp

    # app.register_blueprint(cli_bp)
    """
    if not app.debug and not app.testing:
        if app.config["MAIL_SERVER"]:
            auth = None
            if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
                auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            secure = None
            if app.config["MAIL_USE_TLS"]:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
                fromaddr="no-reply@" + app.config["MAIL_SERVER"],
                toaddrs=app.config["ADMINS"],
                subject="Team Activity Monitor Failure",
                credentials=auth,
                secure=secure,
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)
    """
    return app


# from src.app.models import researcher, gene, pipeline_run_service, pipeline_run
