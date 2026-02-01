# QUICKSTART GUIDE

## Tribal Assessment and CISA Transmission System

This guide will get you started in 5 minutes.

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Verify installation
python3 -c "import cryptography; print('✓ Dependencies installed')"
```

### Quick Start

#### Option 1: Run Complete Assessment (Recommended)

This runs a full assessment, encrypts results, tracks transmission, and logs everything:

```bash
python3 run_assessment.py
```

**Output includes:**
- Security assessment results
- Infrastructure assessment results
- Encryption confirmation (AES-256-GCM)
- Transmission tracking
- Audit logging
- Magnitude summary

#### Option 2: Run Tests

Validate that all components work correctly:

```bash
python3 test_system.py
```

#### Option 3: View CISA Dashboard

See how CISA would view the magnitude of transmitted assessments:

```bash
python3 cisa_magnitude_viewer.py
```

For detailed audit trail:

```bash
python3 cisa_magnitude_viewer.py --detailed
```

### What Gets Created

After running the assessment, you'll have:

```
logs/
├── tribal_data_transmission_log.jsonl    # Main transmission log
├── transmission_[id].json                # Individual transmission records
├── transmission_summary.json             # Summary statistics
└── complete_audit_log.json              # Complete audit trail
```

### Understanding the Output

#### Magnitude Summary

The system shows CISA the magnitude of your tribal infrastructure:

- **Total Assessments**: Number of security/infrastructure assessments
- **Total Findings**: Security and infrastructure findings shared
- **Encryption**: AES-256-GCM (FIPS 140-2 Compliant)
- **Tribal IP Protected**: Automatically filters sovereign information
- **Federal Continuity**: Demonstrates capacity for federal partnership

#### Key Features at a Glance

✓ **Secure Encryption** - Military-grade AES-256-GCM  
✓ **Tribal IP Protection** - Sovereign data never leaves network  
✓ **Complete Audit Trail** - Every transmission logged  
✓ **Data Integrity** - SHA-256 hashing for verification  
✓ **Federal Compliance** - FIPS 140-2 compliant encryption  

### Configuration

Edit `config.json` to customize:

```json
{
  "cisa_endpoints": {
    "primary": "https://cisa.gov/tribal-data-intake"
  },
  "logging": {
    "log_directory": "./logs",
    "audit_retention_days": 2555
  }
}
```

### Security Notes

1. **Tribal Sovereign Data** - Never transmitted outside network
2. **Encryption Keys** - Stored securely (implement key management in production)
3. **Audit Logs** - Retain for 7 years (2555 days) for compliance
4. **Data Classification** - Four levels: Public, Sensitive, Confidential, Tribal Sovereign

### Common Use Cases

#### 1. Run Regular Security Assessment

```bash
python3 run_assessment.py
```

#### 2. Share Capacity with Federal Partners

The system automatically:
- Filters tribal IP
- Encrypts data
- Logs transmission
- Provides CISA with magnitude visibility

#### 3. Review Audit Trail

```bash
# View summary
cat logs/transmission_summary.json

# View complete audit
cat logs/complete_audit_log.json

# View specific transmission
cat logs/transmission_[record_id].json
```

### Troubleshooting

**Issue**: `ImportError: cannot import name 'AESGCM'`  
**Solution**: `pip install --upgrade cryptography`

**Issue**: No logs directory  
**Solution**: Directory is auto-created. Check permissions.

**Issue**: Tests fail  
**Solution**: Ensure dependencies installed: `pip install -r requirements.txt`

### Next Steps

1. ✓ Run the assessment system
2. ✓ Review generated logs
3. ✓ View CISA magnitude dashboard
4. ✓ Customize assessments for your needs
5. ✓ Integrate with your existing systems

### Support

- Review the full [README.md](README.md) for detailed documentation
- Check individual module documentation in source files
- Contact tribal IT for system-specific questions

---

**Remember**: This system protects tribal sovereignty while enabling federal partnership. Your systems speak for you through demonstrated capability.
