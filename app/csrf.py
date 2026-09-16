"""Simple CSRF token for authenticated POST forms."""

import secrets

from flask import abort, request, session


def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def validate_csrf():
    """Reject forged POST requests from signed-in staff."""
    if request.method != "POST":
        return
    if request.endpoint in (None, "static"):
        return
    if not session.get("user_id"):
        return
    sent = request.form.get("_csrf")
    if not sent or sent != session.get("_csrf"):
        abort(400)
