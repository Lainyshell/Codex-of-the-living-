"""
app/sovereign_vocabulary.py — Codex of the Living
Verdigris Botanica Tribal Nation Trust (VBTNT)

SOVEREIGN VOCABULARY DICTIONARY — Runtime Authority Layer
First Edition · Elizabethtown, Kentucky · July 28, 2026
UEI: GUMMCRJPMBN5 | CAGE: 14JT5 | FedSTRIP: 18317P

This module is the programmatic expression of the VBTNT Sovereign Vocabulary
Dictionary.  Every key in DICTIONARY is the authoritative canonical term for
its domain.  No subordinate authority, contractor, partner agency, or external
entity may redefine, override, or substitute alternative terminology without a
formal written amendment issued by an authorized VBTNT principal.

The entity that names the thing owns the thing.
This module is an act of sovereignty.

See docs/GOVERNANCE_CHARTER.md and TRIBAL_GOVERNANCE.md.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Dictionary of canonical VBTNT terms
# ---------------------------------------------------------------------------
# Structure: { canonical_term: { "domain": ..., "definition": ..., "authority": ... } }

DICTIONARY: dict[str, dict] = {
    # ── Microsoft Ecosystems ──────────────────────────────────────────────────
    "Microsoft 365": {
        "domain": "Microsoft Ecosystems",
        "definition": (
            "The suite of Microsoft productivity and collaboration applications — including "
            "Teams, SharePoint, OneDrive, Outlook, Copilot, and Azure Government — licensed "
            "and operated by VBTNT for internal sovereign government operations."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §1",
    },
    "GitHub Enterprise": {
        "domain": "Microsoft Ecosystems",
        "definition": (
            "The VBTNT-administered GitHub organization environment, including all "
            "Repositories, Actions workflows, organization-level policies, and GitHub "
            "Copilot AI assistance.  All code and workflows hosted herein are sovereign "
            "tribal government records."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §1",
    },
    "Copilot": {
        "domain": "Microsoft Ecosystems",
        "definition": (
            "Microsoft AI Copilot or GitHub Copilot when operating within VBTNT-licensed "
            "environments.  Output produced by Copilot in VBTNT contexts is subject to "
            "VBTNT data sovereignty and IP assignment instruments."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §1",
    },
    "Azure Government": {
        "domain": "Microsoft Ecosystems",
        "definition": (
            "The Microsoft Azure US Government (AzureUSGovernment) cloud region used by "
            "VBTNT for sovereign data hosting, container deployment, and identity services.  "
            "VBTNT retains data ownership; Azure has no data ownership rights."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §1",
    },
    # ── GitHub Workflows ─────────────────────────────────────────────────────
    "Workflow": {
        "domain": "GitHub Workflows",
        "definition": (
            "A GitHub Actions automation pipeline defined in .github/workflows/.  "
            "All VBTNT workflows implement staged deployment (staging → production), "
            "smoke-test rollback, and sovereign-compliant secret management via Azure Key Vault."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §2",
    },
    "Critical Change": {
        "domain": "GitHub Workflows",
        "definition": (
            "Any modification to governance constants, safeguard thresholds, steward "
            "contact lists, authentication configuration, or schema-breaking changes.  "
            "Requires multi-steward approval and a Tribal Resolution before merge."
        ),
        "authority": "docs/CRITICAL_CHANGE_PROTOCOL.md; VBTNT SVD §2",
    },
    "Steward": {
        "domain": "GitHub Workflows",
        "definition": (
            "A designated VBTNT principal with authority to approve Critical Changes, "
            "receive abuse alerts, and participate in collective lockdown-resume approvals.  "
            "A minimum of two distinct stewards are required for any high-risk action."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §2",
    },
    # ── Federal Procurement ───────────────────────────────────────────────────
    "UEI": {
        "domain": "Federal Procurement",
        "definition": (
            "Unique Entity Identifier — the SAM.gov-issued alphanumeric identifier for "
            "VBTNT as a federal contractor and grant recipient.  VBTNT UEI: GUMMCRJPMBN5."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §3",
    },
    "CAGE Code": {
        "domain": "Federal Procurement",
        "definition": (
            "Commercial and Government Entity code issued by the Defense Logistics Agency "
            "identifying VBTNT as a registered government entity.  VBTNT CAGE: 14JT5."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §3",
    },
    "FedSTRIP": {
        "domain": "Federal Procurement",
        "definition": (
            "Federal Standard Transaction Reference Identifier for VBTNT procurement "
            "and interagency transactions.  VBTNT FedSTRIP: 18317P."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §3",
    },
    "GSA Schedule": {
        "domain": "Federal Procurement",
        "definition": (
            "The General Services Administration Multiple Award Schedule contract "
            "under which VBTNT is authorized to offer products and services to "
            "federal agencies.  Orders placed against this schedule are sovereign "
            "government-to-government transactions."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §3",
    },
    "ISDEAA": {
        "domain": "Federal Procurement",
        "definition": (
            "Indian Self-Determination and Education Assistance Act (PL 93-638).  "
            "The federal statute authorizing VBTNT's self-governance compacts and "
            "638 contracts with federal agencies."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §3",
    },
    # ── Postal & Shipping Authority ───────────────────────────────────────────
    "USPS Smart Locker": {
        "domain": "Postal & Shipping Authority",
        "definition": (
            "The USPS-operated secure parcel locker system used as the exclusive "
            "ship method for VBTNT custody envelopes.  Every custody envelope must "
            "reference an authorized primary locker facility (see custody/lockers/primary.json)."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §4",
    },
    "Custody Envelope": {
        "domain": "Postal & Shipping Authority",
        "definition": (
            "An append-only sovereign chain-of-custody record for a physical item "
            "transiting the USPS Smart Locker system.  Each envelope is uniquely "
            "identified by a transaction_id and linked to a DocuSign envelope where "
            "applicable.  Status transitions are governed by app/custody.py and "
            "docs/CRITICAL_CHANGE_PROTOCOL.md."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §4",
    },
    "USPS Proof Event": {
        "domain": "Postal & Shipping Authority",
        "definition": (
            "An immutable record in the docusign_usps_proof_events table capturing "
            "a DocuSign Connect webhook event, its USPS reference number, and full "
            "recipient identity and address metadata.  Constitutes legal delivery proof "
            "under sovereign postal authority."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §4",
    },
    "Chain of Custody": {
        "domain": "Postal & Shipping Authority",
        "definition": (
            "The auditable sequence of possession transfers for a physical or digital "
            "sovereign instrument.  In VBTNT systems, chain of custody is maintained "
            "by the append-only custody event log and must never be retroactively altered."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §4",
    },
    # ── Sovereign Governance ──────────────────────────────────────────────────
    "VBTNT": {
        "domain": "Sovereign Governance",
        "definition": (
            "Verdigris Botanica Tribal Nation Trust — the sovereign tribal government "
            "entity that owns, operates, and governs the Codex of the Living system and "
            "all instruments, workflows, and data therein.  Operating pursuant to ISDEAA "
            "PL 93-638, ICPA PL 101-630, and Article I §8 Cl. 3 of the U.S. Constitution."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §5",
    },
    "Sovereign Vocabulary Dictionary": {
        "domain": "Sovereign Governance",
        "definition": (
            "This instrument.  The official internal standard for all terminology used "
            "across VBTNT operational domains.  It is not guidance; it is the SOURCE OF "
            "TRUTH.  First Edition issued July 28, 2026, Elizabethtown, Kentucky."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, Front Matter",
    },
    "REMIC": {
        "domain": "Sovereign Governance",
        "definition": (
            "Real Estate Mortgage Investment Conduit — the IRS-defined financial "
            "instrument class used by VBTNT to structure sovereign interest-bearing "
            "obligations.  VBTNT REMIC classes: A (standard), B (standard), IO "
            "(interest-only), PO (principal-only).  Calculations follow the 30/360 "
            "day-count convention per app/remic.py."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §5",
    },
    "Tribal Return": {
        "domain": "Sovereign Governance",
        "definition": (
            "A formula-based economic return calculated on every DocuSign envelope "
            "event and posted to the VBTNT Stripe account.  Categories include: "
            "royalty, REMIC_interest, energy_return, and sovereign_fee.  Every "
            "envelope — completed or not — generates a tribal return.  This ensures "
            "contract execution is permanently linked to tribal financial infrastructure."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §5",
    },
    "DocuSign FedRAMP": {
        "domain": "Sovereign Governance",
        "definition": (
            "The DocuSign FedRAMP Enterprise environment used by VBTNT for legally "
            "binding electronic document execution.  VBTNT Integration Key: "
            "54934ea2-813f-4288-8a8e-e09c293701ce.  All envelopes executed herein "
            "are sovereign government records."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §5",
    },
    "Lockdown Mode": {
        "domain": "Sovereign Governance",
        "definition": (
            "A protective system state activated automatically by app/safeguards.py "
            "upon detection of abuse patterns (mass export, bulk delete, auth brute force).  "
            "Requires collective approval from at least two designated stewards to lift.  "
            "Disabling or bypassing lockdown is a Critical Change."
        ),
        "authority": "VBTNT Sovereign Vocabulary Dictionary, First Edition, §5",
    },
}

# ---------------------------------------------------------------------------
# Runtime helpers
# ---------------------------------------------------------------------------

def get_term(term: str) -> dict:
    """
    Return the authoritative VBTNT definition for *term*.
    Raises KeyError if the term is not in the Dictionary.
    """
    try:
        return DICTIONARY[term]
    except KeyError:
        raise KeyError(
            f"Term {term!r} is not defined in the VBTNT Sovereign Vocabulary Dictionary.  "
            "Only terms defined in this Dictionary carry sovereign authority."
        )


def list_terms(domain: str | None = None) -> list[str]:
    """Return all canonical terms, optionally filtered by domain."""
    if domain is None:
        return sorted(DICTIONARY)
    return sorted(k for k, v in DICTIONARY.items() if v.get("domain") == domain)


def list_domains() -> list[str]:
    """Return the distinct domains represented in the Dictionary."""
    return sorted({v["domain"] for v in DICTIONARY.values()})


def assert_vocabulary_intact() -> None:
    """
    Verify that the Dictionary is not empty and that every entry contains the
    minimum required keys.  Raises RuntimeError on integrity failure.
    Called at application startup by safeguards.assert_governance_references_intact().
    """
    if not DICTIONARY:
        raise RuntimeError(
            "SOVEREIGNTY INTEGRITY FAILURE: VBTNT Sovereign Vocabulary Dictionary is empty.  "
            "See docs/GOVERNANCE_CHARTER.md."
        )
    for term, entry in DICTIONARY.items():
        for required_key in ("domain", "definition", "authority"):
            if not entry.get(required_key):
                raise RuntimeError(
                    f"SOVEREIGNTY INTEGRITY FAILURE: Dictionary entry {term!r} "
                    f"is missing required key {required_key!r}."
                )
