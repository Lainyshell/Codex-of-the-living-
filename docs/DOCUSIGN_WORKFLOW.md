# FedRAMP DocuSign Workflow
# Verdigris Botanica Tribal Nation — Legal Document Signing & Chain of Custody

**Authority**: Alaina Padgett — alaina@verdigrisbotanicanation.org  
**Tenant Domain**: verdigrisbotanicanation.org  
**DocuSign Environment**: FedRAMP (US Government Cloud)  
**Last Updated**: February 2026

---

## Overview

All VBTN legal documents requiring formal signatures — including Declarations, Resolutions, MOUs, Trust Instruments, and Contracts — must be executed through the VBTN **FedRAMP DocuSign** account. This ensures:

- **Complete transparency**: Every signature event is time-stamped and logged.
- **Chain of custody preservation**: An immutable audit trail from draft to final signed document.
- **Sovereign enforceability**: FedRAMP-authorized signatures are legally recognized and defensible.
- **Automated routing**: Documents are routed to the correct signatories without manual email chains.

---

## 1. DocuSign FedRAMP Account Setup

### 1.1 Create the VBTN FedRAMP DocuSign Account

1. Go to [apps-d.docusign.com](https://apps-d.docusign.com) (DocuSign US Government Cloud).
2. Register with: `alaina@verdigrisbotanicanation.org`
3. Select plan: **DocuSign for Government (FedRAMP)** or **DocuSign eSignature Federal Edition**
4. Verify the domain `verdigrisbotanicanation.org`.
5. Note the following credentials (store in Azure Key Vault `vbtn-github-secrets`):
   - `DOCUSIGN-ACCOUNT-ID`
   - `DOCUSIGN-USER-ID`
   - `DOCUSIGN-INTEGRATION-KEY` (from API app registration below)

### 1.2 DocuSign API App Registration

1. In the DocuSign Admin console, go to **API and Keys**.
2. Create a new app: `VBTN Compliance Door Integration`
3. Note the **Integration Key** → store as `DOCUSIGN-INTEGRATION-KEY` in Azure Key Vault.
4. Under **Authentication**, select **JWT Grant** (for server-to-server automation).
5. Generate an RSA keypair:
   - Store **private key** securely in Azure Key Vault.
   - Upload **public key** to DocuSign.
6. Add redirect URI: `https://github.com/Lainyshell/Codex-of-the-living-`

### 1.3 Configure GitHub Secrets

Add the following to GitHub → Settings → Environments → `compliance` → Secrets:
- `DOCUSIGN_ACCOUNT_ID`
- `DOCUSIGN_USER_ID`
- `DOCUSIGN_INTEGRATION_KEY`
- `DOCUSIGN_PRIVATE_KEY` (RSA private key, base64-encoded)
- `DOCUSIGN_BASE_URL` (FedRAMP base URL: `https://na4.docusign.net/restapi`)

---

## 2. Document Routing Rules

Each VBTN document type has a defined signing workflow:

### Tribal Declaration
| Step | Signer | Role |
|------|--------|------|
| 1 | Alaina Padgett | Tribal Administrator (Author / Approver) |
| 2 | Board Chair (designated) | Witness / Endorser |

### Tribal Resolution
| Step | Signer | Role |
|------|--------|------|
| 1 | Board of Directors (quorum) | Voting signatories |
| 2 | Alaina Padgett | Tribal Administrator (Certifying Officer) |

### Memorandum of Understanding (MOU)
| Step | Signer | Role |
|------|--------|------|
| 1 | Counterparty representative | Agreeing Party |
| 2 | Alaina Padgett | VBTN Tribal Administrator |

### Contract / Agreement
| Step | Signer | Role |
|------|--------|------|
| 1 | Counterparty | Contracting Party |
| 2 | Alaina Padgett | VBTN Authorized Signatory |

### Trust Instrument / Funding Agreement
| Step | Signer | Role |
|------|--------|------|
| 1 | Trustee(s) | Trust Administrator(s) |
| 2 | Alaina Padgett | Tribal Administrator |

---

## 3. Automated Signing Workflow (GitHub Actions + Power Automate)

### 3.1 Workflow Diagram

```
SharePoint Upload
      │
      ▼
Power Automate Flow 1 (New Document Intake)
      │
      ▼
GitHub Issue Created (metadata only, no raw doc)
      │
      ▼
Compliance Check Workflow (.github/workflows/compliance-check.yml)
      │
      ├── FAIL ──▶ Admin notified, document returned for remediation
      │
      └── PASS ──▶ Admin Approval Gate (Teams Adaptive Card)
                         │
                         ├── REJECTED ──▶ Document returned, issue closed
                         │
                         └── APPROVED ──▶ Power Automate Flow 3 (DocuSign Routing)
                                               │
                                               ▼
                                         DocuSign FedRAMP
                                         (Routes to signatories)
                                               │
                                         ┌─────┴─────┐
                                         │           │
                                      SIGNED      DECLINED
                                         │           │
                                         ▼           ▼
                                  Archive to    Admin notified,
                                  SharePoint    workflow closed
                                  (Published)
```

### 3.2 GitHub Actions — DocuSign Step

The `compliance-check.yml` workflow (in `.github/workflows/`) includes a DocuSign routing step that executes after all checks pass and admin approval is received. The step uses the DocuSign eSignature REST API:

```python
# Conceptual — integrated into compliance workflow
import base64, requests

def send_to_docusign(document_name, document_base64, signers, account_id, token):
    """Route a document to DocuSign FedRAMP for signatures."""
    envelope = {
        "emailSubject": f"VBTN Document for Signature: {document_name}",
        "documents": [{
            "documentBase64": document_base64,
            "name": document_name,
            "fileExtension": "pdf",
            "documentId": "1"
        }],
        "recipients": {
            "signers": [
                {
                    "email": signer["email"],
                    "name": signer["name"],
                    "recipientId": str(idx + 1),
                    "routingOrder": str(signer.get("order", idx + 1)),
                    "tabs": {
                        "signHereTabs": [{"documentId": "1", "pageNumber": "1",
                                          "xPosition": "100", "yPosition": "100"}]
                    }
                }
                for idx, signer in enumerate(signers)
            ]
        },
        "status": "sent"
    }
    base_url = "https://na4.docusign.net/restapi"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    resp = requests.post(
        f"{base_url}/v2.1/accounts/{account_id}/envelopes",
        json=envelope,
        headers=headers,
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()
```

---

## 4. Chain of Custody Record

Every document processed through the VBTN compliance pipeline receives an immutable chain-of-custody record containing:

| Field | Source |
|-------|--------|
| Document Name | SharePoint metadata |
| Document Hash (SHA-256) | Computed at upload |
| Uploaded By | SharePoint / Entra ID |
| Upload Timestamp | SharePoint / UTC |
| Compliance Check Result | GitHub Actions log |
| Admin Approval By | Teams / GitHub Issue comment |
| Admin Approval Timestamp | GitHub API |
| DocuSign Envelope ID | DocuSign API response |
| Signatories | DocuSign recipients |
| Signing Completed | DocuSign webhook |
| Final Archive Location | SharePoint URL |

This record is stored as a JSON object in the GitHub issue associated with the document, creating a permanent, auditable history.

---

## 5. Webhook Configuration

Configure DocuSign to notify GitHub Actions when signing events occur:

1. In DocuSign Admin → **Connect**, add a new connection:
   - Name: `VBTN GitHub Compliance`
   - URL: `https://api.github.com/repos/Lainyshell/Codex-of-the-living-/dispatches`
   - Events: `envelope-completed`, `envelope-declined`, `envelope-voided`
   - Authentication: Add GitHub PAT as Authorization header
2. Map DocuSign events to GitHub `repository_dispatch` event types.
3. GitHub Actions `compliance-check.yml` listens for `repository_dispatch` to update the chain-of-custody issue.

---

## 6. Audit & Reporting

### Monthly Audit
A scheduled GitHub Actions workflow (monthly) generates a compliance report including:
- All documents processed in the period
- Completion rates (signed vs. pending vs. declined)
- Average time-to-signature
- Any compliance check failures and resolutions

Reports are pushed to SharePoint `VBTN Compliance Portal/Audit Reports/` automatically.

### On-Demand Report
The Tribal Administrator can trigger a report at any time via GitHub Actions **workflow_dispatch**.

---

## 7. Enforcing Difficult Liaisons and Agencies

For documents requiring signature from external agencies, government entities, or other parties who may be difficult to reach:

1. DocuSign FedRAMP sends automatic reminders at: 3 days, 7 days, 14 days after routing.
2. GitHub Actions escalation workflow opens a GitHub issue flagging the document as **Pending External Signature** after 7 days.
3. Power Automate sends a formal email reminder to the agency on VBTN letterhead using the Exchange Online connector.
4. If no response after 30 days, an issue is created for the Tribal Administrator to determine next steps (escalation, alternative enforcement, or legal action).

---

*Document Authority: Alaina Padgett — alaina@verdigrisbotanicanation.org*  
*Verdigris Botanica Tribal Nation Trust*
