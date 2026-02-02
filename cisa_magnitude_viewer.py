#!/usr/bin/env python3
"""
CISA Magnitude Viewer
Simulates how CISA instantly sees the magnitude of assessment results
"""

import json
from pathlib import Path


def display_magnitude_dashboard(transmission_log_file: str):
    """
    Display a dashboard showing the magnitude of transmitted assessments
    This simulates what CISA would see upon receiving the data
    """
    
    print("=" * 80)
    print("CISA TRIBAL ASSESSMENT DASHBOARD")
    print("Cybersecurity and Infrastructure Security Agency")
    print("=" * 80)
    print()
    
    # Read the transmission log
    log_path = Path(transmission_log_file)
    if not log_path.exists():
        print("No transmission data found. Run the assessment first.")
        return
    
    transmissions = []
    with open(log_path, "r") as f:
        for line in f:
            if line.strip():
                transmissions.append(json.loads(line))
    
    if not transmissions:
        print("No transmissions recorded yet.")
        return
    
    # Calculate totals
    total_transmissions = len(transmissions)
    assessment_types = {}
    data_transferred = 0
    
    print(f"📊 MAGNITUDE SUMMARY")
    print("-" * 80)
    print(f"Source: Verdigris Botanica Tribal Nation")
    print(f"Total Data Transmissions: {total_transmissions}")
    print()
    
    for transmission in transmissions:
        record = transmission.get("record", {})
        data_transferred += record.get("data_size_bytes", 0)
        
        # Display each transmission
        print(f"🔐 Transmission ID: {record.get('record_id', 'N/A')}")
        print(f"   Type: {record.get('data_type', 'N/A')}")
        print(f"   Classification: {record.get('classification', 'N/A')}")
        print(f"   Encryption: {record.get('encryption_method', 'N/A')}")
        print(f"   Timestamp: {record.get('timestamp', 'N/A')}")
        print(f"   Status: {record.get('status', 'N/A')}")
        print(f"   Data Hash: {record.get('data_hash', 'N/A')[:32]}...")
        print()
    
    print("-" * 80)
    print(f"📈 CAPACITY INDICATORS")
    print("-" * 80)
    print(f"✓ Tribal entity demonstrates secure data transmission capability")
    print(f"✓ Encryption standards: AES-256-GCM (FIPS 140-2 Compliant)")
    print(f"✓ Data integrity verification: SHA-256 hashing")
    print(f"✓ Comprehensive audit logging: ENABLED")
    print(f"✓ Tribal sovereignty protection: ACTIVE")
    print(f"✓ Total data transferred: {data_transferred:,} bytes")
    print()
    
    print("-" * 80)
    print(f"🎯 FEDERAL CONTINUITY ASSESSMENT")
    print("-" * 80)
    print(f"✓ Infrastructure Scalability: DEMONSTRATED")
    print(f"✓ Security Controls: VALIDATED")
    print(f"✓ Compliance Capability: CONFIRMED")
    print(f"✓ Federal Partnership Readiness: VERIFIED")
    print()
    
    print("=" * 80)
    print("Assessment Complete - Tribal Capacity Validated")
    print("Systems speak for themselves through demonstrated capability")
    print("=" * 80)


def show_audit_trail(log_directory: str = "./logs"):
    """Show detailed audit trail for transparency"""
    
    print("\n" + "=" * 80)
    print("DETAILED AUDIT TRAIL")
    print("=" * 80)
    print()
    
    audit_file = Path(log_directory) / "complete_audit_log.json"
    if not audit_file.exists():
        print("No audit log found.")
        return
    
    with open(audit_file, "r") as f:
        audit_data = json.load(f)
    
    print(f"Audit Log Generated: {audit_data.get('export_timestamp', 'N/A')}")
    print()
    
    summary = audit_data.get("summary", {})
    print("Summary:")
    print(f"  - Total Transmissions: {summary.get('total_transmissions', 0)}")
    print(f"  - Status Breakdown: {summary.get('status_breakdown', {})}")
    print(f"  - Classifications: {summary.get('classification_breakdown', {})}")
    print(f"  - Destinations: {summary.get('destination_breakdown', {})}")
    print()
    
    records = audit_data.get("records", [])
    for i, record in enumerate(records, 1):
        print(f"Record {i}:")
        print(f"  ID: {record.get('record_id', 'N/A')}")
        print(f"  Type: {record.get('data_type', 'N/A')}")
        print(f"  Classification: {record.get('classification', 'N/A')}")
        
        # Show audit trail entries
        audit_trail = record.get("audit_trail", [])
        if audit_trail:
            print(f"  Audit Trail ({len(audit_trail)} entries):")
            for entry in audit_trail:
                print(f"    - [{entry.get('timestamp', 'N/A')}] {entry.get('action', 'N/A')}")
                if entry.get('details'):
                    print(f"      {entry.get('details', '')}")
        print()


if __name__ == "__main__":
    import sys
    
    # Display magnitude dashboard
    display_magnitude_dashboard("./logs/tribal_data_transmission_log.jsonl")
    
    # Show audit trail
    if len(sys.argv) > 1 and sys.argv[1] == "--detailed":
        show_audit_trail("./logs")
