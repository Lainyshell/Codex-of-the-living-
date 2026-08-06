"""
Contract breach detection and automatic notice generation — VBTNT.

When a contract is found to be in breach this module:

  1. Logs the breach to the ``contract_breaches`` table
  2. Sends an email notice (when BREACH_NOTICE_EMAIL is configured)
  3. Calculates a penalty if BREACH_PENALTY_RATE (float, default 0) > 0
  4. Generates a follow-up DocuSign envelope (when BREACH_FOLLOWUP_TEMPLATE
     is configured)

Breach conditions (auto-detected from webhook events):
  • Envelope status ``voided``
  • Envelope status ``declined``
  • Transaction status ``failed``

All records are tagged with ``jurisdiction = VBTNT``.

Environment variables
---------------------
BREACH_NOTICE_EMAIL      Recipient address for notice emails.
BREACH_FROM_EMAIL        Sender address (default: noreply@vbtnt.gov).
BREACH_SMTP_HOST         SMTP host (default: localhost).
BREACH_SMTP_PORT         SMTP port (default: 25).
BREACH_PENALTY_RATE      Fraction of principal to assess as penalty (e.g. 0.05).
BREACH_FOLLOWUP_TEMPLATE DocuSign template ID for the follow-up envelope.
"""

from __future__ import annotations

import logging
import os

import db

logger = logging.getLogger(__name__)

JURISDICTION = "VBTNT"

# Envelope statuses that constitute a breach
BREACH_STATUSES = frozenset({"voided", "declined"})


def _penalty_rate() -> float:
    try:
        return float(os.environ.get("BREACH_PENALTY_RATE", "0"))
    except ValueError:
        return 0.0


def detect_breach_from_event(
    transaction_id: str | None,
    envelope_status: str | None,
) -> str | None:
    """
    Return a breach_type string if the event indicates a breach, else None.

    Parameters
    ----------
    transaction_id:   DB transaction ID (may be None for unlinked envelopes).
    envelope_status:  Status string from the DocuSign webhook payload.
    """
    if envelope_status and envelope_status.lower() in BREACH_STATUSES:
        return f"envelope_{envelope_status.lower()}"
    if transaction_id:
        txn = db.get_transaction_by_id(transaction_id)
        if txn and txn.get("status") == "failed":
            return "payment_failure"
    return None


def handle_breach(
    transaction_id: str,
    breach_type: str,
    details: dict | None = None,
) -> dict:
    """
    Process a contract breach end-to-end.

    Steps
    -----
    1. Persist the breach record (idempotent — duplicate breaches are skipped).
    2. Send an email notice if BREACH_NOTICE_EMAIL is configured.
    3. Generate a follow-up DocuSign envelope if BREACH_FOLLOWUP_TEMPLATE is set.

    Returns the persisted breach record dict.
    """
    txn = db.get_transaction_by_id(transaction_id)

    # ── 1. Calculate penalty ─────────────────────────────────────────────────
    penalty_amount: str | None = None
    rate = _penalty_rate()
    if rate > 0 and txn:
        try:
            from decimal import Decimal

            principal = Decimal(txn.get("principal") or "0")
            penalty_amount = str(principal * Decimal(str(rate)))
        except Exception:
            pass

    # ── 2. Persist breach record ─────────────────────────────────────────────
    breach = db.log_contract_breach(
        transaction_id=transaction_id,
        breach_type=breach_type,
        penalty_amount=penalty_amount,
        details=details or {},
    )

    # ── 3. Send notice ───────────────────────────────────────────────────────
    _send_notice(breach, txn)

    # ── 4. Generate follow-up envelope ──────────────────────────────────────
    _generate_followup_envelope(breach, txn)

    return breach


def _send_notice(breach: dict, txn: dict | None) -> None:
    """Send a breach notice email if BREACH_NOTICE_EMAIL is configured."""
    notice_email = os.environ.get("BREACH_NOTICE_EMAIL", "")
    if not notice_email:
        return

    smtp_host = os.environ.get("BREACH_SMTP_HOST", "localhost")
    smtp_port_str = os.environ.get("BREACH_SMTP_PORT", "25")
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        smtp_port = 25

    try:
        import smtplib
        from email.message import EmailMessage

        msg = EmailMessage()
        msg["Subject"] = (
            f"[{JURISDICTION}] Contract Breach Notice — {breach['breach_type']}"
        )
        msg["From"] = os.environ.get(
            "BREACH_FROM_EMAIL", f"noreply@{JURISDICTION.lower()}.gov"
        )
        msg["To"] = notice_email

        lines = [
            f"Jurisdiction: {JURISDICTION}",
            f"Breach ID: {breach['id']}",
            f"Transaction ID: {breach['transaction_id']}",
            f"Breach Type: {breach['breach_type']}",
            f"Detected At: {breach['created_at']}",
        ]
        if breach.get("penalty_amount"):
            lines.append(f"Calculated Penalty: {breach['penalty_amount']}")
        if txn:
            lines.append(f"Obligation ID: {txn.get('obligation_id', '')}")
            lines.append(f"Vendor ID: {txn.get('vendor_id', '')}")

        msg.set_content("\n".join(lines))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
            smtp.send_message(msg)

        logger.info(
            "Breach notice sent to %s for transaction %s",
            notice_email,
            breach["transaction_id"],
        )
    except Exception as exc:
        logger.warning("Failed to send breach notice: %s", exc)


def _generate_followup_envelope(breach: dict, txn: dict | None) -> None:
    """Generate a follow-up DocuSign envelope if BREACH_FOLLOWUP_TEMPLATE is set."""
    template_id = os.environ.get("BREACH_FOLLOWUP_TEMPLATE", "")
    notice_email = os.environ.get("BREACH_NOTICE_EMAIL", "")
    if not template_id or not txn or not notice_email:
        return

    try:
        import payments
        from docusign_esign import ApiClient, EnvelopesApi  # type: ignore[import-untyped]
        from docusign_esign.models import (  # type: ignore[import-untyped]
            EnvelopeDefinition,
            Tabs,
            TemplateRole,
            Text,
        )

        access_token = payments._get_docusign_token()
        account_id = payments._ds_env("DOCUSIGN_ACCOUNT_ID")
        base_url = payments._ds_env("DOCUSIGN_BASE_URL")

        tab_values = [
            Text(tab_label="transaction_id", value=txn["id"]),
            Text(tab_label="breach_id", value=breach["id"]),
            Text(tab_label="breach_type", value=breach["breach_type"]),
            Text(tab_label="jurisdiction", value=JURISDICTION),
        ]
        if breach.get("penalty_amount"):
            tab_values.append(
                Text(tab_label="penalty_amount", value=breach["penalty_amount"])
            )

        template_roles = [
            TemplateRole(
                email=notice_email,
                name="Breach Recipient",
                role_name="Recipient",
                tabs=Tabs(text_tabs=tab_values),
            )
        ]
        envelope_def = EnvelopeDefinition(
            template_id=template_id,
            template_roles=template_roles,
            status="sent",
            email_subject=(
                f"[{JURISDICTION}] Follow-up Required: Contract Breach {breach['id']}"
            ),
        )

        api_client = ApiClient()
        api_client.host = f"{base_url}/v2.1"
        api_client.set_default_header("Authorization", f"******")
        result = EnvelopesApi(api_client).create_envelope(
            account_id=account_id,
            envelope_definition=envelope_def,
        )
        logger.info(
            "Follow-up envelope %s created for breach %s",
            result.envelope_id,
            breach["id"],
        )
    except Exception as exc:
        logger.warning("Failed to generate follow-up envelope for breach: %s", exc)
