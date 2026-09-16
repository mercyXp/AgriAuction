"""Phase 17: payments go through sp_record_payment."""

import unittest
from unittest.mock import patch

from mysql.connector import Error as MySQLError

from app import create_app
from tests.support import CSRF, sign_in


class PaymentTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.app.config["SECRET_KEY"] = "test-secret"
        self.client = self.app.test_client()
        sign_in(self.client, role="FINANCE", username="zulu.finance", user_id=4)

    @patch("app.routes.payments.next_timed_reference", return_value="PAY-TEST-1")
    @patch("app.routes.payments.callproc")
    @patch("app.routes.payments.query_all", return_value=[])
    def test_valid_payment(self, _all, mock_call, _ref):
        mock_call.return_value = [{"message": "Payment recorded", "sale_status": "PAID"}]
        response = self.client.post(
            "/payments/create",
            data={
                "sale_id": "11",
                "amount": "100.00",
                "payment_method": "BANK_TRANSFER",
                "payment_date": "2026-09-16T10:00",
                "status": "VERIFIED",
                "_csrf": CSRF,
            },
            follow_redirects=False,
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(mock_call.call_args[0][0], "sp_record_payment")

    @patch("app.routes.payments.callproc")
    @patch("app.routes.payments.query_all", return_value=[])
    def test_overpayment_rejected(self, _all, mock_call):
        err = MySQLError(msg="Payment exceeds the outstanding balance.")
        err.errno = 1644
        err.sqlstate = "45000"
        mock_call.side_effect = err
        response = self.client.post(
            "/payments/create",
            data={
                "sale_id": "6",
                "amount": "1.00",
                "payment_method": "CASH",
                "payment_date": "2026-09-16T10:00",
                "status": "VERIFIED",
                "_csrf": CSRF,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Payment exceeds the outstanding balance", response.data)


if __name__ == "__main__":
    unittest.main()
