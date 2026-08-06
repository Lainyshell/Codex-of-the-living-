# System Architecture
## Codex of the Living — Verdigris Botanica Tribal Nation

**Version:** 1.0
**Date:** 2026-08-06
**Maintainer:** System Steward (see `docs/GOVERNANCE_CHARTER.md`)

---

## 1. System Overview

The Codex of the Living is a sovereign tribal infrastructure system for the **Verdigris Botanica Tribal Nation (VBTN)**. It manages:

- Financial record-keeping and ledger operations
- Document execution (REMIC instruments, tribal agreements, payment vouchers)
- Member and transaction tracking
- Treasury and disbursement workflows
- Integration with federal and commercial platforms

It is owned by and operated under the authority of VBTN. See `TRIBAL_GOVERNANCE.md`.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   Verdigris Botanica Tribal Nation               │
│                      Codex of the Living                         │
│                                                                  │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │   Web Client  │    │  Flask REST API  │    │   Database   │  │
│  │  (Browser /   │───▶│  (app/main.py)   │───▶│  (SQLite /   │  │
│  │   Automation) │    │                  │    │  app/db.py)  │  │
│  └──────────────┘    └────────┬─────────┘    └──────────────┘  │
│                               │                                  │
│              ┌────────────────┼────────────────┐                │
│              ▼                ▼                 ▼                │
│  ┌──────────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │  payments.py     │ │  remic.py    │ │  safeguards.py   │   │
│  │  (DocuSign /     │ │  (REMIC      │ │  (Abuse detect / │   │
│  │   Payment flows) │ │   instrument │ │   lockdown /     │   │
│  └──────────────────┘ │   processing)│ │   alerts)        │   │
│                        └──────────────┘ └──────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                External Integrations                      │  │
│  │  Microsoft Azure US Government  │  DocuSign (JWT auth)   │  │
│  │  (Container hosting, M365, AAD) │  (Document execution)  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Components

### 3.1 Flask API (`app/main.py`)
- Python 3.11 / Flask web application
- RESTful endpoints for all system operations
- CORS configured for authorized tribal domains
- Mounts all sub-modules at startup
- Calls `safeguards.assert_governance_references_intact()` at startup

### 3.2 Database Layer (`app/db.py`)
- SQLite database (file-based, portable)
- Manages: transactions, members, vouchers, ledger entries
- All writes are logged; no silent deletes
- Schema changes are Critical Changes per governance

### 3.3 Payment Module (`app/payments.py`)
- Handles DocuSign JWT authentication
- Manages payment voucher workflows
- Integrates with REMIC disbursement logic
- Config: `DOCUSIGN_INTEGRATION_KEY`, `DOCUSIGN_USER_ID`, `DOCUSIGN_PRIVATE_KEY` (env vars)

### 3.4 REMIC Module (`app/remic.py`)
- REMIC (Real Estate Mortgage Investment Conduit) instrument processing
- Document generation and tracking
- Integrates with payment flows

### 3.5 Safeguards Module (`app/safeguards.py`)
- Abuse pattern detection (mass export, bulk delete, auth brute force)
- Multi-steward alert dispatch (all stewards simultaneously, never single-recipient)
- Lockdown mode with collective-approval resume
- Governance integrity check at startup
- See `docs/ABUSE_DETECTION_RUNBOOK.md` for full policy

### 3.6 Configuration (`app/config.py`)
- Tribal governance references (nation, trust, jurisdiction, frameworks)
- Prohibited uses constants
- Abuse detection thresholds
- Steward alert contacts
- **Critical Change** — requires multi-steward approval to modify

---

## 4. Infrastructure

### Cloud Platform
- **Provider:** Microsoft Azure US Government (AzureUSGovernment)
- **Service:** Azure Container Apps / Web App
- **Identity:** Azure Active Directory (AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID)
- **Region:** US Government (data sovereignty compliant)

### Container
- **Runtime:** Python 3.11-slim (Docker)
- **Orchestration:** Docker Compose (`compose.yaml`)
- **Image:** Built and deployed via GitHub Actions (`azure-container-webapp.yml`)

### Deployment Pipeline
- Staged: `staging` → smoke test → `production`
- Rollback: automated on smoke-test failure
- Workflow: `.github/workflows/azure-container-webapp.yml`
- See `docs/DEPLOYMENT_OPERATIONS_STANDARD.md`

---

## 5. External Integrations

### Microsoft Azure / M365
- **Purpose:** Hosting, identity, email (Exchange Online)
- **Auth:** OIDC with AzureUSGovernment endpoint
- **Data:** No Azure service has data ownership rights (see `legal/DATA_SOVEREIGNTY_AGREEMENT.md`)
- **Docs:** `docs/M365_AZURE_INTEGRATION.md`

### DocuSign
- **Purpose:** Document execution
- **Auth:** JWT (RSA keypair)
- **Integration Key:** 54934ea2-813f-4288-8a8e-e09c293701ce
- **Env vars:** `DOCUSIGN_INTEGRATION_KEY`, `DOCUSIGN_USER_ID`, `DOCUSIGN_PRIVATE_KEY`
- **Docs:** `docs/DOCUSIGN_WORKFLOW.md`

---

## 6. Data Flow (Simplified)

```
Member/Operator request
    ↓
Flask API (authentication check)
    ↓
Safeguards check (rate limits, abuse patterns)
    ↓
Business logic (payments / remic / db)
    ↓
SQLite database (write)
    ↓
External integration (DocuSign, Azure) if required
    ↓
Response to caller
```

---

## 7. Security Architecture

- All secrets in environment variables — never in code
- Azure Key Vault for production secret management
- CORS restricted to authorized origins
- Auth failure tracking with lockout (safeguards module)
- Governance integrity check at every startup
- See `docs/SECURITY_RUNBOOK.md` for full security posture

---

## 8. Portability

The system is designed to be portable away from any single vendor:
- SQLite database is portable (file-based, open format)
- Flask is platform-agnostic
- All integrations are abstracted into specific modules
- See `docs/PORTABILITY_GUIDE.md` for migration paths

---

## 9. Document Map

| Purpose | File |
|---|---|
| Governance | `TRIBAL_GOVERNANCE.md`, `docs/GOVERNANCE_CHARTER.md` |
| Jurisdiction | `JURISDICTION.md` |
| Legal | `legal/` directory |
| Operations | `docs/RUNBOOK.md` |
| Security | `docs/SECURITY_RUNBOOK.md` |
| Threat Model | `docs/THREAT_MODEL.md` |
| Deployment | `docs/DEPLOYMENT_OPERATIONS_STANDARD.md` |
| Portability | `docs/PORTABILITY_GUIDE.md` |
| Abuse Response | `docs/ABUSE_DETECTION_RUNBOOK.md` |
| Training | `docs/STEWARD_TRAINING_GUIDE.md` |
| Why We Built This | `docs/WHY_WE_BUILT_THIS.md` |

---

*This document must be kept current with any architectural change. Significant architectural changes are Critical Changes per `docs/CRITICAL_CHANGE_PROTOCOL.md`.*
