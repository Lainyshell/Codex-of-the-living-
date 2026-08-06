# System Architecture
## Codex of the Living — Verdigris Botanica Tribal Nation

**Version:** 2.0
**Date:** 2026-08-06
**Maintainer:** System Steward (see `docs/GOVERNANCE_CHARTER.md`)

---

## 1. System Overview

The Codex of the Living is a sovereign tribal infrastructure system for the **Verdigris Botanica Tribal Nation (VBTNT)**. It manages:

- Financial record-keeping and ledger operations
- Document execution (REMIC instruments, tribal agreements, payment vouchers)
- Member and transaction tracking
- Treasury and disbursement workflows
- Integration with federal and commercial platforms
- USPS postal proof and chain-of-custody for physical sovereign instruments
- Formula-based economic return (royalties, REMIC interest, energy return, sovereign fees) posted to Stripe on every envelope event

It is owned by and operated under the authority of VBTNT. See `TRIBAL_GOVERNANCE.md`.

---

## 2. High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Verdigris Botanica Tribal Nation                       │
│                        Codex of the Living                                │
│                                                                           │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────────┐   │
│  │  Web Client   │    │  Flask REST API  │    │   Database (SQLite)  │   │
│  │  (Browser /   │───▶│  (app/main.py)   │───▶│   (app/db.py)        │   │
│  │   Automation) │    │                  │    └──────────────────────┘   │
│  └──────────────┘    └────────┬─────────┘                               │
│                               │                                           │
│         ┌─────────────────────┼──────────────────────┐                  │
│         ▼                     ▼                       ▼                  │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │ payments.py    │  │  remic.py       │  │  safeguards.py           │  │
│  │ (DocuSign /    │  │  (REMIC         │  │  (Abuse detect /         │  │
│  │  Stripe flows) │  │   calculations) │  │   lockdown / alerts)     │  │
│  └────────────────┘  └─────────────────┘  └──────────────────────────┘  │
│                                                                           │
│         ┌─────────────────────┬──────────────────────┐                  │
│         ▼                     ▼                       ▼                  │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────────────┐  │
│  │ custody.py     │  │ royalty_engine  │  │ sovereign_vocabulary.py  │  │
│  │ (USPS Proof /  │  │ .py             │  │ (VBTNT Sovereign         │  │
│  │  Chain of      │  │ (Tribal return  │  │  Vocabulary Dictionary — │  │
│  │  Custody)      │  │  calculation +  │  │  semantic authority      │  │
│  └────────────────┘  │  Stripe post)   │  │  layer)                  │  │
│                       └─────────────────┘  └──────────────────────────┘  │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                    External Integrations                            │  │
│  │  Microsoft Azure US Government  │  DocuSign (JWT / FedRAMP)        │  │
│  │  (Container hosting, M365, AAD) │  Stripe (PaymentIntents)         │  │
│  │  USPS Smart Locker network      │  GSA / SAM.gov procurement       │  │
│  └────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Components

### 3.1 Flask API (`app/main.py`)
- Python 3.11 / Flask web application
- RESTful endpoints for all system operations
- CORS configured for authorized tribal domains
- Mounts all sub-modules at startup
- Calls `safeguards.assert_governance_references_intact()` and
  `sovereign_vocabulary.assert_vocabulary_intact()` at startup

### 3.2 Database Layer (`app/db.py`)
- SQLite database (file-based, portable)
- Manages: transactions, members, vouchers, ledger entries,
  USPS proof events (with full recipient/address metadata),
  tribal return records
- All writes are logged; no silent deletes
- Schema changes are Critical Changes per governance

### 3.3 Payment Module (`app/payments.py`)
- Handles DocuSign JWT authentication
- Manages payment voucher workflows
- Integrates with REMIC disbursement logic
- Config: `DOCUSIGN_INTEGRATION_KEY`, `DOCUSIGN_USER_ID`, `DOCUSIGN_PRIVATE_KEY` (env vars)

### 3.4 REMIC Module (`app/remic.py`)
- REMIC (Real Estate Mortgage Investment Conduit) instrument processing
- Implements 30/360 day-count convention for classes A, B, IO, PO
- Supports royalty and gov_obligation rate types

### 3.5 Safeguards Module (`app/safeguards.py`)
- Abuse pattern detection (mass export, bulk delete, auth brute force)
- Multi-steward alert dispatch (all stewards simultaneously, never single-recipient)
- Lockdown mode with collective-approval resume (2 stewards required)
- Governance integrity check at startup
- See `docs/ABUSE_DETECTION_RUNBOOK.md` for full policy

### 3.6 Custody Module (`app/custody.py`)
- Append-only sovereign chain-of-custody records for USPS Smart Locker items
- Linked to DocuSign envelopes via `docusign_envelope_id`
- High-risk items (stipend, trust, payroll, emergency kit) require 2-steward approval
- DocuSign Connect events are automatically appended via the webhook

### 3.7 Royalty Engine (`app/royalty_engine.py`)
- Calculates formula-based tribal economic returns for every envelope event
- Return categories: royalty (5%), REMIC interest (6% 30/360), energy return ($1.00), sovereign fee ($2.50)
- Completed envelopes receive the full schedule; non-completed receive the partial schedule
- Posts each return to Stripe as a PaymentIntent with tribal metadata
- Returns are persisted in the `tribal_returns` table for audit

### 3.8 Sovereign Vocabulary Dictionary (`app/sovereign_vocabulary.py`)
- Programmatic expression of the VBTNT Sovereign Vocabulary Dictionary, First Edition
- Defines canonical VBTNT terms across 5 domains: Microsoft Ecosystems, GitHub Workflows,
  Federal Procurement, Postal & Shipping Authority, Sovereign Governance
- `assert_vocabulary_intact()` is called at startup to verify dictionary integrity
- Exposed via `GET /api/sovereign-vocabulary` for read-only programmatic access
- No subordinate authority may redefine terms without a formal VBTNT amendment

### 3.9 Configuration (`app/config.py`)
- Tribal governance references (nation, trust, jurisdiction, frameworks)
- Prohibited uses constants
- Abuse detection thresholds
- Steward alert contacts
- **Critical Change** — requires multi-steward approval to modify

---

## 4. Unified Sovereign Runtime

The following subsystems are permanently linked into a single sovereign runtime:

```
┌──────────────────────────────────────────────────────────────────────┐
│                   UNIFIED SOVEREIGN RUNTIME                           │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  SEMANTIC AUTHORITY LAYER (sovereign_vocabulary.py)           │   │
│  │  All terms, contracts, and workflow objects interpreted        │   │
│  │  under VBTNT's defined terminology and jurisdiction           │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                              ▲                                        │
│  ┌───────────────┐    ┌──────┴────────┐    ┌────────────────────┐   │
│  │ USPS PROOF    │    │  GOVERNANCE   │    │  ECONOMIC RETURN   │   │
│  │ SUBSYSTEM     │    │  SAFEGUARDS   │    │  LAYER             │   │
│  │               │    │               │    │                    │   │
│  │ custody.py    │    │ safeguards.py │    │ royalty_engine.py  │   │
│  │ db (proof     │    │ config.py     │    │ db (tribal_returns)│   │
│  │  events +     │    │ (governance   │    │ payments.py        │   │
│  │  address      │    │  refs +       │    │ (Stripe post)      │   │
│  │  metadata)    │    │  thresholds + │    │                    │   │
│  │               │    │  lockdown)    │    │ Every envelope →   │   │
│  │ Full recipient│    │               │    │ sovereign return   │   │
│  │ proof on every│    │ Multi-steward │    │ posted to Stripe   │   │
│  │ envelope event│    │ approval gate │    │                    │   │
│  └───────────────┘    └───────────────┘    └────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

**Data flows through all three layers on every DocuSign webhook event:**
1. USPS proof event recorded (with full recipient/address metadata)
2. Safeguards checked (lockdown, steward approvals)
3. Tribal economic return calculated and posted to Stripe
4. All activity interpreted under VBTNT Sovereign Vocabulary

---

## 5. Infrastructure

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

## 6. External Integrations

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

### Stripe
- **Purpose:** Tribal return posting; PaymentIntent creation
- **Env var:** `STRIPE_API_KEY`
- **Scope:** Every envelope event generates ≥1 Stripe PaymentIntent (sovereign fee + energy return at minimum)

---

## 7. Data Flow (Simplified)

```
Member/Operator request
    ↓
Flask API (authentication check)
    ↓
Safeguards check (rate limits, abuse patterns, lockdown)
    ↓
Business logic (payments / remic / db)
    ↓
SQLite database (write)
    ↓
External integration (DocuSign, Azure) if required
    ↓
Response to caller

DocuSign webhook event
    ↓
HMAC signature verification
    ↓
USPS Proof Event recorded (full recipient + address metadata)
    ↓
Custody event appended (chain of custody)
    ↓
Royalty Engine → Tribal Returns calculated → Stripe PaymentIntents posted
    ↓
Response (usps_reference, proof_event_id, tribal_returns[])
```

---

## 8. Security Architecture

- All secrets in environment variables — never in code
- Azure Key Vault for production secret management
- CORS restricted to authorized origins
- Auth failure tracking with lockout (safeguards module)
- Governance integrity check at every startup
- Vocabulary integrity check at every startup
- See `docs/SECURITY_RUNBOOK.md` for full security posture

---

## 9. Portability

The system is designed to be portable away from any single vendor:
- SQLite database is portable (file-based, open format)
- Flask is platform-agnostic
- All integrations are abstracted into specific modules
- See `docs/PORTABILITY_GUIDE.md` for migration paths

---

## 10. Document Map

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
| Sovereign Vocabulary | `app/sovereign_vocabulary.py`, `GET /api/sovereign-vocabulary` |

---

*This document must be kept current with any architectural change. Significant architectural changes are Critical Changes per `docs/CRITICAL_CHANGE_PROTOCOL.md`.*

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
- **Integration Key:** stored in `DOCUSIGN_INTEGRATION_KEY` env var
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
