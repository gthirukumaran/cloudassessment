"""
Report model for CIS-style PDF report generation
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class ReportStatus(enum.Enum):
    """Report generation status"""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportType(enum.Enum):
    """Report type enumeration"""
    CIS_COMPLIANCE = "cis_compliance"
    SECURITY_ASSESSMENT = "security_assessment"
    REMEDIATION_PLAN = "remediation_plan"
    EXECUTIVE_SUMMARY = "executive_summary"
    CUSTOM = "custom"


class Report(Base):
    """Report model for CIS-style PDF report generation"""
    
    __tablename__ = "reports"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)
    status = Column(Enum(ReportStatus), default=ReportStatus.PENDING, nullable=False)
    
    # Associated entities
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    scan_id = Column(UUID(as_uuid=True), ForeignKey("scans.id"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Report configuration
    report_config = Column(JSON, nullable=True)
    template_id = Column(String(100), nullable=True)
    
    # File information
    file_path = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    file_url = Column(String(500), nullable=True)
    
    # Generation metadata
    generation_started_at = Column(DateTime(timezone=True), nullable=True)
    generation_completed_at = Column(DateTime(timezone=True), nullable=True)
    generation_duration_ms = Column(Integer, nullable=True)
    
    # Report statistics
    total_pages = Column(Integer, nullable=True)
    total_findings = Column(Integer, default=0, nullable=False)
    critical_findings = Column(Integer, default=0, nullable=False)
    high_findings = Column(Integer, default=0, nullable=False)
    medium_findings = Column(Integer, default=0, nullable=False)
    low_findings = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="reports")
    
    def __repr__(self):
        return f"<Report(id={self.id}, name='{self.name}', type='{self.report_type.value}', status='{self.status.value}')>"
