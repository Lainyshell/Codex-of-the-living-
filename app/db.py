"""
Persistence layer — SQLite-backed transaction ledger and immutable audit trail.

Schema
------
transactions
    id                TEXT PRIMARY KEY  (UUID)
    idempotency_key   TEXT UNIQUE NOT NULL
    vendor_id         TEXT NOT NULL
    obligation_id     TEXT NOT NULL
    remic_class       TEXT NOT NULL
    rate_type         TEXT NOT NULL
    principal         TEXT NOT NULL   (stored as Decimal string)
    interest          TEXT NOT NULL
    total             TEXT NOT NULL
    royalty_amount    TEXT NOT NULL
    stripe_payment_id TEXT
    docusign_envelope_id TEXT
    status            TEXT NOT NULL   (pending | stripe_created | docusign_sent |
                                       completed | failed)
    created_at        TEXT NOT NULL   (ISO-8601)
    updated_at        TEXT NOT NULL

audit_events
    id                TEXT PRIMARY KEY  (UUID)
    transaction_id    TEXT NOT NULL
    event_type        TEXT NOT NULL
    payload           TEXT NOT NULL   (JSON)
    created_at        TEXT NOT NULL
"""

import json
import os
import sqlite3
import uuid
import hashlib
from contextlib import contextmanager
from datetime import datetime, timezone

_DB_PATH = os.environ.get("PAYMENTS_DB_PATH", "/tmp/payments.db")

_DDL = """
CREATE TABLE IF NOT EXISTS transactions (
    id                   TEXT PRIMARY KEY,
    idempotency_key      TEXT UNIQUE NOT NULL,
    vendor_id            TEXT NOT NULL,
    obligation_id        TEXT NOT NULL,
    remic_class          TEXT NOT NULL,
    rate_type            TEXT NOT NULL,
    principal            TEXT NOT NULL,
    interest             TEXT NOT NULL,
    total                TEXT NOT NULL,
    royalty_amount       TEXT NOT NULL,
    stripe_payment_id    TEXT,
    docusign_envelope_id TEXT,
    status               TEXT NOT NULL,
    created_at           TEXT NOT NULL,
    updated_at           TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id             TEXT PRIMARY KEY,
    transaction_id TEXT NOT NULL,
    event_type     TEXT NOT NULL,
    payload        TEXT NOT NULL,
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shipping_import_batches (
    id                TEXT PRIMARY KEY,
    source_file       TEXT NOT NULL,
    report_type       TEXT NOT NULL,
    generated_at      TEXT NOT NULL,
    transaction_count INTEGER NOT NULL,
    total_amount      TEXT NOT NULL,
    imported_at       TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS shipping_import_rows (
    id                     TEXT PRIMARY KEY,
    batch_id               TEXT NOT NULL,
    line_number            INTEGER NOT NULL,
    recipient              TEXT,
    address                TEXT,
    date_of_delivery       TEXT,
    form_3811_number       TEXT,
    certified_mail_number  TEXT,
    registered_mail_number TEXT,
    transaction_type       TEXT,
    amount                 TEXT,
    raw_amount             TEXT,
    amount_valid           INTEGER NOT NULL,
    source_reference       TEXT,
    source_status          TEXT
);

CREATE TABLE IF NOT EXISTS docusign_usps_proof_events (
    id               TEXT PRIMARY KEY,
    envelope_id      TEXT NOT NULL,
    event_type       TEXT NOT NULL,
    envelope_status  TEXT,
    event_timestamp  TEXT NOT NULL,
    transaction_id   TEXT,
    usps_reference   TEXT NOT NULL,
    recipient_name   TEXT,
    recipient_email  TEXT,
    source_payload   TEXT NOT NULL,
    created_at       TEXT NOT NULL,
    UNIQUE(envelope_id, event_type, event_timestamp)
);
"""

_VALID_STATUSES = frozenset({
    "pending",
    "stripe_created",
    "docusign_sent",
    "completed",
    "failed",
})


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _conn():
    con = sqlite3.connect(_DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    try:
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def init_db() -> None:
    with _conn() as con:
        con.executescript(_DDL)
        shipping_row_columns = {
            row["name"]
            for row in con.execute("PRAGMA table_info(shipping_import_rows)").fetchall()
        }
        if "id" not in shipping_row_columns:
            con.execute("ALTER TABLE shipping_import_rows ADD COLUMN id TEXT")
        con.execute(
            """
            UPDATE shipping_import_rows
            SET id = lower(hex(randomblob(16)))
            WHERE id IS NULL OR id = ''
            """
        )


def create_transaction(
    *,
    idempotency_key: str,
    vendor_id: str,
    obligation_id: str,
    remic_class: str,
    rate_type: str,
    principal: str,
    interest: str,
    total: str,
    royalty_amount: str,
) -> dict:
    """
    Insert a new transaction record with status=pending.
    Raises ValueError if idempotency_key already exists.
    Returns the created row as a dict.
    """
    txn_id = str(uuid.uuid4())
    now = _now()
    with _conn() as con:
        try:
            con.execute(
                """
                INSERT INTO transactions
                    (id, idempotency_key, vendor_id, obligation_id,
                     remic_class, rate_type, principal, interest,
                     total, royalty_amount, status, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    txn_id, idempotency_key, vendor_id, obligation_id,
                    remic_class, rate_type, principal, interest,
                    total, royalty_amount, "pending", now, now,
                ),
            )
        except sqlite3.IntegrityError:
            raise ValueError(
                f"Duplicate idempotency_key: {idempotency_key!r}"
            )
    return get_transaction_by_id(txn_id)


def get_transaction_by_idempotency_key(key: str) -> dict | None:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM transactions WHERE idempotency_key = ?", (key,)
        ).fetchone()
    return dict(row) if row else None


def get_transaction_by_id(txn_id: str) -> dict | None:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM transactions WHERE id = ?", (txn_id,)
        ).fetchone()
    return dict(row) if row else None


def get_transaction_by_docusign_envelope_id(envelope_id: str) -> dict | None:
    with _conn() as con:
        row = con.execute(
            "SELECT * FROM transactions WHERE docusign_envelope_id = ?",
            (envelope_id,),
        ).fetchone()
    return dict(row) if row else None


def update_transaction_status(
    txn_id: str,
    status: str,
    *,
    stripe_payment_id: str | None = None,
    docusign_envelope_id: str | None = None,
) -> None:
    if status not in _VALID_STATUSES:
        raise ValueError(f"Invalid status {status!r}")
    now = _now()
    with _conn() as con:
        if stripe_payment_id and docusign_envelope_id:
            con.execute(
                """UPDATE transactions
                   SET status=?, stripe_payment_id=?, docusign_envelope_id=?, updated_at=?
                   WHERE id=?""",
                (status, stripe_payment_id, docusign_envelope_id, now, txn_id),
            )
        elif stripe_payment_id:
            con.execute(
                """UPDATE transactions
                   SET status=?, stripe_payment_id=?, updated_at=?
                   WHERE id=?""",
                (status, stripe_payment_id, now, txn_id),
            )
        elif docusign_envelope_id:
            con.execute(
                """UPDATE transactions
                   SET status=?, docusign_envelope_id=?, updated_at=?
                   WHERE id=?""",
                (status, docusign_envelope_id, now, txn_id),
            )
        else:
            con.execute(
                "UPDATE transactions SET status=?, updated_at=? WHERE id=?",
                (status, now, txn_id),
            )


def append_audit_event(
    transaction_id: str, event_type: str, payload: dict
) -> None:
    with _conn() as con:
        con.execute(
            """INSERT INTO audit_events (id, transaction_id, event_type, payload, created_at)
               VALUES (?,?,?,?,?)""",
            (
                str(uuid.uuid4()),
                transaction_id,
                event_type,
                json.dumps(payload),
                _now(),
            ),
        )


def get_audit_trail(transaction_id: str) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM audit_events WHERE transaction_id=? ORDER BY created_at",
            (transaction_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def create_shipping_import(report: dict) -> dict:
    batch_id = str(uuid.uuid4())
    imported_at = _now()
    transactions = report.get("transactions", [])
    source_file = report.get("source_file", "")
    report_type = report.get("report_type", "usps_shipping")
    generated_at = report.get("generated_at", imported_at)
    transaction_count = len(transactions)
    total_amount = str(report.get("total_amount", 0))

    with _conn() as con:
        con.execute(
            """
            INSERT INTO shipping_import_batches
                (id, source_file, report_type, generated_at,
                 transaction_count, total_amount, imported_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                batch_id,
                source_file,
                report_type,
                generated_at,
                transaction_count,
                total_amount,
                imported_at,
            ),
        )

        for row in transactions:
            amount = row.get("amount")
            raw_amount = row.get("raw_amount")
            con.execute(
                """
                INSERT INTO shipping_import_rows
                    (id, batch_id, line_number, recipient, address, date_of_delivery,
                     form_3811_number, certified_mail_number, registered_mail_number,
                     transaction_type, amount, raw_amount, amount_valid,
                     source_reference, source_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    batch_id,
                    int(row.get("line_number", 0)),
                    row.get("recipient"),
                    row.get("address"),
                    row.get("date_of_delivery"),
                    row.get("form_3811_number"),
                    row.get("certified_mail_number"),
                    row.get("registered_mail_number"),
                    row.get("transaction_type"),
                    str(amount) if amount is not None else None,
                    str(raw_amount) if raw_amount is not None else None,
                    1 if row.get("amount_valid") else 0,
                    row.get("source_reference"),
                    row.get("source_status"),
                ),
            )

    return {
        "id": batch_id,
        "source_file": source_file,
        "report_type": report_type,
        "generated_at": generated_at,
        "transaction_count": transaction_count,
        "total_amount": total_amount,
        "imported_at": imported_at,
        "transactions": transactions,
    }


def get_shipping_import_batch(batch_id: str) -> dict | None:
    with _conn() as con:
        batch = con.execute(
            "SELECT * FROM shipping_import_batches WHERE id = ?",
            (batch_id,),
        ).fetchone()
        if not batch:
            return None

        rows = con.execute(
            """
            SELECT id, line_number, recipient, address, date_of_delivery, form_3811_number,
                   certified_mail_number, registered_mail_number, transaction_type,
                   amount, raw_amount, amount_valid, source_reference, source_status
            FROM shipping_import_rows
            WHERE batch_id = ?
            ORDER BY line_number
            """,
            (batch_id,),
        ).fetchall()

    payload = dict(batch)
    payload["transactions"] = [
        {
            **dict(row),
            "amount_valid": bool(row["amount_valid"]),
        }
        for row in rows
    ]
    return payload


def create_docusign_usps_proof_event(
    *,
    envelope_id: str,
    event_type: str,
    envelope_status: str | None,
    event_timestamp: str | None,
    transaction_id: str | None,
    recipient_name: str | None,
    recipient_email: str | None,
    source_payload: dict,
) -> dict:
    if not event_timestamp:
        payload_fingerprint = hashlib.sha256(
            json.dumps(source_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()[:24]
        event_timestamp = f"hash-{payload_fingerprint}"

    normalized_timestamp = (
        event_timestamp[:19]
        .replace(":", "")
        .replace("-", "")
        .replace("T", "")
    )
    usps_reference = (
        f"USPS-PROOF-{envelope_id}-{normalized_timestamp}"
    )
    created_at = _now()

    with _conn() as con:
        con.execute(
            """
            INSERT OR IGNORE INTO docusign_usps_proof_events
                (id, envelope_id, event_type, envelope_status, event_timestamp,
                 transaction_id, usps_reference, recipient_name, recipient_email,
                 source_payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid.uuid4()),
                envelope_id,
                event_type,
                envelope_status,
                event_timestamp,
                transaction_id,
                usps_reference,
                recipient_name,
                recipient_email,
                json.dumps(source_payload),
                created_at,
            ),
        )
        row = con.execute(
            """
            SELECT * FROM docusign_usps_proof_events
            WHERE envelope_id = ? AND event_type = ? AND event_timestamp = ?
            """,
            (envelope_id, event_type, event_timestamp),
        ).fetchone()

    if not row:
        raise RuntimeError("Unable to persist USPS proof event")
    return dict(row)


def list_docusign_usps_proof_events(envelope_id: str) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            """
            SELECT id, envelope_id, event_type, envelope_status, event_timestamp,
                   transaction_id, usps_reference, recipient_name, recipient_email,
                   created_at
            FROM docusign_usps_proof_events
            WHERE envelope_id = ?
            ORDER BY event_timestamp, created_at
            """,
            (envelope_id,),
        ).fetchall()
    return [dict(row) for row in rows]
