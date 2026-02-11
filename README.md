# Treasury API

This is a Flask application that fetches average interest rates from the Fiscal Data Treasury API.

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

### Quick Start with Run Script

The easiest way to run the application:

```bash
./run.sh
```

This script will:
- Check dependencies and install them if needed
- Start the Flask application on port 5000
- Display available endpoints

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
