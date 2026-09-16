"""Public pages that do not require a login."""

from flask import Blueprint, flash, redirect, render_template, request, url_for

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
    """Public login page — the entry point to the management system.

    Password checking and sessions are implemented in a later phase.
    Submitting the form does not sign anyone in.
    """
    if request.method == "POST":
        flash(
            "Staff login will be enabled in the authentication phase. No account was signed in.",
            "info",
        )
        return redirect(url_for("main.login"))
    return render_template("login.html")
