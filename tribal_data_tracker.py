#!/usr/bin/env python3
"""
Tribal Data Tracking and Logging System
Tracks all data leaving the tribal secure network with comprehensive audit logging
"""

import json
import hashlib
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path


class DataClassification:
    """Classification levels for tribal data"""
    PUBLIC = "PUBLIC"
    SENSITIVE = "SENSITIVE"
    CONFIDENTIAL = "CONFIDENTIAL"
    TRIBAL_SOVEREIGN = "TRIBAL_SOVEREIGN"


class TransmissionStatus:
    """Status codes for data transmission"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    TRANSMITTED = "TRANSMITTED"
    FAILED = "FAILED"
    LOGGED = "LOGGED"


class DataTransmissionRecord:
    """Record of data transmission for audit purposes"""
    
    def __init__(self, 
                 data_type: str,
                 destination: str,
                 classification: str,
                 data_size_bytes: int):
        self.record_id = self._generate_record_id()
        self.data_type = data_type
        self.destination = destination
        self.classification = classification
        self.data_size_bytes = data_size_bytes
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.status = TransmissionStatus.PENDING
        self.data_hash = None
        self.encryption_method = None
        self.tribal_ip_protected = True
        self.audit_trail = []
    
    def _generate_record_id(self) -> str:
        """Generate unique record ID"""
        timestamp = datetime.utcnow().isoformat()
        random_data = os.urandom(8).hex()
        return hashlib.sha256(f"{timestamp}{random_data}".encode()).hexdigest()[:24]
    
    def add_audit_entry(self, action: str, details: str):
        """Add entry to audit trail"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "action": action,
            "details": details
        }
        self.audit_trail.append(entry)
    
    def set_data_hash(self, data: bytes):
        """Calculate and set hash of transmitted data"""
        self.data_hash = hashlib.sha256(data).hexdigest()
        self.add_audit_entry("DATA_HASHED", f"SHA-256 hash calculated: {self.data_hash[:16]}...")
    
    def set_encryption(self, method: str):
        """Record encryption method used"""
        self.encryption_method = method
        self.add_audit_entry("ENCRYPTED", f"Data encrypted using {method}")
    
    def mark_transmitted(self):
        """Mark record as successfully transmitted"""
        self.status = TransmissionStatus.TRANSMITTED
        self.add_audit_entry("TRANSMITTED", "Data successfully transmitted to destination")
    
    def mark_failed(self, error: str):
        """Mark transmission as failed"""
        self.status = TransmissionStatus.FAILED
        self.add_audit_entry("FAILED", f"Transmission failed: {error}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for logging"""
        return {
            "record_id": self.record_id,
            "data_type": self.data_type,
            "destination": self.destination,
            "classification": self.classification,
            "data_size_bytes": self.data_size_bytes,
            "timestamp": self.timestamp,
            "status": self.status,
            "data_hash": self.data_hash,
            "encryption_method": self.encryption_method,
            "tribal_ip_protected": self.tribal_ip_protected,
            "audit_trail": self.audit_trail
        }


class TribalDataTracker:
    """
    Main tracking system for tribal data leaving the secure network
    Ensures all transmissions are logged and comply with tribal sovereignty
    """
    
    def __init__(self, log_directory: str = "./logs"):
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        self.records: List[DataTransmissionRecord] = []
        self.main_log_file = self.log_directory / "tribal_data_transmission_log.jsonl"
    
    def create_transmission_record(self,
                                   data_type: str,
                                   destination: str,
                                   classification: str,
                                   data_size_bytes: int) -> DataTransmissionRecord:
        """Create a new transmission record"""
        record = DataTransmissionRecord(
            data_type=data_type,
            destination=destination,
            classification=classification,
            data_size_bytes=data_size_bytes
        )
        self.records.append(record)
        record.add_audit_entry("CREATED", "Transmission record created")
        return record
    
    def validate_transmission(self, record: DataTransmissionRecord) -> bool:
        """
        Validate that transmission meets tribal data protection requirements
        """
        # Check classification
        if record.classification == DataClassification.TRIBAL_SOVEREIGN:
            record.add_audit_entry(
                "VALIDATION_FAILED",
                "TRIBAL_SOVEREIGN data cannot leave network"
            )
            return False
        
        # Ensure encryption is set
        if not record.encryption_method:
            record.add_audit_entry(
                "VALIDATION_FAILED",
                "No encryption method specified"
            )
            return False
        
        # Ensure data hash is calculated
        if not record.data_hash:
            record.add_audit_entry(
                "VALIDATION_FAILED",
                "Data hash not calculated"
            )
            return False
        
        record.add_audit_entry("VALIDATION_PASSED", "All validation checks passed")
        record.status = TransmissionStatus.APPROVED
        return True
    
    def log_transmission(self, record: DataTransmissionRecord):
        """Log transmission record to persistent storage"""
        log_entry = {
            "log_timestamp": datetime.utcnow().isoformat() + "Z",
            "record": record.to_dict()
        }
        
        # Append to main log file (JSONL format)
        with open(self.main_log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Create individual record file for detailed audit
        record_file = self.log_directory / f"transmission_{record.record_id}.json"
        with open(record_file, "w") as f:
            json.dump(record.to_dict(), f, indent=2)
        
        record.status = TransmissionStatus.LOGGED
        record.add_audit_entry("LOGGED", f"Record logged to {self.main_log_file}")
    
    def get_transmission_summary(self) -> Dict[str, Any]:
        """Get summary of all tracked transmissions"""
        status_counts = {}
        classification_counts = {}
        destination_counts = {}
        
        for record in self.records:
            # Count by status
            status_counts[record.status] = status_counts.get(record.status, 0) + 1
            # Count by classification
            classification_counts[record.classification] = \
                classification_counts.get(record.classification, 0) + 1
            # Count by destination
            destination_counts[record.destination] = \
                destination_counts.get(record.destination, 0) + 1
        
        return {
            "total_transmissions": len(self.records),
            "status_breakdown": status_counts,
            "classification_breakdown": classification_counts,
            "destination_breakdown": destination_counts,
            "log_file": str(self.main_log_file)
        }
    
    def get_records_by_destination(self, destination: str) -> List[DataTransmissionRecord]:
        """Get all transmission records for a specific destination"""
        return [r for r in self.records if r.destination == destination]
    
    def export_audit_log(self, output_file: str):
        """Export complete audit log for compliance review"""
        audit_data = {
            "export_timestamp": datetime.utcnow().isoformat() + "Z",
            "summary": self.get_transmission_summary(),
            "records": [r.to_dict() for r in self.records]
        }
        
        with open(output_file, "w") as f:
            json.dump(audit_data, f, indent=2)
        
        return output_file


if __name__ == "__main__":
    # Example usage
    tracker = TribalDataTracker()
    
    # Create transmission record
    record = tracker.create_transmission_record(
        data_type="assessment_results",
        destination="CISA",
        classification=DataClassification.SENSITIVE,
        data_size_bytes=1024
    )
    
    # Set encryption and hash
    test_data = b"test data"
    record.set_data_hash(test_data)
    record.set_encryption("AES-256-GCM")
    
    # Validate and log
    if tracker.validate_transmission(record):
        record.mark_transmitted()
        tracker.log_transmission(record)
    
    print("Transmission Summary:")
    print(json.dumps(tracker.get_transmission_summary(), indent=2))
