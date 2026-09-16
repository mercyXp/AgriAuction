"""Phase 13: produce lot validation and create."""

import unittest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch

from app import create_app
from app.routes.lots import validate_lot
from tests.support import CSRF, sign_in


class LotTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret"
        self.client = self.app.test_client()
        sign_in(self.client)

    def _active_lookups(self, mock_one):
        mock_one.side_effect = [
            {"is_active": 1},
            {"is_active": 1, "unit_of_measure": "tonne"},
            {"is_active": 1},
            {"is_active": 1},
        ]

    def test_reject_invalid_window(self):
        with self.app.app_context():
            with patch("app.routes.lots.query_one") as mock_one:
                self._active_lookups(mock_one)
                _data, errors = validate_lot(
                    {
                        "farmer_id": "1",
                        "produce_type_id": "1",
                        "grade_id": "1",
                        "depot_id": "1",
                        "quantity": "12.5",
                        "inspection_date": "2026-09-01",
                        "auction_start": "2026-09-20T10:00",
                        "auction_end": "2026-09-20T09:00",
                        "minimum_bid_price": "500",
                    }
                )
        self.assertIn("auction_end", errors)

    def test_reject_zero_quantity(self):
        with self.app.app_context():
            with patch("app.routes.lots.query_one") as mock_one:
                self._active_lookups(mock_one)
                _data, errors = validate_lot(
                    {
                        "farmer_id": "1",
                        "produce_type_id": "1",
                        "grade_id": "1",
                        "depot_id": "1",
                        "quantity": "0",
                        "inspection_date": "2026-09-01",
                        "auction_start": "2026-09-20T08:00",
                        "auction_end": "2026-09-21T08:00",
                        "minimum_bid_price": "500",
                    }
                )
        self.assertIn("quantity", errors)

    @patch("app.routes.lots._lookups")
    @patch("app.routes.lots.next_lot_number", return_value="LOT-2026-0019")
    @patch("app.routes.lots.execute", return_value=(19, 1))
    @patch("app.routes.lots.query_one")
    def test_create_valid_lot(self, mock_one, mock_execute, _code, mock_lookups):
        mock_lookups.return_value = {
            "farmers": [],
            "produce_types": [],
            "grades": [],
            "depots": [],
        }
        mock_one.side_effect = [
            {"is_active": 1},
            {"is_active": 1, "unit_of_measure": "tonne"},
            {"is_active": 1},
            {"is_active": 1},
        ]
        response = self.client.post(
            "/lots/create",
            data={
                "farmer_id": "1",
                "produce_type_id": "1",
                "grade_id": "1",
                "depot_id": "1",
                "quantity": "12.500",
                "inspection_date": "2026-09-01",
                "auction_start": "2026-09-20T08:00",
                "auction_end": "2026-09-21T16:00",
                "minimum_bid_price": "500.00",
                "_csrf": CSRF,
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        sql = mock_execute.call_args[0][0]
        self.assertIn("INSERT INTO produce_lots", sql)
        self.assertIn("REGISTERED", sql)
        params = mock_execute.call_args[0][1]
        self.assertEqual(params[5], Decimal("12.500"))
        self.assertIsInstance(params[7], date)
        self.assertIsInstance(params[8], datetime)


if __name__ == "__main__":
    unittest.main()
