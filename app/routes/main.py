"""Public pages that do not require a login yet."""

from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    """Landing page for AgriAuction."""
    return render_template("home.html")
