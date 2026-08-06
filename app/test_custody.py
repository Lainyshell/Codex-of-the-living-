import base64
import hashlib
import hmac
import importlib
import json
import os
import tempfile
import unittest
from pathlib import Path

import config
import custody
import db
import main
import safeguards


_PRIMARY_LOCKERS = [
    {
        "location_id": "VBTN-001",
        "facility_id": "1578794",
        "locker_name": "OWENSBORO KY SDC",
        "address": "2970 FAIRVIEW DR",
        "city": "OWENSBORO",
        "state": "KY",
        "zip": "42303",
        "distance_miles": 0.0,
        "dimensions": {"small": "5x5x18"},
    }
]

_SCHEMA = {
    "required": [
        "transaction_id",
        "location_id",
        "direction",
        "item_description",
        "ship_method",
        "destination",
        "custody_status",
        "locker_facility_id",
        "locker_name",
        "locker_address",
        "locker_city",
        "locker_state",
        "locker_zip",
        "sovereign_metadata",
        "events",
    ]
}


class TestCustodyEndpoints(unittest.TestCase):
    def setUp(self):
        self._db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._repo_dir = tempfile.TemporaryDirectory()
        os.environ["PAYMENTS_DB_PATH"] = self._db_file.name
        os.environ["DOCUSIGN_HMAC_KEY"] = "custody-hmac-key"
        self._write_custody_support_files()

        importlib.reload(db)
        importlib.reload(safeguards)
        importlib.reload(custody)
        custody.set_repo_root_for_testing(self._repo_dir.name)
        importlib.reload(main)
        safeguards.config.STEWARD_ALERT_EMAILS = [
            "steward-one@verdigrisbotanicanation.org",
            "steward-two@verdigrisbotanicanation.org",
        ]
        config.STEWARD_ALERT_EMAILS = safeguards.config.STEWARD_ALERT_EMAILS
        self.client = main.app.test_client()

    def tearDown(self):
        self._db_file.close()
        Path(self._db_file.name).unlink(missing_ok=True)
        self._repo_dir.cleanup()
        os.environ.pop("PAYMENTS_DB_PATH", None)
        os.environ.pop("DOCUSIGN_HMAC_KEY", None)
        custody.set_repo_root_for_testing(None)

    def _write_custody_support_files(self):
        repo_root = Path(self._repo_dir.name)
        (repo_root / "custody" / "lockers").mkdir(parents=True, exist_ok=True)
        (repo_root / "custody" / "schema").mkdir(parents=True, exist_ok=True)
        (repo_root / "custody" / "envelopes").mkdir(parents=True, exist_ok=True)
        (repo_root / "custody" / "lockers" / "primary.json").write_text(
            json.dumps(_PRIMARY_LOCKERS),
            encoding="utf-8",
        )
        (repo_root / "custody" / "schema" / "envelope.schema.json").write_text(
            json.dumps(_SCHEMA),
            encoding="utf-8",
        )

    def _envelope_payload(self, **overrides):
        payload = {
            "transaction_id": "COC-2026-1001",
            "location_id": "VBTN-001",
            "direction": "OUTBOUND",
            "item_description": "Tribal ID Card — Physical Card Delivery",
            "destination": "Recipient Pickup",
            "locker_facility_id": "1578794",
            "sovereign_metadata": "vbtn1.onmicrosoft.us",
            "actor": "SYSTEM",
        }
        payload.update(overrides)
        return payload

    def _signed_post(self, payload: dict):
        body = json.dumps(payload).encode("utf-8")
        sig = base64.b64encode(
            hmac.new(b"custody-hmac-key", body, hashlib.sha256).digest()
        ).decode()
        return self.client.post(
            "/api/docusign-webhook",
            data=body,
            content_type="application/json",
            headers={"X-DocuSign-Signature-1": sig},
        )

    def test_custody_events_append_without_mutating_history(self):
        create_response = self.client.post("/api/custody/envelopes", json=self._envelope_payload())
        self.assertEqual(create_response.status_code, 201)

        before = custody.get_envelope("COC-2026-1001")
        first_event = dict(before["events"][0])

        append_response = self.client.post(
            "/api/custody/events",
            json={
                "transaction_id": "COC-2026-1001",
                "actor": "MAILROOM_STEWARD",
                "action": "PLACED_IN_LOCKER",
                "locker_facility_id": "1578794",
            },
        )
        self.assertEqual(append_response.status_code, 200)
        self.assertEqual(append_response.get_json()["custody_status"], "IN_LOCKER")

        after = custody.get_envelope("COC-2026-1001")
        self.assertEqual(len(after["events"]), 2)
        self.assertEqual(after["events"][0], first_event)
        self.assertEqual(after["events"][1]["action"], "PLACED_IN_LOCKER")

    def test_custody_creation_rejects_invalid_primary_locker(self):
        response = self.client.post(
            "/api/custody/envelopes",
            json=self._envelope_payload(
                transaction_id="COC-2026-1002",
                locker_facility_id="9999999",
            ),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json()["message"], "Custody envelope request was invalid.")

    def test_high_risk_retrieval_requires_two_stewards(self):
        create_response = self.client.post(
            "/api/custody/envelopes",
            json=self._envelope_payload(
                transaction_id="COC-2026-1003",
                item_description="Quarterly Stipend Card — $20,000",
            ),
        )
        self.assertEqual(create_response.status_code, 201)

        denied = self.client.post(
            "/api/custody/events",
            json={
                "transaction_id": "COC-2026-1003",
                "actor": "STEWARD_ONE",
                "action": "RETRIEVED",
                "steward_approvals": ["steward-one@verdigrisbotanicanation.org"],
            },
        )
        self.assertEqual(denied.status_code, 403)

        still_pending = custody.get_envelope("COC-2026-1003")
        self.assertEqual(still_pending["custody_status"], "PENDING")
        self.assertEqual(len(still_pending["events"]), 1)

        approved = self.client.post(
            "/api/custody/events",
            json={
                "transaction_id": "COC-2026-1003",
                "actor": "STEWARD_ONE",
                "action": "RETRIEVED",
                "steward_approvals": [
                    "steward-one@verdigrisbotanicanation.org",
                    "steward-two@verdigrisbotanicanation.org",
                ],
            },
        )
        self.assertEqual(approved.status_code, 200)
        self.assertEqual(approved.get_json()["custody_status"], "RETRIEVED")

    def test_docusign_webhook_appends_custody_event(self):
        txn = db.create_transaction(
            idempotency_key="custody-wh",
            vendor_id="V1",
            obligation_id="OBL-1",
            remic_class="A",
            rate_type="gov_obligation",
            principal="100.00",
            interest="1.00",
            total="101.00",
            royalty_amount="0.00",
        )
        db.update_transaction_status(
            txn["id"],
            "docusign_sent",
            docusign_envelope_id="env-custody-001",
        )
        self.client.post(
            "/api/custody/envelopes",
            json=self._envelope_payload(
                transaction_id=txn["id"],
                docusign_envelope_id="env-custody-001",
            ),
        )

        response = self._signed_post({
            "event": "envelope-sent",
            "envelopeId": "env-custody-001",
            "status": "sent",
        })
        self.assertEqual(response.status_code, 200)

        envelope = custody.get_envelope(txn["id"])
        self.assertEqual(envelope["events"][-1]["action"], "DOCUSIGN_ENVELOPE_SENT")
        self.assertEqual(envelope["events"][-1]["details"]["envelope_id"], "env-custody-001")


if __name__ == "__main__":
    unittest.main()
