"""
app/config.py — Codex of the Living
Verdigris Botanica Tribal Nation (VBTN)

TRIBAL GOVERNANCE NOTICE
========================
This system is owned by and operates under the authority of the
Verdigris Botanica Tribal Nation (VBTN). Governing instruments:

  Governance Charter:        docs/GOVERNANCE_CHARTER.md
  Tribal Governance Decl.:   TRIBAL_GOVERNANCE.md
  Jurisdiction Statement:    JURISDICTION.md
  Data Sovereignty:          legal/DATA_SOVEREIGNTY_AGREEMENT.md
  IP Assignment:             legal/IP_ASSIGNMENT.md
  Non-Transferability:       legal/NON_TRANSFERABILITY_CLAUSE.md

GOVERNANCE_INSTRUMENTS_VERSION = "1.0"
GOVERNING_NATION = "Verdigris Botanica Tribal Nation"
GOVERNING_TRUST = "Verdigris Botanica Tribal Nation Trust"
PRIMARY_JURISDICTION = "VBTN Tribal Law"
FEDERAL_FRAMEWORKS = ["2 CFR 200", "FAR", "ISDEAA 25 U.S.C. § 5301"]

Any change to this block is a Critical Change per docs/CRITICAL_CHANGE_PROTOCOL.md
and requires multi-steward approval plus a Tribal Resolution.
"""

# ── TRIBAL GOVERNANCE REFERENCES ─────────────────────────────────────────────
# These constants identify the governing authority of this system.
# They must be present in any fork or derivative work.
# Changing them is a Critical Change — see docs/CRITICAL_CHANGE_PROTOCOL.md.
GOVERNANCE_INSTRUMENTS_VERSION = "1.0"
GOVERNING_NATION = "Verdigris Botanica Tribal Nation"
GOVERNING_TRUST = "Verdigris Botanica Tribal Nation Trust"
PRIMARY_JURISDICTION = "VBTN Tribal Law"
FEDERAL_FRAMEWORKS = ["2 CFR 200", "FAR", "ISDEAA 25 U.S.C. § 5301"]

# Governance document paths (relative to repo root)
GOVERNANCE_CHARTER = "docs/GOVERNANCE_CHARTER.md"
TRIBAL_GOVERNANCE_DECLARATION = "TRIBAL_GOVERNANCE.md"
JURISDICTION_STATEMENT = "JURISDICTION.md"
DATA_SOVEREIGNTY_AGREEMENT = "legal/DATA_SOVEREIGNTY_AGREEMENT.md"
CRITICAL_CHANGE_PROTOCOL = "docs/CRITICAL_CHANGE_PROTOCOL.md"


# ── PROHIBITED USES ───────────────────────────────────────────────────────────
# These uses are ABSOLUTELY PROHIBITED. They apply to all operators, vendors,
# contractors, and stewards — with no exceptions and no overrides.
#
# Full policy: docs/PROHIBITED_USES.md
# Vendor obligations: legal/PARTNER_ETHICAL_AGREEMENT_TEMPLATE.md
# Enforcement: app/safeguards.py
#
# These constants exist so that any developer reading this file
# immediately encounters these constraints.
PROHIBITED_USES = [
    "behavioral_scoring",         # No scoring or rating of individuals
    "predictive_profiling",       # No building predictive profiles of members
    "silent_data_brokering",      # No selling, sharing, or licensing member data
    "unauthorized_surveillance",  # No tracking beyond authorized operational need
    "discrimination_targeting",   # No adverse treatment based on protected characteristics
    "exploitation",               # No extraction of value from members for vendor benefit
    "anti_member_weaponization",  # System must never be used against the Nation's members
]

# This system may NEVER be used as:
#   - a behavioral scoring engine
#   - a predictive policing tool
#   - a silent data broker
#   - a surveillance infrastructure
# These prohibitions are embedded in governance, contracts, and code.
# See docs/PROHIBITED_USES.md for the full policy.


# ── ABUSE DETECTION THRESHOLDS ───────────────────────────────────────────────
# These thresholds govern safeguard triggers. Changing them is a Standard
# Decision requiring System Steward + Tribal Technical Lead approval.
# See docs/ABUSE_DETECTION_RUNBOOK.md for full policy.
ABUSE_MASS_EXPORT_RECORD_THRESHOLD = 500   # records per 15-minute window
ABUSE_MASS_EXPORT_SIZE_THRESHOLD_MB = 50   # megabytes per 15-minute window
ABUSE_BULK_DELETE_THRESHOLD = 100          # records in a single operation
ABUSE_AUTH_FAILURE_THRESHOLD = 10          # failures per 5-minute window
ABUSE_AUTH_LOCKOUT_MINUTES = 30            # lockout duration
ABUSE_LOCKOUT_ESCALATION_COUNT = 3         # lockouts before manual unlock required


# ── STEWARD ALERT CONTACTS ───────────────────────────────────────────────────
# All abuse alerts go to ALL stewards simultaneously — never just one person.
# Update these when stewardship roles are filled.
# Changing this list is a Critical Change.
STEWARD_ALERT_EMAILS = [
    "alaina@verdigrisbotanicanation.org",   # System Steward
    # "tribal-tech-lead@verdigrisbotanicanation.org",  # Add when designated
    # "elder-council@verdigrisbotanicanation.org",     # Add when designated
]
