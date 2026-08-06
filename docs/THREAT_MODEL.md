# Threat Model
## Codex of the Living — Verdigris Botanica Tribal Nation Infrastructure

**Version:** 1.0
**Date:** 2026-08-06
**Review Cycle:** Annual (minimum)
**Maintainer:** System Steward

---

## 1. System and Scope

**System:** Codex of the Living — tribal financial, document, and governance infrastructure

**Assets Protected:**
- Member identity and contact information
- Financial records (transactions, ledgers, disbursements)
- Executed legal and governance documents
- REMIC instruments and trust records
- System credentials and access keys
- Governance and sovereignty instruments

**Out of Scope:** Physical security of endpoints; tribal council meeting security (handled separately)

---

## 2. Threat Actors

### TA-1: External Attacker (Criminal)
**Motivation:** Financial theft, credential theft, ransomware
**Capability:** Medium — commodity attack tools, phishing
**Likely Attack Path:** Phishing for credentials → unauthorized access → data exfiltration or ransomware

### TA-2: Hostile Government Actor
**Motivation:** Surveillance of tribal members, disruption of tribal sovereignty operations
**Capability:** High — nation-state tooling, legal process coercion
**Likely Attack Path:** Legal demand to cloud/DocuSign → compelled disclosure; OR advanced persistent threat against infrastructure

### TA-3: Disgruntled Insider
**Motivation:** Sabotage, unauthorized disclosure, personal gain
**Capability:** High within authorized scope — knows the system
**Likely Attack Path:** Bulk export before departure; unauthorized deletion; credential sharing; governance document tampering

### TA-4: Vendor or Partner Misuse
**Motivation:** Data monetization, competitive advantage
**Capability:** Medium — legitimate API access
**Likely Attack Path:** Unauthorized secondary use of member data; failure to delete on termination; unauthorized analytics

### TA-5: System Capture (Governance Attack)
**Motivation:** Seizing control of the system from VBTN; converting it to serve other interests
**Capability:** Variable — may involve legal, technical, or social engineering
**Likely Attack Path:** Replacing governance references in config; removing tribal jurisdiction claims; pressuring/coercing the System Steward; exploiting succession gap

### TA-6: Accidental / Negligent Insider
**Motivation:** None (unintentional)
**Capability:** Variable
**Likely Attack Path:** Misconfiguration; accidental data exposure; lost credentials; deploying untested code changes

---

## 3. Threat Scenarios and Mitigations

### T-01: Credential Theft via Phishing
| | |
|---|---|
| **Actor** | TA-1, TA-3 |
| **Impact** | High — full system access |
| **Likelihood** | Medium |
| **Mitigations** | MFA on all accounts; Azure Government OIDC (not password-based); key rotation schedule; steward training on phishing recognition |
| **Detection** | Auth failure alerts (safeguards.py); Azure AD sign-in logs |
| **Residual Risk** | Low-Medium |

---

### T-02: Bulk Data Exfiltration
| | |
|---|---|
| **Actor** | TA-1, TA-3, TA-4 |
| **Impact** | Critical — all member data exposed |
| **Likelihood** | Medium |
| **Mitigations** | Mass export rate limiting (safeguards.py); all-steward alerts; audit logging of all data access; data sovereignty contracts with vendors |
| **Detection** | Automated mass export alert; anomaly in access logs |
| **Residual Risk** | Low |

---

### T-03: Governance Tampering (Config/Jurisdiction Alteration)
| | |
|---|---|
| **Actor** | TA-3, TA-5 |
| **Impact** | Critical — removes tribal legal anchoring from system |
| **Likelihood** | Low |
| **Mitigations** | CODEOWNERS requirement on config.py; governance integrity check at startup; Critical Change protocol for config changes; version control history |
| **Detection** | Startup check failure; PR review process |
| **Residual Risk** | Low |

---

### T-04: Vendor Data Misuse
| | |
|---|---|
| **Actor** | TA-4 |
| **Impact** | High — member data used for prohibited purposes |
| **Likelihood** | Medium |
| **Mitigations** | Partner Ethical Agreement (legal/PARTNER_ETHICAL_AGREEMENT_TEMPLATE.md); Data Sovereignty Agreement; contractual audit rights; purpose limitation in contracts |
| **Detection** | Annual vendor review; contractual audit rights |
| **Residual Risk** | Medium (contractual mitigation only — technical enforcement limited) |

---

### T-05: Ransomware / Data Destruction
| | |
|---|---|
| **Actor** | TA-1, TA-3 |
| **Impact** | Critical — system unavailable; data lost |
| **Likelihood** | Low-Medium |
| **Mitigations** | Azure backup enabled; database export capability; container immutability; rollback capability in Azure revisions |
| **Detection** | Azure alerts; health check failures |
| **Residual Risk** | Low |

---

### T-06: Succession Gap Exploitation
| | |
|---|---|
| **Actor** | TA-5 |
| **Impact** | Critical — system captured during leadership transition |
| **Likelihood** | Low-Medium (higher if succession not prepared) |
| **Mitigations** | Governance Charter succession procedures; multi-steward requirement; Elder Council oversight; Stewardship Circle training |
| **Detection** | Stewardship Circle awareness; governance procedures |
| **Residual Risk** | Medium (until Tribal Technical Lead and Elder Council Seat positions are filled) |

---

### T-07: Compelled Government Disclosure
| | |
|---|---|
| **Actor** | TA-2 |
| **Impact** | High — member data disclosed to hostile authority |
| **Likelihood** | Low |
| **Mitigations** | Data sovereignty contracts requiring vendor to notify VBTN before disclosure; AzureUSGovernment (harder to reach); tribal jurisdiction assertion |
| **Detection** | Vendor notification (contractually required) |
| **Residual Risk** | Medium (legal risk, not primarily technical) |

---

## 4. Top Risks Requiring Immediate Action

| Priority | Risk | Action Required |
|---|---|---|
| 🔴 High | Succession gap (no Tribal Technical Lead or Elder Council Seat) | Designate these roles via Tribal Resolution immediately |
| 🔴 High | Steward alert emails incomplete in config.py | Add all steward emails when roles are filled |
| 🟡 Medium | Annual credential rotation not yet scheduled | Schedule and document quarterly/annual rotation |
| 🟡 Medium | Vendor ethical agreements not yet executed | Execute Partner Ethical Agreements with Azure and DocuSign |
| 🟢 Low | Lockdown resume procedure not tested | Schedule a drill within 90 days |

---

## 5. Threat Model Review Process

This threat model must be reviewed:
- **Annually** (minimum)
- After any significant system change
- After any security incident
- When a new vendor or integration is added
- When a new threat actor type is identified

Reviews must be documented with: date, reviewer(s), changes made, and any new threats identified.

---

*This document is version-controlled. All updates are recorded in the repository's commit history.*
