# Codex of the Living — VBTN Compliance Door

**Verdigris Botanica Tribal Nation Trust**  
**Repository Administrator**: Alaina Padgett — alaina@verdigrisbotanicanation.org  
**Domain**: verdigrisbotanicanation.org

---

## 🏛️ Purpose

This repository serves as the **Compliance Door** for the Verdigris Botanica Tribal Nation (VBTN) — the authoritative, audited gateway that enforces document hygiene, chain-of-custody, and workflow controls for all VBTN sovereign data, legal filings, and operational processes.

It connects with the VBTN Microsoft 365 tenant (Azure, Entra ID, SharePoint, OneDrive, Power Automate, Power Apps) and routes legal documents through FedRAMP DocuSign for complete transparency and chain-of-custody preservation.

> **All automation in this repository enforces strict human-in-the-loop (HITL) guardrails.  
> No legal document is signed, published, or distributed without explicit admin approval.**

---

## 🗂️ Enterprise Documentation

| Document | Description |
|----------|-------------|
| [ENTERPRISE_SETUP.md](ENTERPRISE_SETUP.md) | GitHub Enterprise + M365/Azure setup guide |
| [docs/TENANT_DEFINITIONS.md](docs/TENANT_DEFINITIONS.md) | Official VBTN tenant term & document definitions |
| [docs/M365_AZURE_INTEGRATION.md](docs/M365_AZURE_INTEGRATION.md) | Azure Entra ID, SharePoint, OneDrive, Power Automate integration |
| [docs/DOCUSIGN_WORKFLOW.md](docs/DOCUSIGN_WORKFLOW.md) | FedRAMP DocuSign legal document signing workflow |
| [docs/AUTOMATION_GUIDE.md](docs/AUTOMATION_GUIDE.md) | Safe automation with HITL guardrails |
| [CISA_M365_ScubaGear_v1.7.0_Advisory.md](CISA_M365_ScubaGear_v1.7.0_Advisory.md) | M365 security baseline advisory |
| [M365_Security_Compliance_QuickRef.md](M365_Security_Compliance_QuickRef.md) | M365 security quick reference |

---

## ⚙️ Compliance Workflow

Every push and pull request triggers the automated **Compliance Check** workflow (`.github/workflows/compliance-check.yml`) which:

1. Scans for accidentally committed sensitive data
2. Validates document naming conventions
3. Computes SHA-256 integrity hashes for all tracked documents
4. Generates a full compliance summary report
5. Posts results to the pull request for admin review

**No further action (DocuSign routing, publishing) occurs without explicit admin approval.**

---

## 🔗 M365 Integration Architecture

```
SharePoint / OneDrive
      │  (Power Automate)
      ▼
GitHub Compliance Door  ──▶  Compliance Check Workflow
      │                              │
      │                         PASS / FAIL
      │                              │
      ▼                              ▼
  Admin HITL Gate  ◀────────  PR Comment + Teams Alert
      │
  APPROVED
      │
      ▼
FedRAMP DocuSign  ──▶  Signed Document  ──▶  SharePoint Archive
```

---

## Treasury API Application

The repository also includes a Flask application that fetches average interest rates from the Fiscal Data Treasury API (originally sourced from [OD2022/fiscal_treasury_api](https://github.com/OD2022/fiscal_treasury_api)).

- **Status Endpoint**: Check API status at `/`
- **Rates Endpoint**: Fetch average interest rates from the U.S. Treasury Fiscal Data API at `/rates`

## API Details

The application connects to the official U.S. Treasury Fiscal Data API:
- API URL: `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates`

## Project Structure

```
.
├── app/
│   ├── main.py           # Flask application with API endpoints
│   ├── requirements.txt  # Python dependencies (uwsgi, flask, requests)
│   ├── Dockerfile        # Docker container configuration
│   └── .gitignore        # Python-specific gitignore rules
├── compose.yaml          # Docker Compose configuration
└── .github/
    └── workflows/
        └── deploy.yaml   # GitHub Actions deployment workflow
```

## Running Locally

### Quick Start with Run Script

The easiest way to run the application:

```bash
./run.sh
```

This script will:
- Check dependencies and install them if needed
- Start the Flask application on port 5000
- Display available endpoints

### With Docker Compose

```bash
docker-compose up
```

The API will be available at `http://localhost:5000`

### With Python

```bash
cd app
pip install -r requirements.txt
python main.py
```

## API Endpoints

### GET /
Returns the status of the API.

**Response:**
```json
{
  "status": "ok"
}
```

### GET /rates
Fetches the latest average interest rates from the U.S. Treasury Fiscal Data API.

**Response:**
Returns the JSON response from the Treasury API containing average interest rate data.

### POST /business-central/transactions/connect
Connects one or more transactions to a Business Central account by creating journal lines in a target journal batch.

**Required environment variables:**
- `BUSINESS_CENTRAL_TENANT_ID`
- `BUSINESS_CENTRAL_ENVIRONMENT`
- `BUSINESS_CENTRAL_COMPANY_ID`
- `BUSINESS_CENTRAL_BASE_URL` *(optional, defaults to `https://api.businesscentral.dynamics.com/v2.0`)*

**Request body:**
```json
{
  "journalBatchId": "JOURNAL_BATCH_GUID",
  "accessToken": "AZURE_AD_ACCESS_TOKEN",
  "transactions": [
    {
      "accountId": "ACCOUNT_GUID",
      "amount": 250.75,
      "description": "Office supplies",
      "documentNumber": "INV-204",
      "postingDate": "2026-07-24"
    }
  ]
}
```

Each transaction must include `accountId` and `amount`. The endpoint returns counts and details for connected and failed transactions.

## Deployment

The repository includes a GitHub Actions workflow (`.github/workflows/deploy.yaml`) that automatically deploys the application when changes are pushed to the `main` branch. The workflow uses the Defang deployment platform.

## Technologies

- **Python 3.11**: Runtime environment
- **Flask**: Web framework
- **uWSGI**: WSGI HTTP server
- **Docker**: Containerization
- **GitHub Actions**: CI/CD pipeline

---

## Cybersecurity and Compliance

### CISA M365 Security Updates

The repository includes documentation for CISA's latest Microsoft 365 security requirements:

- **[CISA M365 ScubaGear v1.7.0 Advisory](CISA_M365_ScubaGear_v1.7.0_Advisory.md)** - Comprehensive guide to BOD 25-01 compliance requirements
- **[M365 Security Compliance Quick Reference](M365_Security_Compliance_QuickRef.md)** - Quick reference guide for M365 security baseline implementation

These documents provide guidance on:
- ScubaGear v1.7.0 assessment tool requirements
- M365 Secure Configuration Baselines (SCBs)
- BOD 25-01 compliance for federal agencies
- Recommendations for tribal nation M365 security

**Key Updates in ScubaGear v1.7.0:**
- NIST 800-53 FedRAMP high mappings
- Defender UI updates
- Entra ID / AAD UI updates
- New SCuBA Configuration editor feature

For VBTN M365 environment security, refer to these documents for best practices and assessment tools.

---

## Hardware Inventory

### Barcode Scanner

VBTN uses a USB HID barcode scanner (Symbol Technologies / Motorola Solutions, VID_05E0&PID_1200) operating in keyboard-emulation mode. Full device and driver configuration details are documented in:

- **[VBTN Barcode Scanner Configuration](VBTN_Barcode_Scanner_Config.md)** — device IDs, driver info, operating mode, and usage notes.

---

## Repository Contents

This repository contains:
- Treasury API Flask application (in `/app`)
- Tribal governance documents and agreements
- M365 DNS configuration for VBTN services
- Cybersecurity compliance documentation
- Operational procedures and templates
- Hardware inventory (barcode scanner configuration)
