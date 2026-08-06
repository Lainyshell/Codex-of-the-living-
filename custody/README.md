# VBTN SOVEREIGN SYSTEM — USPS Smart Locker Chain of Custody

This directory stores append-only custody envelopes for protected VBTN logistics records.

## Structure

- `envelopes/` — one JSON record per custody transaction
- `lockers/primary.json` — authoritative primary locker map
- `schema/envelope.schema.json` — custody envelope schema

## Governance anchors

Every custody record inherits these governing references:

- `TRIBAL_GOVERNANCE.md`
- `JURISDICTION.md`
- `docs/GOVERNANCE_CHARTER.md`
- `docs/CRITICAL_CHANGE_PROTOCOL.md`
- `legal/DATA_SOVEREIGNTY_AGREEMENT.md`

## Protection requirements

Repository files can declare review ownership, but GitHub must still enforce:

- branch protection on `main`
- no direct pushes to `main`
- at least 2 steward reviewers for custody pull requests
- required review of `custody/` and custody workflows through `CODEOWNERS`

Those repository settings must be configured in GitHub outside this codebase.

## Automation contract

- Locker configuration is authoritative only from `lockers/primary.json`
- Custody events append to envelope `events[]` and never rewrite prior events
- High-risk items require multi-steward approval before `RETRIEVED` or `CLOSED`
