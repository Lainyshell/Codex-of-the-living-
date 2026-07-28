"""Provision Azure Government Microsoft 365 mailboxes via Microsoft Graph.

Expected environment variables:
- GRAPH_BASE_URL / GRAPH_RESOURCE: Azure Government Microsoft Graph endpoints.
- AZURE_CLOUD: Azure CLI cloud name, defaults to AzureUSGovernment.
- DEFAULT_USAGE_LOCATION: fallback location for new mailbox users.
- AZURE_KEY_VAULT_NAME: optional vault used to resolve password_secret_name values.
- MAILBOXES_JSON: inline JSON array of mailbox requests for workflow_dispatch runs.
- MAILBOX_REQUESTS_FILE: optional repository path to a JSON request file.
"""

import json
import os
import re
import subprocess
import sys
from urllib import error, parse, request

GRAPH_BASE_URL = os.environ.get("GRAPH_BASE_URL", "https://graph.microsoft.us/v1.0").rstrip("/")
GRAPH_RESOURCE = os.environ.get("GRAPH_RESOURCE", "https://graph.microsoft.us/")
AZURE_CLOUD = os.environ.get("AZURE_CLOUD", "AzureUSGovernment")
DEFAULT_USAGE_LOCATION = os.environ.get("DEFAULT_USAGE_LOCATION", "US").strip()
AZURE_KEY_VAULT_NAME = os.environ.get("AZURE_KEY_VAULT_NAME", "").strip()
ALWAYS_PROVIDED_UPDATE_KEYS = {"display_name"}


class ValidationError(RuntimeError):
    pass


class GraphClient:
    def __init__(self, token, base_url=GRAPH_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self._sku_map = None

    def request_json(self, method, path, payload=None, expected_statuses=(200,), allow_404=False):
        url = f"{self.base_url}{path}"
        body = None
        headers = {
            "Authorization": "Bearer " + self.token,
            "Accept": "application/json",
        }
        if payload is not None:
            body = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = request.Request(url, data=body, headers=headers, method=method)

        try:
            with request.urlopen(req) as response:
                if response.status not in expected_statuses:
                    raise RuntimeError(
                        f"Graph API {method} {path} returned unexpected status {response.status}."
                    )
                raw = response.read().decode("utf-8")
                if not raw:
                    return {}
                return json.loads(raw)
        except error.HTTPError as exc:
            if allow_404 and exc.code == 404:
                return None
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Graph API {method} {path} failed with {exc.code}: {detail}") from exc

    def get_user(self, user_principal_name):
        encoded_upn = parse.quote(user_principal_name, safe="")
        path = (
            f"/users/{encoded_upn}"
            "?$select=id,displayName,userPrincipalName,givenName,surname,jobTitle,department,"
            "usageLocation,accountEnabled,assignedLicenses"
        )
        return self.request_json("GET", path, allow_404=True)

    def create_user(self, payload):
        return self.request_json("POST", "/users", payload=payload, expected_statuses=(201,))

    def patch_user(self, user_id, payload):
        return self.request_json("PATCH", f"/users/{user_id}", payload=payload, expected_statuses=(204,))

    def assign_licenses(self, user_id, sku_ids):
        add_licenses = [{"skuId": sku_id} for sku_id in sku_ids]
        payload = {"addLicenses": add_licenses, "removeLicenses": []}
        return self.request_json("POST", f"/users/{user_id}/assignLicense", payload=payload)

    def get_sku_map(self):
        if self._sku_map is None:
            response = self.request_json(
                "GET",
                "/subscribedSkus?$select=skuId,skuPartNumber",
            )
            self._sku_map = {
                item["skuPartNumber"].upper(): item["skuId"]
                for item in response.get("value", [])
                if item.get("skuPartNumber") and item.get("skuId")
            }
        return self._sku_map


def parse_bool(value, default=False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        values = value
    else:
        values = str(value).split(",")
    return [str(item).strip() for item in values if str(item).strip()]


def derive_mail_nickname(user_principal_name):
    local_part = user_principal_name.split("@", 1)[0].strip().lower()
    nickname = re.sub(r"[^a-z0-9._-]+", "-", local_part)
    nickname = nickname.strip("-._")
    if not nickname:
        raise ValidationError(f"Unable to derive mail nickname from {user_principal_name}")
    return nickname[:64]


def load_requests():
    inline_payload = os.environ.get("MAILBOXES_JSON", "").strip()
    file_path = os.environ.get("MAILBOX_REQUESTS_FILE", "").strip()

    if inline_payload:
        payload = json.loads(inline_payload)
    elif file_path:
        with open(file_path, encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        raise ValidationError("Set MAILBOXES_JSON or MAILBOX_REQUESTS_FILE before running provisioning.")

    if isinstance(payload, dict):
        payload = payload.get("mailboxes", payload)

    if not isinstance(payload, list) or not payload:
        raise ValidationError("Mailbox request payload must be a non-empty JSON array.")

    return [normalize_request(item, index) for index, item in enumerate(payload, start=1)]


def normalize_request(item, index):
    if not isinstance(item, dict):
        raise ValidationError(f"Mailbox request #{index} must be an object.")

    user_principal_name = (
        item.get("user_principal_name")
        or item.get("userPrincipalName")
        or ""
    ).strip().lower()
    display_name = (item.get("display_name") or item.get("displayName") or "").strip()
    usage_location = (
        item.get("usage_location")
        or item.get("usageLocation")
        or DEFAULT_USAGE_LOCATION
    ).strip().upper()

    if not user_principal_name:
        raise ValidationError(f"Mailbox request #{index} is missing user_principal_name.")
    if not display_name:
        raise ValidationError(f"Mailbox request #{index} is missing display_name.")
    if not usage_location:
        raise ValidationError(f"Mailbox request #{index} is missing usage_location.")

    provided_fields = set()
    field_aliases = {
        "display_name": ("display_name", "displayName"),
        "given_name": ("given_name", "givenName"),
        "surname": ("surname", "surName"),
        "job_title": ("job_title", "jobTitle"),
        "department": ("department",),
        "usage_location": ("usage_location", "usageLocation"),
        "mail_nickname": ("mail_nickname", "mailNickname"),
        "account_enabled": ("account_enabled",),
        "force_change_password_next_sign_in": ("force_change_password_next_sign_in",),
        "license_sku_part_numbers": ("license_sku_part_numbers", "licenseSkuPartNumbers"),
        "password": ("password",),
        "password_secret_name": ("password_secret_name", "passwordSecretName"),
    }
    for normalized_name, aliases in field_aliases.items():
        if any(alias in item for alias in aliases):
            provided_fields.add(normalized_name)

    return {
        "user_principal_name": user_principal_name,
        "display_name": display_name,
        "given_name": (item.get("given_name") or item.get("givenName") or "").strip(),
        "surname": (item.get("surname") or item.get("surName") or "").strip(),
        "job_title": (item.get("job_title") or item.get("jobTitle") or "").strip(),
        "department": (item.get("department") or "").strip(),
        "usage_location": usage_location,
        "mail_nickname": (
            item.get("mail_nickname")
            or item.get("mailNickname")
            or derive_mail_nickname(user_principal_name)
        ).strip(),
        "account_enabled": parse_bool(item.get("account_enabled"), default=True),
        "force_change_password_next_sign_in": parse_bool(
            item.get("force_change_password_next_sign_in"),
            default=True,
        ),
        "license_sku_part_numbers": [
            license_name.upper() for license_name in parse_list(
                item.get("license_sku_part_numbers")
                or item.get("licenseSkuPartNumbers")
            )
        ],
        "password": item.get("password"),
        "password_secret_name": (
            item.get("password_secret_name") or item.get("passwordSecretName") or ""
        ).strip(),
        "provided_fields": provided_fields,
    }


def run_az(*args):
    argv = [str(arg) for arg in args]
    for arg in argv:
        if "\x00" in arg or "\n" in arg or "\r" in arg:
            raise ValidationError("Azure CLI arguments must not contain control characters.")
    result = subprocess.run(
        ["az", *argv],
        capture_output=True,
        check=False,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Azure CLI command failed: az {' '.join(argv)}\n{stderr}")
    return result.stdout.strip()


def ensure_azure_cloud():
    run_az("cloud", "set", "--name", AZURE_CLOUD)


def get_graph_access_token():
    try:
        return run_az(
            "account",
            "get-access-token",
            "--resource-type",
            "ms-graph",
            "--query",
            "accessToken",
            "-o",
            "tsv",
        )
    except RuntimeError:
        return run_az(
            "account",
            "get-access-token",
            "--resource",
            GRAPH_RESOURCE,
            "--query",
            "accessToken",
            "-o",
            "tsv",
        )


def resolve_password(mailbox, dry_run=False):
    if mailbox.get("password"):
        return mailbox["password"]

    secret_name = mailbox.get("password_secret_name")
    if secret_name:
        if not AZURE_KEY_VAULT_NAME:
            raise ValidationError(
                f"AZURE_KEY_VAULT_NAME is required to resolve password secret {secret_name}."
            )
        return run_az(
            "keyvault",
            "secret",
            "show",
            "--vault-name",
            AZURE_KEY_VAULT_NAME,
            "--name",
            secret_name,
            "--query",
            "value",
            "-o",
            "tsv",
        )

    if dry_run:
        return None

    raise ValidationError(
        f"New mailbox {mailbox['user_principal_name']} requires password or password_secret_name."
    )


def build_create_payload(mailbox, password):
    payload = {
        "accountEnabled": mailbox["account_enabled"],
        "displayName": mailbox["display_name"],
        "mailNickname": mailbox["mail_nickname"],
        "userPrincipalName": mailbox["user_principal_name"],
        "usageLocation": mailbox["usage_location"],
    }
    if mailbox["given_name"]:
        payload["givenName"] = mailbox["given_name"]
    if mailbox["surname"]:
        payload["surname"] = mailbox["surname"]
    if mailbox["job_title"]:
        payload["jobTitle"] = mailbox["job_title"]
    if mailbox["department"]:
        payload["department"] = mailbox["department"]
    if password is not None:
        payload["passwordProfile"] = {
            "forceChangePasswordNextSignIn": mailbox["force_change_password_next_sign_in"],
            "password": password,
        }
    return payload


def build_patch_payload(existing_user, mailbox):
    field_map = {
        "displayName": mailbox["display_name"],
        "givenName": mailbox["given_name"],
        "surname": mailbox["surname"],
        "jobTitle": mailbox["job_title"],
        "department": mailbox["department"],
        "usageLocation": mailbox["usage_location"],
        "accountEnabled": mailbox["account_enabled"],
    }
    mutable_fields = {
        "displayName": "display_name",
        "givenName": "given_name",
        "surname": "surname",
        "jobTitle": "job_title",
        "department": "department",
        "usageLocation": "usage_location",
        "accountEnabled": "account_enabled",
    }
    payload = {}
    for field_name, desired_value in field_map.items():
        normalized_name = mutable_fields[field_name]
        if normalized_name not in mailbox.get("provided_fields", ALWAYS_PROVIDED_UPDATE_KEYS):
            continue
        current_value = existing_user.get(field_name)
        if desired_value != current_value:
            payload[field_name] = desired_value
    return payload


def resolve_license_ids(graph_client, sku_part_numbers):
    if not sku_part_numbers:
        return []
    sku_map = graph_client.get_sku_map()
    missing = [sku for sku in sku_part_numbers if sku not in sku_map]
    if missing:
        raise ValidationError(f"Unknown license SKU part numbers: {', '.join(missing)}")
    return [sku_map[sku] for sku in sku_part_numbers]


def provision_mailboxes(graph_client, mailboxes, dry_run=False):
    results = []

    for mailbox in mailboxes:
        existing_user = graph_client.get_user(mailbox["user_principal_name"])
        created = False
        update_fields = []

        if existing_user is None:
            password = resolve_password(mailbox, dry_run=dry_run)
            create_payload = build_create_payload(mailbox, password)
            if dry_run:
                user = {"id": mailbox["user_principal_name"], "assignedLicenses": []}
            else:
                user = graph_client.create_user(create_payload)
            created = True
        else:
            patch_payload = build_patch_payload(existing_user, mailbox)
            if patch_payload:
                update_fields = sorted(patch_payload)
                if not dry_run:
                    graph_client.patch_user(existing_user["id"], patch_payload)
            user = existing_user

        current_licenses = {
            item.get("skuId")
            for item in user.get("assignedLicenses", [])
            if item.get("skuId")
        }
        desired_licenses = set(resolve_license_ids(graph_client, mailbox["license_sku_part_numbers"]))
        licenses_to_add = sorted(desired_licenses - current_licenses)
        if licenses_to_add and not dry_run:
            graph_client.assign_licenses(user["id"], licenses_to_add)

        if dry_run:
            if created:
                action = "plan-create"
            elif update_fields or licenses_to_add:
                action = "plan-update"
            else:
                action = "plan-noop"
        elif created:
            action = "created"
        elif update_fields or licenses_to_add:
            action = "updated"
        else:
            action = "unchanged"

        results.append(
            {
                "user_principal_name": mailbox["user_principal_name"],
                "action": action,
                "updated_fields": update_fields,
                "license_sku_part_numbers": mailbox["license_sku_part_numbers"],
                "licenses_added": licenses_to_add,
            }
        )

    return results


def write_summary(results, dry_run=False):
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    heading = "# Tenant mailbox provisioning preview" if dry_run else "# Tenant mailbox provisioning"
    lines = [
        heading,
        "",
        "| Mailbox | Action | Updated Fields | Requested License SKUs |",
        "|---|---|---|---|",
    ]
    for result in results:
        updated_fields = ", ".join(result["updated_fields"]) or "—"
        licenses = ", ".join(result["license_sku_part_numbers"]) or "—"
        lines.append(
            f"| {result['user_principal_name']} | {result['action']} | {updated_fields} | {licenses} |"
        )

    with open(summary_path, "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")


def main():
    try:
        dry_run = parse_bool(os.environ.get("DRY_RUN"), default=True)
        mailboxes = load_requests()
        ensure_azure_cloud()
        token = get_graph_access_token()
        graph_client = GraphClient(token)
        results = provision_mailboxes(graph_client, mailboxes, dry_run=dry_run)
        write_summary(results, dry_run=dry_run)
        for result in results:
            print(
                f"{result['user_principal_name']}: {result['action']}"
                f" fields={','.join(result['updated_fields']) or '-'}"
                f" licenses={','.join(result['license_sku_part_numbers']) or '-'}"
            )
    except json.JSONDecodeError as exc:
        print(f"Invalid mailbox JSON payload: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
    except (RuntimeError, ValidationError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
