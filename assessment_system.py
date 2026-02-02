#!/usr/bin/env python3
"""
Tribal Assessment System
Conducts security and infrastructure assessments while protecting tribal IP
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum


class AssessmentType(Enum):
    """Types of assessments that can be conducted"""
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    COMPLIANCE = "compliance"
    CAPACITY = "capacity"


class ProtectionLevel(Enum):
    """Data protection levels for tribal information"""
    PUBLIC = "public"
    SENSITIVE = "sensitive"
    CONFIDENTIAL = "confidential"
    TRIBAL_SOVEREIGN = "tribal_sovereign"


class Assessment:
    """Represents a tribal assessment with IP protection"""
    
    def __init__(self, assessment_type: AssessmentType, name: str):
        self.assessment_id = self._generate_id()
        self.assessment_type = assessment_type
        self.name = name
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.findings = []
        self.metadata = {
            "tribe": "Verdigris Botanica Tribal Nation",
            "jurisdiction": "Tribal Sovereign Territory"
        }
    
    def _generate_id(self) -> str:
        """Generate unique assessment ID"""
        timestamp = datetime.utcnow().isoformat()
        return hashlib.sha256(timestamp.encode()).hexdigest()[:16]
    
    def add_finding(self, 
                   finding_type: str,
                   severity: str,
                   description: str,
                   protection_level: ProtectionLevel = ProtectionLevel.SENSITIVE):
        """Add a finding to the assessment"""
        finding = {
            "finding_id": hashlib.sha256(
                f"{self.assessment_id}{len(self.findings)}".encode()
            ).hexdigest()[:12],
            "type": finding_type,
            "severity": severity,
            "description": description,
            "protection_level": protection_level.value,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.findings.append(finding)
    
    def get_shareable_results(self) -> Dict[str, Any]:
        """
        Get assessment results filtered for CISA sharing
        Removes tribal sovereign and confidential information
        """
        shareable_findings = [
            f for f in self.findings 
            if f["protection_level"] in [
                ProtectionLevel.PUBLIC.value,
                ProtectionLevel.SENSITIVE.value
            ]
        ]
        
        return {
            "assessment_id": self.assessment_id,
            "assessment_type": self.assessment_type.value,
            "name": self.name,
            "timestamp": self.timestamp,
            "findings_count": len(shareable_findings),
            "findings": shareable_findings,
            "severity_summary": self._calculate_severity_summary(shareable_findings),
            "metadata": {
                "source": "Tribal Sovereign Entity",
                "classification": "Shared with Federal Partners"
            }
        }
    
    def _calculate_severity_summary(self, findings: List[Dict]) -> Dict[str, int]:
        """Calculate severity distribution"""
        summary = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for finding in findings:
            severity = finding.get("severity", "info").lower()
            if severity in summary:
                summary[severity] += 1
        return summary
    
    def get_full_results(self) -> Dict[str, Any]:
        """Get complete assessment results for internal use only"""
        return {
            "assessment_id": self.assessment_id,
            "assessment_type": self.assessment_type.value,
            "name": self.name,
            "timestamp": self.timestamp,
            "findings_count": len(self.findings),
            "findings": self.findings,
            "severity_summary": self._calculate_severity_summary(self.findings),
            "metadata": self.metadata,
            "protection_note": "Contains Tribal Sovereign Information - Internal Use Only"
        }


class AssessmentSystem:
    """Main assessment system for tribal infrastructure"""
    
    def __init__(self):
        self.assessments: List[Assessment] = []
    
    def create_assessment(self, 
                         assessment_type: AssessmentType,
                         name: str) -> Assessment:
        """Create a new assessment"""
        assessment = Assessment(assessment_type, name)
        self.assessments.append(assessment)
        return assessment
    
    def run_security_assessment(self) -> Assessment:
        """Run a comprehensive security assessment"""
        assessment = self.create_assessment(
            AssessmentType.SECURITY,
            "Tribal Infrastructure Security Assessment"
        )
        
        # Example security checks
        assessment.add_finding(
            finding_type="network_security",
            severity="info",
            description="Network perimeter security validated",
            protection_level=ProtectionLevel.PUBLIC
        )
        
        assessment.add_finding(
            finding_type="encryption",
            severity="info",
            description="Data encryption standards implemented",
            protection_level=ProtectionLevel.PUBLIC
        )
        
        assessment.add_finding(
            finding_type="sovereignty",
            severity="info",
            description="Tribal sovereignty controls active",
            protection_level=ProtectionLevel.TRIBAL_SOVEREIGN
        )
        
        return assessment
    
    def run_infrastructure_assessment(self) -> Assessment:
        """Run infrastructure capacity assessment"""
        assessment = self.create_assessment(
            AssessmentType.INFRASTRUCTURE,
            "Tribal Infrastructure Capacity Assessment"
        )
        
        assessment.add_finding(
            finding_type="capacity",
            severity="info",
            description="Infrastructure capacity validated for federal continuity",
            protection_level=ProtectionLevel.SENSITIVE
        )
        
        assessment.add_finding(
            finding_type="scalability",
            severity="info",
            description="Systems demonstrate scalability for growth",
            protection_level=ProtectionLevel.SENSITIVE
        )
        
        return assessment
    
    def get_assessment(self, assessment_id: str) -> Optional[Assessment]:
        """Retrieve assessment by ID"""
        for assessment in self.assessments:
            if assessment.assessment_id == assessment_id:
                return assessment
        return None


if __name__ == "__main__":
    # Example usage
    system = AssessmentSystem()
    
    print("Running Security Assessment...")
    security_assessment = system.run_security_assessment()
    
    print("Running Infrastructure Assessment...")
    infra_assessment = system.run_infrastructure_assessment()
    
    print("\n=== Assessment Results ===")
    print(json.dumps(security_assessment.get_shareable_results(), indent=2))
