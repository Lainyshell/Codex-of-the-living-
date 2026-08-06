# Critical Change Protocol

**System:** Codex of the Living — Verdigris Botanica Tribal Nation Infrastructure
**Version:** 1.0
**Effective Date:** 2026-08-06

---

## 1. What Is a Critical Change?

A **Critical Change** is any modification to the system that:
- Could alter tribal legal authority or data sovereignty
- Could expose member data to unauthorized parties
- Could disable governance or safety controls
- Is irreversible or difficult to reverse
- Affects who has access to the system

See [`docs/GOVERNANCE_CHARTER.md`](GOVERNANCE_CHARTER.md) Section 4 for the complete list.

---

## 2. Who Must Approve Critical Changes

Every Critical Change requires **all three** of the following:

1. ✅ **System Steward** (`@Lainyshell` or designated successor)
2. ✅ **Tribal Technical Lead** (when designated)
3. ✅ **Elder Council Seat** (when designated)

Until positions 2 and 3 are formally filled, Critical Changes require:
- System Steward approval, **plus**
- Written acknowledgment from at least one Stewardship Circle member, **plus**
- Documentation that the change was made in the absence of a full stewardship body

---

## 3. Required Documentation for Critical Changes

Every Critical Change pull request must include:

### 3a. Change Description
- What is changing and why
- What will be different after the change
- What the impact is if the change fails

### 3b. Tribal Resolution Reference (if required)
Changes affecting: jurisdiction, governance instruments, system shutdowns, bulk data exports, vendor/cloud changes, or data sovereignty settings **must** include:
- Reference number of the Tribal Resolution authorizing the change
- Date of resolution adoption
- Attached copy of the signed resolution (as a PR attachment or linked document)

### 3c. Rollback Plan
- Step-by-step instructions to reverse the change if needed
- Estimated rollback time
- Who is responsible for executing the rollback

### 3d. Steward Sign-offs
Each approving steward must:
- Add a GitHub PR review "Approved"
- Leave a comment in the format:

```
STEWARD APPROVAL
Role: [System Steward / Tribal Technical Lead / Elder Council Seat]
Name: [Full Name]
Date: [YYYY-MM-DD]
Tribal Resolution Ref: [Ref number or "Not required for this change"]
```

---

## 4. The Critical Change Workflow

```
1. Developer opens a PR and marks it with the label: critical-change
2. System Steward reviews and confirms the change is correctly classified
3. All three stewards are requested as reviewers
4. 48-hour minimum review period (no exceptions except declared emergencies)
5. Tribal Resolution attached if required (see Section 3b)
6. All three stewards approve
7. Merge is performed by System Steward only
8. Change is logged in the Critical Change Register (see Section 5)
```

---

## 5. Critical Change Register

All Critical Changes must be logged after merge. Maintain this register in the repository at `docs/CRITICAL_CHANGE_REGISTER.md` with entries in the following format:

```markdown
## [YYYY-MM-DD] — [Brief Description]

- **PR:** #[number]
- **Change Type:** [schema / IAM / jurisdiction / vendor / shutdown / other]
- **Steward Approvals:** System Steward ✅ | Tribal Technical Lead ✅ | Elder Council ✅
- **Tribal Resolution:** [Ref number or "Not required"]
- **Summary:** [One paragraph describing what changed and why]
```

---

## 6. Emergency Changes

In a genuine security emergency (active breach, data exposure, critical vulnerability):

1. The System Steward may act immediately to protect the system
2. The emergency action must be documented within 24 hours
3. All stewards must be notified within 1 hour of the action
4. A retroactive review must occur within 72 hours
5. Emergency actions that constitute Critical Changes must be ratified by the full stewardship body within 7 days

---

## 7. Enforcement

Any pull request touching a Critical Change path that is merged without following this protocol is:
- A violation of the VBTN Governance Charter
- Subject to mandatory rollback and review
- To be reported to the Elder Council Seat

The `CODEOWNERS` file enforces that designated stewards are required reviewers for all critical file paths.

---

*Questions about this protocol should be directed to the System Steward. Questions about whether a change is "critical" should default to: if in doubt, treat it as critical.*
