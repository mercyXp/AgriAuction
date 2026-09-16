"""Signed-in staff home. Full dashboard chrome is added in a later phase."""

from flask import Blueprint, render_template, session

from app.auth import login_required, role_label, role_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def index():
    """Landing page after a successful staff login."""
    return render_template(
        "dashboard.html",
        role_label=role_label(session.get("role")),
    )


@dashboard_bp.route("/administration")
@role_required("ADMIN")
def administration():
    """ADMIN-only page so role checks are enforced on the server."""
    return render_template("administration.html")
