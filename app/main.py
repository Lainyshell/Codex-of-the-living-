import csv
import io
import json
import re
import sqlite3
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ET

import os
import uuid

import requests
from flask import Flask, Response, jsonify, request
from flask_cors import CORS

import config
import db
import payments
import remic
import safeguards

app = Flask(__name__)
# CORS — FCC FRN 0037987799
CORS(app)

# Verify governance references are intact at startup.
# Any tampering with config.py governance constants will cause startup failure.
safeguards.assert_governance_references_intact()
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SHIPPING_SOURCE = REPO_ROOT / "Verified_Transactions_Template.xlsx"
XML_NAMESPACES = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
FIELD_ALIASES = {
    "recipient": ["Recipient", "Name"],
    "address": ["Address"],
    "date_of_delivery": ["Date of Delivery", "Payment Date", "timestamp"],
    "form_3811_number": ["Form 3811 Number", "voucher_number", "AccountID"],
    "certified_mail_number": ["Certified Mail Number"],
    "registered_mail_number": ["Registered Mail Number"],
    "transaction_type": ["Transaction Type", "Role", "Subject"],
    "amount": ["Amount"],
    "source_reference": ["po_number", "account_number", "routing_number"],
    "source_status": ["status"],
}


def parse_decimal(value):
    if value in (None, ""):
        return None

    try:
        return Decimal(str(value).replace(",", "").strip())
    except (InvalidOperation, AttributeError):
        return None


def get_row_value(row, field_name):
    for alias in FIELD_ALIASES[field_name]:
        value = row.get(alias)
        if value in (None, ""):
            value = row.get(alias.lower())
        if value not in (None, ""):
            return value
    return ""


def read_xlsx_rows(path):
    with zipfile.ZipFile(path) as workbook:
        shared_strings = []

        if "xl/sharedStrings.xml" in workbook.namelist():
            root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
            for item in root.findall("main:si", XML_NAMESPACES):
                shared_strings.append(
                    "".join(
                        text.text or ""
                        for text in item.iterfind(".//main:t", XML_NAMESPACES)
                    )
                )

        sheet = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        rows = []

        for row in sheet.findall(".//main:sheetData/main:row", XML_NAMESPACES):
            values_by_index = {}
            for cell in row.findall("main:c", XML_NAMESPACES):
                cell_value = cell.find("main:v", XML_NAMESPACES)
                cell_reference = cell.attrib.get("r", "")
                column_letters = re.match(r"([A-Z]+)", cell_reference)
                column_index = 0

                if column_letters:
                    for letter in column_letters.group(1):
                        column_index = (column_index * 26) + (ord(letter) - 64)
                    column_index -= 1

                if cell_value is None:
                    value = ""
                elif cell.attrib.get("t") == "s":
                    value = shared_strings[int(cell_value.text)]
                else:
                    value = cell_value.text
                values_by_index[column_index] = value

            values = [
                values_by_index.get(index, "")
                for index in range(max(values_by_index, default=-1) + 1)
            ]
            rows.append(values)

        if not rows:
            return []

        headers = rows[0]
        return [dict(zip(headers, row)) for row in rows[1:] if any(row)]


def read_csv_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def read_json_rows(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def load_source_rows(path):
    if path.suffix.lower() == ".xlsx":
        return read_xlsx_rows(path)
    if path.suffix.lower() == ".csv":
        return read_csv_rows(path)
    if path.suffix.lower() == ".json":
        return read_json_rows(path)
    raise ValueError("Unsupported data source format")


def normalize_shipping_row(row, index):
    raw_amount = get_row_value(row, "amount")
    amount_value = parse_decimal(raw_amount)
    return {
        "line_number": index,
        "recipient": get_row_value(row, "recipient"),
        "address": get_row_value(row, "address"),
        "date_of_delivery": get_row_value(row, "date_of_delivery"),
        "form_3811_number": get_row_value(row, "form_3811_number"),
        "certified_mail_number": get_row_value(row, "certified_mail_number"),
        "registered_mail_number": get_row_value(row, "registered_mail_number"),
        "transaction_type": get_row_value(row, "transaction_type"),
        "amount": str(amount_value) if amount_value is not None else None,
        "raw_amount": raw_amount or None,
        "amount_valid": amount_value is not None,
        "source_reference": get_row_value(row, "source_reference"),
        "source_status": get_row_value(row, "source_status"),
    }


def resolve_source_path(source_name):
    if ".." in source_name or "/" in source_name or "\\" in source_name:
        raise ValueError("Invalid source path")

    available_sources = {
        path.name: path
        for suffix in ("*.xlsx", "*.csv", "*.json")
        for path in REPO_ROOT.glob(suffix)
        if path.is_file()
    }
    candidate = available_sources.get(source_name)
    if candidate is None:
        raise FileNotFoundError("Shipping source file was not found")

    resolved_candidate = candidate.resolve()
    if not resolved_candidate.is_relative_to(REPO_ROOT):
        raise ValueError("Invalid source path")

    return resolved_candidate


def build_shipping_report(source_path):
    rows = load_source_rows(source_path)
    transactions = [
        normalize_shipping_row(row, index)
        for index, row in enumerate(rows, start=1)
    ]
    valid_amounts = [
        Decimal(transaction["amount"])
        for transaction in transactions
        if transaction["amount"] is not None
    ]
    total_amount = sum(
        valid_amounts,
        Decimal("0"),
    )
    return {
        "status": "ok",
        "report_type": "usps_shipping",
        "source_file": source_path.name,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "transaction_count": len(transactions),
        "total_amount": float(total_amount),
        "transactions": transactions,
    }


def build_shipping_report_csv(report):
    output = io.StringIO()
    fieldnames = [
        "line_number",
        "recipient",
        "address",
        "date_of_delivery",
        "form_3811_number",
        "certified_mail_number",
        "registered_mail_number",
        "transaction_type",
        "amount",
        "raw_amount",
        "amount_valid",
        "source_reference",
        "source_status",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(report["transactions"])
    return output.getvalue()


def _extract_envelope_event_timestamp(body):
    return (
        body.get("eventDateTime")
        or body.get("generatedDateTime")
        or body.get("data", {}).get("eventDateTime")
        or body.get("data", {}).get("generatedDateTime")
    )


def _extract_envelope_recipient(body):
    if not isinstance(body, dict):
        return None, None

    data = body.get("data", {})
    recipient_name = (
        body.get("recipientName")
        or data.get("recipientName")
        or body.get("recipient", {}).get("name", "")
    )
    recipient_email = (
        body.get("recipientEmail")
        or data.get("recipientEmail")
        or body.get("recipient", {}).get("email", "")
    )
    return recipient_name or None, recipient_email or None

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
@app.route("/shipping-report")
def get_shipping_report():
    source_name = request.args.get("source", DEFAULT_SHIPPING_SOURCE.name)
    output_format = request.args.get("format", "json").lower()

    try:
        source_path = resolve_source_path(source_name)
        report = build_shipping_report(source_path)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid shipping source request."}), 400
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Shipping source file was not found."}), 404

    if output_format == "json":
        return jsonify(report)
    if output_format == "csv":
        safe_filename = re.sub(r"[^A-Za-z0-9._-]+", "-", source_path.stem).strip("-")
        filename_prefix = safe_filename or "shipping-report"
        filename = f"{filename_prefix}.csv"
        return Response(
            build_shipping_report_csv(report),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    return jsonify({
        "status": "error",
        "message": "Unsupported format. Use json or csv.",
    }), 400


@app.route("/api/shipping-import", methods=["POST"])
def import_shipping_report():
    body = request.get_json(silent=True) or {}
    source_name = body.get("source") or request.args.get(
        "source",
        DEFAULT_SHIPPING_SOURCE.name,
    )

    try:
        source_path = resolve_source_path(source_name)
        report = build_shipping_report(source_path)
        batch = db.create_shipping_import(report)
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid shipping source request."}), 400
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Shipping source file was not found."}), 404
    except sqlite3.DatabaseError:
        return jsonify({"status": "error", "message": "Shipping import persistence failed."}), 500

    return jsonify({
        "status": "imported",
        "import_batch_id": batch["id"],
        "source_file": batch["source_file"],
        "report_type": batch["report_type"],
        "generated_at": batch["generated_at"],
        "imported_at": batch["imported_at"],
        "transaction_count": batch["transaction_count"],
        "total_amount": batch["total_amount"],
    }), 201


@app.route("/api/shipping-import/<batch_id>")
def get_shipping_import(batch_id):
    batch = db.get_shipping_import_batch(batch_id)
    if batch is None:
        return jsonify({"status": "error", "message": "Import batch not found."}), 404

    return jsonify({
        "status": "ok",
        "import_batch": {
            "id": batch["id"],
            "source_file": batch["source_file"],
            "report_type": batch["report_type"],
            "generated_at": batch["generated_at"],
            "imported_at": batch["imported_at"],
            "transaction_count": batch["transaction_count"],
            "total_amount": batch["total_amount"],
        },
        "transactions": batch["transactions"],
    }), 200


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
        return jsonify({"error": "REMIC calculation error: invalid input values"}), 422

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
        return jsonify({"error": "Transaction conflict: duplicate submission"}), 409

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
        return jsonify({"error": "Payment creation failed. Check server logs."}), 502

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
        return jsonify({"error": "DocuSign routing failed. Check server logs."}), 502

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
    envelope_status = body.get("status") or body.get("data", {}).get("status")

    if not envelope_id:
        return jsonify({"error": "envelopeId not found in payload"}), 400

    event_timestamp = _extract_envelope_event_timestamp(body)
    recipient_name, recipient_email = _extract_envelope_recipient(body)

    # Find the corresponding transaction (if any)
    txn = None
    with db._conn() as con:
        row = con.execute(
            "SELECT * FROM transactions WHERE docusign_envelope_id = ?",
            (envelope_id,),
        ).fetchone()
        if row:
            txn = dict(row)

    proof_event = db.create_docusign_usps_proof_event(
        envelope_id=envelope_id,
        event_type=event_type or "unknown",
        envelope_status=envelope_status,
        event_timestamp=event_timestamp,
        transaction_id=txn["id"] if txn else None,
        recipient_name=recipient_name,
        recipient_email=recipient_email,
        source_payload=body,
    )

    if event_type != "envelope-completed":
        return jsonify({
            "status": "accepted",
            "event": event_type,
            "envelope_id": envelope_id,
            "usps_reference": proof_event["usps_reference"],
            "proof_event_id": proof_event["id"],
        }), 200

    if not txn:
        return jsonify({
            "status": "tracked",
            "event": event_type,
            "envelope_id": envelope_id,
            "usps_reference": proof_event["usps_reference"],
            "proof_event_id": proof_event["id"],
            "message": "Envelope recorded for USPS proof without local transaction.",
        }), 200

    txn_id = txn["id"]

    if txn["status"] == "completed":
        # Idempotent — already processed
        return jsonify({
            "status": "already_completed",
            "transaction_id": txn_id,
            "usps_reference": proof_event["usps_reference"],
            "proof_event_id": proof_event["id"],
        }), 200

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
        "usps_reference": proof_event["usps_reference"],
        "proof_event_id": proof_event["id"],
    }), 200


@app.route("/api/usps-proof/<envelope_id>")
def get_usps_proof(envelope_id):
    events = db.list_docusign_usps_proof_events(envelope_id)
    if not events:
        return jsonify({"status": "error", "message": "No USPS proof events found."}), 404
    return jsonify({"status": "ok", "envelope_id": envelope_id, "events": events}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0")
