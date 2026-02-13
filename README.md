# Codex of the Living - VBTN Repository

This repository contains operational documentation, agreements, and applications for the Verdigris Botanica Tribal Nation (VBTN), including a Flask application that fetches average interest rates from the Fiscal Data Treasury API.

## Source

Cloned from [OD2022/fiscal_treasury_api](https://github.com/OD2022/fiscal_treasury_api)

## Features

- **Status Endpoint**: Check API status at `/`
- **Rates Endpoint**: Fetch average interest rates from the U.S. Treasury Fiscal Data API at `/rates`

## API Details

The application connects to the official U.S. Treasury Fiscal Data API:
- API URL: `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates`

## Project Structure

```
.
├── app/
│   ├── main.py           # Flask application with API endpoints
│   ├── requirements.txt  # Python dependencies (uwsgi, flask, requests)
│   ├── Dockerfile        # Docker container configuration
│   └── .gitignore        # Python-specific gitignore rules
├── compose.yaml          # Docker Compose configuration
└── .github/
    └── workflows/
        └── deploy.yaml   # GitHub Actions deployment workflow
```

## Running Locally

### With Docker Compose

```bash
docker-compose up
```

The API will be available at `http://localhost:5000`

### With Python

```bash
cd app
pip install -r requirements.txt
python main.py
```

## API Endpoints

### GET /
Returns the status of the API.

**Response:**
```json
{
  "status": "ok"
}
```

### GET /rates
Fetches the latest average interest rates from the U.S. Treasury Fiscal Data API.

**Response:**
Returns the JSON response from the Treasury API containing average interest rate data.

## Deployment

The repository includes a GitHub Actions workflow (`.github/workflows/deploy.yaml`) that automatically deploys the application when changes are pushed to the `main` branch. The workflow uses the Defang deployment platform.

## Technologies

- **Python 3.11**: Runtime environment
- **Flask**: Web framework
- **uWSGI**: WSGI HTTP server
- **Docker**: Containerization
- **GitHub Actions**: CI/CD pipeline

---

## Cybersecurity and Compliance

### CISA M365 Security Updates

The repository includes documentation for CISA's latest Microsoft 365 security requirements:

- **[CISA M365 ScubaGear v1.7.0 Advisory](CISA_M365_ScubaGear_v1.7.0_Advisory.md)** - Comprehensive guide to BOD 25-01 compliance requirements
- **[M365 Security Compliance Quick Reference](M365_Security_Compliance_QuickRef.md)** - Quick reference guide for M365 security baseline implementation

These documents provide guidance on:
- ScubaGear v1.7.0 assessment tool requirements
- M365 Secure Configuration Baselines (SCBs)
- BOD 25-01 compliance for federal agencies
- Recommendations for tribal nation M365 security

**Key Updates in ScubaGear v1.7.0:**
- NIST 800-53 FedRAMP high mappings
- Defender UI updates
- Entra ID / AAD UI updates
- New SCuBA Configuration editor feature

For VBTN M365 environment security, refer to these documents for best practices and assessment tools.

---

## Repository Contents

This repository contains:
- Treasury API Flask application (in `/app`)
- Tribal governance documents and agreements
- M365 DNS configuration for VBTN services
- Cybersecurity compliance documentation
- Operational procedures and templates
