"""AgriAuction application factory.

create_app() builds and returns the Flask application.
A factory is used so tests and production (Gunicorn) can create the app
the same way without running the development server.
"""

import os

from dotenv import load_dotenv
from flask import Flask

load_dotenv()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "development")

    # Database settings are loaded now so later phases can use them.
    # The actual MySQL connection is implemented in Phase 7.
    from app.database import load_db_config

    app.config.update(load_db_config())

    from app.routes.main import main_bp

    app.register_blueprint(main_bp)

    register_error_handlers(app)

    return app


def register_error_handlers(app):
    """Show friendly HTML pages instead of Flask's default error text."""
    from flask import render_template

    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html"), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html"), 500
