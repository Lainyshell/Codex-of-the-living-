"""
Contract Validity Engine — VBTNT.

Validates a contract (transaction) by checking every layer of the
enforcement chain:

  1. envelope_status      — DocuSign envelope is "completed"
  2. signature_complete   — derived from envelope status
  3. usps_proof           — at least one USPS proof event exists
  4. payment_complete     — transaction status is "completed" AND
                            stripe_payment_id is set
  5. metadata_integrity   — all required transaction fields are present

If any check fails the contract is not valid.  The returned report is
audit-ready and includes the VBTNT jurisdiction tag on every record.
"""

from __future__ import annotations

import logging

import db
import payments

logger = logging.getLogger(__name__)

JURISDICTION = "VBTNT"

_REQUIRED_TXN_FIELDS = (
    "vendor_id",
    "obligation_id",
    "remic_class",
    "rate_type",
    "principal",
    "interest",
    "total",
    "royalty_amount",
)


def validate_contract(transaction_id: str) -> dict:
    """
    Run all validity checks for a contract identified by *transaction_id*.

    Returns a dict with shape::

        {
          "valid":          bool,
          "transaction_id": str,
          "jurisdiction":   "VBTNT",
          "checks": {
            "envelope_status":     {"passed": bool, "detail": str},
            "signature_complete":  {"passed": bool, "detail": str},
            "usps_proof":          {"passed": bool, "detail": str},
            "payment_complete":    {"passed": bool, "detail": str},
            "metadata_integrity":  {"passed": bool, "detail": str},
          },
          "invalid_reasons": [str, ...]
        }
    """
    txn = db.get_transaction_by_id(transaction_id)
    if not txn:
        return {
            "valid": False,
            "transaction_id": transaction_id,
            "jurisdiction": JURISDICTION,
            "checks": {},
            "invalid_reasons": ["Transaction not found"],
        }

    checks: dict[str, dict] = {}
    invalid_reasons: list[str] = []

    # ── 1. Payment completion ────────────────────────────────────────────────
    stripe_id = txn.get("stripe_payment_id")
    payment_passed = txn.get("status") == "completed" and bool(stripe_id)
    checks["payment_complete"] = {
        "passed": payment_passed,
        "detail": (
            "Payment completed"
            if payment_passed
            else (
                f"Payment incomplete — status={txn.get('status')!r}, "
                f"stripe_payment_id={'set' if stripe_id else 'missing'}"
            )
        ),
    }
    if not payment_passed:
        invalid_reasons.append("payment_complete check failed")

    # ── 2. Envelope status + 3. Signature completion ─────────────────────────
    envelope_id = txn.get("docusign_envelope_id")
    if not envelope_id:
        env_passed = False
        env_detail = "No DocuSign envelope ID on transaction"
        sig_passed = False
        sig_detail = "No envelope to check signatures against"
    else:
        try:
            env_info = payments.get_docusign_envelope_status(envelope_id)
            env_status = env_info.get("status", "")
            env_passed = env_status == "completed"
            env_detail = f"Envelope status: {env_status}"
            sig_passed = env_passed
            sig_detail = (
                "All signatures collected"
                if sig_passed
                else f"Envelope not yet completed (status={env_status!r})"
            )
        except RuntimeError as exc:
            env_passed = False
            env_detail = f"Could not retrieve envelope status: {exc}"
            sig_passed = False
            sig_detail = "Could not verify signatures (envelope lookup failed)"

    checks["envelope_status"] = {"passed": env_passed, "detail": env_detail}
    checks["signature_complete"] = {"passed": sig_passed, "detail": sig_detail}
    if not env_passed:
        invalid_reasons.append("envelope_status check failed")
    if not sig_passed:
        invalid_reasons.append("signature_complete check failed")

    # ── 4. USPS proof ────────────────────────────────────────────────────────
    usps_events: list[dict] = []
    if envelope_id:
        usps_events = db.list_docusign_usps_proof_events(envelope_id)
    usps_passed = len(usps_events) > 0
    checks["usps_proof"] = {
        "passed": usps_passed,
        "detail": (
            f"{len(usps_events)} USPS proof event(s) on record"
            if usps_passed
            else "No USPS proof events found for this envelope"
        ),
    }
    if not usps_passed:
        invalid_reasons.append("usps_proof check failed")

    # ── 5. Metadata integrity ────────────────────────────────────────────────
    missing_fields = [f for f in _REQUIRED_TXN_FIELDS if not txn.get(f)]
    meta_passed = not missing_fields
    checks["metadata_integrity"] = {
        "passed": meta_passed,
        "detail": (
            "All required fields present"
            if meta_passed
            else f"Missing or empty fields: {missing_fields}"
        ),
    }
    if not meta_passed:
        invalid_reasons.append("metadata_integrity check failed")

    return {
        "valid": not invalid_reasons,
        "transaction_id": transaction_id,
        "jurisdiction": JURISDICTION,
        "checks": checks,
        "invalid_reasons": invalid_reasons,
    }
