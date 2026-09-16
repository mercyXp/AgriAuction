"""Phase 14: bidding rules."""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app import create_app
from app.routes.bids import validate_bid
from tests.support import CSRF, sign_in


class BidRuleTests(unittest.TestCase):
    def setUp(self):
        self.lot = {
            "lot_id": 16,
            "status": "OPEN",
            "minimum_bid_price": Decimal("500.00"),
            "auction_end": datetime(2030, 1, 1, 12, 0, 0),
        }
        self.buyer = {"buyer_id": 1, "is_active": 1}

    def test_valid_bid(self):
        error = validate_bid(self.lot, self.buyer, Decimal("600.00"), datetime(2026, 9, 16))
        self.assertIsNone(error)

    def test_reject_below_minimum(self):
        error = validate_bid(self.lot, self.buyer, Decimal("100.00"), datetime(2026, 9, 16))
        self.assertIn("at least", error)

    def test_reject_closed_lot(self):
        closed = dict(self.lot)
        closed["status"] = "SOLD"
        error = validate_bid(closed, self.buyer, Decimal("600.00"), datetime(2026, 9, 16))
        self.assertIn("already closed", error)


class BidRouteTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret"
        self.client = self.app.test_client()
        sign_in(self.client, role="AUCTION_CLERK", username="tembo.clerk", user_id=3)

    @patch("app.routes.bids.query_all", return_value=[])
    @patch("app.routes.bids.get_db")
    @patch("app.routes.bids.query_one")
    def test_post_rejects_sold_lot(self, mock_one, mock_db, _all):
        mock_db.return_value = MagicMock()
        mock_one.side_effect = [
            {
                "lot_id": 1,
                "status": "SOLD",
                "minimum_bid_price": Decimal("500.00"),
                "auction_end": datetime(2030, 1, 1),
            },
            {"buyer_id": 1, "is_active": 1},
        ]
        response = self.client.post(
            "/bids/create",
            data={
                "lot_id": "1",
                "buyer_id": "1",
                "bid_amount": "600",
                "_csrf": CSRF,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"already closed", response.data)
        mock_db.return_value.rollback.assert_called()


if __name__ == "__main__":
    unittest.main()
