# VBTN Tenant Definitions
# Verdigris Botanica Tribal Nation — Official Term & Concept Glossary

**Document Authority**: Alaina Padgett, Administrator  
**Org Domain**: verdigrisbotanicanation.org  
**Classification**: Internal Governance — Public Release Permitted  
**Last Updated**: February 2026

---

## Purpose

This document establishes official definitions for terms, roles, document types, and system concepts used within the Verdigris Botanica Tribal Nation (VBTN) Microsoft 365 tenant, GitHub compliance repository, and associated automation workflows. These definitions govern how data, documents, and processes are labeled, routed, and handled throughout the VBTN compliance ecosystem.

---

## Part I — Organizational Definitions

### Verdigris Botanica Tribal Nation (VBTN)
A sovereign tribal nation operating as a trust entity. VBTN exercises inherent tribal sovereignty over its data, governance processes, and fiduciary responsibilities. As a sovereign entity, VBTN is not subject to federal BOD directives (e.g., BOD 25-01) but voluntarily adopts federal security best practices to ensure the highest standard of data protection and compliance.

### Verdigris Botanica Tribal Nation Trust (VBTNT)
The trust instrument and legal entity through which VBTN manages assets, funds, and fiduciary obligations on behalf of tribal members. All financial transactions, disbursements, and contracts flow through the Trust. See: `TRVMasterTrustAndFundingAgreement.pdf`.

### Tribal Administrator
The individual designated with administrative authority over VBTN systems, repositories, and compliance processes. **Current Administrator: Alaina Padgett (alaina@verdigrisbotanicanation.org)**.

### Tribal Member
Any individual formally enrolled under `TribalMembershipAgreement.pdf` with recognized membership in the Verdigris Botanica Tribal Nation.

### Tribal Council / Board of Directors
The governing body authorized to pass resolutions, enter contracts, and direct VBTN operations. Resolutions require formal recording per `TribalResolution.pdf` standards.

---

## Part II — Document Type Definitions

### Tribal Declaration
A formal sovereign pronouncement issued by the VBTN Tribal Administrator or Council affirming rights, status, positions, or policies. Declarations carry the full weight of tribal sovereign authority.  
*Example*: `TribalSovereigntyDeclaration.pdf`  
*Routing*: Must pass compliance check → Admin approval → FedRAMP DocuSign signature → SharePoint archive.

### Memorandum of Understanding (MOU)
A non-binding or semi-binding agreement between VBTN and another party documenting mutual intentions, terms, and responsibilities. MOUs must be reviewed by the Tribal Administrator before execution.  
*Routing*: Draft in SharePoint → Compliance check → Human review → DocuSign → Archive.

### Tribal Resolution
A formal decision or directive passed by the VBTN Board of Directors. Resolutions are the primary mechanism for authorizing major actions, contracts, and governance changes.  
*Example*: `TribalResolution.pdf`, `VB Resolution of the board of directors copy.docx`  
*Routing*: Board vote required → Admin signature → FedRAMP DocuSign → Official record.

### Trust Indenture
The foundational legal document establishing the terms, conditions, and obligations of the VBTN Trust instrument.  
*Example*: `TrustIndenture.pdf`

### Trust Funding Agreement
An agreement governing the funding mechanisms, disbursement schedules, and fiduciary controls of the VBTN Trust.  
*Example*: `TrustFundingAgreement.pdf`, `TRVMasterTrustAndFundingAgreement.pdf`

### Disbursement Ledger
A formal financial record documenting all disbursements from the VBTN Trust. Must be cryptographically validated and immutably recorded.  
*Example*: `Schedule_Q_Disbursement_Ledger___Issue_001.csv`, `Verified_Transactions_Template.xlsx`

### Fee Schedule
The official schedule of fees charged by VBTN for services, permits, and administrative actions.  
*Example*: `FeeSchedule.pdf`

### Affidavit
A sworn written statement used to document facts, attest to identities, or support legal proceedings.  
*Example*: `Affidavit as to Fee Book.txt`, `Verdigris_Tribal_Tax_Exemption_Affidavit.docx`

### Infrastructure and Service Agreement
A contract governing the provision of infrastructure, technology, or operational services to or by VBTN.  
*Example*: `InfrastructureandServiceAgreement.pdf`

### Independent Contractor Agreement
A legal agreement governing the engagement of independent contractors by VBTN.  
*Example*: `Independent_Contractor_Agreement.docx`

### Intellectual Property Rights Agreement
A legal agreement governing the ownership, licensing, and protection of intellectual property created within or for VBTN.  
*Example*: `IntellectualPropertyRightsAgreement.pdf`

### Internal Policies and Procedures Manual
The authoritative reference for VBTN internal operational policies, governance procedures, and compliance requirements.  
*Example*: `InternalPoliciesandProceduresManualcomplete.pdf`

### Homestead Declaration
A sovereign declaration relating to land rights and homestead claims by or for VBTN members.  
*Example*: `HomesteadDeclaration.pdf`

---

## Part III — System & Workflow Definitions

### Compliance Door
This GitHub repository (`Lainyshell/Codex-of-the-living-`) serves as the **Compliance Door** — the authoritative, audited gateway enforcing document hygiene, chain-of-custody, and workflow controls for all VBTN operations. No legal document, declaration, or contract achieves official status without passing through the Compliance Door.

### VBTN M365 Tenant
The Microsoft 365 tenant operating under domain `verdigrisbotanicanation.org`, providing:
- **Exchange Online**: Official tribal email
- **SharePoint Online**: Document repository and collaboration
- **OneDrive for Business**: Admin and staff file storage
- **Microsoft Teams**: Internal communications
- **Entra ID (Azure AD)**: Identity and access management
- **Power Automate**: Workflow automation
- **Power Apps**: Custom tribal applications

### Entra ID (Azure Active Directory)
The identity provider for all VBTN systems. All users accessing VBTN GitHub, SharePoint, or integrated applications must authenticate through Entra ID via SAML or OAuth.

### FedRAMP DocuSign
The FedRAMP-authorized instance of DocuSign used by VBTN for legally binding electronic signatures on all tribal legal documents. FedRAMP authorization ensures compliance with federal data handling standards appropriate for sovereign tribal trust data.

### Chain of Custody
The complete, auditable record of who handled, reviewed, approved, and signed a document at every stage of its lifecycle. Maintained via:
- GitHub Actions workflow logs
- DocuSign FedRAMP audit trail
- SharePoint version history
- Azure immutable storage (where applicable)

### Human-in-the-Loop (HITL)
A mandatory design principle requiring human review and approval before any automation proceeds with irreversible actions. All VBTN automations include HITL checkpoints. No legal document may be published, signed, or distributed without explicit human authorization from the Tribal Administrator or designated reviewer.

### Compliance Check
An automated GitHub Actions workflow that validates:
- Document naming conventions
- Required metadata fields
- Classification labels
- File integrity (no tampering since last review)
- Presence of required signatures for routed documents

### SharePoint Document Library (Compliance)
The designated SharePoint library for VBTN legal filings: `VBTN Compliance Documents`. Access restricted to Tribal Administrator and authorized staff.

### Power Automate Flow
A Microsoft Power Automate automated workflow connecting VBTN systems. All flows are approved by the Tribal Administrator and documented in `docs/AUTOMATION_GUIDE.md`.

---

## Part IV — Data Classification Levels

| Level | Label | Description | Examples |
|-------|-------|-------------|---------|
| 1 | `PUBLIC` | May be shared publicly | Tribal declarations, public resolutions |
| 2 | `INTERNAL` | VBTN staff only | Policies, procedures, meeting notes |
| 3 | `CONFIDENTIAL` | Restricted to authorized parties | Contracts, MOUs, legal filings |
| 4 | `SOVEREIGN-RESTRICTED` | Tribal Administrator only | Trust instruments, member data, financial records |

All documents in this repository must carry a data classification label in their metadata.

---

## Part V — Regulatory & Standards References

| Standard / Framework | Applicability |
|---------------------|---------------|
| **FedRAMP** | Cloud services used by VBTN (Azure, DocuSign FedRAMP) |
| **NIST 800-53** | Security control framework voluntarily adopted |
| **CISA ScubaGear v1.7.0** | M365 security baseline assessment (voluntary) |
| **Tribal Sovereignty** | Paramount — supersedes federal mandates where applicable |
| **VBTN Internal Policies** | Binding on all VBTN staff and contractors |
| **DocuSign FedRAMP** | Electronic signature and chain-of-custody standard |

---

*These definitions are effective upon adoption by the Tribal Administrator.*  
*Alaina Padgett — alaina@verdigrisbotanicanation.org*  
*Verdigris Botanica Tribal Nation Trust*
