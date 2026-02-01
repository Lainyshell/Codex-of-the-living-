# Tribal Assessment and CISA Transmission System

## Overview

This system provides secure, encrypted transmission of tribal infrastructure assessment data to CISA (Cybersecurity and Infrastructure Security Agency) while maintaining tribal sovereignty and protecting tribal intellectual property.

## Key Features

### 1. **Assessment System** (`assessment_system.py`)
- Conducts security and infrastructure assessments
- Classifies findings by protection level
- Filters tribal sovereign information from shareable results
- Maintains internal records with full detail

### 2. **Data Tracking** (`tribal_data_tracker.py`)
- Tracks ALL data leaving the tribal secure network
- Creates comprehensive audit trails
- Validates transmission compliance
- Logs to persistent storage for accountability

### 3. **Secure Transmission** (`cisa_transmission.py`)
- Encrypts data using AES-256-GCM (FIPS 140-2 compliant)
- Calculates integrity hashes
- Simulates secure HTTPS transmission to CISA
- Provides transmission receipts and verification

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Quick Start

Run the complete assessment and transmission workflow:

```bash
python3 run_assessment.py
```

This will:
1. Initialize all systems
2. Run security and infrastructure assessments
3. Filter results to protect tribal IP
4. Create tracking records
5. Encrypt the data
6. Validate transmissions
7. Transmit to CISA (simulated)
8. Log all transmissions
9. Generate audit reports

### Individual Components

#### Run Assessment Only

```python
from assessment_system import AssessmentSystem, AssessmentType

system = AssessmentSystem()
assessment = system.run_security_assessment()
results = assessment.get_shareable_results()
```

#### Track Data Transmission

```python
from tribal_data_tracker import TribalDataTracker, DataClassification

tracker = TribalDataTracker()
record = tracker.create_transmission_record(
    data_type="assessment_results",
    destination="CISA",
    classification=DataClassification.SENSITIVE,
    data_size_bytes=1024
)
```

#### Encrypt and Transmit to CISA

```python
from cisa_transmission import SecureTransmitter

transmitter = SecureTransmitter()
package = transmitter.prepare_transmission_package(assessment_data)
result = transmitter.simulate_transmission(package)
```

## Security Features

### Encryption
- **Algorithm**: AES-256-GCM
- **Compliance**: FIPS 140-2
- **Key Length**: 256 bits
- **Mode**: Galois/Counter Mode (authenticated encryption)

### Data Protection Levels
1. **PUBLIC** - Can be freely shared
2. **SENSITIVE** - Shareable with federal partners
3. **CONFIDENTIAL** - Internal use only
4. **TRIBAL_SOVEREIGN** - Never leaves tribal network

### Audit Logging
- All transmissions logged with timestamps
- SHA-256 integrity hashes calculated
- Complete audit trail maintained
- JSONL format for easy parsing

## File Structure

```
.
├── assessment_system.py       # Assessment engine
├── tribal_data_tracker.py     # Data tracking and logging
├── cisa_transmission.py       # Secure transmission handler
├── run_assessment.py          # Main integration script
├── config.json                # Configuration settings
├── requirements.txt           # Python dependencies
├── logs/                      # Log directory (created automatically)
│   ├── tribal_data_transmission_log.jsonl
│   ├── transmission_*.json
│   ├── transmission_summary.json
│   └── complete_audit_log.json
└── README.md                  # This file
```

## Output Files

### Transmission Log
`logs/tribal_data_transmission_log.jsonl` - Main log file in JSON Lines format

### Individual Records
`logs/transmission_[record_id].json` - Detailed record for each transmission

### Audit Reports
- `logs/transmission_summary.json` - Summary statistics
- `logs/complete_audit_log.json` - Complete audit export

## Tribal Sovereignty Protection

This system is designed with tribal sovereignty at its core:

1. **Filtering**: Tribal sovereign and confidential data is automatically filtered before transmission
2. **Logging**: All data leaving the network is tracked and logged
3. **Encryption**: All transmissions use military-grade encryption
4. **Audit Trail**: Complete accountability for all data movements
5. **IP Protection**: Intellectual property remains within tribal control

## Compliance

- **FIPS 140-2**: Encryption standard compliance
- **Tribal Data Governance**: Respects tribal data sovereignty
- **Federal Partnership**: Enables secure collaboration with CISA
- **Audit Ready**: Complete logs for compliance review

## Federal Continuity Capacity

This system demonstrates:
- Scalable infrastructure
- Secure federal data sharing capabilities
- Professional audit and logging practices
- Encryption and security best practices
- Capacity for ongoing federal partnership

## Support

For questions or issues, contact:
- Tribal IT Department
- System Administrator: Postmaster General Alaina Padgett

## License

Proprietary - Verdigris Botanica Tribal Nation
All rights reserved under tribal sovereignty.
