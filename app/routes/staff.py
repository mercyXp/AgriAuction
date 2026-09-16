"""Staff list for ADMIN. Application users, not MySQL accounts."""

from flask import Blueprint, flash, render_template

from app.auth import ROLE_LABELS, role_required
from app.database import query_all

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/")
@role_required("ADMIN")
def index():
    try:
        people = query_all(
            """
            SELECT staff_id, username, email, first_name, last_name, role, is_active, created_at
            FROM staff
            ORDER BY role, last_name, first_name
            """,
            (),
        )
    except RuntimeError:
        flash("Cannot reach the database. Check MySQL and .env.", "danger")
        people = []
    return render_template("staff/index.html", people=people, labels=ROLE_LABELS)
