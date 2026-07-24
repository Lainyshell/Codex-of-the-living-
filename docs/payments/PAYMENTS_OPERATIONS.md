# Payments Operations Guide — VBTN Scan-Based Payment System

**Authority**: Alaina Padgett — alaina@verdigrisbotanicanation.org  
**Component**: Scan-Based Payments (QR → Stripe → DocuSign → REMIC Ledger)  
**Last Updated**: July 2026

---

## Overview

This guide documents the scan-based payment system built into the VBTN Flask application. The system accepts QR-code scan payloads, calculates REMIC interest, creates a Stripe PaymentIntent, routes a DocuSign compliance envelope, and finalizes the transaction when DocuSign confirms completion.

```
QR Scan → POST /api/scan-payment
              │
              ├── Validate payload
              ├── Calculate REMIC interest (remic.py)
              ├── Create Stripe PaymentIntent
              ├── Route DocuSign envelope
              └── Return transaction_id + envelope_id

DocuSign Completion → POST /api/docusign-webhook
                           │
                           ├── Verify HMAC signature
                           ├── Confirm envelope-completed event
                           └── Mark transaction completed in ledger
```

---

## 1. Required Environment Variables

All credentials are read exclusively from environment variables. **Never commit secrets to the repository.**

| Variable | Required | Description |
|---|---|---|
| `STRIPE_API_KEY` | ✅ | Stripe secret key (`sk_live_...` or `sk_test_...`) |
| `DOCUSIGN_ACCOUNT_ID` | ✅ | DocuSign account UUID |
| `DOCUSIGN_BASE_URL` | ✅ | DocuSign REST API base URL, e.g. `https://na4.docusign.net/restapi` |
| `DOCUSIGN_ACCESS_TOKEN` | ✅ | DocuSign OAuth access token for API authentication |
| `DOCUSIGN_HMAC_KEY` | ✅ | DocuSign Connect shared HMAC secret for webhook verification |
| `DOCUSIGN_TEMPLATE_DEFAULT` | ✅ | Fallback DocuSign template UUID |
| `DOCUSIGN_TEMPLATE_GOV_OBLIGATION_A` | ⚠️ | Template UUID for government obligation, class A |
| `DOCUSIGN_TEMPLATE_GOV_OBLIGATION_B` | ⚠️ | Template UUID for government obligation, class B |
| `DOCUSIGN_TEMPLATE_GOV_OBLIGATION_IO` | ⚠️ | Template UUID for government obligation, IO class |
| `DOCUSIGN_TEMPLATE_ROYALTY_A` | ⚠️ | Template UUID for royalty, class A |
| `DOCUSIGN_TEMPLATE_ROYALTY_B` | ⚠️ | Template UUID for royalty, class B |
| `DOCUSIGN_RECIPIENT_COUNT` | ⚠️ | Total number of DocuSign recipients (default: 1) |
| `DOCUSIGN_RECIPIENT_1_NAME` | ⚠️ | Recipient 1 name (vendor — populated per request) |
| `DOCUSIGN_RECIPIENT_2_NAME` | ⚠️ | Recipient 2 name (tribal finance) |
| `DOCUSIGN_RECIPIENT_2_EMAIL` | ⚠️ | Recipient 2 email |
| `DOCUSIGN_RECIPIENT_2_ROLE` | ⚠️ | Recipient 2 role label |
| `DOCUSIGN_RECIPIENT_3_NAME` | ⚠️ | Recipient 3 name (compliance) |
| `DOCUSIGN_RECIPIENT_3_EMAIL` | ⚠️ | Recipient 3 email |
| `PAYMENTS_DB_PATH` | optional | Path for SQLite database (default: `/tmp/payments.db`) |

> ⚠️ = Conditionally required depending on your obligation types and routing configuration.

---

## 2. Endpoint Reference

### `POST /api/scan-payment`

Accepts a QR scan payload, calculates REMIC interest, creates Stripe + DocuSign records.

**Required fields:**

| Field | Type | Description |
|---|---|---|
| `vendor_id` | string | Unique vendor identifier from QR code |
| `vendor_name` | string | Vendor display name |
| `vendor_email` | string | Vendor email for DocuSign routing |
| `obligation_id` | string | Obligation identifier from QR code |
| `principal_amount` | number | Principal obligation amount (positive) |
| `rate_type` | string | `"gov_obligation"` or `"royalty"` |
| `remic_class` | string | `"A"`, `"B"`, `"IO"`, or `"PO"` |
| `pass_through_rate` | number | Annual pass-through rate (e.g. `0.06` for 6%) |
| `days` | integer | Accrual period in days (positive) |

**Optional fields:**

| Field | Type | When required |
|---|---|---|
| `notional` | number | Required when `remic_class = "IO"` |
| `io_rate` | number | Required when `remic_class = "IO"` |
| `gross_revenue` | number | Required when `rate_type = "royalty"` |
| `royalty_rate` | number | Required when `rate_type = "royalty"` |
| `idempotency_key` | string | Supply your own UUID for exactly-once submission |

**Responses:**

| Code | Meaning |
|---|---|
| 201 | Transaction created, Stripe PaymentIntent created, DocuSign envelope sent |
| 200 | Duplicate — idempotency key already processed |
| 400 | Missing or invalid JSON / missing fields |
| 409 | Idempotency key conflict (race condition) |
| 422 | REMIC calculation error (invalid values) |
| 502 | Stripe or DocuSign upstream failure |

**Example request:**
```json
{
  "vendor_id": "V-001",
  "vendor_name": "Example Vendor Inc.",
  "vendor_email": "ap@example.com",
  "obligation_id": "OBL-2026-0042",
  "principal_amount": 25000,
  "rate_type": "gov_obligation",
  "remic_class": "A",
  "pass_through_rate": 0.06,
  "days": 30
}
```

**Example 201 response:**
```json
{
  "status": "docusign_sent",
  "transaction_id": "550e8400-e29b-41d4-a716-446655440000",
  "stripe_payment_id": "pi_3NxxxxxxxABC",
  "envelope_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "principal": "25000.00",
  "interest": "125.00",
  "total": "25125.00"
}
```

---

### `POST /api/docusign-webhook`

Receives DocuSign Connect completion callbacks and finalizes the transaction.

**Authentication:** HMAC-SHA256 — the raw body is signed with `DOCUSIGN_HMAC_KEY`. The signature is sent by DocuSign in the `X-DocuSign-Signature-1` header.

**Behavior:**
- Non-completion events (`envelope-sent`, `envelope-delivered`, etc.) are accepted and logged with a 200 response; no state change occurs.
- `envelope-completed` events mark the transaction `completed` and record an audit event.
- Replayed completion webhooks are idempotent (returns `already_completed`).

---

## 3. REMIC Interest Formulas

All calculations use the 30/360 day-count convention with ROUND_HALF_UP to 2 decimal places.

| Class | Formula |
|---|---|
| A / B | `principal × pass_through_rate × days ÷ 360` |
| IO | `notional × io_rate × days ÷ 360` |
| PO | `interest = 0` (principal only) |
| Royalty variant | `royalty = gross_revenue × royalty_rate`, then `royalty × pass_through_rate × days ÷ 360` |

---

## 4. DocuSign Configuration

### Connect Setup

1. Log in to DocuSign Admin → **Connect** → New Integration.
2. Set **URL to Publish** to `https://<your-domain>/api/docusign-webhook`.
3. Enable **Include HMAC Signature** and copy the generated secret to `DOCUSIGN_HMAC_KEY`.
4. Under **Trigger Events**, enable: `Envelope Completed`, `Envelope Sent`, `Envelope Declined`.
5. Activate the Connect configuration.

### Template Setup

For each obligation type, create a DocuSign template with the following text tabs:

| Tab Label | Field |
|---|---|
| `principal` | Principal amount |
| `interest` | REMIC interest amount |
| `total` | Total payment |
| `remic_class` | REMIC class |
| `payment_id` | Stripe PaymentIntent ID |
| `vendor_id` | Vendor identifier |
| `obligation_id` | Obligation identifier |
| `transaction_id` | Internal transaction UUID |

Set `DOCUSIGN_TEMPLATE_<RATE_TYPE>_<REMIC_CLASS>` to the template UUID for each combination, e.g.:

```
DOCUSIGN_TEMPLATE_GOV_OBLIGATION_A=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DOCUSIGN_TEMPLATE_ROYALTY_B=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DOCUSIGN_TEMPLATE_DEFAULT=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### Routing Order

Recipients are configured via environment variables:

```
DOCUSIGN_RECIPIENT_COUNT=3
DOCUSIGN_RECIPIENT_2_NAME=VBTN Finance
DOCUSIGN_RECIPIENT_2_EMAIL=finance@verdigrisbotanicanation.org
DOCUSIGN_RECIPIENT_2_ROLE=TribalFinance
DOCUSIGN_RECIPIENT_3_NAME=Compliance Officer
DOCUSIGN_RECIPIENT_3_EMAIL=compliance@verdigrisbotanicanation.org
DOCUSIGN_RECIPIENT_3_ROLE=Compliance
```

Recipient 1 (Vendor) is always populated from the scan payload.

---

## 5. Database / Audit Trail

The system uses SQLite (`PAYMENTS_DB_PATH`, default `/tmp/payments.db`) with WAL mode for concurrency safety.

**For production:** Mount the database on a persistent volume (not `/tmp`) and back it up regularly. Set `PAYMENTS_DB_PATH` to a persistent path.

**Transaction statuses:**

| Status | Meaning |
|---|---|
| `pending` | Record created; REMIC calculated |
| `stripe_created` | Stripe PaymentIntent created |
| `docusign_sent` | DocuSign envelope routed |
| `completed` | Envelope signed; payment finalized |
| `failed` | Stripe or DocuSign error |

Every status transition appends an immutable row to `audit_events`.

---

## 6. Running Tests

```bash
cd app
pip install -r requirements.txt
python -m unittest test_payments -v
```

37 tests covering:
- REMIC formula correctness (all classes, royalty variant, edge cases, rounding)
- DB layer (create, dedupe, status update, audit trail)
- API endpoints (success paths, all error conditions, idempotency, webhook verification)

---

## 7. Go-Live Checklist

- [ ] Set `STRIPE_API_KEY` to live key (`sk_live_...`) in GitHub Environment Secrets
- [ ] Set `DOCUSIGN_ACCOUNT_ID`, `DOCUSIGN_BASE_URL`, `DOCUSIGN_ACCESS_TOKEN` in secrets
- [ ] Set `DOCUSIGN_HMAC_KEY` to the Connect HMAC secret
- [ ] Configure at least `DOCUSIGN_TEMPLATE_DEFAULT`
- [ ] Configure routing recipients (`DOCUSIGN_RECIPIENT_COUNT`, names/emails)
- [ ] Set `PAYMENTS_DB_PATH` to a persistent volume path
- [ ] Configure DocuSign Connect to POST to `https://<domain>/api/docusign-webhook`
- [ ] Run tests: `cd app && python -m unittest test_payments -v` — all 37 must pass
- [ ] Deploy via `azure-container-webapp.yml` workflow (staging → smoke test → production)
- [ ] Verify `/` returns `{"status": "ok"}` in production
- [ ] Send one test payment through staging with `sk_test_...` key before switching to live key
- [ ] Confirm DocuSign webhook receives and processes a test completion event

---

*Document Authority: Alaina Padgett — alaina@verdigrisbotanicanation.org*  
*Verdigris Botanica Tribal Nation Trust*
