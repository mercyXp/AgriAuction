"""Phase 11: buyer CRUD."""

import unittest
from unittest.mock import patch

from app import create_app
from app.routes.buyers import validate_buyer
from tests.support import CSRF, sign_in


class BuyerCrudTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret"
        self.client = self.app.test_client()
        sign_in(self.client)
        self.sample = {
            "buyer_id": 1,
            "buyer_code": "BUY-0001",
            "business_name": "Lusaka Grain Traders",
            "contact_person": "Mary Banda",
            "phone": "0977220001",
            "email": "mary@traders-demo.zm",
            "address": "Cairo Road, Lusaka",
            "registration_date": "2024-02-01",
            "is_active": 1,
        }

    def test_validate_rejects_short_name(self):
        _data, errors = validate_buyer(
            {
                "business_name": "A",
                "contact_person": "Mary Banda",
                "phone": "0977220001",
                "email": "",
                "address": "Cairo Road Lusaka",
                "registration_date": "2024-02-01",
            }
        )
        self.assertIn("business_name", errors)

    @patch("app.routes.buyers.query_all")
    def test_list_buyers(self, mock_all):
        mock_all.return_value = [self.sample]
        response = self.client.get("/buyers/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"BUY-0001", response.data)

    @patch("app.routes.buyers.next_code", return_value="BUY-0013")
    @patch("app.routes.buyers.execute", return_value=(13, 1))
    def test_create_buyer(self, mock_execute, _code):
        response = self.client.post(
            "/buyers/create",
            data={
                "business_name": "Chipata Mills",
                "contact_person": "Peter Zulu",
                "phone": "0977220099",
                "email": "",
                "address": "Umodzi Highway, Chipata",
                "registration_date": "2026-09-16",
                "_csrf": CSRF,
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("INSERT INTO buyers", mock_execute.call_args[0][0])

    @patch("app.routes.buyers.execute", return_value=(0, 1))
    @patch("app.routes.buyers.query_one")
    def test_edit_buyer(self, mock_one, mock_execute):
        mock_one.return_value = self.sample
        response = self.client.post(
            "/buyers/1/edit",
            data={
                "business_name": "Lusaka Grain Traders",
                "contact_person": "Mary Banda",
                "phone": "0977220001",
                "email": "mary@traders-demo.zm",
                "address": "Cairo Road, Lusaka",
                "registration_date": "2024-02-01",
                "_csrf": CSRF,
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("UPDATE buyers", mock_execute.call_args[0][0])

    @patch("app.routes.buyers.buyer_history_count", return_value=4)
    @patch("app.routes.buyers.execute", return_value=(0, 1))
    @patch("app.routes.buyers.query_one")
    def test_deactivate_does_not_delete(self, mock_one, mock_execute, _hist):
        mock_one.return_value = self.sample
        response = self.client.post(
            "/buyers/1/deactivate",
            data={"_csrf": CSRF},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        sql = mock_execute.call_args[0][0]
        self.assertIn("is_active = 0", sql)
        self.assertNotIn("DELETE", sql.upper())


if __name__ == "__main__":
    unittest.main()
