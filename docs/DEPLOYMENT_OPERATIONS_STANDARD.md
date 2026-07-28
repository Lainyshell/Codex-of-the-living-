# Deployment & Operations Standard — Treasury API

**Authority**: Alaina Padgett — alaina@verdigrisbotanicanation.org  
**Repository**: `Lainyshell/Codex-of-the-living-`  
**Last Updated**: July 2026

---

## 1. Single Production Deployment Path

This repository uses one active app deployment workflow:

- **Active workflow**: `.github/workflows/azure-container-webapp.yml` (`Release Treasury API`)
- **Deployment target**: Azure Web App container deployment
- **Container source**: `app/Dockerfile` built and pushed to GHCR

No secondary app deployment workflow should be active in parallel.

---

## 2. Release Pipeline Contract

The production release pipeline is:

1. **Build and publish container image**
2. **Deploy to `staging` environment**
3. **Run staging smoke checks** (`/` and `/rates`)
4. **Deploy to `production` environment**
5. **Run production smoke checks** (`/` and `/rates`)
6. **Rollback to previous image tag if production smoke checks fail**

### Required GitHub Environment Configuration

Configure these environments in repository settings:

- `staging`
- `production`

For controlled promotion, configure required reviewers on `production`.

### Required Variables and Secrets

Repository/Environment variables:
- `AZURE_KEY_VAULT_NAME`
- `AZURE_WEBAPP_NAME_STAGING` or `AZURE_WEBAPP_NAME_STAGING_SECRET_NAME`
- `AZURE_WEBAPP_NAME_PRODUCTION` or `AZURE_WEBAPP_NAME_PRODUCTION_SECRET_NAME`
- `AZURE_WEBAPP_DEFAULT_HOSTNAME_SUFFIX` (default `azurewebsites.us` for Azure Government)
- `PRODUCTION_BASE_URL` (used by observability workflow)

Environment secrets:
- `AZURE_CLIENT_ID`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

Optional fallback secrets:
- `AZURE_CREDENTIALS`
- `AZURE_WEBAPP_PUBLISH_PROFILE_STAGING`
- `AZURE_WEBAPP_PUBLISH_PROFILE_PRODUCTION`

Optional Azure Key Vault secret-name variables:
- `AZURE_WEBAPP_NAME_SECRET_NAME`
- `AZURE_WEBAPP_PUBLISH_PROFILE_STAGING_SECRET_NAME`
- `AZURE_WEBAPP_PUBLISH_PROFILE_PRODUCTION_SECRET_NAME`

Optional alert webhook secrets:
- `TEAMS_WEBHOOK_URL`
- `ALERT_EMAIL_WEBHOOK_URL`

---

## 3. Required Checks and Branch Governance

Set branch protection for `main` with:

- Pull request review required
- Required status checks:
  - `Document Hygiene & Compliance Check`
  - `Build and Publish Container`
  - `Deploy to Staging`
  - `Deploy to Production`
- Restrict direct pushes

This preserves HITL governance and ensures compliance + runtime checks gate releases.

---

## 4. End-to-End Visualization

Operational visibility is provided by:

- **Release workflow run graph** (`Release Treasury API`) for commit → build → deploy transitions
- **Operations observability workflow** (`.github/workflows/operations-observability.yml`) for:
  - Deployment success rate
  - Uptime signal
  - `/rates` dependency health and latency
  - Compliance lane status and approval state

The observability workflow publishes a dashboard summary to each run and uploads JSON artifacts for audit use.

---

## 5. Precision Monitoring and Alerting

`Operations Observability` enforces SLO-oriented checks:

- Uptime status (`/`)
- `/rates` dependency availability
- `/rates` response latency threshold
- Deployment success rate across recent runs
- Failed deployment-run count threshold

When a breach is detected, webhook alerts are sent to configured Teams/email endpoints.

Structured telemetry records include:
- commit SHA
- workflow run ID
- deployment/compliance outcome
- latency and probe state

---

## 6. Security and Data-Scope Guardrails

- Deployment image build context is `./app` only.
- Tribal governance documents in repository root are excluded from app container build.
- Azure Government deployments default to `AzureUSGovernment` and use GitHub OIDC (`id-token: write`) for Azure login.
- Secrets should live in Azure Key Vault, with GitHub environment secrets reserved for OIDC metadata and break-glass fallback credentials.
- Compliance workflow HITL controls remain active and unchanged.

---

## 7. Production Readiness Drill (Runbook)

Execute this drill before declaring production ready:

1. Merge a PR into `main`.
2. Verify the OIDC identity has federated credentials for the GitHub repository/environment pair and can read the deployment Key Vault.
3. Run a staging activation deployment and verify full release workflow success in order: build → staging → production.
4. Confirm smoke checks pass for `/` and `/rates`.
5. Confirm Operations Observability summary reflects healthy state.
6. Validate alert path by inducing a non-destructive synthetic failure in staging or via threshold override.
7. Validate rollback path by forcing a failed production smoke check and confirming previous image redeploy.
8. Archive run links and artifacts for audit traceability.

If all checks pass, this document is the frozen deployment standard for future releases.
