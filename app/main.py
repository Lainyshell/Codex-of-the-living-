
import os
import uuid

import requests
from flask import Flask, jsonify, request

import db
import payments
import remic

app = Flask(__name__)

# Initialise the database on startup
db.init_db()


# ---------------------------------------------------------------------------
# Existing endpoints — unchanged
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return {"status": "ok"}


@app.route("/rates")
def get_rates():
    # Declare string with the URL
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?page[number]=1&page[size]=10"

    headers = {
        "Content-Type": "application/json",
    }

    # Fetch the data with timeout to prevent hanging
    response = requests.get(url, headers=headers, timeout=10)

    if response.status_code != 200:
        return {
            "status": "error",
            "code": response.status_code,
            "message": "Failed to fetch rates from Treasury API",
        }

    # Convert the response to JSON
    data = response.json()

    # Return the data
    return data


# ---------------------------------------------------------------------------
# Scan-based payment endpoint
# ---------------------------------------------------------------------------

_REQUIRED_SCAN_FIELDS = {
    "vendor_id",
    "obligation_id",
    "principal_amount",
    "rate_type",
    "remic_class",
    "pass_through_rate",
    "days",
}


@app.route("/api/scan-payment", methods=["POST"])
def scan_payment():
    """
    Accept a QR-scan payment payload, calculate REMIC interest,
    create a Stripe PaymentIntent, and route a DocuSign envelope.

    Required JSON fields:
        vendor_id         str
        vendor_name       str
        vendor_email      str
        obligation_id     str
        principal_amount  number  (positive)
        rate_type         str     "gov_obligation" | "royalty"
        remic_class       str     "A" | "B" | "IO" | "PO"
        pass_through_rate number  (annual rate, e.g. 0.05 for 5 %)
        days              int     (accrual period in days, positive)

    Optional fields (required for IO class):
        notional          number
        io_rate           number

    Optional fields (required for royalty rate_type):
        gross_revenue     number
        royalty_rate      number

    Optional:
        idempotency_key   str  — supply your own; a UUID is generated if absent
    """
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Request body must be valid JSON"}), 400

    missing = _REQUIRED_SCAN_FIELDS - set(body.keys())
    if missing:
        return jsonify({"error": f"Missing required fields: {sorted(missing)}"}), 400

    vendor_name = body.get("vendor_name", "").strip()
    vendor_email = body.get("vendor_email", "").strip()
    if not vendor_name or not vendor_email:
        return jsonify({"error": "vendor_name and vendor_email are required"}), 400

    idempotency_key = body.get("idempotency_key") or str(uuid.uuid4())

    # --- Check for duplicate submission ---
    existing = db.get_transaction_by_idempotency_key(idempotency_key)
    if existing:
        return jsonify({"status": "duplicate", "transaction": existing}), 200

    # --- REMIC calculation ---
    try:
        calc = remic.calculate_interest(
            principal=body["principal_amount"],
            pass_through_rate=body["pass_through_rate"],
            days=int(body["days"]),
            remic_class=body["remic_class"],
            rate_type=body["rate_type"],
            notional=body.get("notional"),
            io_rate=body.get("io_rate"),
            gross_revenue=body.get("gross_revenue"),
            royalty_rate=body.get("royalty_rate"),
        )
    except (ValueError, TypeError) as exc:
        return jsonify({"error": f"REMIC calculation error: {exc}"}), 422

    principal_str = str(calc["total_amount"] - calc["interest_amount"])
    interest_str = str(calc["interest_amount"])
    total_str = str(calc["total_amount"])
    royalty_str = str(calc["royalty_amount"])

    # Total in cents for Stripe (USD)
    try:
        total_cents = int(float(total_str) * 100)
    except (ValueError, OverflowError):
        return jsonify({"error": "Unable to compute total amount in cents"}), 422
    if total_cents <= 0:
        return jsonify({"error": "Computed total must be positive"}), 422

    # --- Persist initial transaction record ---
    try:
        txn = db.create_transaction(
            idempotency_key=idempotency_key,
            vendor_id=body["vendor_id"],
            obligation_id=body["obligation_id"],
            remic_class=body["remic_class"],
            rate_type=body["rate_type"],
            principal=principal_str,
            interest=interest_str,
            total=total_str,
            royalty_amount=royalty_str,
        )
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 409

    txn_id = txn["id"]
    db.append_audit_event(txn_id, "scan_received", {
        "vendor_id": body["vendor_id"],
        "obligation_id": body["obligation_id"],
        "remic_class": body["remic_class"],
        "rate_type": body["rate_type"],
        "principal": principal_str,
        "interest": interest_str,
        "total": total_str,
    })

    # --- Stripe PaymentIntent ---
    template_key = f"{body['rate_type']}_{body['remic_class']}"
    try:
        stripe_result = payments.create_stripe_payment(
            amount_cents=total_cents,
            vendor_id=body["vendor_id"],
            obligation_id=body["obligation_id"],
            remic_class=body["remic_class"],
            interest_amount=interest_str,
            docusign_template=template_key,
            idempotency_key=f"stripe-{idempotency_key}",
        )
    except RuntimeError as exc:
        db.update_transaction_status(txn_id, "failed")
        db.append_audit_event(txn_id, "stripe_error", {"error": str(exc)})
        return jsonify({"error": f"Payment creation failed: {exc}"}), 502

    db.update_transaction_status(
        txn_id, "stripe_created",
        stripe_payment_id=stripe_result["stripe_payment_id"],
    )
    db.append_audit_event(txn_id, "stripe_created", {
        "stripe_payment_id": stripe_result["stripe_payment_id"],
        "status": stripe_result["status"],
    })

    # --- DocuSign envelope ---
    try:
        ds_result = payments.send_docusign_envelope(
            vendor_name=vendor_name,
            vendor_email=vendor_email,
            rate_type=body["rate_type"],
            remic_class=body["remic_class"],
            principal=principal_str,
            interest=interest_str,
            total=total_str,
            stripe_payment_id=stripe_result["stripe_payment_id"],
            vendor_id=body["vendor_id"],
            obligation_id=body["obligation_id"],
            transaction_id=txn_id,
        )
    except RuntimeError as exc:
        db.update_transaction_status(txn_id, "failed")
        db.append_audit_event(txn_id, "docusign_error", {"error": str(exc)})
        return jsonify({"error": f"DocuSign routing failed: {exc}"}), 502

    db.update_transaction_status(
        txn_id, "docusign_sent",
        docusign_envelope_id=ds_result["envelope_id"],
    )
    db.append_audit_event(txn_id, "docusign_sent", {
        "envelope_id": ds_result["envelope_id"],
        "envelope_status": ds_result["status"],
    })

    return jsonify({
        "status": "docusign_sent",
        "transaction_id": txn_id,
        "stripe_payment_id": stripe_result["stripe_payment_id"],
        "envelope_id": ds_result["envelope_id"],
        "principal": principal_str,
        "interest": interest_str,
        "total": total_str,
    }), 201


# ---------------------------------------------------------------------------
# DocuSign webhook endpoint
# ---------------------------------------------------------------------------

@app.route("/api/docusign-webhook", methods=["POST"])
def docusign_webhook():
    """
    Receive DocuSign Connect webhook callbacks.

    DocuSign must be configured to POST to this URL and to include an
    HMAC-SHA256 signature in the X-DocuSign-Signature-1 header.

    The shared HMAC key must be set in DOCUSIGN_HMAC_KEY.
    """
    hmac_key = os.environ.get("DOCUSIGN_HMAC_KEY", "")
    if not hmac_key:
        return jsonify({"error": "Webhook authentication is not configured"}), 500

    signature = request.headers.get("X-DocuSign-Signature-1", "")
    if not signature:
        return jsonify({"error": "Missing signature header"}), 401

    raw_body = request.get_data()
    if not payments.verify_docusign_hmac(raw_body, signature, hmac_key):
        return jsonify({"error": "Signature verification failed"}), 401

    body = request.get_json(silent=True)
    if not body:
        return jsonify({"error": "Invalid JSON body"}), 400

    envelope_id = (
        body.get("envelopeId")
        or body.get("data", {}).get("envelopeId")
    )
    event_type = body.get("event", "")

    if not envelope_id:
        return jsonify({"error": "envelopeId not found in payload"}), 400

    if event_type != "envelope-completed":
        # Accept but take no action for non-completion events
        return jsonify({"status": "accepted", "event": event_type}), 200

    # Find the corresponding transaction
    with db._conn() as con:
        row = con.execute(
            "SELECT * FROM transactions WHERE docusign_envelope_id = ?",
            (envelope_id,),
        ).fetchone()

    if not row:
        return jsonify({"error": f"No transaction found for envelope {envelope_id}"}), 404

    txn = dict(row)
    txn_id = txn["id"]

    if txn["status"] == "completed":
        # Idempotent — already processed
        return jsonify({"status": "already_completed", "transaction_id": txn_id}), 200

    db.update_transaction_status(txn_id, "completed")
    db.append_audit_event(txn_id, "envelope_completed", {
        "envelope_id": envelope_id,
        "docusign_event": event_type,
        "raw_status": body.get("status"),
    })

    return jsonify({
        "status": "completed",
        "transaction_id": txn_id,
        "envelope_id": envelope_id,
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0")
