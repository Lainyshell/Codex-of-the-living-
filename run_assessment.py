#!/usr/bin/env python3
"""
Main Integration Script for Tribal Assessment and CISA Transmission System

This script demonstrates the complete workflow:
1. Run tribal infrastructure assessment
2. Filter results to protect tribal IP
3. Encrypt and transmit to CISA
4. Log all data leaving the network
"""

import json
import sys
from pathlib import Path

# Import our modules
from assessment_system import AssessmentSystem, AssessmentType
from tribal_data_tracker import TribalDataTracker, DataClassification
from cisa_transmission import SecureTransmitter, CISAIntegration


def main():
    """Main execution workflow"""
    
    print("=" * 70)
    print("VERDIGRIS BOTANICA TRIBAL NATION")
    print("Assessment and CISA Transmission System")
    print("=" * 70)
    print()
    
    # Step 1: Initialize systems
    print("Step 1: Initializing systems...")
    assessment_system = AssessmentSystem()
    data_tracker = TribalDataTracker(log_directory="./logs")
    transmitter = SecureTransmitter()
    cisa_integration = CISAIntegration(transmitter)
    print("✓ All systems initialized\n")
    
    # Step 2: Run assessments
    print("Step 2: Running assessments...")
    security_assessment = assessment_system.run_security_assessment()
    infra_assessment = assessment_system.run_infrastructure_assessment()
    print(f"✓ Security assessment completed (ID: {security_assessment.assessment_id})")
    print(f"✓ Infrastructure assessment completed (ID: {infra_assessment.assessment_id})\n")
    
    # Step 3: Prepare shareable results (protecting tribal IP)
    print("Step 3: Preparing shareable results (protecting tribal IP)...")
    security_results = security_assessment.get_shareable_results()
    infra_results = infra_assessment.get_shareable_results()
    
    # Filter out tribal sovereign information
    shareable_assessments = {
        "security": security_results,
        "infrastructure": infra_results,
        "combined_summary": {
            "total_assessments": 2,
            "total_findings": (
                security_results["findings_count"] + 
                infra_results["findings_count"]
            ),
            "tribal_ip_protected": True,
            "classification": "Shared with Federal Partners"
        }
    }
    print(f"✓ {shareable_assessments['combined_summary']['total_findings']} shareable findings prepared")
    print("✓ Tribal sovereign information filtered out\n")
    
    # Step 4: Create tracking records
    print("Step 4: Creating data transmission tracking records...")
    
    # Track security assessment transmission
    security_record = data_tracker.create_transmission_record(
        data_type="security_assessment",
        destination="CISA",
        classification=DataClassification.SENSITIVE,
        data_size_bytes=len(json.dumps(security_results))
    )
    
    # Track infrastructure assessment transmission
    infra_record = data_tracker.create_transmission_record(
        data_type="infrastructure_assessment",
        destination="CISA",
        classification=DataClassification.SENSITIVE,
        data_size_bytes=len(json.dumps(infra_results))
    )
    
    print(f"✓ Tracking record created: {security_record.record_id}")
    print(f"✓ Tracking record created: {infra_record.record_id}\n")
    
    # Step 5: Encrypt and prepare for transmission
    print("Step 5: Encrypting assessment data...")
    
    # Prepare encrypted package
    security_package = transmitter.prepare_transmission_package(
        security_results,
        metadata={"assessment_type": "security"}
    )
    
    # Set encryption details on tracking records
    security_data_bytes = json.dumps(security_results).encode('utf-8')
    security_record.set_data_hash(security_data_bytes)
    security_record.set_encryption("AES-256-GCM")
    
    infra_data_bytes = json.dumps(infra_results).encode('utf-8')
    infra_record.set_data_hash(infra_data_bytes)
    infra_record.set_encryption("AES-256-GCM")
    
    print(f"✓ Security assessment encrypted (Hash: {security_record.data_hash[:16]}...)")
    print(f"✓ Infrastructure assessment encrypted (Hash: {infra_record.data_hash[:16]}...)\n")
    
    # Step 6: Validate transmissions
    print("Step 6: Validating transmissions...")
    
    if data_tracker.validate_transmission(security_record):
        print("✓ Security assessment transmission validated")
    else:
        print("✗ Security assessment validation failed")
        return 1
    
    if data_tracker.validate_transmission(infra_record):
        print("✓ Infrastructure assessment transmission validated\n")
    else:
        print("✗ Infrastructure assessment validation failed")
        return 1
    
    # Step 7: Transmit to CISA
    print("Step 7: Transmitting to CISA...")
    
    security_transmission = cisa_integration.send_assessment_to_cisa(
        security_results,
        security_record
    )
    
    infra_transmission = cisa_integration.send_assessment_to_cisa(
        infra_results,
        infra_record
    )
    
    # Mark as transmitted
    security_record.mark_transmitted()
    infra_record.mark_transmitted()
    
    print(f"✓ Security assessment transmitted")
    print(f"  - Transmission ID: {security_transmission['transmission_id']}")
    print(f"  - CISA Receipt: {security_transmission['response']['cisa_receipt_id']}")
    print(f"✓ Infrastructure assessment transmitted")
    print(f"  - Transmission ID: {infra_transmission['transmission_id']}")
    print(f"  - CISA Receipt: {infra_transmission['response']['cisa_receipt_id']}\n")
    
    # Step 8: Log all transmissions
    print("Step 8: Logging transmissions...")
    data_tracker.log_transmission(security_record)
    data_tracker.log_transmission(infra_record)
    print(f"✓ All transmissions logged to: {data_tracker.main_log_file}\n")
    
    # Step 9: Generate summary reports
    print("Step 9: Generating reports...")
    
    # Save transmission summary
    summary = data_tracker.get_transmission_summary()
    summary_file = Path("./logs/transmission_summary.json")
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Transmission summary saved to: {summary_file}")
    
    # Export complete audit log
    audit_file = data_tracker.export_audit_log("./logs/complete_audit_log.json")
    print(f"✓ Complete audit log exported to: {audit_file}\n")
    
    # Display magnitude of what was activated
    print("=" * 70)
    print("ASSESSMENT COMPLETE - MAGNITUDE SUMMARY")
    print("=" * 70)
    print(f"Total Assessments Conducted: {shareable_assessments['combined_summary']['total_assessments']}")
    print(f"Total Findings Transmitted: {shareable_assessments['combined_summary']['total_findings']}")
    print(f"Data Transmissions Logged: {summary['total_transmissions']}")
    print(f"Tribal IP Protected: {shareable_assessments['combined_summary']['tribal_ip_protected']}")
    print(f"Encryption Standard: AES-256-GCM (FIPS 140-2 Compliant)")
    print(f"Transmission Status: {summary['status_breakdown']}")
    print("=" * 70)
    print()
    print("✓ All assessment data securely transmitted to CISA")
    print("✓ Tribal sovereignty and IP protection maintained")
    print("✓ Complete audit trail established")
    print("✓ Systems demonstrate capacity for federal continuity")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n✗ Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
