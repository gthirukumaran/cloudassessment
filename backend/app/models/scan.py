"""
Scan models for cloud security assessment
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class ScanStatus(enum.Enum):
    """Scan status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScanType(enum.Enum):
    """Scan type enumeration"""
    AZURE = "azure"
    AWS = "aws"
    GCP = "gcp"
    MULTI_CLOUD = "multi_cloud"


class SeverityLevel(enum.Enum):
    """Finding severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class Scan(Base):
    """Scan model for cloud security assessments"""
    
    __tablename__ = "scans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scan_type = Column(Enum(ScanType), nullable=False)
    status = Column(Enum(ScanStatus), default=ScanStatus.PENDING, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Scan configuration
    scan_config = Column(JSON, nullable=True)
    target_resources = Column(JSON, nullable=True)
    
    # Scan results
    total_findings = Column(Integer, default=0, nullable=False)
    critical_findings = Column(Integer, default=0, nullable=False)
    high_findings = Column(Integer, default=0, nullable=False)
    medium_findings = Column(Integer, default=0, nullable=False)
    low_findings = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="scans")
    organization = relationship("Organization", back_populates="scans")
    results = relationship("ScanResult", back_populates="scan")
    findings = relationship("Finding", back_populates="scan")
    
    def __repr__(self):
        return f"<Scan(id={self.id}, name='{self.name}', status='{self.status.value}')>"


class ScanResult(Base):
    """Scan result model for detailed scan outcomes"""
    
    __tablename__ = "scan_results"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)
    
    # Result data
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=False)
    resource_name = Column(String(255), nullable=False)
    compliance_status = Column(String(50), nullable=False)
    risk_score = Column(Integer, nullable=True)
    
    # Detailed results
    findings_count = Column(Integer, default=0, nullable=False)
    compliance_checks = Column(JSON, nullable=True)
    raw_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    scan = relationship("Scan", back_populates="results")
    
    def __repr__(self):
        return f"<ScanResult(id={self.id}, resource='{self.resource_name}', status='{self.compliance_status}')>"


class Finding(Base):
    """Finding model for security issues discovered during scans"""
    
    __tablename__ = "findings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=False)
    
    # Finding details
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    category = Column(String(100), nullable=False)
    
    # Resource information
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=False)
    resource_name = Column(String(255), nullable=False)
    
    # Technical details
    finding_type = Column(String(100), nullable=False)
    compliance_framework = Column(String(100), nullable=True)
    compliance_control = Column(String(100), nullable=True)
    
    # Remediation
    remediation_steps = Column(Text, nullable=True)
    remediation_cost = Column(String(50), nullable=True)
    remediation_effort = Column(String(50), nullable=True)
    
    # AI Analysis
    ai_analysis = Column(Text, nullable=True)
    ai_confidence = Column(Integer, nullable=True)
    
    # Status
    is_false_positive = Column(Boolean, default=False, nullable=False)
    is_resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Metadata
    raw_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    scan = relationship("Scan", back_populates="findings")
    
    def __repr__(self):
        return f"<Finding(id={self.id}, title='{self.title}', severity='{self.severity.value}')>"
