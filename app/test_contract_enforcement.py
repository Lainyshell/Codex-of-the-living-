"""
Tests for the Contract Validity Engine, Breach module, and Contract
Enforcement API endpoints.
"""

import json
import os
import tempfile
import unittest
from unittest.mock import patch

import db
import breach as breach_module
import contract_validity
from main import app


def _make_txn(extra=None):
    """Helper: create a fully-populated transaction in the DB."""
    import uuid

    key = str(uuid.uuid4())
    txn = db.create_transaction(
        idempotency_key=key,
        vendor_id="vendor-1",
        obligation_id="ob-1",
        remic_class="A",
        rate_type="gov_obligation",
        principal="100000",
        interest="5000",
        total="105000",
        royalty_amount="1000",
    )
    if extra:
        db.update_transaction_status(txn["id"], extra.get("status", "pending"),
                                     **{k: v for k, v in extra.items() if k != "status"})
        txn = db.get_transaction_by_id(txn["id"])
    return txn


class TestContractValidityEngine(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        db.init_db()

    def tearDown(self):
        os.environ.pop("PAYMENTS_DB_PATH", None)
        self._tmp.close()
        os.unlink(self._tmp.name)

    def test_unknown_transaction_is_invalid(self):
        report = contract_validity.validate_contract("nonexistent-id")
        self.assertFalse(report["valid"])
        self.assertIn("Transaction not found", report["invalid_reasons"])
        self.assertEqual(report["jurisdiction"], "VBTNT")

    def test_pending_transaction_fails_multiple_checks(self):
        txn = _make_txn()
        report = contract_validity.validate_contract(txn["id"])
        self.assertFalse(report["valid"])
        # Payment, envelope, signature, usps must all fail
        self.assertFalse(report["checks"]["payment_complete"]["passed"])
        self.assertFalse(report["checks"]["envelope_status"]["passed"])
        self.assertFalse(report["checks"]["signature_complete"]["passed"])
        self.assertFalse(report["checks"]["usps_proof"]["passed"])

    def test_metadata_integrity_passes_for_complete_record(self):
        txn = _make_txn()
        report = contract_validity.validate_contract(txn["id"])
        # All required fields are present so metadata check should pass
        self.assertTrue(report["checks"]["metadata_integrity"]["passed"])

    def test_jurisdiction_always_vbtnt(self):
        txn = _make_txn()
        report = contract_validity.validate_contract(txn["id"])
        self.assertEqual(report["jurisdiction"], "VBTNT")

    def test_completed_with_stripe_passes_payment_check(self):
        txn = _make_txn()
        db.update_transaction_status(
            txn["id"], "completed", stripe_payment_id="pi_test123"
        )
        # envelope still missing, so valid=False; but payment check passes
        with patch("payments.get_docusign_envelope_status") as mock_env:
            mock_env.return_value = {"status": "completed", "envelope_id": "env-1"}
            # We still need to set envelope_id on the txn for this path:
            report = contract_validity.validate_contract(txn["id"])
        self.assertTrue(report["checks"]["payment_complete"]["passed"])

    def test_all_checks_pass_for_fully_completed_contract(self):
        """Simulate a fully valid contract by mocking DocuSign and seeding USPS proof."""
        import uuid
        txn = _make_txn()
        env_id = str(uuid.uuid4())
        db.update_transaction_status(
            txn["id"], "completed",
            stripe_payment_id="pi_done",
            docusign_envelope_id=env_id,
        )
        # Seed a USPS proof event
        db.create_docusign_usps_proof_event(
            envelope_id=env_id,
            event_type="envelope-delivered",
            envelope_status="delivered",
            event_timestamp="2026-01-01T00:00:00Z",
            transaction_id=txn["id"],
            recipient_name="Test",
            recipient_email="test@example.com",
            source_payload={"test": True},
        )

        with patch("payments.get_docusign_envelope_status") as mock_env:
            mock_env.return_value = {"status": "completed", "envelope_id": env_id}
            report = contract_validity.validate_contract(txn["id"])

        self.assertTrue(report["valid"])
        self.assertEqual(report["invalid_reasons"], [])
        for check_name, check in report["checks"].items():
            self.assertTrue(check["passed"], f"{check_name} should pass")


class TestBreachModule(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        db.init_db()

    def tearDown(self):
        os.environ.pop("PAYMENTS_DB_PATH", None)
        self._tmp.close()
        os.unlink(self._tmp.name)

    def test_no_breach_for_pending_transaction(self):
        txn = _make_txn()
        result = breach_module.detect_breach_from_event(
            transaction_id=txn["id"],
            envelope_status="sent",
        )
        self.assertIsNone(result)

    def test_voided_envelope_detected_as_breach(self):
        result = breach_module.detect_breach_from_event(
            transaction_id=None,
            envelope_status="voided",
        )
        self.assertEqual(result, "envelope_voided")

    def test_declined_envelope_detected_as_breach(self):
        result = breach_module.detect_breach_from_event(
            transaction_id=None,
            envelope_status="declined",
        )
        self.assertEqual(result, "envelope_declined")

    def test_failed_transaction_detected_as_breach(self):
        txn = _make_txn()
        db.update_transaction_status(txn["id"], "failed")
        result = breach_module.detect_breach_from_event(
            transaction_id=txn["id"],
            envelope_status=None,
        )
        self.assertEqual(result, "payment_failure")

    def test_handle_breach_persists_record(self):
        txn = _make_txn()
        breach_record = breach_module.handle_breach(
            transaction_id=txn["id"],
            breach_type="envelope_voided",
            details={"envelope_id": "env-test"},
        )
        self.assertIsNotNone(breach_record["id"])
        self.assertEqual(breach_record["breach_type"], "envelope_voided")
        self.assertEqual(breach_record["jurisdiction"], "VBTNT")
        self.assertEqual(breach_record["transaction_id"], txn["id"])

    def test_breach_is_retrievable_from_db(self):
        txn = _make_txn()
        breach_module.handle_breach(
            transaction_id=txn["id"],
            breach_type="envelope_declined",
        )
        breaches = db.list_contract_breaches(txn["id"])
        self.assertEqual(len(breaches), 1)
        self.assertEqual(breaches[0]["breach_type"], "envelope_declined")

    def test_penalty_calculated_when_rate_set(self):
        txn = _make_txn()
        with patch.dict(os.environ, {"BREACH_PENALTY_RATE": "0.1"}):
            breach_record = breach_module.handle_breach(
                transaction_id=txn["id"],
                breach_type="test",
            )
        # principal=100000, rate=0.1 → penalty=10000
        self.assertIsNotNone(breach_record["penalty_amount"])
        from decimal import Decimal
        self.assertAlmostEqual(float(breach_record["penalty_amount"]), 10000.0)


class TestContractEnforcementAPI(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        db.init_db()
        self.client = app.test_client()

    def tearDown(self):
        os.environ.pop("PAYMENTS_DB_PATH", None)
        self._tmp.close()
        os.unlink(self._tmp.name)

    def test_status_404_for_unknown_contract(self):
        response = self.client.get("/api/contracts/unknown-id/status")
        # validate_contract returns invalid (not found) → 422
        self.assertEqual(response.status_code, 422)
        payload = response.get_json()
        self.assertFalse(payload["report"]["valid"])

    def test_evidence_404_for_unknown_contract(self):
        response = self.client.get("/api/contracts/unknown-id/evidence")
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_unknown_contract(self):
        response = self.client.get("/api/contracts/unknown-id/returns")
        self.assertEqual(response.status_code, 404)

    def test_status_returns_validity_report(self):
        txn = _make_txn()
        response = self.client.get(f"/api/contracts/{txn['id']}/status")
        self.assertIn(response.status_code, (200, 422))
        payload = response.get_json()
        self.assertIn("report", payload)
        report = payload["report"]
        self.assertEqual(report["jurisdiction"], "VBTNT")
        self.assertIn("checks", report)
        self.assertIn("invalid_reasons", report)

    def test_evidence_returns_bundle(self):
        txn = _make_txn()
        response = self.client.get(f"/api/contracts/{txn['id']}/evidence")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["jurisdiction"], "VBTNT")
        self.assertIn("transaction", payload)
        self.assertIn("audit_trail", payload)
        self.assertIn("usps_proof_events", payload)
        self.assertIn("breaches", payload)

    def test_returns_endpoint_returns_empty_list_when_no_envelope(self):
        txn = _make_txn()
        response = self.client.get(f"/api/contracts/{txn['id']}/returns")
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["jurisdiction"], "VBTNT")
        self.assertIsInstance(payload["tribal_returns"], list)


class TestJurisdictionHeaders(unittest.TestCase):
    """Verify VBTNT jurisdiction tag propagates across the enforcement chain."""

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        db.init_db()

    def tearDown(self):
        os.environ.pop("PAYMENTS_DB_PATH", None)
        self._tmp.close()
        os.unlink(self._tmp.name)

    def test_usps_proof_event_has_jurisdiction_vbtnt(self):
        import uuid
        env_id = str(uuid.uuid4())
        event = db.create_docusign_usps_proof_event(
            envelope_id=env_id,
            event_type="test-event",
            envelope_status="sent",
            event_timestamp="2026-01-01T00:00:00Z",
            transaction_id=None,
            recipient_name=None,
            recipient_email=None,
            source_payload={"x": 1},
        )
        self.assertEqual(event.get("jurisdiction"), "VBTNT")

    def test_listed_usps_proof_events_include_jurisdiction(self):
        import uuid
        env_id = str(uuid.uuid4())
        db.create_docusign_usps_proof_event(
            envelope_id=env_id,
            event_type="test-event",
            envelope_status="sent",
            event_timestamp="2026-01-01T00:00:01Z",
            transaction_id=None,
            recipient_name=None,
            recipient_email=None,
            source_payload={},
        )
        events = db.list_docusign_usps_proof_events(env_id)
        self.assertTrue(len(events) > 0)
        self.assertEqual(events[0]["jurisdiction"], "VBTNT")

    def test_contract_breach_record_has_jurisdiction_vbtnt(self):
        txn = _make_txn()
        breach_record = breach_module.handle_breach(
            transaction_id=txn["id"],
            breach_type="test_breach",
        )
        self.assertEqual(breach_record["jurisdiction"], "VBTNT")

    @patch("stripe.PaymentIntent.create")
    def test_stripe_payment_metadata_includes_jurisdiction(self, mock_create):
        import payments as pay_module

        mock_create.return_value = {
            "id": "pi_test",
            "client_secret": "secret",
            "status": "requires_payment_method",
        }
        os.environ["STRIPE_API_KEY"] = "sk_test_fake"
        pay_module.create_stripe_payment(
            amount_cents=10000,
            vendor_id="v1",
            obligation_id="ob1",
            remic_class="A",
            interest_amount="100",
            docusign_template="tmpl_A",
            idempotency_key="idem-test",
        )
        call_kwargs = mock_create.call_args[1]
        self.assertEqual(call_kwargs["metadata"]["jurisdiction"], "VBTNT")


if __name__ == "__main__":
    unittest.main()
