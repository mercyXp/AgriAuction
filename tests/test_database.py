"""Phase 7: MySQL connection, failure, and cleanup."""

import unittest
from unittest.mock import MagicMock, patch

from app import create_app
from app.database import get_db, ping_db, query_one


class DatabaseConnectionTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True

    def _fake_connection(self):
        db = MagicMock()
        db.is_connected.return_value = True

        def close():
            db.is_connected.return_value = False

        db.close.side_effect = close

        cursor = MagicMock()
        cursor.fetchone.return_value = {"ok": 1, "n": 7}
        db.cursor.return_value = cursor
        return db

    @patch("app.database.mysql.connector.connect")
    def test_successful_connection(self, mock_connect):
        fake = self._fake_connection()
        mock_connect.return_value = fake

        with self.app.app_context():
            self.assertTrue(ping_db())
            row = query_one("SELECT %s AS n", (7,))
            self.assertEqual(row["n"], 7)
            self.assertIs(get_db(), fake)
            self.assertTrue(get_db().is_connected())

        mock_connect.assert_called_once()
        kwargs = mock_connect.call_args.kwargs
        self.assertEqual(kwargs["user"], self.app.config["DB_USER"])
        self.assertEqual(kwargs["database"], self.app.config["DB_NAME"])
        self.assertEqual(kwargs["password"], self.app.config["DB_PASSWORD"])

    def test_failed_connection(self):
        self.app.config["DB_USER"] = "agriauction_app"
        self.app.config["DB_PASSWORD"] = "wrong-password-phase7-test"
        with self.app.app_context():
            with self.assertRaises(RuntimeError) as ctx:
                get_db()
        self.assertIn("Could not connect to MySQL", str(ctx.exception))

    @patch("app.database.mysql.connector.connect")
    def test_connection_cleanup(self, mock_connect):
        fake = self._fake_connection()
        mock_connect.return_value = fake

        with self.app.app_context():
            db = get_db()
            self.assertTrue(db.is_connected())

        fake.close.assert_called_once()
        self.assertFalse(db.is_connected())

    def test_params_must_be_a_tuple(self):
        with self.app.app_context():
            with self.assertRaises(TypeError):
                query_one("SELECT %s AS n", 7)

    def test_public_pages_do_not_need_mysql(self):
        client = self.app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_live_mysql_if_account_exists(self):
        try:
            with self.app.app_context():
                self.assertTrue(ping_db())
                db = get_db()
                self.assertTrue(db.is_connected())
            self.assertFalse(db.is_connected())
        except RuntimeError as err:
            self.skipTest(
                "Create agriauction_app (Phase 6) and set DB_PASSWORD in .env. "
                f"Current error: {err}"
            )


if __name__ == "__main__":
    unittest.main()
