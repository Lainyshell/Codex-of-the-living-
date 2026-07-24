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
