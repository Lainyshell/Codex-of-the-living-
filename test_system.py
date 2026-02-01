#!/usr/bin/env python3
"""
Tests for the Assessment and CISA Transmission System
Validates core functionality and security features
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from assessment_system import AssessmentSystem, AssessmentType, ProtectionLevel
from tribal_data_tracker import TribalDataTracker, DataClassification
from cisa_transmission import SecureTransmitter


def test_assessment_system():
    """Test assessment creation and IP protection"""
    print("Testing Assessment System...")
    
    system = AssessmentSystem()
    
    # Test creating assessment
    assessment = system.create_assessment(
        AssessmentType.SECURITY,
        "Test Security Assessment"
    )
    assert assessment.assessment_id is not None
    assert assessment.assessment_type == AssessmentType.SECURITY
    print("  ✓ Assessment creation works")
    
    # Test adding findings with different protection levels
    assessment.add_finding(
        "test_finding",
        "high",
        "Test finding",
        ProtectionLevel.PUBLIC
    )
    assessment.add_finding(
        "tribal_finding",
        "low",
        "Tribal sovereign information",
        ProtectionLevel.TRIBAL_SOVEREIGN
    )
    assert len(assessment.findings) == 2
    print("  ✓ Adding findings works")
    
    # Test IP protection filtering
    shareable = assessment.get_shareable_results()
    assert shareable["findings_count"] == 1  # Only public finding
    print("  ✓ Tribal IP filtering works correctly")
    
    full_results = assessment.get_full_results()
    assert len(full_results["findings"]) == 2  # All findings
    print("  ✓ Full internal results contain all data")
    
    print("✓ Assessment System tests passed\n")
    return True


def test_data_tracker():
    """Test data tracking and logging"""
    print("Testing Data Tracker...")
    
    # Use temporary directory for testing
    test_log_dir = "/tmp/test_logs"
    tracker = TribalDataTracker(log_directory=test_log_dir)
    
    # Test record creation
    record = tracker.create_transmission_record(
        data_type="test_assessment",
        destination="CISA",
        classification=DataClassification.SENSITIVE,
        data_size_bytes=1024
    )
    assert record.record_id is not None
    assert record.classification == DataClassification.SENSITIVE
    print("  ✓ Transmission record creation works")
    
    # Test encryption and hash
    test_data = b"test data for hashing"
    record.set_data_hash(test_data)
    record.set_encryption("AES-256-GCM")
    assert record.data_hash is not None
    assert record.encryption_method == "AES-256-GCM"
    print("  ✓ Hash and encryption recording works")
    
    # Test validation
    is_valid = tracker.validate_transmission(record)
    assert is_valid is True
    print("  ✓ Transmission validation works")
    
    # Test that tribal sovereign data is blocked
    sovereign_record = tracker.create_transmission_record(
        data_type="sovereign_data",
        destination="CISA",
        classification=DataClassification.TRIBAL_SOVEREIGN,
        data_size_bytes=512
    )
    sovereign_record.set_data_hash(b"test")
    sovereign_record.set_encryption("AES-256-GCM")
    is_valid = tracker.validate_transmission(sovereign_record)
    assert is_valid is False
    print("  ✓ Tribal sovereign data protection works")
    
    # Test logging
    record.mark_transmitted()
    tracker.log_transmission(record)
    assert record.status == "LOGGED"
    assert tracker.main_log_file.exists()
    print("  ✓ Transmission logging works")
    
    # Test summary
    summary = tracker.get_transmission_summary()
    assert summary["total_transmissions"] == 2
    assert "CISA" in summary["destination_breakdown"]
    print("  ✓ Summary generation works")
    
    print("✓ Data Tracker tests passed\n")
    return True


def test_secure_transmitter():
    """Test encryption and transmission"""
    print("Testing Secure Transmitter...")
    
    transmitter = SecureTransmitter()
    
    # Test encryption
    test_data = b"Test assessment data"
    encrypted = transmitter.encrypt_data(test_data)
    assert "ciphertext" in encrypted
    assert "nonce" in encrypted
    assert encrypted["algorithm"] == "AES-256-GCM"
    print("  ✓ Data encryption works")
    
    # Test decryption (verification)
    decrypted = transmitter.decrypt_data(encrypted)
    assert decrypted == test_data
    print("  ✓ Encryption/decryption round-trip works")
    
    # Test package preparation
    assessment_data = {
        "assessment_id": "test123",
        "findings": ["finding1", "finding2"]
    }
    package = transmitter.prepare_transmission_package(assessment_data)
    assert package["transmission_id"] is not None
    assert package["destination"] == "CISA"
    assert package["tribal_sovereignty_protected"] is True
    assert package["data_hash"] is not None
    print("  ✓ Transmission package preparation works")
    
    # Test encryption verification
    is_encrypted = transmitter.verify_encryption(package)
    assert is_encrypted is True
    print("  ✓ Encryption verification works")
    
    # Test transmission simulation
    result = transmitter.simulate_transmission(package)
    assert result["status"] == "SIMULATED_SUCCESS"
    assert "cisa_receipt_id" in result["response"]
    print("  ✓ Transmission simulation works")
    
    print("✓ Secure Transmitter tests passed\n")
    return True


def test_integrated_workflow():
    """Test complete end-to-end workflow"""
    print("Testing Integrated Workflow...")
    
    # Initialize all components
    assessment_system = AssessmentSystem()
    tracker = TribalDataTracker(log_directory="/tmp/integrated_test_logs")
    transmitter = SecureTransmitter()
    
    # Create and run assessment
    assessment = assessment_system.run_security_assessment()
    shareable_results = assessment.get_shareable_results()
    print("  ✓ Assessment created")
    
    # Create tracking record
    json_data = json.dumps(shareable_results).encode('utf-8')
    record = tracker.create_transmission_record(
        data_type="security_assessment",
        destination="CISA",
        classification=DataClassification.SENSITIVE,
        data_size_bytes=len(json_data)
    )
    print("  ✓ Tracking record created")
    
    # Prepare for transmission
    record.set_data_hash(json_data)
    record.set_encryption("AES-256-GCM")
    print("  ✓ Encryption set")
    
    # Validate
    is_valid = tracker.validate_transmission(record)
    assert is_valid is True
    print("  ✓ Transmission validated")
    
    # Transmit
    package = transmitter.prepare_transmission_package(shareable_results)
    result = transmitter.simulate_transmission(package)
    print("  ✓ Transmitted to CISA")
    
    # Log
    record.mark_transmitted()
    tracker.log_transmission(record)
    print("  ✓ Logged transmission")
    
    # Verify tribal IP protection
    assert shareable_results["metadata"]["classification"] == "Shared with Federal Partners"
    # Check that tribal sovereign and confidential findings were filtered
    for finding in shareable_results["findings"]:
        assert finding["protection_level"] != ProtectionLevel.TRIBAL_SOVEREIGN.value
        assert finding["protection_level"] != ProtectionLevel.CONFIDENTIAL.value
    print("  ✓ Tribal IP protected throughout workflow")
    
    # Additional test: Verify CONFIDENTIAL data is also filtered
    assessment_with_confidential = assessment_system.create_assessment(
        AssessmentType.SECURITY,
        "Test with Confidential Data"
    )
    assessment_with_confidential.add_finding(
        "public_finding",
        "low",
        "Public information",
        ProtectionLevel.PUBLIC
    )
    assessment_with_confidential.add_finding(
        "confidential_finding",
        "high",
        "Confidential tribal information",
        ProtectionLevel.CONFIDENTIAL
    )
    assessment_with_confidential.add_finding(
        "sovereign_finding",
        "medium",
        "Tribal sovereign data",
        ProtectionLevel.TRIBAL_SOVEREIGN
    )
    
    confidential_shareable = assessment_with_confidential.get_shareable_results()
    # Should only have the public finding
    assert confidential_shareable["findings_count"] == 1
    assert confidential_shareable["findings"][0]["protection_level"] == ProtectionLevel.PUBLIC.value
    print("  ✓ CONFIDENTIAL and TRIBAL_SOVEREIGN data properly filtered")
    
    print("✓ Integrated Workflow test passed\n")
    return True


def main():
    """Run all tests"""
    print("=" * 70)
    print("ASSESSMENT AND CISA TRANSMISSION SYSTEM - TEST SUITE")
    print("=" * 70)
    print()
    
    tests = [
        test_assessment_system,
        test_data_tracker,
        test_secure_transmitter,
        test_integrated_workflow
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed: {str(e)}\n")
            failed += 1
    
    print("=" * 70)
    print(f"TEST RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
