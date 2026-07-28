# M365 & Azure Integration Guide
# Verdigris Botanica Tribal Nation — Microsoft Cloud Connectivity

**Authority**: Alaina Padgett — alaina@verdigrisbotanicanation.org  
**Tenant Domain**: verdigrisbotanicanation.org  
**Last Updated**: February 2026

---

## Overview

This guide describes how the VBTN GitHub Compliance Door integrates with the Microsoft 365 tenant (`verdigrisbotanicanation.org`) including Azure, Entra ID, SharePoint, OneDrive, Power Automate, and Power Apps. The integration creates a secure, sovereign data pipeline where Microsoft 365 serves as the authoritative data store and GitHub serves as the compliance and workflow enforcement layer.

---

## 1. Microsoft Entra ID (Azure AD) — Identity

### SAML SSO Configuration for GitHub

All GitHub organization members must authenticate using VBTN Entra ID credentials.

**In Azure Portal → Entra ID → Enterprise Applications:**

1. Click **+ New application** → Search for **GitHub Enterprise Cloud – Organization**
2. Name: `VBTN GitHub SSO`
3. Under **Single sign-on → SAML**, configure:
   ```
   Identifier (Entity ID): https://github.com/orgs/Lainyshell
   Reply URL:              https://github.com/orgs/Lainyshell/saml/consume
   Sign-on URL:            https://github.com/orgs/Lainyshell/sso
   ```
4. **User Attributes & Claims:**
   | Claim | Source Attribute |
   |-------|-----------------|
   | Unique User Identifier | `user.userprincipalname` |
   | `full_name` | `user.displayname` |
   | `emails` | `user.mail` |
5. Download the **Federation Metadata XML**.
6. Assign users: `alaina@verdigrisbotanicanation.org` (Owner), additional staff as needed.

**In GitHub Organization Settings → Security → SAML single sign-on:**
1. Paste the **SAML SSO URL** and **Certificate** from the Azure metadata XML.
2. Test SSO, then **Enforce SAML SSO**.

---

## 2. SharePoint Online — Document Repository

### Document Library Structure

VBTN SharePoint is organized as follows for compliance integration:

```
SharePoint Site: VBTN Compliance Portal
├── Tribal Filings/
│   ├── Declarations/
│   ├── Resolutions/
│   ├── MOUs/
│   └── Affidavits/
├── Legal Documents/
│   ├── Contracts/
│   ├── Trust Instruments/
│   └── Agreements/
├── Financial Records/
│   ├── Disbursement Ledgers/
│   └── Fee Schedules/
└── Published Documents/          ← Signed, final documents
    └── [Year]/[Month]/
```

### Connecting SharePoint to GitHub (via Power Automate)

A Power Automate flow monitors the SharePoint `Tribal Filings` library and notifies the GitHub compliance workflow when new documents are uploaded:

1. **Trigger**: "When a file is created or modified" in SharePoint library
2. **Action**: HTTP POST to GitHub Actions API to trigger compliance review workflow
3. **Human Gate**: Admin receives Teams/email notification and must approve before GitHub workflow proceeds

See Section 4 (Power Automate) for flow configuration details.

### Accessing VBTN SharePoint from GitHub Actions

GitHub Actions authenticates to SharePoint using an **Azure App Registration**:

1. In **Azure Portal → Entra ID → App Registrations**, create or extend:
   - Name: `vbtn-github-actions`
   - Supported account types: Single tenant
2. If the same app registration is used for both SharePoint and mailbox automation:
   - Standardize GitHub environment secrets on `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID`
   - Keep SharePoint client-secret usage only where legacy connectors still require it
3. Under **API Permissions**, add:
   - `Sites.ReadWrite.All` (SharePoint)
   - `Files.ReadWrite.All` (OneDrive / SharePoint)
   - `User.ReadWrite.All` (tenant mailbox user creation and updates)
   - `LicenseAssignment.ReadWrite.All` (mailbox license assignment)
   - `Organization.Read.All` (license SKU discovery)
4. Grant admin consent for the Microsoft Graph application permissions above.
5. These mailbox permissions are highly privileged:
   - Limit them to the OIDC-backed provisioning app registration
   - Require GitHub `compliance` environment approval before every run
   - Review Entra ID audit logs after each provisioning run
6. Store mailbox bootstrap passwords in **Azure Key Vault** (for example `MAILBOX-OPS-PASSWORD`) and reference them from the manual provisioning workflow input.
7. Note the **Application (client) ID** → GitHub Secret: `AZURE_CLIENT_ID`
8. Note the **Directory (tenant) ID** → GitHub Secret: `AZURE_TENANT_ID`
9. Note the **Subscription ID** → GitHub Secret: `AZURE_SUBSCRIPTION_ID`

---

## 3. OneDrive for Business — Admin Files

OneDrive is used by the Tribal Administrator (alaina@verdigrisbotanicanation.org) for working copies of documents prior to formal submission to SharePoint compliance libraries.

**Recommended OneDrive folder structure:**
```
OneDrive — alaina@verdigrisbotanicanation.org
├── VBTN Working Docs/
│   ├── Drafts/
│   ├── For Review/
│   └── Ready for Signing/
└── Archive/
```

Documents in **Ready for Signing** are moved to SharePoint `Tribal Filings` and trigger the compliance + DocuSign workflow automatically.

---

## 4. Power Automate — Workflow Automation

### Required Flows

The following Power Automate flows support the VBTN compliance pipeline. All flows enforce **human-in-the-loop (HITL)** approval before irreversible actions.

#### Flow 1: New Document Intake
- **Trigger**: New file in SharePoint `Tribal Filings` library
- **Steps**:
  1. Extract document metadata (name, type, author, date)
  2. Post to GitHub via API: create a new issue in `Codex-of-the-living-` with document metadata and classification request
  3. Send Teams/email notification to Alaina Padgett for review
  4. **HITL Gate**: Await admin approval before proceeding
  5. On approval: trigger `compliance-check.yml` workflow

#### Flow 2: Compliance Check Result Notification
- **Trigger**: GitHub Actions `compliance-check.yml` workflow completes
- **Steps**:
  1. Parse workflow result (pass/fail)
  2. If **pass**: Notify admin — document ready for DocuSign routing
  3. If **fail**: Send detailed failure report to admin and document owner
  4. **HITL Gate**: Admin must acknowledge and either remediate or route to DocuSign

#### Flow 3: DocuSign Routing
- **Trigger**: Admin approves document for signing (Teams Adaptive Card response)
- **Steps**:
  1. Send document from SharePoint to DocuSign FedRAMP via API
  2. Route to designated signatories per document type
  3. Track signing status
  4. On completion: move to `Published Documents` in SharePoint

#### Flow 4: Email/Inbox Triage for Tribal Filings
- **Trigger**: Incoming email to alaina@verdigrisbotanicanation.org with keywords: `declaration`, `resolution`, `MOU`, `affidavit`, `filing`
- **Steps**:
  1. Attach email and any attachments to SharePoint `Tribal Filings/Inbox Review`
  2. Create task in Microsoft To Do / Planner for Alaina to review
  3. **HITL Gate**: Admin decides classification and disposition
  4. Admin moves to appropriate folder → triggers Flow 1

### Setting Up Power Automate Flows

1. Go to [make.powerautomate.com](https://make.powerautomate.com) with your VBTN credentials.
2. Create each flow described above using the **Automated cloud flow** template.
3. For GitHub API calls, use the **HTTP** connector with:
   - Method: `POST`
   - URI: `https://api.github.com/repos/Lainyshell/Codex-of-the-living-/dispatches`
   - Headers: `Authorization: token <GITHUB_PAT>`, `Accept: application/vnd.github.v3+json`
   - Body: `{"event_type": "compliance-review", "client_payload": {"document": "<name>"}}`
4. Store the GitHub PAT in **Azure Key Vault** and reference via Power Automate **Key Vault connector**.

### Manual Tenant Mailbox Provisioning Workflow

`/.github/workflows/provision-tenant-mailboxes.yml` provides a manual, approval-gated workflow for creating or updating Exchange-backed Microsoft 365 users in the VBTN tenant.

- **Trigger**: `workflow_dispatch` only
- **Approval gate**: GitHub `compliance` environment reviewer
- **Cloud**: `AzureUSGovernment`
- **Script**: `scripts/provision_mailboxes.py`
- **Microsoft Graph base URL**: `https://graph.microsoft.us/v1.0`

Provide a JSON array in the `mailboxes_json` workflow input. Each mailbox entry supports:

```json
[
  {
    "user_principal_name": "operations@verdigrisbotanicanation.org",
    "display_name": "VBTN Operations",
    "given_name": "VBTN",
    "surname": "Operations",
    "department": "Operations",
    "job_title": "Operations Mailbox",
    "usage_location": "US",
    "license_sku_part_numbers": ["EXCHANGESTANDARD"],
    "password_secret_name": "MAILBOX-OPERATIONS-PASSWORD"
  }
]
```

Use `dry_run=true` first to preview create/update and license-assignment actions before making tenant changes.

---

## 5. Power Apps — Custom Tribal Applications

Power Apps deployed on the VBTN tenant connect to this GitHub repository for workflow status and compliance data.

### Compliance Dashboard App
A Power App providing Alaina and authorized staff with a real-time view of:
- Pending document reviews
- Compliance check results
- DocuSign signing queue
- Published documents archive

**Data Sources:**
- SharePoint `Tribal Filings` library
- GitHub Actions API (via Power Automate connector)
- DocuSign API

### Deployment
1. Open [make.powerapps.com](https://make.powerapps.com).
2. Import the VBTN Compliance Dashboard app package (to be created).
3. Connect to the SharePoint site `VBTN Compliance Portal`.
4. Publish and share with alaina@verdigrisbotanicanation.org.

---

## 6. Azure Key Vault — Secrets Management

All credentials and secrets used by GitHub Actions and Power Automate are stored in Azure Key Vault.

**Vault Name**: `vbtn-github-secrets`  
**Resource Group**: `vbtn-compliance`  
**Location**: East US (or nearest to tribal operations)

| Secret Name | Description |
|-------------|-------------|
| `GITHUB-PAT` | GitHub Personal Access Token for API calls |
| `DOCUSIGN-INTEGRATION-KEY` | DocuSign FedRAMP integration key |
| `DOCUSIGN-ACCOUNT-ID` | DocuSign FedRAMP account ID |
| `DOCUSIGN-USER-ID` | DocuSign user ID (Alaina Padgett) |
| `SHAREPOINT-CLIENT-ID` | Azure App Registration client ID |
| `SHAREPOINT-CLIENT-SECRET` | Azure App Registration client secret |
| `AZURE-TENANT-ID` | VBTN Azure tenant ID |

**Access Policy**: Only `vbtn-github-actions` app registration and admin (`alaina@verdigrisbotanicanation.org`) may read secrets.

---

## 7. DNS Configuration

VBTN DNS records for M365 are documented in `VBTN_DNS_Records_For_M365.xlsx`. Key records:

- **MX record**: Routes email to Exchange Online
- **SPF / DKIM / DMARC**: Email authentication and anti-spoofing
- **CNAME autodiscover**: Outlook autodiscover
- **TXT domain verification**: Entra ID domain verification

Verify DNS health at: [Microsoft 365 Admin Center → Domains](https://admin.microsoft.com/#/Domains)

---

## 8. Security Baseline (ScubaGear)

Per `CISA_M365_ScubaGear_v1.7.0_Advisory.md` and VBTN's voluntary adoption of federal security best practices:

```powershell
# Run ScubaGear assessment against VBTN M365 tenant
Install-Module -Name ScubaGear -Force
Invoke-SCuBA -ProductNames * -OutPath ./scuba-reports/
```

Schedule monthly assessments and store reports in SharePoint `VBTN Compliance Portal/Security Assessments`.       

---

*Document Authority: Alaina Padgett — alaina@verdigrisbotanicanation.org*  
*Verdigris Botanica Tribal Nation Trust*
