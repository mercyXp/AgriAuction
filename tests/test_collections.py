"""Phase 18: collections require a fully paid sale."""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app import create_app
from tests.support import CSRF, sign_in


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret"
        self.client = self.app.test_client()
        sign_in(self.client, role="FINANCE", username="zulu.finance", user_id=4)

    @patch("app.routes.collections.next_timed_reference", return_value="COL-TEST-1")
    @patch("app.routes.collections.execute")
    @patch("app.routes.collections.get_db")
    @patch("app.routes.collections.query_one")
    @patch("app.routes.collections.query_all", return_value=[])
    def test_valid_collection(self, _all, mock_one, mock_db, mock_execute, _ref):
        db = MagicMock()
        mock_db.return_value = db
        mock_one.side_effect = [
            {"sale_id": 8, "status": "PAID", "lot_id": 8, "quantity": Decimal("10")},
            None,
        ]
        mock_execute.return_value = (1, 1)
        response = self.client.post(
            "/collections/create",
            data={
                "sale_id": "8",
                "collected_quantity": "10",
                "collection_date": "2026-09-16T11:00",
                "collected_by": "Depot clerk Mwansa",
                "notes": "",
                "_csrf": CSRF,
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        db.commit.assert_called()
        sql_joined = " ".join(call.args[0] for call in mock_execute.call_args_list)
        self.assertIn("INSERT INTO collections", sql_joined)
        self.assertIn("COLLECTED", sql_joined)

    @patch("app.routes.collections.get_db")
    @patch("app.routes.collections.query_one")
    @patch("app.routes.collections.query_all", return_value=[])
    def test_unpaid_sale_rejected(self, _all, mock_one, mock_db):
        db = MagicMock()
        mock_db.return_value = db
        mock_one.return_value = {
            "sale_id": 2,
            "status": "PAYMENT_PENDING",
            "lot_id": 2,
            "quantity": Decimal("10"),
        }
        response = self.client.post(
            "/collections/create",
            data={
                "sale_id": "2",
                "collected_quantity": "10",
                "collection_date": "2026-09-16T11:00",
                "collected_by": "Depot clerk Mwansa",
                "notes": "",
                "_csrf": CSRF,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"fully paid", response.data)
        db.commit.assert_not_called()
        db.rollback.assert_called()


if __name__ == "__main__":
    unittest.main()
