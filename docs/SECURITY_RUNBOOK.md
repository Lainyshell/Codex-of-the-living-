# Security Runbook
## Codex of the Living — Verdigris Botanica Tribal Nation Infrastructure

**Version:** 1.0
**Date:** 2026-08-06
**Maintainer:** System Steward
**Review Cycle:** Quarterly (access review) / Annual (full review)

---

## 1. Security Principles

1. **Least Privilege:** Every account has only the minimum access needed
2. **No Shared Credentials:** Every person has their own account; no group passwords
3. **Rotate Often:** Keys and credentials have defined rotation schedules
4. **Alert All Stewards:** Security events always notify multiple people
5. **Audit Everything:** All significant actions are logged
6. **Assume Breach:** Design and plan as if an attacker may already be present

---

## 2. Identity and Access Management (IAM)

### 2.1 Accounts and Roles

| Account | Platform | Access Level | Assigned To |
|---|---|---|---|
| GitHub Org Admin | GitHub | Full repository admin | System Steward |
| Azure Subscription Owner | Azure US Gov | Infrastructure admin | System Steward |
| Azure AD Global Admin | Azure AD | Identity admin | System Steward |
| DocuSign Admin | DocuSign | Account admin | System Steward |
| System Steward GitHub | GitHub | CODEOWNERS / merge authority | @Lainyshell |
| Tribal Technical Lead GitHub | GitHub | [Add when designated] | [TBD] |

### 2.2 Service Principals and App Registrations

| Service | Credential Type | Scope | Rotation Schedule |
|---|---|---|---|
| GitHub Actions → Azure | OIDC (federated) | Deploy to target resource group | N/A (no secret) |
| App → DocuSign | RSA keypair (JWT) | Send envelopes, read status | Annual |
| Azure Key Vault | Managed Identity | Read secrets | N/A (managed) |

### 2.3 Access Principles

- **No root/global admin for daily operations** — use scoped service accounts
- **MFA required** on all human accounts (GitHub, Azure, DocuSign)
- **No personal email** on production accounts — use @verdigrisbotanicanation.org addresses
- **No credentials in code** — all secrets in Azure Key Vault or GitHub secrets

---

## 3. Secrets Management

### 3.1 Secret Inventory

| Secret | Platform | Used By | Notes |
|---|---|---|---|
| `DOCUSIGN_INTEGRATION_KEY` | GitHub Secrets / Key Vault | CI/CD, app runtime | Rotate annually |
| `DOCUSIGN_USER_ID` | GitHub Secrets / Key Vault | App runtime | Static; update on DocuSign user change |
| `DOCUSIGN_PRIVATE_KEY` | GitHub Secrets / Key Vault | App runtime | Rotate annually |
| `AZURE_TENANT_ID` | GitHub Secrets | CI/CD OIDC | Update if tenant changes |
| `AZURE_SUBSCRIPTION_ID` | GitHub Secrets | CI/CD OIDC | Update if subscription changes |
| `ALERT_SMTP_PASS` | Key Vault | safeguards.py alerts | Rotate quarterly |

### 3.2 Key Rotation Schedule

| Secret | Rotation Frequency | Next Review |
|---|---|---|
| DocuSign RSA keypair | Annual | [Set date] |
| Alert SMTP credentials | Quarterly | [Set date] |
| Azure service principal | Annual (or on personnel change) | [Set date] |
| Database encryption key (if added) | Annual | [Set date] |

### 3.3 Rotation Procedure

1. Generate new credential in target platform
2. Add new credential to Azure Key Vault / GitHub Secrets under a new name (e.g., `_v2`)
3. Deploy and test with new credential
4. Remove old credential from Key Vault / GitHub Secrets
5. Document rotation in the security log
6. Do NOT store old credentials in any backup or archive

---

## 4. Audit Logging

### 4.1 What Is Logged

| Event | Location | Retention |
|---|---|---|
| All API requests | Application logs (Azure Container) | 90 days |
| Authentication attempts | Azure AD sign-in logs | 90 days |
| Abuse pattern detections | `safeguards.py` + application logs | 1 year |
| GitHub Actions deployments | GitHub Actions logs | 90 days |
| GitHub PR reviews and merges | GitHub repository history | Permanent |
| Azure resource changes | Azure Activity Log | 90 days |
| DocuSign envelope activity | DocuSign audit log | Per DocuSign retention policy |

### 4.2 Log Review Schedule

- **Weekly:** Review safeguards abuse event log for any new patterns
- **Monthly:** Review Azure AD sign-in logs for anomalous access
- **Quarterly:** Full audit log review across all platforms
- **After any incident:** Immediate log review for timeline reconstruction

---

## 5. Incident Response

### 5.1 Severity Definitions

| Severity | Definition | Response Time |
|---|---|---|
| **S1 — Critical** | Active breach, data exfiltration, ransomware, governance tampering | Immediate (within 1 hour) |
| **S2 — High** | Suspected credential compromise, abuse pattern detected, unauthorized access attempt | Within 4 hours |
| **S3 — Medium** | Policy violation, unusual access pattern, vendor concern | Within 24 hours |
| **S4 — Low** | Configuration drift, minor policy issue | Within 7 days |

### 5.2 Incident Response Steps

**For any incident:**

1. **CONTAIN** — Do not let the attacker know they've been detected if possible; isolate affected systems if needed
2. **PRESERVE** — Export logs immediately before they rotate; screenshot key evidence
3. **ALERT** — Notify all stewards per `docs/ABUSE_DETECTION_RUNBOOK.md` alert procedure
4. **ASSESS** — Determine what was accessed, modified, or exfiltrated
5. **REMEDIATE** — Rotate compromised credentials; patch vulnerabilities; restore from backup if needed
6. **DOCUMENT** — Write a full incident report within 72 hours
7. **REVIEW** — Post-incident review within 7 days; update threat model if needed

### 5.3 S1 Emergency Actions (Breach in Progress)

1. Activate lockdown mode: `POST /admin/lockdown/activate` (or via admin panel)
2. Revoke compromised credentials immediately (Azure portal, GitHub settings, DocuSign)
3. Alert all stewards simultaneously
4. Do NOT attempt to investigate from a compromised account — use a clean device
5. Preserve all logs
6. Consider notifying members if their data was accessed

---

## 6. Quarterly Access Review Checklist

Perform this review every 90 days:

- [ ] List all GitHub repository collaborators — remove any who no longer need access
- [ ] List all Azure subscription members — verify each account is still needed
- [ ] List all DocuSign users — verify roles are correct
- [ ] Review GitHub Actions secrets — confirm all are still in use
- [ ] Review Azure Key Vault access policies — confirm least privilege
- [ ] Test steward alert emails — confirm all addresses are reachable
- [ ] Review `app/config.py` `STEWARD_ALERT_EMAILS` — confirm current and complete
- [ ] Check for any credentials due for rotation
- [ ] Review abuse event log for patterns not yet documented

Document the review completion date and reviewer in `docs/CRITICAL_CHANGE_REGISTER.md`.

---

## 7. Annual Security Review Checklist

In addition to the quarterly checklist:

- [ ] Full threat model review (`docs/THREAT_MODEL.md`)
- [ ] Rotate DocuSign RSA keypair
- [ ] Review and update all vendor security agreements
- [ ] Test full backup restore procedure
- [ ] Test lockdown and resume drill with all stewards
- [ ] Review CODEOWNERS and branch protection rules
- [ ] Review all PROHIBITED_USES prohibitions for any new risk vectors
- [ ] Update this runbook for any changes

---

## 8. Known Gaps and Accepted Risks

| Gap | Risk | Mitigation | Status |
|---|---|---|---|
| Tribal Technical Lead not yet designated | Single point of failure for succession | Priority: designate immediately | 🔴 Open |
| Elder Council Seat not yet designated | Incomplete multi-steward approval capability | Priority: designate immediately | 🔴 Open |
| Database encryption at rest | Data readable if storage is accessed directly | Azure infrastructure encryption provides baseline; evaluate SQLite encryption extension | 🟡 Accepted pending review |
| No Web Application Firewall (WAF) | Vulnerable to common web attacks | Consider Azure Front Door / WAF | 🟡 Accepted pending review |

---

*This document is a living runbook. Update it whenever the security posture changes. An outdated security runbook is almost worse than none.*
