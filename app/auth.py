"""Staff authentication and server-side authorization.

Application users live in the staff table. MySQL users (agriauction_app)
are a different thing — see docs/security.md.

Session cookies store only:
    user_id, username, role
"""

from functools import wraps

import bcrypt
from flask import abort, flash, redirect, request, session, url_for

from app.database import query_one

# Roles that exist on staff.role (MySQL ENUM).
ROLES = ("ADMIN", "OPERATOR", "AUCTION_CLERK", "FINANCE", "VIEWER")

ROLE_LABELS = {
    "ADMIN": "Administrator",
    "OPERATOR": "Operator",
    "AUCTION_CLERK": "Auction clerk",
    "FINANCE": "Finance",
    "VIEWER": "Viewer",
}


def role_label(role):
    """Human-readable role name for templates."""
    return ROLE_LABELS.get(role, role or "")


def password_matches(plain_password, password_hash):
    """Return True if the plain password matches the stored bcrypt hash."""
    if not plain_password or not password_hash:
        return False
    try:
        hashed = (
            password_hash.encode("utf-8")
            if isinstance(password_hash, str)
            else password_hash
        )
        if len(plain_password.encode("utf-8")) > 72:
            return False
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed)
    except (ValueError, TypeError):
        return False


def find_staff_by_username(username):
    """Look up a staff row by username. Password hash is included for login."""
    return query_one(
        """
        SELECT staff_id, username, password_hash, role, is_active
        FROM staff
        WHERE username = %s
        """,
        (username,),
    )


def login_user(staff, remember=False):
    """Store the signed-in staff member in the Flask session."""
    session.clear()
    session["user_id"] = staff["staff_id"]
    session["username"] = staff["username"]
    session["role"] = staff["role"]
    session.permanent = bool(remember)


def logout_user():
    """Remove staff identity from the session."""
    session.clear()


def current_session_user():
    """Session identity for templates, or None if signed out."""
    if not session.get("user_id"):
        return None
    return {
        "user_id": session.get("user_id"),
        "username": session.get("username"),
        "role": session.get("role"),
        "role_label": role_label(session.get("role")),
    }


def safe_next_url(fallback):
    """Allow only same-site relative paths (no open redirects)."""
    target = request.args.get("next") or request.form.get("next")
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return fallback


def login_required(view):
    """Redirect anonymous users to the login page."""

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("main.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    """Allow only the listed staff roles. Returns 403 otherwise.

    Authorization is enforced here, not by hiding links in HTML.
    """

    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
