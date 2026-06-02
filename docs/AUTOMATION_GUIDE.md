# Automation Guide — Human-in-the-Loop Guardrails
# Verdigris Botanica Tribal Nation — Safe Automation Practices

**Authority**: Alaina Padgett — alaina@verdigrisbotanicanation.org  
**Tenant Domain**: verdigrisbotanicanation.org  
**Last Updated**: February 2026

---

## Guiding Principle

> **All automation in VBTN systems is assistive, not autonomous.**  
> No automation shall create, modify, sign, publish, or distribute a legal document without explicit human approval from the Tribal Administrator or designated reviewer.

This document defines which parts of the VBTN compliance pipeline can be safely automated, which require human approval, and which must always remain manual.

---

## 1. The HITL (Human-in-the-Loop) Framework

### Three Tiers of Actions

| Tier | Category | Examples | Automation Level |
|------|----------|----------|-----------------|
| **A** | Fully Automatable | Notifications, status checks, document hashing, report generation | ✅ Fully automated |
| **B** | Automatable with HITL Gate | Document routing, compliance checks, archive operations | ⚠️ Automated but requires human approval before proceeding |
| **C** | Always Manual | Document signing, legal filing, financial disbursements, public declarations | 🔴 Never automated — human only |

### HITL Gate Mechanism

For all **Tier B** actions, automation halts and presents the admin with an approval request via:
1. **Microsoft Teams Adaptive Card** — with document summary and Approve / Reject buttons
2. **Email notification** to alaina@verdigrisbotanicanation.org with one-click approval link
3. **GitHub Issue** created with `needs-review` label — admin must comment `APPROVE` or `REJECT`

Automation **only proceeds** when the admin explicitly approves via one of these channels. All approval decisions are logged with timestamp and approver identity.

---

## 2. What Can Be Safely Automated (Tier A)

### Document Intake Notifications
When a new document is uploaded to SharePoint:
- Automatically notify the admin (Teams, email)
- Extract and log document metadata (name, type, author, size, hash)
- Create a GitHub tracking issue with document metadata
- Apply a preliminary classification label based on filename pattern matching

### Compliance Checks
On document intake or push to repository:
- Check document naming conventions
- Verify required metadata fields are present
- Compute SHA-256 hash for integrity tracking
- Check for sensitive data patterns (PII, credentials) that should not be committed
- Generate compliance check report

### Scheduled Reporting
- Monthly ScubaGear M365 security assessment (report only — no auto-remediation)
- Monthly document processing summary
- Weekly pending document status report

### Archiving Completed Documents
After a document is fully signed (DocuSign webhook confirms completion):
- Move to `Published Documents` in SharePoint
- Update GitHub issue status to `closed` with `signed-archived` label
- Append chain-of-custody record to issue

---

## 3. Actions Requiring HITL Approval (Tier B)

### Document Routing to DocuSign
- **Trigger**: Compliance check passes
- **HITL gate**: Admin reviews compliance report and explicitly approves routing
- **What admin sees**: Document name, type, classification, compliance summary, proposed signatories
- **Approval window**: 48 hours before escalation

### Publishing to Public-Facing Channels
- **Trigger**: Admin request or workflow event
- **HITL gate**: Admin reviews document and confirms it is approved for public release
- **Applies to**: Tribal Declarations, public Resolutions, press releases

### External Agency Notifications
- **Trigger**: Document signed and ready for submission to external party
- **HITL gate**: Admin approves the specific notification content and recipient list

### SharePoint Folder Reorganization
- **Trigger**: Monthly archiving workflow
- **HITL gate**: Admin approves the archive list before files are moved

---

## 4. Always Manual Actions (Tier C)

The following actions are **never automated** regardless of system capability:

| Action | Reason |
|--------|--------|
| Signing legal documents | Requires sovereign intent and conscious act |
| Approving financial disbursements | Fiduciary responsibility — requires human judgment |
| Enrolling / revoking tribal members | Affects sovereign status of individuals |
| Executing contracts with external agencies | Legal liability requires deliberate human act |
| Publicly declaring tribal policy positions | Sovereign speech — must reflect actual tribal intent |
| Modifying trust instruments | Highest legal consequence — zero tolerance for automation |
| Revoking documents or declarations | Irreversible with potential legal consequences |

---

## 5. GitHub Actions Workflow — Safe Automation

### `.github/workflows/compliance-check.yml`

This workflow runs automatically on:
- Push to any branch
- Pull request creation or update
- `repository_dispatch` events from Power Automate

**What it does (all Tier A):**
1. Checks out the repository
2. Scans for any accidentally committed sensitive data
3. Validates document naming conventions for any new/modified files
4. Computes hashes of tracked documents
5. Generates a compliance summary report
6. Posts the report as a comment on the associated pull request or issue
7. Sets the workflow status (pass/fail)

**What it does NOT do automatically:**
- It does not route documents to DocuSign
- It does not publish documents publicly
- It does not modify any SharePoint content

### Triggering DocuSign Routing (Requires Admin Approval)
After the compliance check passes, the admin must manually trigger the DocuSign routing step:
1. Review the compliance check report in the GitHub pull request / issue
2. Comment `APPROVE SIGNING: <document-name>` on the GitHub issue
3. The `compliance-check.yml` workflow listens for this comment (via `issue_comment` event) and proceeds with DocuSign routing only when the exact approval phrase is present from the admin account (`@Lainyshell`)

---

## 6. Power Automate — Safe Flow Design

### Approval Connectors
All Power Automate flows that route documents or send external communications use the **Approvals** connector to create an approval request before proceeding.

```
[Trigger] → [Get document metadata] → [Post compliance summary] 
         → [Create Approval: "Approve document for routing?"] 
         → [Wait for response] 
         → [If Approved] → [Proceed with routing]
         → [If Rejected] → [Notify admin, close loop]
```

### Error Handling
All flows include:
- **Try/Catch** blocks to handle API failures gracefully
- **Admin notification** on any flow failure
- **No silent failures**: Every failure creates a Teams/email alert and a GitHub issue

---

## 7. Inbox & SharePoint Triage Automation

### Safe Email Triage (Tier B)
The email triage Power Automate flow (see `docs/M365_AZURE_INTEGRATION.md`, Flow 4) can:
- ✅ Automatically copy attachments to SharePoint `Tribal Filings/Inbox Review`
- ✅ Automatically create a review task for the admin
- ✅ Automatically apply a preliminary classification label

The flow **cannot**:
- 🔴 Delete or archive the original email without admin approval
- 🔴 Forward or reply to the sender without admin approval
- 🔴 Automatically classify a document as `SOVEREIGN-RESTRICTED`

### Safe SharePoint Triage (Tier B)
When a document is uploaded to SharePoint:
- ✅ Automatically notify admin
- ✅ Automatically extract metadata
- ✅ Automatically compute document hash
- ✅ Automatically check for naming convention compliance

The flow **cannot**:
- 🔴 Move files between classification levels without admin approval
- 🔴 Grant or revoke SharePoint access without admin approval
- 🔴 Delete any document (deletion is always manual with 30-day recycle bin recovery)

---

## 8. GitHub Secrets Management

All secrets used in GitHub Actions are stored as **Environment Secrets** under the `compliance` environment, which requires a required reviewer (admin) before any workflow using these secrets can proceed.

**To configure:**
1. Go to GitHub → Settings → Environments → `compliance`
2. Under **Required reviewers**, add: `@Lainyshell`
3. This creates an automatic HITL gate for any workflow deployment using DocuSign, SharePoint, or Azure secrets

---

## 9. Audit Log

Every automated and human action in the VBTN compliance pipeline is logged:

| System | Log Location |
|--------|-------------|
| GitHub Actions | GitHub Actions run history (90-day retention) |
| Power Automate | Power Automate run history + Azure Monitor |
| DocuSign | DocuSign Audit Events (FedRAMP audit log) |
| SharePoint | SharePoint version history + compliance center |
| Entra ID | Azure AD sign-in and audit logs |

Logs are retained for a minimum of **7 years** in accordance with tribal record-keeping requirements.

---

*Document Authority: Alaina Padgett — alaina@verdigrisbotanicanation.org*  
*Verdigris Botanica Tribal Nation Trust*
