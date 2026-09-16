"""Phase 8: staff login, session, and role checks."""

import unittest
from unittest.mock import patch

import bcrypt

from app import create_app


def _hash(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=4)).decode("utf-8")


class AuthTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret"
        self.client = self.app.test_client()
        self.password = "Admin#2026"
        self.admin = {
            "staff_id": 1,
            "username": "chanda.admin",
            "password_hash": _hash(self.password),
            "role": "ADMIN",
            "is_active": 1,
        }
        self.viewer = {
            "staff_id": 5,
            "username": "banda.viewer",
            "password_hash": _hash("Viewer#2026"),
            "role": "VIEWER",
            "is_active": 1,
        }

    def test_session_cookie_flags(self):
        self.assertTrue(self.app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(self.app.config["SESSION_COOKIE_SAMESITE"], "Lax")
        self.assertFalse(self.app.config["SESSION_COOKIE_SECURE"])

    def test_dashboard_requires_login(self):
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

    @patch("app.routes.main.find_staff_by_username")
    def test_login_creates_session_and_redirects(self, mock_find):
        mock_find.return_value = self.admin
        response = self.client.post(
            "/login",
            data={"username": "chanda.admin", "password": self.password},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/dashboard"))
        with self.client.session_transaction() as sess:
            self.assertEqual(sess["user_id"], 1)
            self.assertEqual(sess["username"], "chanda.admin")
            self.assertEqual(sess["role"], "ADMIN")
            self.assertNotIn("password_hash", sess)

    @patch("app.routes.main.find_staff_by_username")
    def test_wrong_password_does_not_create_session(self, mock_find):
        mock_find.return_value = self.admin
        response = self.client.post(
            "/login",
            data={"username": "chanda.admin", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid username or password", response.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

    @patch("app.routes.main.find_staff_by_username")
    def test_inactive_staff_cannot_login(self, mock_find):
        inactive = dict(self.admin)
        inactive["is_active"] = 0
        mock_find.return_value = inactive
        response = self.client.post(
            "/login",
            data={"username": "chanda.admin", "password": self.password},
        )
        self.assertIn(b"inactive", response.data)
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

    @patch("app.routes.main.find_staff_by_username")
    def test_logout_clears_session(self, mock_find):
        mock_find.return_value = self.admin
        self.client.post(
            "/login",
            data={"username": "chanda.admin", "password": self.password},
        )
        response = self.client.post("/logout", follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        with self.client.session_transaction() as sess:
            self.assertNotIn("user_id", sess)

    def test_administration_forbidden_for_viewer(self):
        """VIEWER is blocked even when they request the URL directly."""
        with self.client.session_transaction() as sess:
            sess["user_id"] = 5
            sess["username"] = "banda.viewer"
            sess["role"] = "VIEWER"
        response = self.client.get("/administration")
        self.assertEqual(response.status_code, 403)

    def test_administration_allowed_for_admin(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "chanda.admin"
            sess["role"] = "ADMIN"
        response = self.client.get("/administration")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Administration", response.data)

    @patch("app.routes.main.find_staff_by_username")
    def test_open_redirect_is_rejected(self, mock_find):
        mock_find.return_value = self.admin
        response = self.client.post(
            "/login",
            data={
                "username": "chanda.admin",
                "password": self.password,
                "next": "https://evil.example",
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/dashboard"))


if __name__ == "__main__":
    unittest.main()
