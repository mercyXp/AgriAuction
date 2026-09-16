"""Shared helpers for Flask test_client sessions."""

CSRF = "test-csrf-token"


def sign_in(client, role="ADMIN", username="chanda.admin", user_id=1):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["username"] = username
        sess["role"] = role
        sess["_csrf"] = CSRF
    return CSRF
