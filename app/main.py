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
import custody
import db
import payments
import remic
import royalty_engine
import safeguards
import sovereign_vocabulary

app = Flask(__name__)
# CORS — FCC FRN 0037987799
CORS(app)

# Verify governance references are intact at startup.
# Any tampering with config.py governance constants will cause startup failure.
safeguards.assert_governance_references_intact()
# Verify the Sovereign Vocabulary Dictionary is intact.
sovereign_vocabulary.assert_vocabulary_intact()
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
        return None, None, None, None, None, None, None

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

    # Address metadata: DocuSign may nest under data.envelopeSummary.recipients.signers[0]
    # or under body.recipient directly.
    signer: dict = {}
    summary = data.get("envelopeSummary", {}) or {}
    signers = summary.get("recipients", {}).get("signers", [])
    if signers and isinstance(signers, list):
        signer = signers[0] if isinstance(signers[0], dict) else {}
    if not signer:
        signer = body.get("recipient", {}) or {}

    tabs = signer.get("tabs", {}) or {}
    address_tabs = tabs.get("addressTabs", []) or []
    tab_map: dict[str, str] = {}
    for tab in address_tabs:
        if isinstance(tab, dict):
            label = (tab.get("tabLabel") or "").lower()
            val = tab.get("value") or ""
            if val:
                tab_map[label] = val

    recipient_address = tab_map.get("address") or signer.get("address") or None
    recipient_city = tab_map.get("city") or signer.get("city") or None
    recipient_state = tab_map.get("state") or signer.get("state") or None
    recipient_zip = (
        tab_map.get("zip") or tab_map.get("postalcode")
        or signer.get("zip") or signer.get("postalCode") or None
    )
    recipient_phone = (
        tab_map.get("phone") or signer.get("phone") or signer.get("phoneNumber") or None
    )

    return (
        recipient_name or None,
        recipient_email or None,
        recipient_address,
        recipient_city,
        recipient_state,
        recipient_zip,
        recipient_phone,
    )

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


@app.route("/api/custody/envelopes", methods=["POST"])
def create_custody_envelope():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Request body must be valid JSON"}), 400

    try:
        envelope = custody.create_envelope(body)
    except FileExistsError:
        return jsonify({"status": "error", "message": "Custody envelope already exists."}), 409
    except (FileNotFoundError, ValueError) as exc:
        app.logger.warning("Custody envelope create rejected: %s", exc)
        return jsonify({"status": "error", "message": "Custody envelope request was invalid."}), 400

    return jsonify({
        "status": "created",
        "transaction_id": envelope["transaction_id"],
        "custody_status": envelope["custody_status"],
        "locker_facility_id": envelope["locker_facility_id"],
        "event_count": len(envelope["events"]),
    }), 201


@app.route("/api/custody/envelopes/<transaction_id>")
def get_custody_envelope(transaction_id):
    try:
        envelope = custody.get_envelope(transaction_id)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Custody envelope not found."}), 404
    except ValueError as exc:
        app.logger.warning("Custody envelope read rejected: %s", exc)
        return jsonify({"status": "error", "message": "Custody envelope request was invalid."}), 400
    return jsonify({"status": "ok", "envelope": envelope}), 200


@app.route("/api/custody/events", methods=["POST"])
def ingest_custody_event():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Request body must be valid JSON"}), 400

    try:
        envelope = custody.ingest_event_payload(body)
    except FileNotFoundError:
        return jsonify({"status": "error", "message": "Custody envelope not found."}), 404
    except PermissionError as exc:
        app.logger.warning("Custody event rejected: %s", exc)
        return jsonify({
            "status": "error",
            "message": "High-risk custody items require approval from at least two designated stewards.",
        }), 403
    except ValueError as exc:
        app.logger.warning("Custody event rejected: %s", exc)
        return jsonify({"status": "error", "message": "Custody event request was invalid."}), 400

    return jsonify({
        "status": "appended",
        "transaction_id": envelope["transaction_id"],
        "custody_status": envelope["custody_status"],
        "event_count": len(envelope["events"]),
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
    (
        recipient_name,
        recipient_email,
        recipient_address,
        recipient_city,
        recipient_state,
        recipient_zip,
        recipient_phone,
    ) = _extract_envelope_recipient(body)

    # Find the corresponding transaction (if any)
    txn = db.get_transaction_by_docusign_envelope_id(envelope_id)

    proof_event = db.create_docusign_usps_proof_event(
        envelope_id=envelope_id,
        event_type=event_type or "unknown",
        envelope_status=envelope_status,
        event_timestamp=event_timestamp,
        transaction_id=txn["id"] if txn else None,
        recipient_name=recipient_name,
        recipient_email=recipient_email,
        recipient_address=recipient_address,
        recipient_city=recipient_city,
        recipient_state=recipient_state,
        recipient_zip=recipient_zip,
        recipient_phone=recipient_phone,
        source_payload=body,
    )
    custody_envelope = custody.append_docusign_event(
        transaction_id=txn["id"] if txn else None,
        envelope_id=envelope_id,
        event_type=event_type or "unknown",
        envelope_status=envelope_status,
        payload=body,
    )

    # ── Economic-return layer: post tribal returns for every envelope event ──
    tribal_return_ids = _post_tribal_returns(
        envelope_id=envelope_id,
        envelope_status=envelope_status or event_type or "unknown",
        txn=txn,
        body=body,
    )

    # ── Insurance claim auto-trigger ──
    claim_id = _maybe_create_insurance_claim(
        envelope_id=envelope_id,
        event_type=event_type or "",
        envelope_status=envelope_status,
        txn=txn,
        body=body,
    )

    # ── COD transaction auto-trigger ──
    cod_id = _maybe_create_cod_transaction(
        envelope_id=envelope_id,
        proof_event=proof_event,
        txn=txn,
        body=body,
        recipient_name=recipient_name,
        recipient_address=recipient_address,
    )

    if event_type != "envelope-completed":
        response_payload = {
            "status": "accepted",
            "event": event_type,
            "envelope_id": envelope_id,
            "usps_reference": proof_event["usps_reference"],
            "proof_event_id": proof_event["id"],
            "tribal_returns": tribal_return_ids,
        }
        if claim_id:
            response_payload["insurance_claim_id"] = claim_id
        if cod_id:
            response_payload["cod_transaction_id"] = cod_id
        if custody_envelope:
            response_payload["custody_status"] = custody_envelope["custody_status"]
        return jsonify(response_payload), 200

    if not txn:
        response_payload = {
            "status": "tracked",
            "event": event_type,
            "envelope_id": envelope_id,
            "usps_reference": proof_event["usps_reference"],
            "proof_event_id": proof_event["id"],
            "tribal_returns": tribal_return_ids,
            "message": "Envelope recorded for USPS proof without local transaction.",
        }
        if claim_id:
            response_payload["insurance_claim_id"] = claim_id
        if cod_id:
            response_payload["cod_transaction_id"] = cod_id
        if custody_envelope:
            response_payload["custody_status"] = custody_envelope["custody_status"]
        return jsonify(response_payload), 200

    txn_id = txn["id"]

    if txn["status"] == "completed":
        # Idempotent — already processed
        response_payload = {
            "status": "already_completed",
            "transaction_id": txn_id,
            "usps_reference": proof_event["usps_reference"],
            "proof_event_id": proof_event["id"],
            "tribal_returns": tribal_return_ids,
        }
        if claim_id:
            response_payload["insurance_claim_id"] = claim_id
        if cod_id:
            response_payload["cod_transaction_id"] = cod_id
        if custody_envelope:
            response_payload["custody_status"] = custody_envelope["custody_status"]
        return jsonify(response_payload), 200

    db.update_transaction_status(txn_id, "completed")
    db.append_audit_event(txn_id, "envelope_completed", {
        "envelope_id": envelope_id,
        "docusign_event": event_type,
        "raw_status": body.get("status"),
    })

    response_payload = {
        "status": "completed",
        "transaction_id": txn_id,
        "envelope_id": envelope_id,
        "usps_reference": proof_event["usps_reference"],
        "proof_event_id": proof_event["id"],
        "tribal_returns": tribal_return_ids,
    }
    if claim_id:
        response_payload["insurance_claim_id"] = claim_id
    if cod_id:
        response_payload["cod_transaction_id"] = cod_id
    if custody_envelope:
        response_payload["custody_status"] = custody_envelope["custody_status"]
    return jsonify(response_payload), 200


def _post_tribal_returns(
    *,
    envelope_id: str,
    envelope_status: str,
    txn: dict | None,
    body: dict,
) -> list[str]:
    """
    Calculate and persist tribal economic returns for an envelope event.
    Attempts to post each return to Stripe; logs failures without blocking
    the webhook response.  Returns a list of created tribal_return record IDs.
    """
    principal = None
    gross_revenue = None
    if txn:
        try:
            principal = txn.get("principal")
            total = txn.get("total")
            if total:
                gross_revenue = total
        except Exception:
            pass

    try:
        return_items = royalty_engine.calculate_tribal_returns(
            envelope_status=envelope_status,
            principal=principal,
            gross_revenue=gross_revenue,
        )
    except Exception as exc:
        app.logger.error("Royalty engine error for envelope %s: %s", envelope_id, exc)
        return []

    record_ids: list[str] = []
    stripe_key_available = bool(os.environ.get("STRIPE_API_KEY", ""))

    for item in return_items:
        stripe_payment_id = None
        if stripe_key_available:
            try:
                cents = royalty_engine.amount_to_cents(item["amount"])
                if cents >= royalty_engine.STRIPE_MINIMUM_CENTS:
                    import stripe  # type: ignore[import-untyped]
                    stripe.api_key = os.environ["STRIPE_API_KEY"]
                    intent = stripe.PaymentIntent.create(
                        amount=cents,
                        currency="usd",
                        metadata={
                            "return_type": item["return_type"],
                            "envelope_id": envelope_id,
                            "transaction_id": txn["id"] if txn else "",
                            "envelope_status": envelope_status,
                            "source": "vbtnt_tribal_return",
                        },
                        idempotency_key=(
                            f"tribal-return-{envelope_id}-"
                            f"{item['return_type']}-{envelope_status}"
                        ),
                    )
                    stripe_payment_id = intent["id"]
            except Exception as exc:
                app.logger.warning(
                    "Stripe post failed for tribal return %s envelope %s: %s",
                    item["return_type"], envelope_id, exc,
                )

        try:
            record = db.create_tribal_return(
                envelope_id=envelope_id,
                transaction_id=txn["id"] if txn else None,
                envelope_status=envelope_status,
                return_type=item["return_type"],
                amount=item["amount"],
                stripe_payment_id=stripe_payment_id,
            )
            record_ids.append(record["id"])
        except Exception as exc:
            app.logger.error(
                "Failed to persist tribal return %s for envelope %s: %s",
                item["return_type"], envelope_id, exc,
            )

    return record_ids


@app.route("/api/usps-proof/<envelope_id>")
def get_usps_proof(envelope_id):
    events = db.list_docusign_usps_proof_events(envelope_id)
    if not events:
        return jsonify({"status": "error", "message": "No USPS proof events found."}), 404
    return jsonify({"status": "ok", "envelope_id": envelope_id, "events": events}), 200


@app.route("/api/tribal-returns/<envelope_id>")
def get_tribal_returns(envelope_id):
    records = db.list_tribal_returns(envelope_id)
    if not records:
        return jsonify({"status": "error", "message": "No tribal return records found."}), 404
    return jsonify({"status": "ok", "envelope_id": envelope_id, "tribal_returns": records}), 200


# ---------------------------------------------------------------------------
# Insurance claims
# ---------------------------------------------------------------------------

# Envelope event types / statuses that auto-trigger a claim
_CLAIM_TRIGGER_TYPES = frozenset({
    "loss_report", "damage_notice", "contract_dispute", "insurance_claim",
})
_CLAIM_TRIGGER_STATUSES = frozenset({
    "loss_report", "damage_notice", "contract_dispute",
})

# DocuSign template tag/label → claim type mapping
_TEMPLATE_CLAIM_TYPE_MAP: dict[str, str] = {
    "loss_report": "loss",
    "damage_notice": "damage",
    "contract_dispute": "liability",
    "insurance_claim": "general",
}


def _extract_claim_type(event_type: str, envelope_status: str | None, body: dict) -> str | None:
    """Return a claim_type string if this event should trigger a claim, else None."""
    for trigger in _CLAIM_TRIGGER_TYPES:
        if trigger in (event_type or "").lower():
            return _TEMPLATE_CLAIM_TYPE_MAP.get(trigger, "general")
    if envelope_status:
        for trigger in _CLAIM_TRIGGER_STATUSES:
            if trigger in envelope_status.lower():
                return _TEMPLATE_CLAIM_TYPE_MAP.get(trigger, "general")
    # Check DocuSign template tags in the payload
    data = body.get("data", {}) or {}
    template_id = (
        data.get("envelopeSummary", {}).get("templateId")
        or body.get("templateId")
        or ""
    )
    custom_fields = (
        data.get("envelopeSummary", {}).get("customFields", {})
        or body.get("customFields", {})
        or {}
    )
    text_fields = custom_fields.get("textCustomFields", []) or []
    for field in text_fields:
        if isinstance(field, dict):
            label = (field.get("name") or field.get("tabLabel") or "").lower()
            value = (field.get("value") or "").lower()
            if label in ("claim_type", "claimtype") and value:
                return value
            for trigger in _CLAIM_TRIGGER_TYPES:
                if trigger in label or trigger in value:
                    return _TEMPLATE_CLAIM_TYPE_MAP.get(trigger, "general")
    return None


def _maybe_create_insurance_claim(
    *,
    envelope_id: str,
    event_type: str,
    envelope_status: str | None,
    txn: dict | None,
    body: dict,
) -> str | None:
    """Auto-create an insurance_claims row if the event warrants it. Returns claim_id or None."""
    claim_type = _extract_claim_type(event_type, envelope_status, body)
    if not claim_type:
        return None
    try:
        record = db.create_insurance_claim(
            envelope_id=envelope_id,
            claim_type=claim_type,
            claim_status="open",
            source_payload=body,
        )
        return record["claim_id"]
    except Exception as exc:
        app.logger.error("Failed to auto-create insurance claim for envelope %s: %s", envelope_id, exc)
        return None


def _maybe_create_cod_transaction(
    *,
    envelope_id: str,
    proof_event: dict,
    txn: dict | None,
    body: dict,
    recipient_name: str | None,
    recipient_address: str | None,
) -> str | None:
    """Auto-create a cod_transactions row if the envelope is COD-tagged. Returns cod_id or None."""
    # Detect COD flag in DocuSign tabs or USPS metadata
    is_cod = False
    cod_amount = None

    data = body.get("data", {}) or {}
    summary = data.get("envelopeSummary", {}) or {}
    signers = summary.get("recipients", {}).get("signers", []) or []
    signer = signers[0] if signers and isinstance(signers[0], dict) else {}
    tabs = signer.get("tabs", {}) or {}

    for tab_list_key in ("textTabs", "checkboxTabs", "radioGroupTabs"):
        for tab in (tabs.get(tab_list_key) or []):
            if not isinstance(tab, dict):
                continue
            label = (tab.get("tabLabel") or tab.get("name") or "").lower()
            value = (tab.get("value") or tab.get("selected") or "").lower()
            if "cod" in label or "collect_on_delivery" in label:
                is_cod = True
            if label in ("cod_amount", "codamount") and value:
                cod_amount = value

    # Also check top-level body keys
    if not is_cod:
        for key in ("cod", "collect_on_delivery", "isCOD", "is_cod"):
            if body.get(key):
                is_cod = True
                break

    if not is_cod:
        return None

    # Derive amount from transaction total or body
    if cod_amount is None:
        cod_amount = (
            (txn.get("total") if txn else None)
            or str(body.get("cod_amount", "0"))
        )

    try:
        record = db.create_cod_transaction(
            envelope_id=envelope_id,
            cod_amount=cod_amount,
            usps_reference=proof_event.get("usps_reference"),
            recipient_name=recipient_name,
            recipient_address=recipient_address,
        )
        return record["cod_id"]
    except Exception as exc:
        app.logger.error("Failed to auto-create COD transaction for envelope %s: %s", envelope_id, exc)
        return None


@app.route("/api/insurance-claims", methods=["POST"])
def create_insurance_claim():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Request body must be valid JSON"}), 400

    envelope_id = body.get("envelope_id", "").strip()
    claim_type = body.get("claim_type", "").strip()
    if not envelope_id or not claim_type:
        return jsonify({"status": "error", "message": "envelope_id and claim_type are required"}), 400

    try:
        record = db.create_insurance_claim(
            envelope_id=envelope_id,
            claim_type=claim_type,
            claim_status=body.get("claim_status", "open"),
            policy_number=body.get("policy_number"),
            carrier_name=body.get("carrier_name"),
            loss_amount=str(body["loss_amount"]) if body.get("loss_amount") is not None else None,
            deductible=str(body["deductible"]) if body.get("deductible") is not None else None,
            payout_amount=str(body["payout_amount"]) if body.get("payout_amount") is not None else None,
            incident_date=body.get("incident_date"),
            jurisdiction=body.get("jurisdiction"),
            source_payload=body.get("source_payload") or body,
        )
    except ValueError as exc:
        return jsonify({"status": "error", "message": "Invalid claim data: check claim_status and required fields."}), 400

    return jsonify({"status": "created", "claim": record}), 201


@app.route("/api/insurance-claims/<claim_id>", methods=["GET"])
def get_insurance_claim(claim_id):
    record = db.get_insurance_claim(claim_id)
    if record is None:
        return jsonify({"status": "error", "message": "Insurance claim not found."}), 404
    return jsonify({"status": "ok", "claim": record}), 200


@app.route("/api/insurance-claims", methods=["GET"])
def list_insurance_claims():
    envelope_id = request.args.get("envelope_id")
    records = db.list_insurance_claims(envelope_id=envelope_id)
    return jsonify({"status": "ok", "claims": records, "count": len(records)}), 200


@app.route("/api/insurance-claims/<claim_id>/status", methods=["PATCH"])
def update_insurance_claim_status(claim_id):
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Request body must be valid JSON"}), 400
    claim_status = body.get("claim_status", "").strip()
    if not claim_status:
        return jsonify({"status": "error", "message": "claim_status is required"}), 400
    try:
        db.update_insurance_claim_status(
            claim_id,
            claim_status,
            payout_amount=str(body["payout_amount"]) if body.get("payout_amount") is not None else None,
        )
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid claim_status value."}), 400
    record = db.get_insurance_claim(claim_id)
    if record is None:
        return jsonify({"status": "error", "message": "Insurance claim not found."}), 404
    return jsonify({"status": "updated", "claim": record}), 200


# ---------------------------------------------------------------------------
# COD transactions
# ---------------------------------------------------------------------------

@app.route("/api/cod-transactions", methods=["POST"])
def create_cod_transaction():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Request body must be valid JSON"}), 400

    envelope_id = body.get("envelope_id", "").strip()
    cod_amount = body.get("cod_amount")
    if not envelope_id or cod_amount is None:
        return jsonify({"status": "error", "message": "envelope_id and cod_amount are required"}), 400

    try:
        record = db.create_cod_transaction(
            envelope_id=envelope_id,
            cod_amount=str(cod_amount),
            usps_reference=body.get("usps_reference"),
            recipient_name=body.get("recipient_name"),
            recipient_address=body.get("recipient_address"),
            currency=body.get("currency", "USD"),
            status=body.get("status", "pending"),
            payment_channel=body.get("payment_channel"),
        )
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid COD transaction data: check status and required fields."}), 400

    return jsonify({"status": "created", "cod_transaction": record}), 201


@app.route("/api/cod-transactions/<cod_id>", methods=["GET"])
def get_cod_transaction(cod_id):
    record = db.get_cod_transaction(cod_id)
    if record is None:
        return jsonify({"status": "error", "message": "COD transaction not found."}), 404
    return jsonify({"status": "ok", "cod_transaction": record}), 200


@app.route("/api/cod-transactions", methods=["GET"])
def list_cod_transactions():
    envelope_id = request.args.get("envelope_id")
    records = db.list_cod_transactions(envelope_id=envelope_id)
    return jsonify({"status": "ok", "cod_transactions": records, "count": len(records)}), 200


# ---------------------------------------------------------------------------
# Policies
# ---------------------------------------------------------------------------

@app.route("/api/policies", methods=["POST"])
def create_policy():
    body = request.get_json(silent=True)
    if not body:
        return jsonify({"status": "error", "message": "Request body must be valid JSON"}), 400

    policy_number = body.get("policy_number", "").strip()
    carrier_name = body.get("carrier_name", "").strip()
    coverage_type = body.get("coverage_type", "").strip()
    if not policy_number or not carrier_name or not coverage_type:
        return jsonify({"status": "error", "message": "policy_number, carrier_name, and coverage_type are required"}), 400

    try:
        record = db.create_policy(
            policy_number=policy_number,
            carrier_name=carrier_name,
            coverage_type=coverage_type,
            limit_amount=str(body["limit"]) if body.get("limit") is not None else None,
            deductible=str(body["deductible"]) if body.get("deductible") is not None else None,
            effective_date=body.get("effective_date"),
            expiration_date=body.get("expiration_date"),
            insured_entity=body.get("insured_entity"),
            notes=body.get("notes"),
        )
    except ValueError:
        return jsonify({"status": "error", "message": "Policy already exists with this policy_number."}), 409

    return jsonify({"status": "created", "policy": record}), 201


@app.route("/api/policies/<policy_number>", methods=["GET"])
def get_policy(policy_number):
    record = db.get_policy(policy_number)
    if record is None:
        return jsonify({"status": "error", "message": "Policy not found."}), 404
    return jsonify({"status": "ok", "policy": record}), 200


@app.route("/api/policies", methods=["GET"])
def list_policies():
    records = db.list_policies()
    return jsonify({"status": "ok", "policies": records, "count": len(records)}), 200


@app.route("/api/sovereign-vocabulary")
def get_sovereign_vocabulary():
    """
    Return the full VBTNT Sovereign Vocabulary Dictionary.
    This is the runtime-authoritative source of truth for all VBTNT terminology.
    """
    domain_filter = request.args.get("domain")
    if domain_filter:
        terms = {
            k: v for k, v in sovereign_vocabulary.DICTIONARY.items()
            if v.get("domain") == domain_filter
        }
        if not terms:
            return jsonify({
                "status": "error",
                "message": f"No terms found for domain {domain_filter!r}.",
            }), 404
        return jsonify({
            "status": "ok",
            "domain": domain_filter,
            "term_count": len(terms),
            "terms": terms,
        }), 200

    return jsonify({
        "status": "ok",
        "edition": "First Edition",
        "issued": "2026-07-28",
        "issuing_authority": "Verdigris Botanica Tribal Nation Trust",
        "uei": "GUMMCRJPMBN5",
        "cage": "14JT5",
        "fedstrip": "18317P",
        "domains": sovereign_vocabulary.list_domains(),
        "term_count": len(sovereign_vocabulary.DICTIONARY),
        "terms": sovereign_vocabulary.DICTIONARY,
    }), 200




if __name__ == "__main__":
    app.run(host="0.0.0.0")
