"""Phase 9–10: dashboard navigation and farmer CRUD."""

import unittest
from unittest.mock import patch

from app import create_app
from app.routes.farmers import validate_farmer
from tests.support import CSRF


class DashboardNavTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret"
        self.client = self.app.test_client()

    def _login(self, role, username="chanda.admin", user_id=1):
        with self.client.session_transaction() as sess:
            sess["user_id"] = user_id
            sess["username"] = username
            sess["role"] = role
            sess["_csrf"] = "test-csrf-token"

    def test_admin_sees_farmers_and_administration(self):
        self._login("ADMIN")
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'href="/farmers/"', response.data)
        self.assertIn(b'href="/administration"', response.data)
        self.assertIn(b"app-sidebar", response.data)

    def test_viewer_does_not_get_farmers_link(self):
        self._login("VIEWER", "banda.viewer", 5)
        response = self.client.get("/dashboard")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'href="/farmers/"', response.data)
        self.assertIn(b'href="/reports/"', response.data)

    def test_viewer_forbidden_on_farmers_url(self):
        self._login("VIEWER", "banda.viewer", 5)
        response = self.client.get("/farmers/")
        self.assertEqual(response.status_code, 403)

    def test_clerk_forbidden_on_farmers_url(self):
        self._login("AUCTION_CLERK", "tembo.clerk", 3)
        response = self.client.get("/farmers/")
        self.assertEqual(response.status_code, 403)

    def test_operator_forbidden_on_administration(self):
        self._login("OPERATOR", "mwansa.operator", 2)
        response = self.client.get("/administration")
        self.assertEqual(response.status_code, 403)


class FarmerCrudTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret"
        self.client = self.app.test_client()
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "chanda.admin"
            sess["role"] = "ADMIN"
            sess["_csrf"] = CSRF
        self.sample = {
            "farmer_id": 1,
            "farmer_code": "FRM-0001",
            "first_name": "Joseph",
            "last_name": "Mutale",
            "phone": "0977110001",
            "email": "j.mutale@farms-demo.zm",
            "address": "Plot 12, Chongwe Road, Lusaka",
            "farm_name": "Green Valley Farm",
            "registration_date": "2024-01-15",
            "is_active": 1,
        }

    def test_validate_rejects_short_name(self):
        data, errors = validate_farmer(
            {
                "first_name": "J",
                "last_name": "Mutale",
                "phone": "0977110001",
                "email": "",
                "address": "Plot 12 Lusaka",
                "farm_name": "Green Valley",
                "registration_date": "2024-01-15",
            }
        )
        self.assertIn("first_name", errors)

    @patch("app.routes.farmers.query_all")
    def test_list_farmers(self, mock_all):
        mock_all.return_value = [self.sample]
        response = self.client.get("/farmers/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FRM-0001", response.data)
        self.assertIn(b"Green Valley Farm", response.data)

    @patch("app.routes.farmers.query_all")
    def test_search_passes_like_params(self, mock_all):
        mock_all.return_value = []
        self.client.get("/farmers/", query_string={"q": "Phiri", "status": "active"})
        sql, params = mock_all.call_args[0]
        self.assertIn("LIKE", sql)
        self.assertIn("is_active = 1", sql)
        self.assertEqual(params[0], "Phiri")
        self.assertEqual(params[1], "%Phiri%")

    @patch("app.routes.farmers.next_farmer_code", return_value="FRM-0013")
    @patch("app.routes.farmers.execute", return_value=(13, 1))
    def test_create_farmer(self, mock_execute, _mock_code):
        response = self.client.post(
            "/farmers/create",
            data={
                "first_name": "Linda",
                "last_name": "Phiri",
                "phone": "0977110099",
                "email": "",
                "address": "Chipata District",
                "farm_name": "New Dawn Farm",
                "registration_date": "2026-09-16",
                "_csrf": CSRF,
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/farmers/13"))
        sql = mock_execute.call_args[0][0]
        self.assertIn("INSERT INTO farmers", sql)
        self.assertNotIn("DELETE", sql)

    @patch("app.routes.farmers.farmer_lot_count", return_value=2)
    @patch("app.routes.farmers.query_one")
    def test_view_farmer(self, mock_one, _lots):
        mock_one.return_value = self.sample
        response = self.client.get("/farmers/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Green Valley Farm", response.data)
        self.assertIn(b"Deactivate", response.data)

    @patch("app.routes.farmers.execute")
    @patch("app.routes.farmers.query_one")
    def test_edit_farmer(self, mock_one, mock_execute):
        mock_one.return_value = self.sample
        mock_execute.return_value = (0, 1)
        response = self.client.post(
            "/farmers/1/edit",
            data={
                "first_name": "Joseph",
                "last_name": "Mutale",
                "phone": "0977110001",
                "email": "j.mutale@farms-demo.zm",
                "address": "Plot 12, Chongwe Road, Lusaka",
                "farm_name": "Green Valley Farm",
                "registration_date": "2024-01-15",
                "_csrf": CSRF,
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        sql = mock_execute.call_args[0][0]
        self.assertIn("UPDATE farmers", sql)

    @patch("app.routes.farmers.farmer_lot_count", return_value=3)
    @patch("app.routes.farmers.execute")
    @patch("app.routes.farmers.query_one")
    def test_deactivate_does_not_delete(self, mock_one, mock_execute, _lots):
        mock_one.return_value = self.sample
        mock_execute.return_value = (0, 1)
        response = self.client.post(
            "/farmers/1/deactivate",
            data={"_csrf": CSRF},
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        sql = mock_execute.call_args[0][0]
        self.assertIn("is_active = 0", sql)
        self.assertNotIn("DELETE", sql.upper())


if __name__ == "__main__":
    unittest.main()
