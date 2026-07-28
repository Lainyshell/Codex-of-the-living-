# Verdigris Botanica Tribal Nation Treasury
## Activation Guide (Provisional)

This guide defines the steps required to activate the Treasury system in staging
and production.

---

## 1. Pre‑Activation Checklist

### Azure Government
- OIDC federated credentials configured
- Web App deployed via GitHub Actions
- Key Vault reachable (FORTPADGETT)
- Cosmos DB reachable

### DocuSign
- JWT Grant configured
- Connect webhook configured
- HMAC key stored in Key Vault

### Stripe (optional)
- API keys stored in Key Vault

### GitHub
- All environment secrets populated
- azure-container-webapp.yml hardened and validated

---

## 2. Activation Steps (Staging)

1. Trigger **Release Treasury API → staging**.
2. Confirm:
   - Azure login (OIDC) succeeds
   - App deploys to AzureUSGovernment
   - Smoke test passes
   - DocuSign webhook reaches staging endpoint
   - Payment verification logic runs
   - Email delivery works
   - Ledger writes succeed

3. Review staging email outputs:
   - Internal secure PDF
   - Vendor receipt PDF

4. Approve staging activation.

---

## 3. Activation Steps (Production)

1. Trigger **Release Treasury API → production**.
2. Confirm:
   - Azure login (OIDC) succeeds
   - Production app deploys
   - Smoke test passes
   - DocuSign Connect points to production endpoint
   - Payment verification logic runs
   - Email delivery works
   - Ledger writes succeed

3. Review production email outputs.

4. Approve production activation.

---

## 4. Post‑Activation

- Monitor webhook logs
- Monitor Cosmos DB ledger entries
- Validate email delivery
- Prepare printer IP onboarding
