"""AgriAuction application factory.

create_app() builds and returns the Flask application.
A factory is used so tests and production (Gunicorn) can create the app
the same way without running the development server.
"""

import logging
import os
from datetime import timedelta

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

    # Session cookies: HttpOnly and SameSite always. Secure only on HTTPS
    # (production). Local http://127.0.0.1 must keep Secure off or the
    # browser will not store the cookie.
    is_production = os.getenv("FLASK_ENV") == "production"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = is_production
    app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=14)

    if is_production:
        app.config["DEBUG"] = False
        app.logger.setLevel(logging.INFO)

    from app.database import init_app as init_db_app, load_db_config

    app.config.update(load_db_config())
    init_db_app(app)

    from app.auth import current_session_user
    from app.csrf import csrf_token, validate_csrf
    from app.helpers import dt_local
    from app.nav import items_for_role
    from app.utils import format_zmw

    @app.context_processor
    def inject_template_globals():
        user = current_session_user()
        return {
            "current_user": user,
            "nav_items": items_for_role(user["role"] if user else None),
            "csrf_token": csrf_token(),
            "format_zmw": format_zmw,
            "dt_local": dt_local,
        }

    @app.template_filter("zmw")
    def zmw_filter(value):
        return format_zmw(value)

    app.before_request(validate_csrf)

    from app.routes.main import main_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.farmers import farmers_bp
    from app.routes.buyers import buyers_bp
    from app.routes.catalogue import produce_bp, grades_bp, depots_bp
    from app.routes.lots import lots_bp
    from app.routes.bids import bids_bp
    from app.routes.auctions import auctions_bp
    from app.routes.sales import sales_bp
    from app.routes.payments import payments_bp
    from app.routes.collections import collections_bp
    from app.routes.reports import reports_bp
    from app.routes.staff import staff_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(farmers_bp)
    app.register_blueprint(buyers_bp)
    app.register_blueprint(produce_bp)
    app.register_blueprint(grades_bp)
    app.register_blueprint(depots_bp)
    app.register_blueprint(lots_bp)
    app.register_blueprint(bids_bp)
    app.register_blueprint(auctions_bp)
    app.register_blueprint(sales_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(collections_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(staff_bp)

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
        app.logger.exception("Unhandled server error")
        return render_template("errors/500.html"), 500
