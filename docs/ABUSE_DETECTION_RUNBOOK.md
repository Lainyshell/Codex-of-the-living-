# Abuse Detection and Response Runbook

**System:** Codex of the Living — Verdigris Botanica Tribal Nation Infrastructure
**Version:** 1.0
**Effective Date:** 2026-08-06

---

## 1. Purpose

This runbook defines:
- What abuse patterns the system monitors
- What automated responses trigger on detection
- How stewards are alerted
- How to review, confirm, and respond to abuse events
- How to resume normal operations after a lockdown

The safeguards module (`app/safeguards.py`) implements the automated detection and response described here.

---

## 2. Monitored Abuse Patterns

### 2.1 Mass Export Attempt
**Definition:** A single user or session attempts to export, download, or query more than **500 records** or **50 MB** of member/financial data within any rolling 15-minute window.

**Rationale:** Legitimate operational use does not require bulk export at this scale in a short period. Mass export suggests data theft, unauthorized research, or preparation for data brokering.

**Automated Response:**
1. Request is blocked and returns HTTP 429 with error code `ABUSE_MASS_EXPORT`
2. All stewards are alerted immediately via email
3. The triggering session is flagged for review
4. Further bulk operations from that session require explicit steward approval

---

### 2.2 Unauthorized Bulk Delete
**Definition:** A single request or scripted sequence attempts to delete more than **100 records** outside a documented maintenance window.

**Rationale:** Bulk deletion is rare in normal operations. Unauthorized bulk deletion may indicate sabotage, cover-up of misconduct, or ransomware activity.

**Automated Response:**
1. Operation is blocked
2. All stewards are alerted immediately
3. A mandatory 24-hour hold is placed on bulk delete operations
4. Delete can proceed only after explicit approval by two stewards

---

### 2.3 Unauthorized Jurisdiction Change Attempt
**Definition:** Any configuration change attempt that would alter the `TRIBAL_GOVERNANCE` references, jurisdiction settings, or governance instrument identifiers in `app/config.py`.

**Rationale:** Altering governance references at the code level is an attempt to decouple the system from VBTN authority — a severe governance violation.

**Automated Response:**
1. Change is blocked at the application layer
2. All stewards are alerted with the specific change attempted
3. Incident is logged with full context (user, timestamp, payload)
4. Access for the attempting account is suspended pending review

---

### 2.4 Repeated Authentication Failure
**Definition:** More than **10 failed authentication attempts** from a single IP or account within 5 minutes.

**Rationale:** Indicates brute-force or credential stuffing attack.

**Automated Response:**
1. Account/IP is locked for 30 minutes
2. System Steward is alerted
3. After 3 lockout events in 24 hours, account requires manual steward unlock

---

### 2.5 Suspicious Query Pattern
**Definition:** Queries that systematically walk through member records (sequential ID enumeration), query fields associated with prohibited uses (behavioral, predictive), or access records outside the user's authorized scope.

**Rationale:** Indicates data harvesting or preparation for prohibited profiling.

**Automated Response:**
1. Session is flagged and rate-limited
2. System Steward is alerted
3. If pattern continues, session is terminated and account suspended

---

### 2.6 Privilege Escalation Attempt
**Definition:** A user attempts to access admin endpoints, modify role assignments, or execute operations outside their assigned permission level.

**Rationale:** Indicates attempted unauthorized access expansion.

**Automated Response:**
1. Attempt is blocked and logged
2. System Steward is alerted immediately
3. After 3 attempts, account is suspended pending review

---

## 3. Alert Routing

All abuse alerts are sent to **all three** of the following simultaneously. No single person is the sole recipient:

| Role | Contact | Alert Channel |
|---|---|---|
| System Steward | alaina@verdigrisbotanicanation.org | Email + system log |
| Tribal Technical Lead | [To be designated] | Email + system log |
| Elder Council Seat | [To be designated] | Email + system log |

Alert emails include:
- Abuse pattern type
- Timestamp and duration
- Affected account/session
- Data scope involved (if applicable)
- Automated action taken
- Link to relevant log entry

---

## 4. Lockdown Mode

**Lockdown Mode** activates when:
- Any two or more abuse patterns trigger within a 1-hour window, **or**
- A severity-1 event occurs (unauthorized jurisdiction change, mass delete, bulk export > 10,000 records), **or**
- A steward manually activates it via the admin panel

**In Lockdown Mode:**
- All write operations are suspended
- All bulk read operations are suspended
- Routine read operations for authenticated users continue
- All stewards are notified via email
- The system displays a maintenance notice to users

---

## 5. Resuming from Lockdown

Lockdown can only be lifted by explicit collective approval:

1. At least **two designated stewards** must independently confirm (via separate logins) that the threat has been assessed and resolved
2. Both stewards must document their assessment in the system log
3. If the trigger was a Critical Change type, a full post-incident review is required before resuming

**Commands are intentionally not listed here** — the resume procedure is documented in the secure runbook maintained by the System Steward and accessible to the Stewardship Circle.

---

## 6. Post-Incident Review

After every lockdown or severity-1 abuse event:

1. **Within 24 hours:** System Steward documents the incident timeline
2. **Within 72 hours:** Full stewardship body reviews the incident
3. **Within 7 days:** Post-incident report is added to `docs/CRITICAL_CHANGE_REGISTER.md`
4. **Within 30 days:** Any required safeguard improvements are implemented
5. **Annually:** All incidents from the past year are reviewed for pattern analysis

---

## 7. Testing

Safeguard mechanisms should be tested:
- **Monthly:** Automated test of alert routing (confirm emails are received)
- **Quarterly:** Simulated abuse pattern (with all stewards notified in advance)
- **Annually:** Full lockdown and resume drill

---

*Questions about this runbook should be directed to the System Steward. See `app/safeguards.py` for implementation details.*
