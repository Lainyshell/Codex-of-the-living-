# Portability Guide
## Codex of the Living — Migration Paths and Vendor Independence

**Version:** 1.0
**Date:** 2026-08-06
**Purpose:** Ensure VBTN can move this system if any vendor turns hostile, changes terms, or becomes unavailable.

---

## Principle: No Lock-In

The Codex of the Living is designed so that **no single vendor's departure can destroy the system**. This guide documents what it would take to migrate away from each current dependency.

This is not a plan to leave any vendor — it is a plan that makes the Nation permanently free to do so.

---

## 1. Current Dependencies

| Dependency | Purpose | Lock-in Risk | Portability Rating |
|---|---|---|---|
| Microsoft Azure US Government | Hosting, identity, M365 | Medium | 🟡 Moderate effort |
| DocuSign | Document execution | Low-Medium | 🟢 Replaceable |
| GitHub | Source control, CI/CD | Low | 🟢 Replaceable |
| SQLite | Database | Very Low | 🟢 Highly portable |
| Python / Flask | Application runtime | Very Low | 🟢 Open source |

---

## 2. Migrating Away from Microsoft Azure

### What Azure provides today:
- Container hosting (Azure Container Apps / Web App)
- Identity and authentication (Azure Active Directory / Entra ID)
- Secrets management (Azure Key Vault)
- Microsoft 365 (Exchange, SharePoint)

### Migration Path: Hosting

**Target platforms (tribal-suitable):**
- AWS GovCloud (US) — similar federal/tribal compliance posture
- Any FedRAMP-authorized container platform (Cloud.gov, etc.)
- Self-hosted on tribal-controlled servers (maximum sovereignty)

**Steps:**
1. Export container image from Azure Container Registry
2. Push image to target platform's container registry
3. Update environment variables in target platform's secrets management
4. Update DNS to point to new platform
5. Update GitHub Actions deployment workflow (`azure-container-webapp.yml`) to target new platform
6. Verify health check endpoints
7. Update `docs/ARCHITECTURE.md`

**Data:** SQLite database file is portable — copy via `docker cp` or Azure Storage download.

**Estimated effort:** 1–2 weeks technical work; 2–4 weeks planning and testing

---

### Migration Path: Identity (Azure AD → Alternative)

Options:
- **Keycloak** (open source, self-hosted) — full replacement for Azure AD
- **AWS Cognito GovCloud** — if migrating hosting to AWS
- **Okta Government** — commercial alternative

Steps involve updating OAuth/OIDC configuration in the Flask app and updating all service principal references.

---

### Migration Path: Microsoft 365

Exchange Online → alternatives:
- **ProtonMail for Business** (strong privacy)
- **Self-hosted email** on VPS (maximum control)
- **Google Workspace for Government** (if acceptable)

SharePoint → alternatives:
- **Nextcloud** (open source, self-hosted)
- Any WebDAV-compatible document store

---

## 3. Migrating Away from DocuSign

### What DocuSign provides today:
- Electronic signature collection
- Document envelope management
- Audit trail and certificate of completion

### Alternative Platforms:
| Platform | Notes |
|---|---|
| **Adobe Sign** | Strong compliance; similar API |
| **HelloSign (Dropbox Sign)** | Simpler API; lower cost |
| **Documenso** | Open source, self-hostable — maximum sovereignty |
| **eSignLive (Notarize)** | Good for tribal/government use |

### Migration Steps:
1. Select replacement platform
2. Update `app/payments.py` — DocuSign-specific calls are contained here
3. Update environment variables (`DOCUSIGN_*` → new platform vars)
4. Test document workflows end-to-end
5. Update `docs/DOCUSIGN_WORKFLOW.md`
6. Execute new Partner Ethical Agreement with replacement vendor

**Estimated effort:** 2–4 weeks (code changes are localized to `payments.py`)

---

## 4. Migrating Away from GitHub

### What GitHub provides today:
- Source code repository
- Issue tracking
- GitHub Actions CI/CD

### Alternative Platforms:
- **GitLab** (on-premises or .com) — full CI/CD replacement
- **Gitea** (self-hosted, open source) — maximum control
- **Azure DevOps** (if staying on Azure)

### Migration Steps:
1. Export repository: `git clone --mirror https://github.com/Lainyshell/Codex-of-the-living-`
2. Push to new platform: `git push --mirror [new-remote]`
3. Migrate GitHub Actions workflows to new CI/CD format (GitLab CI, etc.)
4. Update CODEOWNERS equivalent on new platform
5. Update branch protection rules

**Estimated effort:** 1 week

---

## 5. Data Portability

### Database (SQLite)
- **Format:** Open, documented, universally readable
- **Export:** `sqlite3 codex.db .dump > backup.sql`
- **Import to PostgreSQL:** `pgloader` or manual migration
- **Import to MySQL:** Similar tooling

### Document Exports
All documents processed through the system should be exportable as:
- **PDF** — for executed documents
- **JSON** — for transaction and ledger data
- **CSV** — for bulk data exports

No proprietary format should be used for primary storage. If a vendor stores data in a proprietary format, add a migration task to extract it to open formats.

---

## 6. Portability Checklist (Annual Review)

- [ ] Verify SQLite database can be successfully exported and re-imported
- [ ] Verify container image can be run outside Azure
- [ ] Test DocuSign API calls against staging environment of at least one alternative
- [ ] Confirm all environment variables are documented in `docs/SECURITY_RUNBOOK.md`
- [ ] Verify GitHub repository can be cloned and run locally without Azure dependencies
- [ ] Review vendor agreements for any new lock-in clauses

---

*If you're reading this because a vendor has turned hostile or become unavailable — this guide is your starting point. The Nation's data and code belong to the Nation. We can move.*
