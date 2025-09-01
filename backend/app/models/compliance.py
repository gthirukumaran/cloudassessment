"""\nCompliance framework models for custom security frameworks\n"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.database import Base


class FrameworkType(enum.Enum):
    """Framework type enumeration"""
    STANDARD = "standard"  # Built-in frameworks like CIS, NIST
    CUSTOM = "custom"      # User-defined frameworks


class ControlType(enum.Enum):
    """Control type enumeration"""
    AUTOMATED = "automated"    # Can be automatically checked
    MANUAL = "manual"          # Requires manual verification
    HYBRID = "hybrid"          # Combination of automated and manual


class ComplianceFramework(Base):
    """Compliance framework model for storing custom and standard frameworks"""
    
    __tablename__ = "compliance_frameworks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False, default="1.0")
    framework_type = Column(Enum(FrameworkType), nullable=False, default=FrameworkType.CUSTOM)
    
    # Framework metadata
    industry = Column(String(100), nullable=True)  # e.g., "Healthcare", "Finance"
    region = Column(String(100), nullable=True)    # e.g., "US", "EU", "Global"
    tags = Column(JSON, nullable=True)             # Array of tags for categorization
    
    # Ownership and permissions
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)  # Can be used by other orgs
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    controls = relationship("ComplianceControl", back_populates="framework", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<ComplianceFramework(id={self.id}, name='{self.name}', type='{self.framework_type}')>"


class ComplianceControl(Base):
    """Compliance control model for storing individual controls within frameworks"""
    
    __tablename__ = "compliance_controls"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    framework_id = Column(UUID(as_uuid=True), ForeignKey("compliance_frameworks.id"), nullable=False)
    
    # Control identification
    control_id = Column(String(100), nullable=False)  # e.g., "CC-1.1", "CUSTOM-001"
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    
    # Control classification
    category = Column(String(100), nullable=False)    # e.g., "Access Control", "Data Protection"
    subcategory = Column(String(100), nullable=True)  # More specific categorization
    control_type = Column(Enum(ControlType), nullable=False, default=ControlType.AUTOMATED)
    
    # Risk and compliance
    severity = Column(String(20), nullable=False, default="medium")  # critical, high, medium, low
    risk_rating = Column(Integer, nullable=True)      # 1-10 scale
    compliance_weight = Column(Integer, nullable=False, default=1)  # Weight in overall score
    
    # Implementation details
    implementation_guidance = Column(Text, nullable=True)
    remediation_steps = Column(Text, nullable=True)
    remediation_cost = Column(String(50), nullable=True)    # low, medium, high
    remediation_effort = Column(String(50), nullable=True)  # hours, days, weeks
    
    # Technical implementation
    check_script = Column(Text, nullable=True)        # Script/query for automated checks
    check_parameters = Column(JSON, nullable=True)    # Parameters for the check
    resource_types = Column(JSON, nullable=True)      # Azure resource types to check
    
    # References and documentation
    references = Column(JSON, nullable=True)          # Array of reference URLs/documents
    tags = Column(JSON, nullable=True)               # Array of tags
    
    # Control status
    is_active = Column(Boolean, default=True, nullable=False)
    order_index = Column(Integer, nullable=False, default=0)  # Order within framework
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    framework = relationship("ComplianceFramework", back_populates="controls")
    
    def __repr__(self):
        return f"<ComplianceControl(id={self.id}, control_id='{self.control_id}', title='{self.title[:50]}')>"


class CustomScanTemplate(Base):
    """Template for custom scans with specific framework and control selections"""
    
    __tablename__ = "custom_scan_templates"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Template configuration
    framework_id = Column(UUID(as_uuid=True), ForeignKey("compliance_frameworks.id"), nullable=False)
    selected_controls = Column(JSON, nullable=False)  # Array of control IDs to include
    scan_config = Column(JSON, nullable=True)         # Additional scan configuration
    
    # Ownership
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    framework = relationship("ComplianceFramework")
    creator = relationship("User", foreign_keys=[created_by])
    organization = relationship("Organization")
    
    def __repr__(self):
        return f"<CustomScanTemplate(id={self.id}, name='{self.name}')>"