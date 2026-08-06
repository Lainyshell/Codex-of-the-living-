# Operational Runbook
## Codex of the Living — "If I'm Gone, Here's How to Keep It Running"

**System:** Codex of the Living — Verdigris Botanica Tribal Nation Infrastructure
**Version:** 1.0
**Date:** 2026-08-06
**Maintained by:** System Steward (Alaina Padgett)
**For:** Tribal Technical Lead, Stewardship Circle, Emergency Successors

---

## IMPORTANT: Read This First

This runbook is written for someone who needs to keep this system running without me. If you're reading this because something has happened to me, I'm sorry — and I'm glad I wrote this down.

You don't need to understand every line of code. You need to know:
1. What the system does and why it matters
2. Where everything lives
3. Who to call if you're stuck
4. How to keep it alive

The system belongs to the Verdigris Botanica Tribal Nation — not to me personally. It outlives me by design.

---

## 1. What This System Does

The Codex of the Living manages the Nation's:
- **Financial records** — transactions, ledgers, disbursements
- **Document execution** — payment vouchers, REMIC instruments, tribal agreements
- **Treasury workflows** — tracking what's owed, what's been paid, what's in process

It runs as a web application (accessible via browser or API), stores data in a SQLite database, and connects to Azure (hosting) and DocuSign (document signing).

---

## 2. Where Everything Lives

### Code Repository
- **GitHub:** `https://github.com/Lainyshell/Codex-of-the-living-`
- **Branch:** `main` (production)
- **Access:** Requires GitHub account with repository access

### Live Application
- **Platform:** Microsoft Azure US Government
- **Access:** Azure portal at `https://portal.azure.us`
- **Credentials:** In Azure Key Vault (see Section 4)

### Database
- **Type:** SQLite (file-based)
- **Location:** On the Azure container filesystem; backed up to Azure Storage
- **To export:** `GET /export/transactions` endpoint or direct file copy from container

### Secrets and Credentials
- **Location:** Azure Key Vault (production) and GitHub repository secrets (CI/CD)
- **What's there:** DocuSign keys, Azure credentials, SMTP alert credentials
- **Who can access:** System Steward; after succession, the new designated Steward

---

## 3. Day-to-Day Operations

### Checking System Health
```
GET https://[app-url]/health
```
Returns system status. If it returns 200 OK, the system is running.

### Viewing Logs
- Azure portal → Container Apps → Logs
- Or: GitHub Actions → recent workflow runs

### Restarting the Application
- Azure portal → Container App → Restart
- Or: Trigger a new deployment via GitHub Actions (`azure-container-webapp.yml`)

### Deploying an Update
1. Make changes in a branch
2. Open a pull request
3. Get required steward approvals (see `docs/CRITICAL_CHANGE_PROTOCOL.md` for critical changes)
4. Merge to `main`
5. GitHub Actions automatically deploys to staging, runs smoke tests, then promotes to production

---

## 4. Emergency Access

### If You Don't Have Credentials
1. Contact the **Elder Council Seat** — they hold emergency access authority
2. Contact **Microsoft Azure support** with the tenant ID to recover access
3. The GitHub organization admin can grant repository access
4. DocuSign account recovery via `admin@verdigrisbotanicanation.org`

### Emergency Contacts
| Role | Contact |
|---|---|
| System Steward | alaina@verdigrisbotanicanation.org |
| Tribal Technical Lead | [To be designated] |
| Elder Council Seat | [To be designated] |
| Azure Support | 1-800-642-7676 (US Gov) |
| DocuSign Support | support@docusign.com |
| GitHub Support | support.github.com |

### If the System Is Down
1. Check Azure portal — is the container running?
2. Check recent deployments — did a bad deploy go out?
3. Roll back: Azure portal → Container App → Revision Management → Activate previous revision
4. If database is corrupted: restore from most recent Azure Storage backup
5. Alert all stewards per `docs/ABUSE_DETECTION_RUNBOOK.md`

---

## 5. Key Files to Know

| File | What it does |
|---|---|
| `app/main.py` | Main application — all API endpoints |
| `app/db.py` | Database operations |
| `app/payments.py` | Payment and DocuSign workflows |
| `app/remic.py` | REMIC instrument processing |
| `app/config.py` | Governance references and system configuration |
| `app/safeguards.py` | Abuse detection and lockdown |
| `app/requirements.txt` | Python dependencies |
| `app/Dockerfile` | Container build instructions |
| `compose.yaml` | Local development setup |

---

## 6. If the System Is in Lockdown

See `docs/ABUSE_DETECTION_RUNBOOK.md` Section 5.

Short version:
1. Two stewards must independently approve the resume
2. Each calls: `POST /admin/lockdown/approve` with their credentials
3. System resumes automatically after two approvals
4. Document what triggered the lockdown in `docs/CRITICAL_CHANGE_REGISTER.md`

---

## 7. Running Locally (for Testing/Development)

Requirements: Python 3.11, Docker

```bash
# Clone the repository
git clone https://github.com/Lainyshell/Codex-of-the-living-

# Set environment variables (never commit these)
export DOCUSIGN_INTEGRATION_KEY=...
export DOCUSIGN_USER_ID=...
export DOCUSIGN_PRIVATE_KEY=...
export AZURE_TENANT_ID=...

# Run with Docker Compose
docker compose up

# Or run directly
cd app
pip install -r requirements.txt
python main.py
```

---

## 8. Annual Maintenance Checklist

- [ ] Rotate all credentials (DocuSign keys, Azure service principals)
- [ ] Review and update steward contact list in `app/config.py`
- [ ] Review access list — remove any accounts no longer active
- [ ] Run full threat model review (`docs/THREAT_MODEL.md`)
- [ ] Test lockdown and resume procedure with all stewards
- [ ] Update architecture docs if anything has changed
- [ ] Verify database backup integrity
- [ ] Review all vendor agreements for upcoming renewals

---

## 9. Succession Checklist

If you are taking over as System Steward:

- [ ] Tribal Resolution has been adopted naming you as Steward
- [ ] GitHub repository access transferred
- [ ] Azure subscription access granted
- [ ] DocuSign admin access transferred
- [ ] Azure Key Vault access granted
- [ ] All steward alert emails updated in `app/config.py` (Critical Change)
- [ ] CODEOWNERS file updated (Critical Change)
- [ ] All stewards and Stewardship Circle notified
- [ ] Read and acknowledge: `TRIBAL_GOVERNANCE.md`, `JURISDICTION.md`, `docs/GOVERNANCE_CHARTER.md`, `docs/PROHIBITED_USES.md`
- [ ] Complete steward training: `docs/STEWARD_TRAINING_GUIDE.md`

---

*This document should be updated whenever the system changes. Keep it honest — the person reading it in an emergency needs the truth, not the version that makes things look easy.*
