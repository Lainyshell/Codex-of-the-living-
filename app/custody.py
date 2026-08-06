"""
Append-only custody envelope storage and validation.
"""

from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile

import safeguards

logger = logging.getLogger(__name__)
_REPO_ROOT_OVERRIDE: Path | None = None

_VALID_FILE_TOKEN = re.compile(r"^[A-Za-z0-9._-]+$")
_VALID_DIRECTIONS = {"OUTBOUND", "INBOUND"}
_VALID_STATUSES = {"PENDING", "IN_LOCKER", "RETRIEVED", "CLOSED"}
_LOCKER_ACTIONS = {
    "LOCKER_OPENED": None,
    "ITEM_PLACED": "IN_LOCKER",
    "PLACED_IN_LOCKER": "IN_LOCKER",
    "ITEM_REMOVED": "RETRIEVED",
    "RETRIEVED": "RETRIEVED",
    "CLOSED": "CLOSED",
}
_GOVERNANCE_REFERENCES = {
    "tribal_governance": "TRIBAL_GOVERNANCE.md",
    "jurisdiction": "JURISDICTION.md",
    "governance_charter": "docs/GOVERNANCE_CHARTER.md",
    "critical_change_protocol": "docs/CRITICAL_CHANGE_PROTOCOL.md",
    "data_sovereignty": "legal/DATA_SOVEREIGNTY_AGREEMENT.md",
}


def _repo_root() -> Path:
    if _REPO_ROOT_OVERRIDE is not None:
        return _REPO_ROOT_OVERRIDE
    return Path(__file__).resolve().parent.parent


def set_repo_root_for_testing(repo_root: str | Path | None) -> None:
    global _REPO_ROOT_OVERRIDE
    _REPO_ROOT_OVERRIDE = Path(repo_root).resolve() if repo_root else None


def _custody_root() -> Path:
    return _repo_root() / "custody"


def _envelopes_dir() -> Path:
    return _custody_root() / "envelopes"


def _lockers_path() -> Path:
    return _custody_root() / "lockers" / "primary.json"


def _schema_path() -> Path:
    return _custody_root() / "schema" / "envelope.schema.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensure_structure() -> None:
    _envelopes_dir().mkdir(parents=True, exist_ok=True)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_envelope_path(path: Path) -> Path:
    resolved_dir = _envelopes_dir().resolve()
    resolved_path = path.resolve(strict=False)
    if resolved_path.parent != resolved_dir or resolved_path.suffix != ".json":
        raise ValueError("Custody envelope path must stay within custody/envelopes")
    return resolved_path


def _load_envelope_json(path: Path) -> dict:
    safe_path = _assert_envelope_path(path)
    payload = json.loads(safe_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Custody envelope must be a JSON object")
    return payload


def _write_envelope_json(path: Path, payload: dict) -> None:
    safe_path = _assert_envelope_path(path)
    safe_path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile("w", encoding="utf-8", dir=safe_path.parent, delete=False) as handle:
        handle.write(json.dumps(payload, indent=2))
        handle.write("\n")
        temp_name = handle.name
    Path(temp_name).replace(safe_path)


def _validate_identifier(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")
    value = value.strip()
    if not _VALID_FILE_TOKEN.fullmatch(value):
        raise ValueError(f"{field_name} contains unsupported characters")
    return value


def load_primary_lockers() -> list[dict]:
    lockers_path = _lockers_path()
    if not lockers_path.exists():
        raise FileNotFoundError("Primary locker configuration was not found")
    payload = _load_json(lockers_path)
    if not isinstance(payload, list):
        raise ValueError("Primary locker configuration must be a list")
    return payload


def _load_schema() -> dict:
    schema_path = _schema_path()
    if not schema_path.exists():
        raise FileNotFoundError("Custody schema was not found")
    payload = _load_json(schema_path)
    if not isinstance(payload, dict):
        raise ValueError("Custody schema must be a JSON object")
    return payload


def _find_primary_locker(location_id: str, locker_facility_id: str) -> dict:
    for locker in load_primary_lockers():
        if (
            str(locker.get("location_id", "")).strip() == location_id
            and str(locker.get("facility_id", "")).strip() == locker_facility_id
        ):
            return locker
    raise ValueError("Locker facility is not authorized for the specified location")


def _normalize_event(raw_event: dict) -> dict:
    if not isinstance(raw_event, dict):
        raise ValueError("Custody event must be a JSON object")

    actor = raw_event.get("actor")
    action = raw_event.get("action")
    if not isinstance(actor, str) or not actor.strip():
        raise ValueError("Custody event actor is required")
    if not isinstance(action, str) or not action.strip():
        raise ValueError("Custody event action is required")

    normalized_action = action.strip().upper().replace("-", "_").replace(" ", "_")
    resulting_status = raw_event.get("resulting_status")
    if isinstance(resulting_status, str) and resulting_status.strip():
        resulting_status = resulting_status.strip().upper()
    else:
        resulting_status = _LOCKER_ACTIONS.get(normalized_action)

    if resulting_status is not None and resulting_status not in _VALID_STATUSES:
        raise ValueError("Custody event resulting_status is invalid")

    details = raw_event.get("details") or {}
    if not isinstance(details, dict):
        raise ValueError("Custody event details must be an object")

    normalized = {
        "timestamp": raw_event.get("timestamp") or _now(),
        "actor": actor.strip(),
        "action": normalized_action,
        "resulting_status": resulting_status,
        "details": details,
    }

    steward_approvals = raw_event.get("steward_approvals") or []
    if steward_approvals:
        if not isinstance(steward_approvals, list):
            raise ValueError("steward_approvals must be a list")
        normalized["steward_approvals"] = [
            approval.strip()
            for approval in steward_approvals
            if isinstance(approval, str) and approval.strip()
        ]

    return normalized


def _derive_status(current_status: str, events: list[dict]) -> str:
    for event in reversed(events):
        resulting_status = event.get("resulting_status")
        if resulting_status:
            return resulting_status
    return current_status


def validate_envelope_document(document: dict) -> None:
    schema = _load_schema()
    required_fields = schema.get("required", [])
    for field_name in required_fields:
        if field_name not in document:
            raise ValueError(f"Custody envelope missing required field: {field_name}")

    for field_name in ("transaction_id", "location_id", "destination", "item_description"):
        if not isinstance(document.get(field_name), str) or not document[field_name].strip():
            raise ValueError(f"Custody envelope field {field_name} must be a non-empty string")

    if document.get("direction") not in _VALID_DIRECTIONS:
        raise ValueError("Custody envelope direction is invalid")

    if document.get("custody_status") not in _VALID_STATUSES:
        raise ValueError("Custody envelope custody_status is invalid")

    if document.get("ship_method") != "USPS Smart Locker":
        raise ValueError("Custody envelopes must use USPS Smart Locker")

    if not isinstance(document.get("events"), list) or not document["events"]:
        raise ValueError("Custody envelope must contain at least one event")

    for event in document["events"]:
        normalized = _normalize_event(event)
        if normalized != event:
            raise ValueError("Custody envelope events must already be normalized")

    location_id = document["location_id"].strip()
    locker_facility_id = str(document["locker_facility_id"]).strip()
    locker = _find_primary_locker(location_id, locker_facility_id)
    if document.get("locker_name") != locker.get("locker_name"):
        raise ValueError("Custody envelope locker_name must match primary locker config")
    if document.get("locker_address") != locker.get("address"):
        raise ValueError("Custody envelope locker_address must match primary locker config")
    if document.get("locker_city") != locker.get("city"):
        raise ValueError("Custody envelope locker_city must match primary locker config")
    if document.get("locker_state") != locker.get("state"):
        raise ValueError("Custody envelope locker_state must match primary locker config")
    if document.get("locker_zip") != locker.get("zip"):
        raise ValueError("Custody envelope locker_zip must match primary locker config")


def _envelope_path(transaction_id: str) -> Path:
    safe_id = _validate_identifier(transaction_id, "transaction_id")
    return _envelopes_dir() / f"{safe_id}.json"


def get_envelope(transaction_id: str) -> dict:
    path = _envelope_path(transaction_id)
    if not path.exists():
        raise FileNotFoundError("Custody envelope was not found")
    payload = _load_envelope_json(path)
    validate_envelope_document(payload)
    return payload


def find_envelope_by_docusign_envelope_id(docusign_envelope_id: str) -> dict | None:
    if not docusign_envelope_id:
        return None
    for path in _envelopes_dir().glob("*.json"):
        try:
            payload = _load_envelope_json(path)
            if payload.get("docusign_envelope_id") == docusign_envelope_id:
                validate_envelope_document(payload)
                return payload
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("Skipping invalid custody envelope %s: %s", path.name, exc)
    return None


def create_envelope(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Envelope payload must be a JSON object")

    transaction_id = _validate_identifier(payload.get("transaction_id", ""), "transaction_id")
    location_id = payload.get("location_id", "").strip()
    locker_facility_id = str(payload.get("locker_facility_id", "")).strip()
    locker = _find_primary_locker(location_id, locker_facility_id)
    now = payload.get("created_at") or _now()

    event_payloads = deepcopy(payload.get("events") or [])
    if not event_payloads:
        event_payloads = [{
            "timestamp": now,
            "actor": payload.get("actor", "SYSTEM"),
            "action": "CREATED",
            "resulting_status": "PENDING",
            "details": {
                "source": "custody.create_envelope",
                "direction": payload.get("direction", "OUTBOUND"),
            },
        }]
    normalized_events = [_normalize_event(event) for event in event_payloads]

    envelope = {
        "transaction_id": transaction_id,
        "location_id": location_id,
        "direction": payload.get("direction", "OUTBOUND"),
        "item_description": payload.get("item_description", "").strip(),
        "ship_method": "USPS Smart Locker",
        "destination": payload.get("destination", "").strip(),
        "custody_status": "PENDING",
        "locker_facility_id": locker["facility_id"],
        "locker_name": locker["locker_name"],
        "locker_address": locker["address"],
        "locker_city": locker["city"],
        "locker_state": locker["state"],
        "locker_zip": locker["zip"],
        "locker_distance_miles": locker.get("distance_miles"),
        "locker_dimensions": locker.get("dimensions"),
        "sovereign_metadata": payload.get("sovereign_metadata", "vbtn1.onmicrosoft.us"),
        "governance_documents": _GOVERNANCE_REFERENCES,
        "docusign_envelope_id": payload.get("docusign_envelope_id"),
        "created_at": now,
        "updated_at": normalized_events[-1]["timestamp"],
        "events": normalized_events,
    }
    envelope["custody_status"] = _derive_status(envelope["custody_status"], envelope["events"])

    validate_envelope_document(envelope)

    path = _envelope_path(transaction_id)
    if path.exists():
        raise FileExistsError("Custody envelope already exists")

    _ensure_structure()
    _write_envelope_json(path, envelope)
    return envelope


def append_event(
    *,
    transaction_id: str | None = None,
    docusign_envelope_id: str | None = None,
    event: dict,
) -> dict:
    envelope = (
        get_envelope(transaction_id)
        if transaction_id
        else find_envelope_by_docusign_envelope_id(docusign_envelope_id or "")
    )
    if envelope is None:
        raise FileNotFoundError("Custody envelope was not found")

    updated = deepcopy(envelope)
    normalized_event = _normalize_event(event)
    target_status = normalized_event.get("resulting_status")

    event_facility = normalized_event["details"].get("locker_facility_id")
    if event_facility and str(event_facility).strip() != str(updated["locker_facility_id"]).strip():
        raise ValueError("Event locker facility does not match custody envelope")

    safeguards.enforce_custody_status_transition(
        item_description=updated["item_description"],
        target_status=target_status,
        actor=normalized_event["actor"],
        steward_approvals=normalized_event.get("steward_approvals", []),
        transaction_id=updated["transaction_id"],
    )

    updated["events"].append(normalized_event)
    updated["custody_status"] = _derive_status(updated["custody_status"], updated["events"])
    updated["updated_at"] = normalized_event["timestamp"]

    validate_envelope_document(updated)
    _write_envelope_json(_envelope_path(updated["transaction_id"]), updated)
    return updated


def ingest_event_payload(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Custody event payload must be a JSON object")
    event = {
        "timestamp": payload.get("timestamp"),
        "actor": payload.get("actor"),
        "action": payload.get("action"),
        "resulting_status": payload.get("resulting_status") or payload.get("custody_status"),
        "details": payload.get("details") or {},
        "steward_approvals": payload.get("steward_approvals") or [],
    }
    if payload.get("locker_facility_id"):
        event["details"]["locker_facility_id"] = str(payload["locker_facility_id"])
    return append_event(
        transaction_id=payload.get("transaction_id"),
        docusign_envelope_id=payload.get("docusign_envelope_id"),
        event=event,
    )


def append_docusign_event(
    *,
    transaction_id: str | None,
    envelope_id: str,
    event_type: str,
    envelope_status: str | None,
    payload: dict,
) -> dict | None:
    details = {
        "source": "docusign_webhook",
        "envelope_id": envelope_id,
        "event_type": event_type,
        "envelope_status": envelope_status,
    }
    if transaction_id:
        details["transaction_id"] = transaction_id

    try:
        return append_event(
            transaction_id=transaction_id,
            docusign_envelope_id=None if transaction_id else envelope_id,
            event={
                "actor": "DOCUSIGN_CONNECT",
                "action": f"DOCUSIGN_{(event_type or 'unknown').upper().replace('-', '_')}",
                "details": details | {"source_payload": payload},
            },
        )
    except FileNotFoundError:
        return None
