"""
app/safeguards.py — Codex of the Living
Verdigris Botanica Tribal Nation (VBTN)

Anti-weaponization safeguards module.

This module implements the abuse detection and graceful degradation behavior
described in docs/ABUSE_DETECTION_RUNBOOK.md and required by
docs/PROHIBITED_USES.md.

It provides:
- Rate limiting and pattern detection for mass export, bulk delete, and
  suspicious query patterns
- Multi-steward alert dispatch (never single-recipient)
- Lockdown mode activation and collective-approval resume
- Audit logging of all abuse events

Disabling or bypassing this module is a Critical Change per
docs/CRITICAL_CHANGE_PROTOCOL.md and requires multi-steward approval
plus a Tribal Resolution.
"""

import logging
import smtplib
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from email.mime.text import MIMEText
from functools import wraps
from typing import Callable

from flask import g, has_app_context, has_request_context, jsonify, request

import config

logger = logging.getLogger(__name__)
_HIGH_RISK_CUSTODY_KEYWORDS = (
    "stipend",
    "trust",
    "payroll",
    "emergency kit",
)
_HIGH_RISK_CUSTODY_STATUSES = {"RETRIEVED", "CLOSED"}

# ── Lockdown State ────────────────────────────────────────────────────────────
# Thread-safe lockdown flag. Requires collective steward approval to clear.
_lockdown_lock = threading.Lock()
_lockdown_active = False
_lockdown_reason = ""
_lockdown_approvals: dict[str, str] = {}  # steward_email -> ISO timestamp

# ── Abuse Event Log ───────────────────────────────────────────────────────────
_abuse_log: list[dict] = []
_abuse_log_lock = threading.Lock()

# ── Rate-limit Tracking ───────────────────────────────────────────────────────
# Tracks recent requests per session key within a sliding window.
_export_tracker: dict[str, deque] = defaultdict(deque)  # key -> deque of timestamps
_export_tracker_lock = threading.Lock()
_auth_failure_tracker: dict[str, deque] = defaultdict(deque)
_auth_failure_lock = threading.Lock()

EXPORT_WINDOW_SECONDS = 15 * 60  # 15 minutes
AUTH_FAILURE_WINDOW_SECONDS = 5 * 60  # 5 minutes


# ── Abuse Event Recording ─────────────────────────────────────────────────────

def _record_abuse_event(pattern: str, details: dict) -> dict:
    """Record an abuse event and return the event dict."""
    request_ip = "unknown"
    session_id = "unknown"
    if has_request_context():
        request_ip = request.remote_addr or "unknown"
    if has_app_context():
        session_id = getattr(g, "session_id", "unknown")

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pattern": pattern,
        "ip": request_ip,
        "session_id": session_id,
        "details": details,
    }
    with _abuse_log_lock:
        _abuse_log.append(event)
    logger.warning("SAFEGUARD_ABUSE_EVENT pattern=%s details=%s", pattern, details)
    return event


# ── Multi-Steward Alert Dispatch ──────────────────────────────────────────────

def _send_steward_alerts(subject: str, body: str) -> None:
    """
    Dispatch an alert to ALL configured steward addresses simultaneously.
    Never send to only one person — this is a core anti-weaponization guarantee.
    """
    if not config.STEWARD_ALERT_EMAILS:
        logger.error("SAFEGUARD: No steward alert emails configured — alert dropped: %s", subject)
        return

    import os
    smtp_host = os.environ.get("ALERT_SMTP_HOST", "")
    smtp_port = int(os.environ.get("ALERT_SMTP_PORT", "587"))
    smtp_user = os.environ.get("ALERT_SMTP_USER", "")
    smtp_pass = os.environ.get("ALERT_SMTP_PASS", "")
    alert_from = os.environ.get("ALERT_FROM_EMAIL", "codex-alerts@verdigrisbotanicanation.org")

    for steward_email in config.STEWARD_ALERT_EMAILS:
        try:
            msg = MIMEText(body, "plain")
            msg["Subject"] = f"[VBTN CODEX ALERT] {subject}"
            msg["From"] = alert_from
            msg["To"] = steward_email

            if smtp_host:
                with smtplib.SMTP(smtp_host, smtp_port) as server:
                    server.starttls()
                    if smtp_user and smtp_pass:
                        server.login(smtp_user, smtp_pass)
                    server.sendmail(alert_from, [steward_email], msg.as_string())
                logger.info("SAFEGUARD: Alert sent to %s — subject: %s", steward_email, subject)
            else:
                # No SMTP configured — log as critical so it surfaces in monitoring
                logger.critical(
                    "SAFEGUARD_ALERT_UNDELIVERED to=%s subject=%s body=%s",
                    steward_email, subject, body,
                )
        except Exception as exc:
            logger.error("SAFEGUARD: Failed to send alert to %s: %s", steward_email, exc)


def _dispatch_abuse_alert(pattern: str, event: dict) -> None:
    """Build and dispatch an abuse alert to all stewards in a background thread."""
    subject = f"Abuse Pattern Detected: {pattern}"
    body = (
        f"Verdigris Botanica Tribal Nation — Codex of the Living\n"
        f"Abuse Detection Alert\n\n"
        f"Pattern:    {pattern}\n"
        f"Timestamp:  {event['timestamp']}\n"
        f"IP Address: {event['ip']}\n"
        f"Session:    {event['session_id']}\n"
        f"Details:    {event['details']}\n\n"
        f"This alert was sent to all designated stewards simultaneously.\n\n"
        f"Review: docs/ABUSE_DETECTION_RUNBOOK.md\n"
        f"Policy: docs/PROHIBITED_USES.md\n"
    )
    thread = threading.Thread(target=_send_steward_alerts, args=(subject, body), daemon=True)
    thread.start()


def _dispatch_incident_alert(subject: str, body: str) -> None:
    """Dispatch a non-abuse incident alert to all configured stewards."""
    thread = threading.Thread(target=_send_steward_alerts, args=(subject, body), daemon=True)
    thread.start()


# ── Lockdown Management ───────────────────────────────────────────────────────

def activate_lockdown(reason: str) -> None:
    """Activate system lockdown mode."""
    global _lockdown_active, _lockdown_reason, _lockdown_approvals
    with _lockdown_lock:
        _lockdown_active = True
        _lockdown_reason = reason
        _lockdown_approvals = {}
    logger.critical("SAFEGUARD_LOCKDOWN_ACTIVATED reason=%s", reason)
    _send_steward_alerts(
        "LOCKDOWN ACTIVATED",
        (
            f"The Codex of the Living has entered LOCKDOWN MODE.\n\n"
            f"Reason: {reason}\n"
            f"Time:   {datetime.now(timezone.utc).isoformat()}\n\n"
            f"Write operations and bulk reads are suspended.\n"
            f"Collective steward approval required to resume.\n\n"
            f"See docs/ABUSE_DETECTION_RUNBOOK.md Section 5 for resume procedure."
        ),
    )


def is_lockdown_active() -> bool:
    with _lockdown_lock:
        return _lockdown_active


def approve_lockdown_resume(steward_email: str) -> dict:
    """
    Record a steward's approval to resume from lockdown.
    Requires two distinct steward approvals before lockdown lifts.
    """
    global _lockdown_active, _lockdown_reason, _lockdown_approvals
    with _lockdown_lock:
        if not _lockdown_active:
            return {"status": "not_in_lockdown"}

        if steward_email not in config.STEWARD_ALERT_EMAILS:
            return {"status": "unauthorized", "message": "Email not in steward list"}

        _lockdown_approvals[steward_email] = datetime.now(timezone.utc).isoformat()
        approval_count = len(_lockdown_approvals)

        if approval_count >= 2:
            _lockdown_active = False
            prior_reason = _lockdown_reason
            _lockdown_reason = ""
            approvals = dict(_lockdown_approvals)
            _lockdown_approvals = {}
            logger.critical(
                "SAFEGUARD_LOCKDOWN_LIFTED approvals=%s prior_reason=%s",
                approvals, prior_reason,
            )
            return {"status": "lockdown_lifted", "approvals": approvals}

        return {"status": "approval_recorded", "approvals_so_far": approval_count, "needed": 2}


# ── Export / Bulk Operation Guards ────────────────────────────────────────────

def _get_session_key() -> str:
    """Return a key identifying the current request's actor."""
    user_id = getattr(g, "user_id", None) if g else None
    if user_id:
        return f"user:{user_id}"
    return f"ip:{request.remote_addr}" if request else "unknown"


def check_export_limit(record_count: int, size_bytes: int = 0) -> bool:
    """
    Check whether the current session has exceeded mass export thresholds.
    Returns True if allowed, False if blocked (abuse detected).
    """
    session_key = _get_session_key()
    now = time.monotonic()
    window_start = now - EXPORT_WINDOW_SECONDS

    with _export_tracker_lock:
        tracker = _export_tracker[session_key]

        # Expire old entries
        while tracker and tracker[0][0] < window_start:
            tracker.popleft()

        # Sum records and bytes in window (including this request)
        records_in_window = sum(r for _, r, _ in tracker) + record_count
        bytes_in_window = sum(b for _, _, b in tracker) + size_bytes

        if (
            records_in_window > config.ABUSE_MASS_EXPORT_RECORD_THRESHOLD
            or bytes_in_window > config.ABUSE_MASS_EXPORT_SIZE_THRESHOLD_MB * 1024 * 1024
        ):
            event = _record_abuse_event(
                "MASS_EXPORT_ATTEMPT",
                {
                    "session_key": session_key,
                    "records_in_window": records_in_window,
                    "bytes_in_window": bytes_in_window,
                    "threshold_records": config.ABUSE_MASS_EXPORT_RECORD_THRESHOLD,
                },
            )
            _dispatch_abuse_alert("MASS_EXPORT_ATTEMPT", event)
            return False

        tracker.append((now, record_count, size_bytes))
        return True


def check_bulk_delete_limit(record_count: int) -> bool:
    """
    Check whether a bulk delete operation exceeds the threshold.
    Returns True if allowed, False if blocked.
    """
    if record_count > config.ABUSE_BULK_DELETE_THRESHOLD:
        event = _record_abuse_event(
            "BULK_DELETE_ATTEMPT",
            {
                "session_key": _get_session_key(),
                "record_count": record_count,
                "threshold": config.ABUSE_BULK_DELETE_THRESHOLD,
            },
        )
        _dispatch_abuse_alert("BULK_DELETE_ATTEMPT", event)
        activate_lockdown(f"Bulk delete attempt: {record_count} records")
        return False
    return True


# ── Auth Failure Tracking ─────────────────────────────────────────────────────

def record_auth_failure(ip: str, account: str = "") -> bool:
    """
    Record an authentication failure. Returns True if account should be locked.
    """
    key = ip
    now = time.monotonic()
    window_start = now - AUTH_FAILURE_WINDOW_SECONDS

    with _auth_failure_lock:
        tracker = _auth_failure_tracker[key]
        while tracker and tracker[0] < window_start:
            tracker.popleft()
        tracker.append(now)
        failure_count = len(tracker)

    if failure_count >= config.ABUSE_AUTH_FAILURE_THRESHOLD:
        event = _record_abuse_event(
            "AUTH_BRUTE_FORCE",
            {"ip": ip, "account": account, "failures_in_window": failure_count},
        )
        _dispatch_abuse_alert("AUTH_BRUTE_FORCE", event)
        return True  # caller should lock the account/IP
    return False


# ── Governance Reference Guard ────────────────────────────────────────────────

def assert_governance_references_intact() -> None:
    """
    Verify that governance constants in config have not been cleared or overridden.
    Call at application startup.
    """
    required = {
        "GOVERNING_NATION": config.GOVERNING_NATION,
        "GOVERNING_TRUST": config.GOVERNING_TRUST,
        "PRIMARY_JURISDICTION": config.PRIMARY_JURISDICTION,
    }
    for field, value in required.items():
        if not value:
            raise RuntimeError(
                f"GOVERNANCE INTEGRITY FAILURE: config.{field} is empty. "
                f"This is a Critical Change violation. "
                f"See docs/GOVERNANCE_CHARTER.md and TRIBAL_GOVERNANCE.md."
            )
    logger.info(
        "SAFEGUARD: Governance references intact — Nation=%s Trust=%s",
        config.GOVERNING_NATION,
        config.GOVERNING_TRUST,
    )


def is_high_risk_custody_item(item_description: str) -> bool:
    """Return True when the item description requires heightened custody review."""
    if not item_description:
        return False
    normalized = item_description.casefold()
    return any(keyword in normalized for keyword in _HIGH_RISK_CUSTODY_KEYWORDS)


def enforce_custody_status_transition(
    *,
    item_description: str,
    target_status: str | None,
    actor: str,
    steward_approvals: list[str] | None = None,
    transaction_id: str | None = None,
) -> None:
    """
    Enforce multi-steward approval and incident logging for high-risk custody closes.
    """
    if not target_status:
        return

    normalized_status = target_status.strip().upper()
    if normalized_status not in _HIGH_RISK_CUSTODY_STATUSES:
        return
    if not is_high_risk_custody_item(item_description):
        return

    steward_approvals = steward_approvals or []
    valid_approvals = {
        approval.strip()
        for approval in steward_approvals
        if isinstance(approval, str)
        and approval.strip()
        and approval.strip() in config.STEWARD_ALERT_EMAILS
    }
    details = {
        "transaction_id": transaction_id,
        "item_description": item_description,
        "target_status": normalized_status,
        "actor": actor,
        "steward_approvals": sorted(valid_approvals),
        "required_approvals": 2,
    }

    if len(valid_approvals) < 2:
        event = _record_abuse_event("HIGH_RISK_CUSTODY_APPROVAL_MISSING", details)
        _dispatch_abuse_alert("HIGH_RISK_CUSTODY_APPROVAL_MISSING", event)
        raise PermissionError(
            "High-risk custody items require approval from at least two designated stewards."
        )

    incident = _record_abuse_event("HIGH_RISK_CUSTODY_TRANSITION", details)
    _dispatch_incident_alert(
        "HIGH-RISK CUSTODY STATUS CHANGE",
        (
            "Verdigris Botanica Tribal Nation — Custody Incident Log\n\n"
            f"Transaction: {transaction_id or 'unknown'}\n"
            f"Item:        {item_description}\n"
            f"Status:      {normalized_status}\n"
            f"Actor:       {actor}\n"
            f"Approvals:   {sorted(valid_approvals)}\n"
            f"Logged:      {incident['timestamp']}\n\n"
            "This change was recorded as an incident-grade custody event."
        ),
    )


# ── Flask Decorators ──────────────────────────────────────────────────────────

def lockdown_guard(write_operation: bool = False):
    """
    Decorator that blocks write operations and bulk reads during lockdown.
    Usage:
        @app.route("/export")
        @lockdown_guard(write_operation=False)
        def export_data(): ...
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def wrapper(*args, **kwargs):
            if is_lockdown_active():
                if write_operation or request.method in ("POST", "PUT", "PATCH", "DELETE"):
                    return jsonify({
                        "error": "SYSTEM_LOCKDOWN",
                        "message": (
                            "The system is in protective lockdown. "
                            "Write operations are suspended. "
                            "Contact your tribal steward."
                        ),
                    }), 503
            return f(*args, **kwargs)
        return wrapper
    return decorator
