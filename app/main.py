import os
import requests
from flask import Flask
from flask import request


app = Flask(__name__)


def _missing_fields(payload, required_fields):
    return [field for field in required_fields if field not in payload or payload[field] in (None, "")]


def _business_central_journal_lines_url(journal_batch_id):
    base_url = os.getenv("BUSINESS_CENTRAL_BASE_URL", "https://api.businesscentral.dynamics.com/v2.0").rstrip("/")
    tenant_id = os.getenv("BUSINESS_CENTRAL_TENANT_ID")
    environment = os.getenv("BUSINESS_CENTRAL_ENVIRONMENT")
    company_id = os.getenv("BUSINESS_CENTRAL_COMPANY_ID")

    missing_config = []
    if not tenant_id:
        missing_config.append("BUSINESS_CENTRAL_TENANT_ID")
    if not environment:
        missing_config.append("BUSINESS_CENTRAL_ENVIRONMENT")
    if not company_id:
        missing_config.append("BUSINESS_CENTRAL_COMPANY_ID")

    if missing_config:
        return None, missing_config

    url = (
        f"{base_url}/{tenant_id}/{environment}/api/v2.0/companies({company_id})"
        f"/journalBatches({journal_batch_id})/journalLines"
    )
    return url, None


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


@app.route("/business-central/transactions/connect", methods=["POST"])
def connect_transactions_to_business_central_account():
    payload = request.get_json(silent=True) or {}
    missing = _missing_fields(payload, ["journalBatchId", "transactions"])
    if missing:
        return {
            "status": "error",
            "message": "Missing required fields",
            "missingFields": missing
        }, 400

    if not isinstance(payload["transactions"], list) or len(payload["transactions"]) == 0:
        return {
            "status": "error",
            "message": "transactions must be a non-empty array"
        }, 400

    access_token = payload.get("accessToken")
    if not access_token:
        authorization_header = request.headers.get("Authorization", "")
        if authorization_header.lower().startswith("bearer "):
            access_token = authorization_header[7:].strip()

    if not access_token:
        return {
            "status": "error",
            "message": "Missing access token. Provide accessToken in payload or an Authorization header."
        }, 401

    endpoint_url, missing_config = _business_central_journal_lines_url(payload["journalBatchId"])
    if missing_config:
        return {
            "status": "error",
            "message": "Missing Business Central environment configuration",
            "missingConfig": missing_config
        }, 500

    auth_scheme = "Bearer"
    headers = {
        "Authorization": f"{auth_scheme} {access_token}",
        "Content-Type": "application/json",
    }

    connected = []
    failed = []

    for index, transaction in enumerate(payload["transactions"], start=1):
        tx_missing = _missing_fields(transaction, ["accountId", "amount"])
        if tx_missing:
            failed.append({
                "index": index,
                "reason": "Missing required transaction fields",
                "missingFields": tx_missing
            })
            continue

        journal_line = {
            "lineNumber": index * 10000,
            "accountId": transaction["accountId"],
            "amount": transaction["amount"],
            "description": transaction.get("description", ""),
            "documentNumber": transaction.get("documentNumber", f"TXN-{index}"),
            "postingDate": transaction.get("postingDate"),
        }
        journal_line = {key: value for key, value in journal_line.items() if value is not None}

        try:
            bc_response = requests.post(endpoint_url, headers=headers, json=journal_line, timeout=20)
            if bc_response.status_code in (200, 201):
                created_line = bc_response.json()
                connected.append({
                    "index": index,
                    "journalLineId": created_line.get("id"),
                })
            else:
                failed.append({
                    "index": index,
                    "statusCode": bc_response.status_code,
                    "reason": "Business Central rejected the transaction",
                })
        except requests.RequestException:
            failed.append({
                "index": index,
                "reason": "Failed to submit transaction to Business Central",
            })

    status_code = 200 if len(failed) == 0 else 207
    return {
        "status": "ok" if len(failed) == 0 else "partial",
        "connectedCount": len(connected),
        "failedCount": len(failed),
        "connected": connected,
        "failed": failed,
    }, status_code

if __name__ == '__main__':
    app.run(host='0.0.0.0')
