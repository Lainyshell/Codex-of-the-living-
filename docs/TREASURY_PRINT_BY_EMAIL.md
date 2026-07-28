# Verdigris Botanica Tribal Nation Treasury
## Print‑By‑Email Orchestration Contract (Provisional)

This contract defines how the Treasury system handles membership payments,
DocuSign envelope completion, and document generation when printers do not yet
have static IPs. All secure and vendor-facing documents are delivered via email
to the Treasury operator (Alaina) for manual printing.

---

## 1. Trigger Conditions

The print-by-email workflow activates only when:

1. A DocuSign envelope reaches `completed` status.
2. The associated payment is verified as `paid` or `cleared`.
3. The Treasury API successfully validates:
   - DocuSign HMAC signature
   - Envelope status
   - Payment status
   - Ledger write to Cosmos DB

If any validation fails, **no email is sent**.

---

## 2. Document Outputs

Upon successful validation, the Treasury API generates two documents:

### 2.1 Internal Secure Document (MICR-equivalent payload)
Contains:
- Membership ID  
- Envelope ID  
- Payment ID  
- Internal ledger ID  
- Amount  
- Timestamp  
- Hidden security markers (hashes, internal codes)

Purpose:
- Internal treasury record  
- Audit trail  
- Future MICR printing once printers have static IPs

Delivery:
- Sent as a PDF attachment to Alaina's Treasury inbox.

### 2.2 Vendor-Facing Receipt
Contains:
- Vendor name  
- Amount paid  
- Date/time  
- PO or order number  
- Membership/program reference  
- Last 4 of payment instrument  
- Treasury contact information  

Purpose:
- Vendor documentation  
- Proof of payment  
- Procurement support

Delivery:
- Sent as a PDF attachment to Alaina's Treasury inbox.

---

## 3. Email Delivery Rules

### 3.1 Recipient
All documents are emailed to:

**Alaina Padgett — Treasury Operations**  
`alaina@vbtprintlab.org`  
`alaina@verdigrisbotanicanation.org`

### 3.2 Subject Format

```
[TREASURY] <MembershipID> | <EnvelopeID> | <PaymentID> | <Timestamp>
```

### 3.3 Attachments
- `internal_secure_<ledgerID>.pdf`
- `vendor_receipt_<paymentID>.pdf`

### 3.4 Body Template

```
Treasury Document Delivery — Verdigris Botanica Tribal Nation

Membership ID:  <membership_id>
Envelope ID:    <envelope_id>
Payment ID:     <payment_id>
Ledger ID:      <ledger_id>
Amount:         <amount>
Generated At:   <timestamp>

Attachments:
  1. Internal Secure Document (internal_secure_<ledgerID>.pdf)
  2. Vendor Receipt (vendor_receipt_<paymentID>.pdf)

This message was generated automatically by the Treasury API.
Do not reply to this message.
```

---

## 4. Ledger Requirements

Before email is sent, the Treasury API must write:

- `payment_id`
- `envelope_id`
- `membership_id`
- `ledger_id`
- `internal_doc_generated_at`
- `vendor_doc_generated_at`
- `email_sent_at`

If ledger write fails, **email is not sent**.

---

## 5. Future Activation: Printer Orchestration

Once printers have static IPs:

- MICR printer receives secure document automatically.
- Standard printer receives vendor receipt automatically.
- Email fallback becomes optional.

This contract remains valid until printer IPs are registered in Key Vault.

---

## 6. Governance

1. No document may be emailed without verified payment and completed envelope.
2. No vendor receipt may be generated without an internal secure document.
3. All events must be logged in Cosmos DB.
4. Staging must validate email delivery before production activation.
