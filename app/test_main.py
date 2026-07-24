import unittest

from main import app


class ShippingReportEndpointTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_default_shipping_report_uses_verified_transactions_template(self):
        response = self.client.get("/shipping-report")

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["source_file"], "Verified_Transactions_Template.xlsx")
        self.assertEqual(payload["transaction_count"], 2)
        self.assertEqual(payload["total_amount"], 200000.0)
        self.assertEqual(payload["transactions"][0]["recipient"], "Judge Simcoe")

    def test_shipping_report_maps_csv_ledger_fields(self):
        response = self.client.get(
            "/shipping-report?source=Schedule_Q_Disbursement_Ledger___Issue_001.csv"
        )

        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["transaction_count"], 4)
        self.assertEqual(payload["transactions"][0]["recipient"], "Alaina Padgett")
        self.assertEqual(
            payload["transactions"][0]["transaction_type"],
            "Postmaster General & Trustee",
        )

    def test_shipping_report_can_render_csv_output(self):
        response = self.client.get("/shipping-report?format=csv")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")
        body = response.get_data(as_text=True)
        self.assertIn("line_number,recipient,address,date_of_delivery", body)
        self.assertIn("Judge Simcoe", body)

    def test_shipping_report_rejects_out_of_repo_paths(self):
        response = self.client.get("/shipping-report?source=../README.md")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["status"], "error")


if __name__ == "__main__":
    unittest.main()
