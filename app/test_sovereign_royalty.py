"""
Test suite — Sovereign Vocabulary Dictionary and Royalty Engine.

Run with:
    cd app && pip install -r requirements.txt && python -m unittest test_sovereign_royalty -v
"""

import importlib
import json
import os
import sys
import tempfile
import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

_APP_DIR = os.path.dirname(os.path.abspath(__file__))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

os.environ.setdefault("PAYMENTS_DB_PATH", "/tmp/test_sovereign_royalty.db")

import db  # noqa: E402
import royalty_engine  # noqa: E402
import sovereign_vocabulary  # noqa: E402


# ===========================================================================
# Sovereign Vocabulary Dictionary tests
# ===========================================================================

class TestSovereignVocabulary(unittest.TestCase):

    def test_dictionary_is_not_empty(self):
        self.assertGreater(len(sovereign_vocabulary.DICTIONARY), 0)

    def test_every_entry_has_required_keys(self):
        for term, entry in sovereign_vocabulary.DICTIONARY.items():
            with self.subTest(term=term):
                self.assertIn("domain", entry, f"{term!r} missing domain")
                self.assertIn("definition", entry, f"{term!r} missing definition")
                self.assertIn("authority", entry, f"{term!r} missing authority")
                self.assertTrue(entry["domain"], f"{term!r} domain is empty")
                self.assertTrue(entry["definition"], f"{term!r} definition is empty")
                self.assertTrue(entry["authority"], f"{term!r} authority is empty")

    def test_get_known_term(self):
        entry = sovereign_vocabulary.get_term("VBTNT")
        self.assertEqual(entry["domain"], "Sovereign Governance")
        self.assertIn("Verdigris Botanica Tribal Nation Trust", entry["definition"])

    def test_get_unknown_term_raises_key_error(self):
        with self.assertRaises(KeyError):
            sovereign_vocabulary.get_term("NOT_A_REAL_TERM_XYZ")

    def test_list_terms_all(self):
        terms = sovereign_vocabulary.list_terms()
        self.assertIn("VBTNT", terms)
        self.assertIn("REMIC", terms)
        self.assertIn("USPS Smart Locker", terms)

    def test_list_terms_by_domain(self):
        federal = sovereign_vocabulary.list_terms(domain="Federal Procurement")
        for term in federal:
            self.assertEqual(
                sovereign_vocabulary.DICTIONARY[term]["domain"], "Federal Procurement"
            )
        self.assertIn("UEI", federal)
        self.assertIn("CAGE Code", federal)

    def test_list_terms_unknown_domain_returns_empty(self):
        result = sovereign_vocabulary.list_terms(domain="NonexistentDomain")
        self.assertEqual(result, [])

    def test_list_domains_returns_all_expected(self):
        domains = sovereign_vocabulary.list_domains()
        expected = {
            "Microsoft Ecosystems",
            "GitHub Workflows",
            "Federal Procurement",
            "Postal & Shipping Authority",
            "Sovereign Governance",
        }
        for d in expected:
            self.assertIn(d, domains)

    def test_assert_vocabulary_intact_passes(self):
        # Should not raise
        sovereign_vocabulary.assert_vocabulary_intact()

    def test_usps_smart_locker_is_defined(self):
        entry = sovereign_vocabulary.get_term("USPS Smart Locker")
        self.assertEqual(entry["domain"], "Postal & Shipping Authority")

    def test_tribal_return_is_defined(self):
        entry = sovereign_vocabulary.get_term("Tribal Return")
        self.assertIn("Stripe", entry["definition"])

    def test_critical_change_is_defined(self):
        entry = sovereign_vocabulary.get_term("Critical Change")
        self.assertEqual(entry["domain"], "GitHub Workflows")


# ===========================================================================
# Royalty Engine tests
# ===========================================================================

class TestRoyaltyEngineNonCompleted(unittest.TestCase):
    """Non-completed envelopes: only sovereign_fee + energy_return."""

    def _calc(self, status="sent"):
        return royalty_engine.calculate_tribal_returns(envelope_status=status)

    def test_non_completed_returns_two_items(self):
        items = self._calc("sent")
        self.assertEqual(len(items), 2)

    def test_non_completed_has_sovereign_fee(self):
        items = self._calc("sent")
        types = {i["return_type"] for i in items}
        self.assertIn(royalty_engine.RETURN_TYPE_SOVEREIGN_FEE, types)

    def test_non_completed_has_energy_return(self):
        items = self._calc("voided")
        types = {i["return_type"] for i in items}
        self.assertIn(royalty_engine.RETURN_TYPE_ENERGY, types)

    def test_non_completed_sovereign_fee_amount(self):
        items = self._calc("declined")
        fee = next(i for i in items if i["return_type"] == royalty_engine.RETURN_TYPE_SOVEREIGN_FEE)
        self.assertEqual(Decimal(fee["amount"]), royalty_engine.SOVEREIGN_FEE)

    def test_non_completed_energy_return_amount(self):
        items = self._calc("created")
        energy = next(i for i in items if i["return_type"] == royalty_engine.RETURN_TYPE_ENERGY)
        self.assertEqual(Decimal(energy["amount"]), royalty_engine.ENERGY_RETURN)

    def test_no_royalty_on_non_completed(self):
        items = self._calc("sent")
        types = {i["return_type"] for i in items}
        self.assertNotIn(royalty_engine.RETURN_TYPE_ROYALTY, types)

    def test_no_remic_on_non_completed(self):
        items = self._calc("sent")
        types = {i["return_type"] for i in items}
        self.assertNotIn(royalty_engine.RETURN_TYPE_REMIC, types)


class TestRoyaltyEngineCompleted(unittest.TestCase):
    """Completed envelopes: full schedule."""

    def _calc(self, **kw):
        defaults = dict(
            envelope_status="completed",
            principal="10000",
            gross_revenue="10000",
        )
        defaults.update(kw)
        return royalty_engine.calculate_tribal_returns(**defaults)

    def test_completed_has_four_items(self):
        items = self._calc()
        types = {i["return_type"] for i in items}
        self.assertIn(royalty_engine.RETURN_TYPE_SOVEREIGN_FEE, types)
        self.assertIn(royalty_engine.RETURN_TYPE_ENERGY, types)
        self.assertIn(royalty_engine.RETURN_TYPE_ROYALTY, types)
        self.assertIn(royalty_engine.RETURN_TYPE_REMIC, types)

    def test_royalty_default_rate(self):
        # gross_revenue=10000, royalty_rate=5% → royalty=500.00
        items = self._calc(gross_revenue="10000")
        royalty = next(i for i in items if i["return_type"] == royalty_engine.RETURN_TYPE_ROYALTY)
        self.assertEqual(Decimal(royalty["amount"]), Decimal("500.00"))

    def test_royalty_custom_rate(self):
        # gross_revenue=20000, royalty_rate=2.5% → royalty=500.00
        items = self._calc(gross_revenue="20000", royalty_rate="0.025")
        royalty = next(i for i in items if i["return_type"] == royalty_engine.RETURN_TYPE_ROYALTY)
        self.assertEqual(Decimal(royalty["amount"]), Decimal("500.00"))

    def test_remic_interest_default(self):
        # principal=10000, rate=6%, days=30 → 10000*0.06*30/360 = 50.00
        items = self._calc(principal="10000", gross_revenue=None)
        remic = next(i for i in items if i["return_type"] == royalty_engine.RETURN_TYPE_REMIC)
        self.assertEqual(Decimal(remic["amount"]), Decimal("50.00"))

    def test_remic_custom_days(self):
        # principal=10000, rate=6%, days=60 → 100.00
        items = self._calc(principal="10000", gross_revenue=None, accrual_days=60)
        remic = next(i for i in items if i["return_type"] == royalty_engine.RETURN_TYPE_REMIC)
        self.assertEqual(Decimal(remic["amount"]), Decimal("100.00"))

    def test_no_royalty_when_gross_revenue_absent(self):
        items = royalty_engine.calculate_tribal_returns(
            envelope_status="completed",
            principal="5000",
        )
        types = {i["return_type"] for i in items}
        self.assertNotIn(royalty_engine.RETURN_TYPE_ROYALTY, types)

    def test_no_remic_when_principal_absent(self):
        items = royalty_engine.calculate_tribal_returns(
            envelope_status="completed",
            gross_revenue="10000",
        )
        types = {i["return_type"] for i in items}
        self.assertNotIn(royalty_engine.RETURN_TYPE_REMIC, types)

    def test_negative_gross_revenue_raises(self):
        with self.assertRaises(ValueError):
            royalty_engine.calculate_tribal_returns(
                envelope_status="completed",
                gross_revenue="-100",
            )

    def test_non_positive_principal_raises(self):
        with self.assertRaises(ValueError):
            royalty_engine.calculate_tribal_returns(
                envelope_status="completed",
                principal="-500",
            )


class TestAmountToCents(unittest.TestCase):

    def test_exact_conversion(self):
        self.assertEqual(royalty_engine.amount_to_cents("2.50"), 250)

    def test_rounding_half_up(self):
        self.assertEqual(royalty_engine.amount_to_cents("0.015"), 2)

    def test_zero(self):
        self.assertEqual(royalty_engine.amount_to_cents("0.00"), 0)

    def test_large_amount(self):
        self.assertEqual(royalty_engine.amount_to_cents("500.00"), 50000)


# ===========================================================================
# DB tribal_returns tests
# ===========================================================================

class TestDbTribalReturns(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        importlib.reload(db)
        db.init_db()

    def tearDown(self):
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass

    def test_create_and_list(self):
        record = db.create_tribal_return(
            envelope_id="env-tr-001",
            transaction_id=None,
            envelope_status="sent",
            return_type="sovereign_fee",
            amount="2.50",
        )
        self.assertEqual(record["envelope_id"], "env-tr-001")
        self.assertEqual(record["return_type"], "sovereign_fee")
        self.assertEqual(record["amount"], "2.50")
        self.assertIsNone(record["stripe_payment_id"])

        records = db.list_tribal_returns("env-tr-001")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["id"], record["id"])

    def test_update_stripe(self):
        record = db.create_tribal_return(
            envelope_id="env-tr-002",
            transaction_id=None,
            envelope_status="completed",
            return_type="royalty",
            amount="500.00",
        )
        db.update_tribal_return_stripe(record["id"], "pi_test_abc")
        updated = db.get_tribal_return(record["id"])
        self.assertEqual(updated["stripe_payment_id"], "pi_test_abc")
        self.assertIsNotNone(updated["posted_at"])

    def test_list_returns_empty_for_unknown_envelope(self):
        records = db.list_tribal_returns("env-does-not-exist")
        self.assertEqual(records, [])


# ===========================================================================
# USPS proof event address metadata tests
# ===========================================================================

class TestUspsProofAddressMetadata(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        importlib.reload(db)
        db.init_db()

    def tearDown(self):
        try:
            os.unlink(self._tmp.name)
        except OSError:
            pass

    def test_proof_event_stores_address(self):
        event = db.create_docusign_usps_proof_event(
            envelope_id="env-addr-001",
            event_type="envelope-completed",
            envelope_status="completed",
            event_timestamp="2026-07-28T10:00:00Z",
            transaction_id=None,
            recipient_name="Alaina Padgett",
            recipient_email="alaina@verdigrisbotanicanation.org",
            recipient_address="123 Sovereign Way",
            recipient_city="Elizabethtown",
            recipient_state="KY",
            recipient_zip="42701",
            recipient_phone="555-123-4567",
            source_payload={"test": True},
        )
        self.assertEqual(event["recipient_name"], "Alaina Padgett")
        self.assertEqual(event["recipient_address"], "123 Sovereign Way")
        self.assertEqual(event["recipient_city"], "Elizabethtown")
        self.assertEqual(event["recipient_state"], "KY")
        self.assertEqual(event["recipient_zip"], "42701")
        self.assertEqual(event["recipient_phone"], "555-123-4567")

    def test_proof_event_lists_address(self):
        db.create_docusign_usps_proof_event(
            envelope_id="env-addr-002",
            event_type="envelope-sent",
            envelope_status="sent",
            event_timestamp="2026-07-28T11:00:00Z",
            transaction_id=None,
            recipient_name="Test Person",
            recipient_email="test@example.com",
            recipient_address="456 Tribal Blvd",
            recipient_city="Owensboro",
            recipient_state="KY",
            recipient_zip="42303",
            recipient_phone=None,
            source_payload={},
        )
        events = db.list_docusign_usps_proof_events("env-addr-002")
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["recipient_address"], "456 Tribal Blvd")
        self.assertIsNone(events[0]["recipient_phone"])

    def test_proof_event_address_nullable(self):
        # All address fields optional
        event = db.create_docusign_usps_proof_event(
            envelope_id="env-addr-003",
            event_type="envelope-sent",
            envelope_status="sent",
            event_timestamp="2026-07-28T12:00:00Z",
            transaction_id=None,
            recipient_name=None,
            recipient_email=None,
            source_payload={"minimal": True},
        )
        self.assertIsNone(event["recipient_address"])
        self.assertIsNone(event["recipient_city"])
        self.assertIsNone(event["recipient_state"])
        self.assertIsNone(event["recipient_zip"])
        self.assertIsNone(event["recipient_phone"])


# ===========================================================================
# API endpoint tests for new routes
# ===========================================================================

class TestNewApiEndpoints(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        os.environ["PAYMENTS_DB_PATH"] = self._tmp.name
        os.environ["DOCUSIGN_HMAC_KEY"] = "test-hmac-key-svr"
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

    def test_sovereign_vocabulary_endpoint(self):
        resp = self.app.get("/api/sovereign-vocabulary")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("terms", data)
        self.assertIn("VBTNT", data["terms"])
        self.assertIn("REMIC", data["terms"])
        self.assertGreater(data["term_count"], 0)

    def test_sovereign_vocabulary_domain_filter(self):
        resp = self.app.get("/api/sovereign-vocabulary?domain=Federal+Procurement")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["domain"], "Federal Procurement")
        for term_data in data["terms"].values():
            self.assertEqual(term_data["domain"], "Federal Procurement")

    def test_sovereign_vocabulary_unknown_domain(self):
        resp = self.app.get("/api/sovereign-vocabulary?domain=InvalidDomain")
        self.assertEqual(resp.status_code, 404)

    def test_tribal_returns_endpoint_not_found(self):
        resp = self.app.get("/api/tribal-returns/env-does-not-exist")
        self.assertEqual(resp.status_code, 404)

    def _signed_post(self, payload: dict):
        import base64
        import hashlib
        import hmac
        body = json.dumps(payload).encode("utf-8")
        sig = base64.b64encode(
            hmac.new(b"test-hmac-key-svr", body, hashlib.sha256).digest()
        ).decode()
        return self.app.post(
            "/api/docusign-webhook",
            data=body,
            content_type="application/json",
            headers={"X-DocuSign-Signature-1": sig},
        )

    def test_webhook_response_includes_tribal_returns(self):
        resp = self._signed_post({
            "event": "envelope-sent",
            "envelopeId": "env-tr-webhook-001",
            "status": "sent",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("tribal_returns", data)
        self.assertIsInstance(data["tribal_returns"], list)
        # Should have at least sovereign_fee + energy_return
        self.assertGreaterEqual(len(data["tribal_returns"]), 2)

    def test_tribal_returns_endpoint_returns_records(self):
        self._signed_post({
            "event": "envelope-sent",
            "envelopeId": "env-tr-api-002",
            "status": "sent",
        })
        resp = self.app.get("/api/tribal-returns/env-tr-api-002")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["envelope_id"], "env-tr-api-002")
        self.assertGreaterEqual(len(data["tribal_returns"]), 2)

    def test_webhook_completed_includes_tribal_returns(self):
        resp = self._signed_post({
            "event": "envelope-completed",
            "envelopeId": "env-tr-complete-001",
            "status": "completed",
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("tribal_returns", data)
        # Non-completed path (no linked txn): only sovereign_fee + energy_return
        self.assertGreaterEqual(len(data["tribal_returns"]), 2)


if __name__ == "__main__":
    unittest.main()
