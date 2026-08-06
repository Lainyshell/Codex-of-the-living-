# Prohibited Uses Policy

**System:** Codex of the Living — Verdigris Botanica Tribal Nation Infrastructure
**Version:** 1.0
**Effective Date:** 2026-08-06
**Governing Authority:** Verdigris Botanica Tribal Nation

---

## Statement of Purpose

The Codex of the Living was built to serve the Verdigris Botanica Tribal Nation and its members — to support their sovereignty, financial dignity, and governance. It must never be turned against them.

This document defines uses that are **absolutely prohibited** — by anyone, for any reason, under any circumstances, without exception. These prohibitions apply to the System Steward, all stewards, all contractors, all vendors, and all partners.

These prohibitions are:
- Hard-coded in `app/config.py`
- Required in all vendor agreements (see `legal/PARTNER_ETHICAL_AGREEMENT_TEMPLATE.md`)
- Enforced by the safeguards module (`app/safeguards.py`)
- Protected by governance requirements (see `docs/GOVERNANCE_CHARTER.md`)

---

## Absolute Prohibitions

### 1. Behavioral Scoring

**PROHIBITED:** Using this system to create, maintain, or contribute to any score, rating, ranking, or assessment of individual behavior, predicted behavior, risk, or trustworthiness.

This includes but is not limited to:
- Credit scores derived from non-financial behavioral data
- "Reliability" scores for members
- Engagement scores or "participation ratings"
- Any algorithmic ranking of individuals based on their conduct

**Why:** Behavioral scoring systems inevitably encode bias, create second-class categories, and undermine the dignity and equality of every person in the Nation.

---

### 2. Predictive Profiling

**PROHIBITED:** Using this system to build predictive profiles of individuals — including inferring future behavior, needs, vulnerabilities, or risks from historical data.

This includes:
- Predicting who is likely to default, commit violations, or leave the Nation
- Building demographic or behavioral "profiles" for targeting
- Feeding member data into external machine learning or AI systems for profiling purposes

**Why:** Predictive profiling is a form of pre-crime judgment. It removes agency from individuals and treats people as probabilities, not persons.

---

### 3. Silent Data Brokering

**PROHIBITED:** Sharing, selling, licensing, or allowing access to VBTN member data by any third party without:
- Explicit Tribal Resolution authorizing the specific disclosure
- Notification to affected members where legally required
- Data sovereignty protections in place

This includes:
- API access granted to data analytics companies
- Embedding member data in any external platform beyond what is strictly necessary for authorized functions
- Allowing vendor "anonymized analytics" that could re-identify members

**Why:** Data brokering — even "anonymized" — is a form of extraction. VBTN data belongs to VBTN and its members. It is not a commodity.

---

### 4. Unauthorized Surveillance

**PROHIBITED:** Monitoring, tracking, or logging member activities beyond what is necessary for authorized system functions, or making such monitoring available to external parties.

This includes:
- Logging member location data
- Tracking patterns of system use to infer personal circumstances
- Providing access to logs or activity data to law enforcement or government agencies without valid legal process and notice to VBTN
- Building monitoring dashboards that expose individual member behavior

**Why:** Surveillance is a tool of control. This system must not become a surveillance infrastructure aimed at the Nation's own members.

---

### 5. Discrimination and Targeting

**PROHIBITED:** Using this system or its data to treat any individual differently based on protected characteristics, or to enable any external party to do so.

This includes:
- Differential access to services based on race, tribal membership, religion, or national origin
- Providing data to parties known to engage in discriminatory practices
- Enabling targeting for adverse treatment in housing, employment, credit, or public accommodation

---

### 6. Exploitation

**PROHIBITED:** Structuring system features or data access in ways designed to extract value from VBTN members for the benefit of any vendor, partner, or individual.

This includes:
- Designing features to maximize data collection beyond operational need
- Creating data dependencies that transfer leverage to vendors
- Allowing vendor contracts that give vendors ongoing rights to member data after termination

---

## Consequences of Violation

Any person or entity that violates these prohibitions:

1. Has committed a material breach of their agreement with VBTN
2. Loses all access to the system immediately upon discovery
3. Must return and delete all VBTN data
4. Is subject to legal action under tribal law and applicable federal law
5. Will be reported to the Elder Council and the full stewardship body

---

## Reporting Prohibited Use

If you observe or suspect a prohibited use:

1. **Do not delete or alter any evidence**
2. Immediately notify the System Steward and at least one other steward
3. Document what you observed and when
4. The stewardship body will convene within 48 hours to assess

If the System Steward is the suspected violator, notify the Elder Council Seat directly.

---

## References

- Anti-weaponization code: `app/safeguards.py`
- Governance code references: `app/config.py` (PROHIBITED_USES block)
- Vendor contracts: `legal/PARTNER_ETHICAL_AGREEMENT_TEMPLATE.md`
- Abuse detection: `docs/ABUSE_DETECTION_RUNBOOK.md`
- Governance charter: `docs/GOVERNANCE_CHARTER.md`

---

*This policy may not be amended without a Tribal Resolution and approval by the full stewardship body.*
