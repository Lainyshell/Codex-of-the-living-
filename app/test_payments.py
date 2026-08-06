"""
Test suite — scan-based payments: REMIC calculations and API endpoints.

Run with:
    cd app && pip install -r requirements.txt && python -m unittest test_payments -v
"""

import json
import os
import sys
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Ensure app/ is on the path when tests are run from repo root or app/
# ---------------------------------------------------------------------------
_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

# Use an in-memory / temp DB for tests
os.environ.setdefault("PAYMENTS_DB_PATH", "/tmp/test_payments.db")

import db  # noqa: E402
import remic  # noqa: E402


# ===========================================================================
# REMIC calculation tests
# ===========================================================================

class TestRemicStandardClass(unittest.TestCase):
    """Standard interest-bearing classes: A and B."""

    def _calc(self, **kw):
        defaults = dict(
            principal=10000,
            pass_through_rate=0.06,
            days=30,
            remic_class="A",
            rate_type="gov_obligation",
        )
        defaults.update(kw)
        return remic.calculate_interest(**defaults)

    def test_class_a_basic(self):
        result = self._calc()
        # 10000 * 0.06 * 30/360 = 50.00
        self.assertEqual(result["interest_amount"], Decimal("50.00"))
        self.assertEqual(result["total_amount"], Decimal("10050.00"))
        self.assertEqual(result["royalty_amount"], Decimal("0"))

    def test_class_b_basic(self):
        result = self._calc(remic_class="B")
        self.assertEqual(result["interest_amount"], Decimal("50.00"))

    def test_rounding_half_up(self):
        # 10001 * 0.06 * 30/360 = 50.005 → rounds to 50.01
        result = self._calc(principal=10001)
        self.assertEqual(result["interest_amount"], Decimal("50.01"))

    def test_fractional_rate(self):
        # 12000 * 0.055 * 60/360 = 110.00
        result = self._calc(principal=12000, pass_through_rate=0.055, days=60)
        self.assertEqual(result["interest_amount"], Decimal("110.00"))


class TestRemicIOClass(unittest.TestCase):
    """IO (Interest-Only) class."""

    def test_io_class_basic(self):
        result = remic.calculate_interest(
            principal=5000,
            pass_through_rate=0.05,
            days=30,
            remic_class="IO",
            notional=100000,
            io_rate=0.04,
        )
        # 100000 * 0.04 * 30/360 = 333.33
        self.assertEqual(result["interest_amount"], Decimal("333.33"))

    def test_io_class_missing_notional(self):
        with self.assertRaises(ValueError):
            remic.calculate_interest(
                principal=5000,
                pass_through_rate=0.05,
                days=30,
                remic_class="IO",
            )


class TestRemicPOClass(unittest.TestCase):
    """PO (Principal-Only) class: interest must always be zero."""

    def test_po_interest_is_zero(self):
        result = remic.calculate_interest(
            principal=50000,
            pass_through_rate=0.08,
            days=90,
            remic_class="PO",
        )
        self.assertEqual(result["interest_amount"], Decimal("0"))
        self.assertEqual(result["total_amount"], Decimal("50000"))

    def test_po_royalty_interest_is_zero(self):
        result = remic.calculate_interest(
            principal=50000,
            pass_through_rate=0.08,
            days=90,
            remic_class="PO",
            rate_type="royalty",
            gross_revenue=200000,
            royalty_rate=0.05,
        )
        self.assertEqual(result["interest_amount"], Decimal("0"))


class TestRemicRoyaltyVariant(unittest.TestCase):
    """Royalty rate_type: royalty first, then REMIC interest on royalty."""

    def test_royalty_class_a(self):
        result = remic.calculate_interest(
            principal=0.01,  # principal still required but minimal
            pass_through_rate=0.06,
            days=30,
            remic_class="A",
            rate_type="royalty",
            gross_revenue=200000,
            royalty_rate=0.05,
        )
        # royalty = 200000 * 0.05 = 10000.00
        # interest = 10000 * 0.06 * 30/360 = 50.00
        self.assertEqual(result["royalty_amount"], Decimal("10000.00"))
        self.assertEqual(result["interest_amount"], Decimal("50.00"))

    def test_royalty_missing_gross_revenue(self):
        with self.assertRaises(ValueError):
            remic.calculate_interest(
                principal=1000,
                pass_through_rate=0.05,
                days=30,
                remic_class="A",
                rate_type="royalty",
            )


class TestRemicValidation(unittest.TestCase):
    """Input validation for REMIC calculator."""

    def _base(self, **kw):
        defaults = dict(
            principal=1000, pass_through_rate=0.05, days=30, remic_class="A"
        )
        defaults.update(kw)
        return remic.calculate_interest(**defaults)

    def test_invalid_rate_type(self):
        with self.assertRaises(ValueError):
            self._base(rate_type="mortgage")

    def test_invalid_remic_class(self):
        with self.assertRaises(ValueError):
            self._base(remic_class="Z")

    def test_zero_days(self):
        with self.assertRaises(ValueError):
            self._base(days=0)

    def test_negative_principal(self):
        with self.assertRaises(ValueError):
            self._base(principal=-100)


# ===========================================================================
# DB layer tests
# ===========================================================================

class TestDb(unittest.TestCase):

    def setUp(self):
        # Each test gets a fresh DB
        import tempfile
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        # Reload db module state
        import importlib
        importlib.reload(db)
        db.init_db()

    def tearDown(self):
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass

    def _make_txn(self, ikey="ikey-001"):
        return db.create_transaction(
            idempotency_key=ikey,
            vendor_id="V1",
            obligation_id="OBL-001",
            remic_class="A",
            rate_type="gov_obligation",
            principal="1000.00",
            interest="5.00",
            total="1005.00",
            royalty_amount="0.00",
        )

    def test_create_and_retrieve(self):
        txn = self._make_txn()
        self.assertEqual(txn["status"], "pending")
        fetched = db.get_transaction_by_id(txn["id"])
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["vendor_id"], "V1")

    def test_duplicate_idempotency_key(self):
        self._make_txn()
        with self.assertRaises(ValueError):
            self._make_txn()

    def test_update_status(self):
        txn = self._make_txn()
        db.update_transaction_status(txn["id"], "stripe_created", stripe_payment_id="pi_123")
        updated = db.get_transaction_by_id(txn["id"])
        self.assertEqual(updated["status"], "stripe_created")
        self.assertEqual(updated["stripe_payment_id"], "pi_123")

    def test_audit_trail(self):
        txn = self._make_txn()
        db.append_audit_event(txn["id"], "scan_received", {"foo": "bar"})
        db.append_audit_event(txn["id"], "stripe_created", {"pi": "pi_123"})
        events = db.get_audit_trail(txn["id"])
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["event_type"], "scan_received")


# ===========================================================================
# API endpoint tests
# ===========================================================================

class TestScanPaymentEndpoint(unittest.TestCase):

    def setUp(self):
        import tempfile
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        import importlib
        importlib.reload(db)
        db.init_db()

        import main
        importlib.reload(main)
        self.app = main.app.test_client()

    def tearDown(self):
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass

    def _payload(self, **overrides):
        base = {
            "vendor_id": "V-001",
            "vendor_name": "Test Vendor",
            "vendor_email": "vendor@example.com",
            "obligation_id": "OBL-2026-001",
            "principal_amount": 10000,
            "rate_type": "gov_obligation",
            "remic_class": "A",
            "pass_through_rate": 0.06,
            "days": 30,
        }
        base.update(overrides)
        return base

    @patch("payments.create_stripe_payment")
    @patch("payments.send_docusign_envelope")
    def test_successful_scan(self, mock_ds, mock_stripe):
        mock_stripe.return_value = {
            "stripe_payment_id": "pi_test_123",
            "client_secret": "pi_test_123_secret",
            "status": "requires_payment_method",
        }
        mock_ds.return_value = {
            "envelope_id": "env-abc-123",
            "status": "sent",
        }
        resp = self.app.post(
            "/api/scan-payment",
            json=self._payload(),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["status"], "docusign_sent")
        self.assertIn("transaction_id", data)
        self.assertEqual(data["stripe_payment_id"], "pi_test_123")
        self.assertEqual(data["envelope_id"], "env-abc-123")
        # 10000 * 0.06 * 30/360 = 50.00
        self.assertEqual(data["interest"], "50.00")

    def test_missing_required_field(self):
        payload = self._payload()
        del payload["obligation_id"]
        resp = self.app.post("/api/scan-payment", json=payload)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("obligation_id", resp.get_json()["error"])

    def test_missing_vendor_email(self):
        payload = self._payload()
        del payload["vendor_email"]
        resp = self.app.post("/api/scan-payment", json=payload)
        self.assertEqual(resp.status_code, 400)

    def test_invalid_remic_class(self):
        resp = self.app.post("/api/scan-payment", json=self._payload(remic_class="Z"))
        self.assertEqual(resp.status_code, 422)

    def test_invalid_rate_type(self):
        resp = self.app.post("/api/scan-payment", json=self._payload(rate_type="mortgage"))
        self.assertEqual(resp.status_code, 422)

    def test_empty_body(self):
        resp = self.app.post(
            "/api/scan-payment",
            data="not-json",
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    @patch("payments.create_stripe_payment")
    @patch("payments.send_docusign_envelope")
    def test_duplicate_idempotency_key(self, mock_ds, mock_stripe):
        mock_stripe.return_value = {
            "stripe_payment_id": "pi_dup_test",
            "client_secret": "secret",
            "status": "requires_payment_method",
        }
        mock_ds.return_value = {"envelope_id": "env-dup", "status": "sent"}
        payload = self._payload(idempotency_key="fixed-key-001")
        # First call
        r1 = self.app.post("/api/scan-payment", json=payload)
        self.assertEqual(r1.status_code, 201)
        # Second call with same key
        r2 = self.app.post("/api/scan-payment", json=payload)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["status"], "duplicate")

    @patch("payments.create_stripe_payment")
    def test_stripe_failure_returns_502(self, mock_stripe):
        mock_stripe.side_effect = RuntimeError("Stripe key not configured")
        resp = self.app.post("/api/scan-payment", json=self._payload())
        self.assertEqual(resp.status_code, 502)

    @patch("payments.create_stripe_payment")
    @patch("payments.send_docusign_envelope")
    def test_docusign_failure_returns_502(self, mock_ds, mock_stripe):
        mock_stripe.return_value = {
            "stripe_payment_id": "pi_ok",
            "client_secret": "sec",
            "status": "requires_payment_method",
        }
        mock_ds.side_effect = RuntimeError("DocuSign not configured")
        resp = self.app.post("/api/scan-payment", json=self._payload())
        self.assertEqual(resp.status_code, 502)

    @patch("payments.create_stripe_payment")
    @patch("payments.send_docusign_envelope")
    def test_po_class_zero_interest(self, mock_ds, mock_stripe):
        mock_stripe.return_value = {
            "stripe_payment_id": "pi_po",
            "client_secret": "sec",
            "status": "requires_payment_method",
        }
        mock_ds.return_value = {"envelope_id": "env-po", "status": "sent"}
        resp = self.app.post(
            "/api/scan-payment",
            json=self._payload(remic_class="PO"),
        )
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data["interest"], "0")


class TestDocuSignWebhookEndpoint(unittest.TestCase):

    def setUp(self):
        import tempfile
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        os.environ["DOCUSIGN_HMAC_KEY"] = "test-hmac-secret-key"
        import importlib
        importlib.reload(db)
        db.init_db()
        import main
        importlib.reload(main)
        self.app = main.app.test_client()

    def tearDown(self):
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass
        os.environ.pop("DOCUSIGN_HMAC_KEY", None)

    def _signed_post(self, payload: dict, hmac_key: str = "test-hmac-secret-key"):
        import base64
        import hashlib
        import hmac
        body = json.dumps(payload).encode("utf-8")
        sig = base64.b64encode(
            hmac.new(hmac_key.encode(), body, hashlib.sha256).digest()
        ).decode()
        return self.app.post(
            "/api/docusign-webhook",
            data=body,
            content_type="application/json",
            headers={"X-DocuSign-Signature-1": sig},
        )

    def _seed_transaction(self, envelope_id="env-xyz-999"):
        txn = db.create_transaction(
            idempotency_key="wh-ikey-001",
            vendor_id="V-WH",
            obligation_id="OBL-WH",
            remic_class="B",
            rate_type="gov_obligation",
            principal="5000.00",
            interest="25.00",
            total="5025.00",
            royalty_amount="0.00",
        )
        db.update_transaction_status(
            txn["id"], "docusign_sent", docusign_envelope_id=envelope_id
        )
        return txn

    def test_envelope_completed_marks_transaction(self):
        txn = self._seed_transaction("env-completed-001")
        resp = self._signed_post({
            "event": "envelope-completed",
            "envelopeId": "env-completed-001",
            "status": "completed",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "completed")
        self.assertTrue(data["usps_reference"].startswith("USPS-PROOF-"))
        updated = db.get_transaction_by_id(txn["id"])
        self.assertEqual(updated["status"], "completed")

    def test_non_completion_event_accepted(self):
        resp = self._signed_post({
            "event": "envelope-sent",
            "envelopeId": "env-any",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "accepted")
        self.assertEqual(data["envelope_id"], "env-any")
        self.assertTrue(data["usps_reference"].startswith("USPS-PROOF-"))

    def test_invalid_signature_rejected(self):
        body = json.dumps({"event": "envelope-completed", "envelopeId": "env-x"}).encode()
        resp = self.app.post(
            "/api/docusign-webhook",
            data=body,
            content_type="application/json",
            headers={"X-DocuSign-Signature-1": "bad-sig"},
        )
        self.assertEqual(resp.status_code, 401)

    def test_missing_signature_header_rejected(self):
        body = json.dumps({"event": "envelope-completed"}).encode()
        resp = self.app.post(
            "/api/docusign-webhook",
            data=body,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 401)

    def test_unknown_envelope_completion_is_tracked(self):
        resp = self._signed_post({
            "event": "envelope-completed",
            "envelopeId": "env-does-not-exist",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "tracked")
        self.assertEqual(data["envelope_id"], "env-does-not-exist")
        self.assertTrue(data["usps_reference"].startswith("USPS-PROOF-"))

    def test_idempotent_completion(self):
        txn = self._seed_transaction("env-idempotent-001")
        db.update_transaction_status(txn["id"], "completed")
        resp = self._signed_post({
            "event": "envelope-completed",
            "envelopeId": "env-idempotent-001",
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["status"], "already_completed")

    def test_usps_proof_endpoint_returns_recorded_events(self):
        self._signed_post({
            "event": "envelope-sent",
            "envelopeId": "env-proof-001",
            "status": "sent",
        })
        resp = self.app.get("/api/usps-proof/env-proof-001")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["envelope_id"], "env-proof-001")
        self.assertEqual(len(data["events"]), 1)
        self.assertEqual(data["events"][0]["event_type"], "envelope-sent")


# ===========================================================================
# HMAC verification unit tests
# ===========================================================================

class TestHmacVerification(unittest.TestCase):

    def test_valid_signature(self):
        import base64
        import hashlib
        import hmac
        from payments import verify_docusign_hmac
        key = "my-secret"
        body = b'{"event":"envelope-completed"}'
        sig = base64.b64encode(
            hmac.new(key.encode(), body, hashlib.sha256).digest()
        ).decode()
        self.assertTrue(verify_docusign_hmac(body, sig, key))

    def test_invalid_signature(self):
        from payments import verify_docusign_hmac
        self.assertFalse(verify_docusign_hmac(b"body", "wrong-sig", "key"))

    def test_wrong_key(self):
        import base64
        import hashlib
        import hmac
        from payments import verify_docusign_hmac
        body = b"data"
        sig = base64.b64encode(
            hmac.new(b"correct-key", body, hashlib.sha256).digest()
        ).decode()
        self.assertFalse(verify_docusign_hmac(body, sig, "wrong-key"))


# ===========================================================================
# Settle-signed-envelopes endpoint tests
# ===========================================================================

class TestSettleSignedEnvelopes(unittest.TestCase):

    def setUp(self):
        import importlib
        import tempfile
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        importlib.reload(db)
        db.init_db()
        import main
        importlib.reload(main)
        self.app = main.app.test_client()
        self._main = main

    def tearDown(self):
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass

    def _seed_sent_txn(self, envelope_id: str, ikey: str) -> dict:
        txn = db.create_transaction(
            idempotency_key=ikey,
            vendor_id="V1",
            obligation_id="OBL1",
            remic_class="A",
            rate_type="gov_obligation",
            principal="1000.00",
            interest="10.00",
            total="1010.00",
            royalty_amount="0.00",
        )
        db.update_transaction_status(txn["id"], "docusign_sent", docusign_envelope_id=envelope_id)
        return db.get_transaction_by_id(txn["id"])

    @patch("payments.get_docusign_envelope_status")
    def test_settles_completed_envelopes(self, mock_status):
        txn = self._seed_sent_txn("env-settle-1", "ikey-settle-1")
        mock_status.return_value = {"envelope_id": "env-settle-1", "status": "completed"}

        resp = self.app.post("/api/settle-signed-envelopes")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn(txn["id"], data["settled"])
        self.assertEqual(data["settled_count"], 1)
        self.assertEqual(data["skipped_count"], 0)
        updated = db.get_transaction_by_id(txn["id"])
        self.assertEqual(updated["status"], "completed")

    @patch("payments.get_docusign_envelope_status")
    def test_skips_non_completed_envelopes(self, mock_status):
        txn = self._seed_sent_txn("env-settle-2", "ikey-settle-2")
        mock_status.return_value = {"envelope_id": "env-settle-2", "status": "sent"}

        resp = self.app.post("/api/settle-signed-envelopes")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn(txn["id"], data["skipped"])
        self.assertEqual(data["settled_count"], 0)
        updated = db.get_transaction_by_id(txn["id"])
        self.assertEqual(updated["status"], "docusign_sent")

    @patch("payments.get_docusign_envelope_status")
    def test_records_failed_lookups(self, mock_status):
        txn = self._seed_sent_txn("env-settle-3", "ikey-settle-3")
        mock_status.side_effect = RuntimeError("network error")

        resp = self.app.post("/api/settle-signed-envelopes")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["failed_count"], 1)
        self.assertEqual(data["failed"][0]["transaction_id"], txn["id"])
        self.assertIn("DocuSign status lookup failed", data["failed"][0]["error"])
        updated = db.get_transaction_by_id(txn["id"])
        self.assertEqual(updated["status"], "docusign_sent")

    @patch("payments.get_docusign_envelope_status")
    def test_empty_when_no_pending(self, mock_status):
        resp = self.app.post("/api/settle-signed-envelopes")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["settled_count"], 0)
        self.assertEqual(data["skipped_count"], 0)
        self.assertEqual(data["failed_count"], 0)
        mock_status.assert_not_called()

    @patch("payments.get_docusign_envelope_status")
    def test_idempotent_already_completed(self, mock_status):
        """Transactions already completed are not in docusign_sent; they are ignored."""
        txn = self._seed_sent_txn("env-settle-4", "ikey-settle-4")
        db.update_transaction_status(txn["id"], "completed")
        mock_status.return_value = {"envelope_id": "env-settle-4", "status": "completed"}

        resp = self.app.post("/api/settle-signed-envelopes")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["settled_count"], 0)
        mock_status.assert_not_called()


# ===========================================================================
# db.get_transactions_by_status unit tests
# ===========================================================================

class TestGetTransactionsByStatus(unittest.TestCase):

    def setUp(self):
        import importlib
        import tempfile
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        importlib.reload(db)
        db.init_db()

    def tearDown(self):
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass

    def _create_txn(self, ikey: str, status: str, envelope_id: str | None = None) -> dict:
        txn = db.create_transaction(
            idempotency_key=ikey,
            vendor_id="V",
            obligation_id="O",
            remic_class="A",
            rate_type="royalty",
            principal="100.00",
            interest="1.00",
            total="101.00",
            royalty_amount="0.00",
        )
        db.update_transaction_status(txn["id"], status, docusign_envelope_id=envelope_id)
        return db.get_transaction_by_id(txn["id"])

    def test_returns_matching_status(self):
        t1 = self._create_txn("k1", "docusign_sent", "env-a")
        self._create_txn("k2", "completed")
        rows = db.get_transactions_by_status("docusign_sent")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], t1["id"])

    def test_empty_when_no_match(self):
        self._create_txn("k3", "completed")
        rows = db.get_transactions_by_status("docusign_sent")
        self.assertEqual(rows, [])

    def test_multiple_results(self):
        self._create_txn("k4", "docusign_sent", "env-b")
        self._create_txn("k5", "docusign_sent", "env-c")
        rows = db.get_transactions_by_status("docusign_sent")
        self.assertEqual(len(rows), 2)


if __name__ == "__main__":
    unittest.main()
