"""Public pages that do not require a login."""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from app.auth import (
    find_staff_by_username,
    login_user,
    logout_user,
    password_matches,
    safe_next_url,
)
from app.database import MySQLError

main_bp = Blueprint("main", __name__)

# Replace placeholder names and roles in this list when the group is confirmed.
TEAM_MEMBERS = [
    {
        "placeholder": "GROUP MEMBER 1",
        "programme": "Computer Science Student",
        "role": "ROLE",
    },
    {
        "placeholder": "GROUP MEMBER 2",
        "programme": "Computer Science Student",
        "role": "ROLE",
    },
    {
        "placeholder": "GROUP MEMBER 3",
        "programme": "Computer Science Student",
        "role": "ROLE",
    },
    {
        "placeholder": "GROUP MEMBER 4",
        "programme": "Computer Science Student",
        "role": "ROLE",
    },
]


@main_bp.route("/")
def home():
    """Public landing page. No private dashboard data is shown here."""
    return render_template("home.html", team_members=TEAM_MEMBERS)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    """Staff login: look up the account, check bcrypt, start a session."""
    if session.get("user_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        remember = bool(request.form.get("remember"))

        if not username or not password:
            flash("Enter your username and password.", "danger")
            return render_template("login.html", username=username)

        try:
            staff = find_staff_by_username(username)
        except RuntimeError:
            flash(
                "Cannot reach the database. Check that MySQL is running and .env is set.",
                "danger",
            )
            return render_template("login.html", username=username)
        except MySQLError:
            flash("A database error occurred while signing in.", "danger")
            return render_template("login.html", username=username)

        if staff is None or not password_matches(password, staff["password_hash"]):
            flash("Invalid username or password.", "danger")
            return render_template("login.html", username=username)

        if not staff["is_active"]:
            flash("This staff account is inactive. Contact an administrator.", "danger")
            return render_template("login.html", username=username)

        login_user(staff, remember=remember)
        flash("Signed in successfully.", "success")
        return redirect(safe_next_url(url_for("dashboard.index")))

    return render_template("login.html", username="")


@main_bp.route("/logout", methods=["POST"])
def logout():
    """End the staff session."""
    logout_user()
    flash("You have been signed out.", "success")
    return redirect(url_for("main.login"))
