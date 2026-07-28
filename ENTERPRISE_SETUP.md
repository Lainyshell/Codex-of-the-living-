# Enterprise Setup Guide — Verdigris Botanica Tribal Nation (VBTN)

## Organization Identity

| Field | Value |
|-------|-------|
| **Organization Name** | Verdigris Botanica Tribal Nation Trust |
| **Primary Domain** | verdigrisbotanicanation.org |
| **Repository Administrator** | Alaina Padgett |
| **Admin Email** | alaina@verdigrisbotanicanation.org |
| **Purpose** | Sovereign Tribal Compliance & Data Governance Portal |

---

## 1. GitHub Enterprise Account Setup

### 1.1 Steps to Enable GitHub Enterprise

1. Navigate to [github.com/enterprise](https://github.com/enterprise) and begin an Enterprise trial or purchase.
2. Set the **Enterprise slug** to `verdigris-botanica-tribal-nation` (or equivalent).
3. Add the organization `Lainyshell/Codex-of-the-living-` to the enterprise account.
4. Designate **alaina@verdigrisbotanicanation.org** as the **Enterprise Owner** and **Organization Admin**.
5. Enable **SAML Single Sign-On (SSO)** using the Microsoft Entra ID (Azure AD) tenant for verdigrisbotanicanation.org (see Section 2).
6. Enforce two-factor authentication (2FA) for all members.
7. Configure **IP allow lists** to restrict access to known VBTN network ranges where applicable.

### 1.2 Repository Settings

- **Visibility**: Private (sovereign tribal data)
- **Branch protection** on `main`:
  - Require pull request reviews before merging
  - Require status checks to pass (compliance workflow)
  - Require signed commits
  - Restrict who can push: admin only (alaina@verdigrisbotanicanation.org)
- **CODEOWNERS**: Enforced via `.github/CODEOWNERS`

### 1.3 GitHub Advanced Security

Enable the following for sovereign data protection:
- Secret scanning (block accidental credential commits)
- Dependabot security alerts
- Code scanning (CodeQL)

---

## 2. Microsoft Azure / Entra ID Integration

### 2.1 SAML SSO with GitHub Enterprise

Configure GitHub Enterprise SAML SSO to authenticate against the VBTN Microsoft Entra ID tenant:

1. In **Azure Portal → Entra ID → Enterprise Applications**, create a new app:
   - Template: **GitHub Enterprise Cloud – Organization**
2. Configure **Single Sign-On** with SAML:
   - **Identifier (Entity ID)**: `https://github.com/orgs/Lainyshell`
   - **Reply URL**: `https://github.com/orgs/Lainyshell/saml/consume`
   - **Sign-on URL**: `https://github.com/orgs/Lainyshell/sso`
3. Map Entra ID user attributes:
   - `user.userprincipalname` → `NameID`
   - `user.displayname` → `full_name`
   - `user.mail` → `emails`
4. Assign the `alaina@verdigrisbotanicanation.org` account and any other authorized VBTN staff.
5. In **GitHub Enterprise → Organization Settings → Security → SAML single sign-on**, paste the Entra metadata URL.
6. Test and enforce SSO.

### 2.2 Azure Key Vault for Secrets

All repository secrets and API credentials must be stored in **Azure Key Vault** under the VBTN tenant:
- Key Vault Name: `vbtn-github-secrets`
- Access Policy: VBTN Admins only
- Secrets to store:
  - `GITHUB_ACTIONS_TOKEN`
  - `DOCUSIGN_INTEGRATION_KEY`
  - `DOCUSIGN_ACCOUNT_ID`
  - `SHAREPOINT_CLIENT_ID`
  - `SHAREPOINT_CLIENT_SECRET`

Reference these from GitHub Actions through Azure login plus Key Vault reads. Keep only OIDC metadata (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`) and emergency fallback credentials in GitHub Environments.

### 2.3 PowerApps & Power Automate Integration

Power Automate flows connect this repository to VBTN operational workflows:

| Flow Name | Trigger | Action |
|-----------|---------|--------|
| `New Document Alert` | New file committed to `main` | Notify admin via Teams/email |
| `Compliance Check Failed` | Compliance workflow fails | Create Power Automate approval task |
| `Legal Doc Signed` | DocuSign webhook | Update SharePoint document library status |
| `SharePoint to GitHub` | New filing uploaded to SharePoint | Open GitHub issue for review |

See `docs/AUTOMATION_GUIDE.md` for full Power Automate setup instructions.

---

## 3. Compliance Door Architecture

This GitHub repository acts as the **Compliance Door** — the authoritative, audited gateway for all VBTN sovereign data, legal filings, and workflow enforcement.

```
┌────────────────────────────────────────────────────────────────────┐
│                     VBTN Compliance Door                           │
│               (GitHub: Codex-of-the-Living)                        │
│                                                                    │
│   ┌──────────┐   ┌──────────────┐   ┌──────────────────────────┐  │
│   │ SharePoint│──▶│ GitHub Repo  │──▶│  Compliance Workflow      │  │
│   │ OneDrive  │   │ (this repo)  │   │  (GitHub Actions CI)     │  │
│   └──────────┘   └──────┬───────┘   └──────────┬───────────────┘  │
│                          │                       │                  │
│   ┌──────────┐           │            ┌──────────▼────────────┐    │
│   │ Entra ID │◀──────────┘            │  Human Review Gate    │    │
│   │ (SSO)    │                        │  (Admin Approval)     │    │
│   └──────────┘                        └──────────┬────────────┘    │
│                                                   │                 │
│   ┌──────────┐                        ┌──────────▼────────────┐    │
│   │DocuSign  │◀───────────────────────│  FedRAMP DocuSign     │    │
│   │FedRAMP   │                        │  Chain of Custody     │    │
│   └──────────┘                        └───────────────────────┘    │
└────────────────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. Tribal documents are uploaded to SharePoint / OneDrive.
2. Power Automate pushes metadata (not the raw document) to this GitHub repository for audit logging.
3. GitHub Actions runs the **Compliance Check** workflow to validate document hygiene.
4. If checks pass, an **admin approval gate** is required (human-in-the-loop).
5. Legal documents requiring signatures are routed to **FedRAMP DocuSign** via webhook.
6. Signed documents are archived back to SharePoint with an immutable audit trail.

---

## 4. Security & Sovereignty Principles

- All tribal data remains within the **VBTN Microsoft 365 tenant** (`verdigrisbotanicanation.org`).
- GitHub is used only as a **workflow orchestration and compliance audit layer** — no raw Personally Identifiable Information (PII) or sensitive tribal records are committed to GitHub.
- All automation includes **human-in-the-loop (HITL) checkpoints** before irreversible actions.
- Sovereign immunity and tribal data sovereignty are preserved through VBTN-controlled Entra ID identity management.
- FedRAMP-authorized services (Azure, DocuSign FedRAMP) are used exclusively for regulated data.

---

## 5. Next Steps Checklist

### GitHub Enterprise
- [ ] Upgrade GitHub organization to GitHub Enterprise Cloud
- [ ] Set enterprise owner: alaina@verdigrisbotanicanation.org
- [ ] Enable SAML SSO (Entra ID)
- [ ] Enforce 2FA for all members
- [ ] Enable GitHub Advanced Security (secret scanning, Dependabot, CodeQL)
- [ ] Configure branch protection on `main`

### Azure / M365
- [ ] Configure Entra ID SAML app for GitHub SSO
- [ ] Create `vbtn-github-secrets` Key Vault
- [ ] Add GitHub Actions secrets to Key Vault and GitHub Environment
- [ ] Configure Power Automate flows (see `docs/AUTOMATION_GUIDE.md`)
- [ ] Verify SharePoint document library integration

### DocuSign FedRAMP
- [ ] Set up DocuSign FedRAMP account
- [ ] Configure webhook for GitHub Actions
- [ ] Test legal document signing workflow (see `docs/DOCUSIGN_WORKFLOW.md`)

### Compliance
- [ ] Run initial ScubaGear M365 assessment
- [ ] Review `docs/TENANT_DEFINITIONS.md` and customize definitions
- [ ] Enable compliance check workflow (`.github/workflows/compliance-check.yml`)
- [ ] Schedule monthly compliance assessments

---

*Document Authority: Alaina Padgett, Administrator — Verdigris Botanica Tribal Nation Trust*  
*Last Updated: February 2026*
