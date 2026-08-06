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

## 📦 Sovereign Chain of Custody

The repository includes a protected custody domain for **VBTN SOVEREIGN SYSTEM — USPS Smart Locker Chain of Custody** records.

- **Custody envelopes** live in `/home/runner/work/Codex-of-the-living-/Codex-of-the-living-/custody/envelopes/`
- **Primary locker config** lives in `/home/runner/work/Codex-of-the-living-/Codex-of-the-living-/custody/lockers/primary.json`
- **Custody schema** lives in `/home/runner/work/Codex-of-the-living-/Codex-of-the-living-/custody/schema/envelope.schema.json`
- **Governance notes** live in `/home/runner/work/Codex-of-the-living-/Codex-of-the-living-/custody/README.md`

Custody events are append-only, locker validation is driven only by the primary locker map, and high-risk items require multi-steward approval before `RETRIEVED` or `CLOSED`.

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
├── scripts/
│   └── provision_mailboxes.py # Microsoft 365 tenant mailbox provisioning utility
├── compose.yaml          # Docker Compose configuration
└── .github/
    └── workflows/
        ├── azure-container-webapp.yml        # Build + staged Azure release workflow
        ├── operations-observability.yml      # Operations dashboard and alerting workflow
        └── provision-tenant-mailboxes.yml    # Manual tenant mailbox provisioning workflow
```

## Running Locally

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

### GET /shipping-report
Builds a USPS-style shipping report from repository transaction data.

**Query parameters:**
- `source` *(optional)*: Filename of a supported `.xlsx`, `.csv`, or `.json` transaction file in the repository root. Defaults to `Verified_Transactions_Template.xlsx`.
- `format` *(optional)*: `json` (default) or `csv`

**Response:**
- `json`: A normalized shipping report with USPS tracking-related fields, transaction count, and total amount
- `csv`: A downloadable shipping report with one row per transaction

## Deployment

The repository uses a single production app deployment workflow:

- **Release workflow**: `.github/workflows/azure-container-webapp.yml`
- **Observability workflow**: `.github/workflows/operations-observability.yml`
- **Mailbox provisioning workflow**: `.github/workflows/provision-tenant-mailboxes.yml`
- **Deployment/operations standard**: [`docs/DEPLOYMENT_OPERATIONS_STANDARD.md`](docs/DEPLOYMENT_OPERATIONS_STANDARD.md)

The release workflow builds from `app/Dockerfile`, deploys staging then production, runs post-deploy smoke checks on `/` and `/rates`, and attempts rollback to the previous image tag if production smoke checks fail.

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
