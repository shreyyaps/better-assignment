from flask import Flask

from app.api.task_routes import task_bp
from app.core.config import Settings
from app.db.session import init_db


def create_app() -> Flask:
    settings = Settings()

    app = Flask(__name__)
    app.config["SETTINGS"] = settings

    init_db(settings.database_url)

    app.register_blueprint(task_bp, url_prefix="/tasks")

    @app.after_request
    def add_cors_headers(response):  # type: ignore[override]
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return response

    return app
