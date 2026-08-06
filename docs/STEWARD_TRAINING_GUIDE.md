# Steward Training Guide
## Codex of the Living — What Every Steward Must Know

**For:** All members of the Stewardship Circle
**Plain language. No jargon.**
**Date:** 2026-08-06

---

## Welcome

If you're reading this, you've been entrusted with helping protect something important: the Verdigris Botanica Tribal Nation's own infrastructure. This is the system that manages our finances, our documents, and our records.

You don't need to be a programmer to be a steward. You need to understand:
1. What this system does
2. What it must never do
3. How to recognize when something is wrong
4. What to do if something goes wrong

That's it. This guide covers all four.

---

## Part 1: What This System Does

### The Simple Version
The Codex of the Living is like the Nation's filing cabinet and ledger — but digital.

It stores and manages:
- **Financial records** — money that's come in, gone out, or is in process
- **Documents** — agreements, vouchers, REMIC instruments, tribal paperwork
- **Transactions** — a record of what happened, when, and to whom

It connects to a few external services:
- **Microsoft Azure** — the servers where it lives (think: the building that holds the filing cabinet)
- **DocuSign** — the service that handles electronic signatures on documents

### Who Runs It
The **System Steward** (currently Alaina Padgett) is responsible for day-to-day operations.

The **Tribal Technical Lead** and **Elder Council Seat** (positions to be filled) share authority over major decisions.

You, as a **Stewardship Circle member**, are part of the safety net. You're the people who know enough to notice if something is wrong — and who have the authority to say so.

---

## Part 2: What This System Must Never Do

This is the most important part of your training. Read it carefully.

### ❌ It must never score or rate members
The system cannot be used to create scores, ratings, or rankings of people. No "reliability scores." No "risk ratings." No sorting people by how likely they are to do something in the future.

**Why:** That's not what it's for, and that kind of scoring always harms the people being scored.

---

### ❌ It must never be used to surveil members
The system cannot track what people do, where they go, who they talk to, or how they behave — beyond what's necessary to process a transaction.

**Why:** Surveillance is a tool of control. This system belongs to the Nation — it must never be turned against the Nation's own members.

---

### ❌ It must never sell or share member data
No one — no company, no government agency, no researcher — gets access to member data without a Tribal Resolution explicitly authorizing it.

**Why:** Our data belongs to us. It is not a product.

---

### ❌ It must never be used to target or discriminate
No one's access to services, benefits, or treatment can be altered based on race, religion, membership status, or any other characteristic — through this system or because of this system.

---

### ❌ It must never be turned against the Nation
No vendor, government agency, or outside party can use this system as a tool against the Nation's members — legally, financially, or otherwise.

The full policy is in `docs/PROHIBITED_USES.md`. Read it.

---

## Part 3: How to Recognize Misuse

You don't need to understand the code to notice when something is wrong. Here are the warning signs:

### Red Flags in How People Talk About the System
- Someone asks to "add scoring" or "risk profiling" features
- A vendor or partner asks for "broader data access" beyond their specific service
- Someone suggests exporting all member data to a third party for "analysis"
- Someone talks about using the system to "monitor" members' behavior
- Anyone outside the stewardship body asks to control access to the system

### Red Flags in System Behavior
- You receive an alert email that you don't recognize
- The system seems slow or behaves strangely after a recent change
- Someone tells you the system has been "updated" but you weren't notified
- Governance documents have been changed (TRIBAL_GOVERNANCE.md, JURISDICTION.md, etc.)
- The steward alert email list has been shortened — especially to just one person

### Red Flags in Governance
- Someone is trying to change the governance structure without a Tribal Resolution
- A new vendor agreement is being signed without going through the stewardship body
- Someone is trying to rush a "Critical Change" without the required approvals
- The succession structure is being altered without Elder Council involvement

---

## Part 4: What To Do If Something Is Wrong

### Step 1: Don't act alone
This is a stewardship — decisions are made together. You don't have to fix it yourself.

### Step 2: Document what you observed
Write down:
- What you noticed
- When you noticed it
- Who was involved (if anyone)
- Any screenshots or messages you have

### Step 3: Alert the stewardship body
Contact:
- **System Steward:** alaina@verdigrisbotanicanation.org
- **Tribal Technical Lead:** [To be designated]
- **Elder Council Seat:** [To be designated]

If the System Steward is the person you're concerned about, go directly to the Elder Council Seat.

### Step 4: Do not delete or alter evidence
Even if something seems embarrassing or minor — preserve the record. It may matter later.

### Step 5: Wait for collective decision
The stewardship body will convene within 48 hours of a concern being raised. Major actions should wait for that review unless there's an active emergency (e.g., a breach in progress).

---

## Part 5: Your Role as a Steward

Being in the Stewardship Circle means:

- **You care about the Nation** — you're not just technically involved; you're invested in this system being used honorably
- **You pay attention** — you notice when things feel off, and you say something
- **You hold the line** — when someone tries to use this system in a way it wasn't meant to be used, you object
- **You share the load** — you make sure no single person (including the System Steward) bears the full weight of protecting this

You have authority. Use it.

---

## Part 6: Key Documents to Read

After completing this training, read the following (in order):

1. `docs/WHY_WE_BUILT_THIS.md` — the founding story; why this matters
2. `TRIBAL_GOVERNANCE.md` — what law governs this system
3. `JURISDICTION.md` — who has authority
4. `docs/PROHIBITED_USES.md` — the hard limits
5. `docs/GOVERNANCE_CHARTER.md` — the full governance structure
6. `docs/RUNBOOK.md` — how to keep the system running

---

## Acknowledgment

By serving in the Stewardship Circle, I acknowledge that I have read and understood this training guide, and I commit to:
- Upholding the principles of this system
- Reporting misuse when I see it
- Protecting the Nation's sovereignty over its own infrastructure

**Name:** ___________________________
**Date:** ___________________________
**Signature:** ___________________________

---

*This guide should be updated whenever the system or governance structure changes. Every new Stewardship Circle member should receive this training before their first steward action.*
