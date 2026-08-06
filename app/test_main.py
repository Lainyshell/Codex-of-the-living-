import tempfile
import unittest
from pathlib import Path

from main import app, load_source_rows, parse_decimal


class TestShippingReportEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_default_source_is_verified_transactions(self):
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

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["status"], "error")

    def test_shipping_import_persists_normalized_transactions(self):
        response = self.client.post(
            "/api/shipping-import",
            json={"source": "Schedule_Q_Disbursement_Ledger___Issue_001.csv"},
        )

        self.assertEqual(response.status_code, 201)
        payload = response.get_json()
        self.assertEqual(payload["status"], "imported")
        self.assertEqual(payload["source_file"], "Schedule_Q_Disbursement_Ledger___Issue_001.csv")
        self.assertEqual(payload["transaction_count"], 4)

        batch_response = self.client.get(
            f"/api/shipping-import/{payload['import_batch_id']}"
        )
        self.assertEqual(batch_response.status_code, 200)
        batch_payload = batch_response.get_json()
        self.assertEqual(batch_payload["import_batch"]["transaction_count"], 4)
        self.assertEqual(batch_payload["transactions"][0]["recipient"], "Alaina Padgett")
        self.assertTrue(batch_payload["transactions"][0]["amount_valid"])

    def test_shipping_import_rejects_out_of_repo_paths(self):
        response = self.client.post(
            "/api/shipping-import",
            json={"source": "../README.md"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["status"], "error")


class TestShippingReportHelper(unittest.TestCase):
    def test_parse_decimal_handles_supported_and_invalid_values(self):
        self.assertEqual(str(parse_decimal("1,234.50")), "1234.50")
        self.assertIsNone(parse_decimal("TBD"))
        self.assertIsNone(parse_decimal(None))

    def test_load_source_rows_rejects_unsupported_extensions(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as handle:
            handle.write(b"unsupported")
            temp_path = Path(handle.name)

        try:
            with self.assertRaises(ValueError):
                load_source_rows(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
