import csv
import io
import json
import re
import zipfile
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
import xml.etree.ElementTree as ET

import requests
from flask import Flask, Response, jsonify, request


app = Flask(__name__)
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SHIPPING_SOURCE = REPO_ROOT / "Verified_Transactions_Template.xlsx"
XML_NAMESPACES = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
FIELD_ALIASES = {
    "recipient": ["Recipient", "Name", "issued_by"],
    "address": ["Address"],
    "date_of_delivery": ["Date of Delivery", "Payment Date", "timestamp"],
    "form_3811_number": ["Form 3811 Number", "voucher_number", "AccountID"],
    "certified_mail_number": ["Certified Mail Number", "routing_number"],
    "registered_mail_number": ["Registered Mail Number", "po_number", "account_number"],
    "transaction_type": ["Transaction Type", "Role", "Subject", "status"],
    "amount": ["Amount", "amount"],
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
    }


def resolve_source_path(source_name):
    available_sources = {
        path.name: path
        for suffix in ("*.xlsx", "*.csv", "*.json")
        for path in REPO_ROOT.glob(suffix)
        if path.is_file()
    }
    candidate = available_sources.get(source_name)
    if candidate is None:
        raise FileNotFoundError("Shipping source file was not found")
    return candidate.resolve()


def build_shipping_report(source_path):
    rows = load_source_rows(source_path)
    transactions = [
        normalize_shipping_row(row, index)
        for index, row in enumerate(rows, start=1)
    ]
    total_amount = sum(
        (Decimal(transaction["amount"]) for transaction in transactions if transaction["amount"] is not None),
        Decimal("0"),
    )
    return {
        "status": "ok",
        "report_type": "usps_shipping",
        "source_file": source_path.name,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
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
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(report["transactions"])
    return output.getvalue()


@app.route("/")
def index():
    return { "status": "ok" }


@app.route("/rates")
def get_rates():
    # Declare string with the URL
    url = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?page[number]=1&page[size]=10"
    
    headers = {
        "Content-Type": "application/json",
    }

    # Fetch the data with timeout to prevent hanging
    response = requests.get(url, headers=headers, timeout=10)

    if (response.status_code != 200):
        return { 
            "status": "error",
            "code": response.status_code,
            "message": "Failed to fetch rates from Treasury API"
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
        return Response(
            build_shipping_report_csv(report),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={source_path.stem}-shipping-report.csv"
            },
        )

    return jsonify({
        "status": "error",
        "message": "Unsupported format. Use json or csv.",
    }), 400


if __name__ == '__main__':
    app.run(host='0.0.0.0')
