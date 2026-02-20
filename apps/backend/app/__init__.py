from flask import Flask

from app.api.email_routes import email_bp
from app.core.config import Settings
from app.db.session import init_db
from app.scheduler.email_scheduler import start_email_scheduler, stop_email_scheduler


def create_app() -> Flask:
    settings = Settings()

    app = Flask(__name__)
    app.config["SETTINGS"] = settings

    init_db(settings.database_url)

    app.register_blueprint(email_bp, url_prefix="/emails")

    scheduler = start_email_scheduler(app)

    @app.teardown_appcontext
    def shutdown_scheduler(_exception: Exception | None) -> None:
        stop_email_scheduler(scheduler)

    return app
