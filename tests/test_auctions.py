"""Phase 15: auction close uses the stored procedure and UNIQUE(lot_id)."""

import unittest
from pathlib import Path
from unittest.mock import patch

from app import create_app
from tests.support import CSRF, sign_in


class AuctionCloseTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret"
        self.client = self.app.test_client()
        sign_in(self.client, role="AUCTION_CLERK", username="tembo.clerk", user_id=3)

    @patch("app.routes.auctions.callproc")
    @patch("app.routes.auctions.query_one")
    def test_highest_bid_path_calls_procedure(self, mock_one, mock_call):
        mock_one.return_value = {
            "lot_id": 16,
            "lot_number": "LOT-2026-0016",
            "status": "OPEN",
        }
        mock_call.return_value = [
            {
                "lot_status": "SOLD",
                "sale_reference": "SAL-TEST",
                "message": "Auction closed — winner recorded",
            }
        ]
        response = self.client.post(
            "/auctions/16/close",
            data={"_csrf": CSRF},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        mock_call.assert_called_once_with("sp_close_auction", (16,))

    @patch("app.routes.auctions.callproc")
    @patch("app.routes.auctions.query_one")
    def test_no_bids_shows_no_winner(self, mock_one, mock_call):
        mock_one.return_value = {
            "lot_id": 13,
            "lot_number": "LOT-2026-0013",
            "status": "OPEN",
        }
        mock_call.return_value = [
            {"lot_status": "UNSOLD", "message": "Auction closed — no winner"}
        ]
        response = self.client.post(
            "/auctions/13/close",
            data={"_csrf": CSRF},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/auctions/13/result"))
        mock_call.assert_called_once_with("sp_close_auction", (13,))

    @patch("app.routes.auctions.callproc")
    @patch("app.routes.auctions.query_one")
    def test_duplicate_sale_blocked_when_already_sold(self, mock_one, mock_call):
        mock_one.return_value = {
            "lot_id": 5,
            "lot_number": "LOT-2026-0005",
            "status": "SOLD",
        }
        response = self.client.post(
            "/auctions/5/close",
            data={"_csrf": CSRF},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        mock_call.assert_not_called()

    def test_schema_has_unique_lot_id_on_sales(self):
        schema = Path("database/schema.sql").read_text(encoding="utf-8")
        self.assertIn("UNIQUE KEY uq_sales_lot_id (lot_id)", schema)

    def test_procedure_uses_transaction_and_rollback(self):
        sql = Path("database/procedures.sql").read_text(encoding="utf-8")
        self.assertIn("START TRANSACTION", sql)
        self.assertIn("FOR UPDATE", sql)
        self.assertIn("ROLLBACK", sql)
        self.assertIn("COMMIT", sql)


if __name__ == "__main__":
    unittest.main()
