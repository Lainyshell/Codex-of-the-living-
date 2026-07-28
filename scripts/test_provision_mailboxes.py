import os
import sys
import unittest
from unittest.mock import patch

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import provision_mailboxes as pm  # noqa: E402

FULL_PROVIDED_FIELDS = {
    "display_name",
    "given_name",
    "surname",
    "job_title",
    "department",
    "usage_location",
    "account_enabled",
    "license_sku_part_numbers",
}
PROVIDED_FIELDS_WITHOUT_LICENSES = FULL_PROVIDED_FIELDS - {"license_sku_part_numbers"}


class FakeGraphClient:
    def __init__(self, users=None, sku_map=None):
        self.users = users or {}
        self.sku_map = sku_map or {}
        self.created_payloads = []
        self.patched_payloads = []
        self.assigned_payloads = []

    def get_user(self, user_principal_name):
        user = self.users.get(user_principal_name)
        if user is None:
            return None
        return {
            key: value[:] if isinstance(value, list) else value
            for key, value in user.items()
        }

    def create_user(self, payload):
        self.created_payloads.append(payload)
        return {"id": "created-user", "assignedLicenses": []}

    def patch_user(self, user_id, payload):
        self.patched_payloads.append((user_id, payload))
        return {}

    def assign_licenses(self, user_id, sku_ids):
        self.assigned_payloads.append((user_id, sku_ids))
        return {}

    def get_sku_map(self):
        return self.sku_map


class TestProvisionMailboxes(unittest.TestCase):
    def test_derive_mail_nickname_sanitizes_local_part(self):
        self.assertEqual(pm.derive_mail_nickname("Ops Team+1@verdigris.org"), "ops-team-1")
        with self.assertRaises(pm.ValidationError):
            pm.derive_mail_nickname("---@verdigris.org")
        self.assertEqual(
            pm.derive_mail_nickname(f"{'a' * 80}@verdigris.org"),
            "a" * 64,
        )

    def test_load_requests_uses_defaults_and_normalizes_keys(self):
        original_mailboxes_json = os.environ.get("MAILBOXES_JSON")
        original_usage = pm.DEFAULT_USAGE_LOCATION
        pm.DEFAULT_USAGE_LOCATION = "US"
        os.environ["MAILBOXES_JSON"] = (
            '[{"userPrincipalName":"ops@verdigris.org","displayName":"Ops","licenseSkuPartNumbers":"sku-one, sku-two"}]'
        )
        try:
            payload = pm.load_requests()
        finally:
            if original_mailboxes_json is None:
                os.environ.pop("MAILBOXES_JSON", None)
            else:
                os.environ["MAILBOXES_JSON"] = original_mailboxes_json
            pm.DEFAULT_USAGE_LOCATION = original_usage

        self.assertEqual(payload[0]["user_principal_name"], "ops@verdigris.org")
        self.assertEqual(payload[0]["usage_location"], "US")
        self.assertEqual(payload[0]["license_sku_part_numbers"], ["SKU-ONE", "SKU-TWO"])
        self.assertEqual(payload[0]["mail_nickname"], "ops")

    def test_provision_mailboxes_creates_new_user_in_dry_run(self):
        client = FakeGraphClient(sku_map={"EXCHANGESTANDARD": "sku-1"})
        requests = [
            {
                "user_principal_name": "compliance@verdigris.org",
                "display_name": "Compliance",
                "given_name": "Compliance",
                "surname": "Mailbox",
                "job_title": "Compliance",
                "department": "Operations",
                "usage_location": "US",
                "mail_nickname": "compliance",
                "account_enabled": True,
                "force_change_password_next_sign_in": True,
                "license_sku_part_numbers": ["EXCHANGESTANDARD"],
                "password": None,
                "password_secret_name": "",
                "provided_fields": FULL_PROVIDED_FIELDS,
            }
        ]

        results = pm.provision_mailboxes(client, requests, dry_run=True)

        self.assertEqual(results[0]["action"], "plan-create")
        self.assertEqual(client.created_payloads, [])
        self.assertEqual(client.assigned_payloads, [])

    def test_provision_mailboxes_updates_existing_user_and_assigns_license(self):
        client = FakeGraphClient(
            users={
                "ops@verdigris.org": {
                    "id": "user-1",
                    "displayName": "Old Ops",
                    "givenName": "Old",
                    "surname": "Name",
                    "jobTitle": "Analyst",
                    "department": "Legacy",
                    "usageLocation": "US",
                    "accountEnabled": True,
                    "assignedLicenses": [],
                }
            },
            sku_map={"EXCHANGESTANDARD": "sku-1"},
        )
        requests = [
            {
                "user_principal_name": "ops@verdigris.org",
                "display_name": "Operations",
                "given_name": "Ops",
                "surname": "Mailbox",
                "job_title": "Operations",
                "department": "Treasury",
                "usage_location": "US",
                "mail_nickname": "ops",
                "account_enabled": True,
                "force_change_password_next_sign_in": True,
                "license_sku_part_numbers": ["EXCHANGESTANDARD"],
                "password": None,
                "password_secret_name": "",
                "provided_fields": FULL_PROVIDED_FIELDS,
            }
        ]

        results = pm.provision_mailboxes(client, requests, dry_run=False)

        self.assertEqual(results[0]["action"], "updated")
        self.assertEqual(client.patched_payloads[0][0], "user-1")
        self.assertIn("displayName", client.patched_payloads[0][1])
        self.assertEqual(client.assigned_payloads, [("user-1", ["sku-1"])])

    def test_provision_mailboxes_requires_password_for_new_user(self):
        client = FakeGraphClient()
        requests = [
            {
                "user_principal_name": "ops@verdigris.org",
                "display_name": "Operations",
                "given_name": "Ops",
                "surname": "Mailbox",
                "job_title": "Operations",
                "department": "Treasury",
                "usage_location": "US",
                "mail_nickname": "ops",
                "account_enabled": True,
                "force_change_password_next_sign_in": True,
                "license_sku_part_numbers": [],
                "password": None,
                "password_secret_name": "",
                "provided_fields": PROVIDED_FIELDS_WITHOUT_LICENSES,
            }
        ]

        with self.assertRaises(pm.ValidationError):
            pm.provision_mailboxes(client, requests, dry_run=False)

    def test_build_patch_payload_can_clear_explicitly_provided_optional_fields(self):
        existing_user = {
            "displayName": "Operations",
            "givenName": "Ops",
            "surname": "Mailbox",
            "jobTitle": "Analyst",
            "department": "Legacy",
            "usageLocation": "US",
            "accountEnabled": True,
        }
        mailbox = {
            "display_name": "Operations",
            "given_name": "Ops",
            "surname": "Mailbox",
            "job_title": "",
            "department": "",
            "usage_location": "US",
            "account_enabled": False,
            "provided_fields": {"display_name", "job_title", "department", "account_enabled"},
        }

        payload = pm.build_patch_payload(existing_user, mailbox)

        self.assertEqual(payload["jobTitle"], "")
        self.assertEqual(payload["department"], "")
        self.assertFalse(payload["accountEnabled"])

    def test_resolve_password_requires_key_vault_name_for_secret_reference(self):
        mailbox = {
            "user_principal_name": "ops@verdigris.org",
            "password": None,
            "password_secret_name": "MAILBOX-OPS-PASSWORD",
        }
        original_vault_name = pm.AZURE_KEY_VAULT_NAME
        pm.AZURE_KEY_VAULT_NAME = ""
        try:
            with self.assertRaises(pm.ValidationError):
                pm.resolve_password(mailbox, dry_run=False)
        finally:
            pm.AZURE_KEY_VAULT_NAME = original_vault_name

    def test_resolve_password_reads_key_vault_secret(self):
        mailbox = {
            "user_principal_name": "ops@verdigris.org",
            "password": None,
            "password_secret_name": "MAILBOX-OPS-PASSWORD",
        }
        original_vault_name = pm.AZURE_KEY_VAULT_NAME
        pm.AZURE_KEY_VAULT_NAME = "vbtn-github-secrets"
        try:
            with patch.object(pm, "run_az", return_value="SecretPass123!") as run_az:
                password = pm.resolve_password(mailbox, dry_run=False)
        finally:
            pm.AZURE_KEY_VAULT_NAME = original_vault_name

        self.assertEqual(password, "SecretPass123!")
        run_az.assert_called_once()

    def test_resolve_password_surfaces_key_vault_lookup_failures(self):
        mailbox = {
            "user_principal_name": "ops@verdigris.org",
            "password": None,
            "password_secret_name": "MAILBOX-OPS-PASSWORD",
        }
        original_vault_name = pm.AZURE_KEY_VAULT_NAME
        pm.AZURE_KEY_VAULT_NAME = "vbtn-github-secrets"
        try:
            with patch.object(pm, "run_az", side_effect=RuntimeError("secret not found")):
                with self.assertRaises(RuntimeError):
                    pm.resolve_password(mailbox, dry_run=False)
        finally:
            pm.AZURE_KEY_VAULT_NAME = original_vault_name


if __name__ == "__main__":
    unittest.main()
