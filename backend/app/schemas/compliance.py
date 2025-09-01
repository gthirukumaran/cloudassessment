"""\nCompliance framework schemas for API requests and responses\n"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.models.compliance import FrameworkType, ControlType


# Framework Schemas
class ComplianceFrameworkCreate(BaseModel):
    """Schema for creating a new compliance framework"""
    name: str = Field(..., description="Framework name (unique identifier)", min_length=1, max_length=255)
    display_name: str = Field(..., description="Human-readable framework name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Framework description")
    version: str = Field("1.0", description="Framework version")
    framework_type: FrameworkType = Field(FrameworkType.CUSTOM, description="Framework type")
    industry: Optional[str] = Field(None, description="Target industry", max_length=100)
    region: Optional[str] = Field(None, description="Target region", max_length=100)
    tags: Optional[List[str]] = Field(None, description="Framework tags")
    is_public: bool = Field(False, description="Whether framework is public")


class ComplianceFrameworkUpdate(BaseModel):
    """Schema for updating a compliance framework"""
    display_name: Optional[str] = Field(None, description="Human-readable framework name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Framework description")
    version: Optional[str] = Field(None, description="Framework version")
    industry: Optional[str] = Field(None, description="Target industry", max_length=100)
    region: Optional[str] = Field(None, description="Target region", max_length=100)
    tags: Optional[List[str]] = Field(None, description="Framework tags")
    is_public: Optional[bool] = Field(None, description="Whether framework is public")
    is_active: Optional[bool] = Field(None, description="Whether framework is active")


class ComplianceFrameworkResponse(BaseModel):
    """Schema for compliance framework response"""
    id: uuid.UUID = Field(..., description="Framework unique identifier")
    name: str = Field(..., description="Framework name")
    display_name: str = Field(..., description="Human-readable framework name")
    description: Optional[str] = Field(None, description="Framework description")
    version: str = Field(..., description="Framework version")
    framework_type: FrameworkType = Field(..., description="Framework type")
    industry: Optional[str] = Field(None, description="Target industry")
    region: Optional[str] = Field(None, description="Target region")
    tags: Optional[List[str]] = Field(None, description="Framework tags")
    created_by: uuid.UUID = Field(..., description="Creator user ID")
    organization_id: uuid.UUID = Field(..., description="Organization ID")
    is_public: bool = Field(..., description="Whether framework is public")
    is_active: bool = Field(..., description="Whether framework is active")
    controls_count: Optional[int] = Field(None, description="Number of controls in framework")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


# Control Schemas
class ComplianceControlCreate(BaseModel):
    """Schema for creating a new compliance control"""
    control_id: str = Field(..., description="Control identifier", min_length=1, max_length=100)
    title: str = Field(..., description="Control title", min_length=1, max_length=500)
    description: str = Field(..., description="Control description")
    category: str = Field(..., description="Control category", max_length=100)
    subcategory: Optional[str] = Field(None, description="Control subcategory", max_length=100)
    control_type: ControlType = Field(ControlType.AUTOMATED, description="Control type")
    severity: str = Field("medium", description="Control severity", pattern="^(critical|high|medium|low)$")
    risk_rating: Optional[int] = Field(None, description="Risk rating (1-10)", ge=1, le=10)
    compliance_weight: int = Field(1, description="Weight in compliance score", ge=1, le=10)
    implementation_guidance: Optional[str] = Field(None, description="Implementation guidance")
    remediation_steps: Optional[str] = Field(None, description="Remediation steps")
    remediation_cost: Optional[str] = Field(None, description="Remediation cost", pattern="^(low|medium|high)$")
    remediation_effort: Optional[str] = Field(None, description="Remediation effort")
    check_script: Optional[str] = Field(None, description="Automated check script")
    check_parameters: Optional[Dict[str, Any]] = Field(None, description="Check parameters")
    resource_types: Optional[List[str]] = Field(None, description="Target resource types")
    references: Optional[List[str]] = Field(None, description="Reference URLs/documents")
    tags: Optional[List[str]] = Field(None, description="Control tags")
    order_index: int = Field(0, description="Order within framework")


class ComplianceControlUpdate(BaseModel):
    """Schema for updating a compliance control"""
    title: Optional[str] = Field(None, description="Control title", min_length=1, max_length=500)
    description: Optional[str] = Field(None, description="Control description")
    category: Optional[str] = Field(None, description="Control category", max_length=100)
    subcategory: Optional[str] = Field(None, description="Control subcategory", max_length=100)
    control_type: Optional[ControlType] = Field(None, description="Control type")
    severity: Optional[str] = Field(None, description="Control severity", pattern="^(critical|high|medium|low)$")
    risk_rating: Optional[int] = Field(None, description="Risk rating (1-10)", ge=1, le=10)
    compliance_weight: Optional[int] = Field(None, description="Weight in compliance score", ge=1, le=10)
    implementation_guidance: Optional[str] = Field(None, description="Implementation guidance")
    remediation_steps: Optional[str] = Field(None, description="Remediation steps")
    remediation_cost: Optional[str] = Field(None, description="Remediation cost", pattern="^(low|medium|high)$")
    remediation_effort: Optional[str] = Field(None, description="Remediation effort")
    check_script: Optional[str] = Field(None, description="Automated check script")
    check_parameters: Optional[Dict[str, Any]] = Field(None, description="Check parameters")
    resource_types: Optional[List[str]] = Field(None, description="Target resource types")
    references: Optional[List[str]] = Field(None, description="Reference URLs/documents")
    tags: Optional[List[str]] = Field(None, description="Control tags")
    order_index: Optional[int] = Field(None, description="Order within framework")
    is_active: Optional[bool] = Field(None, description="Whether control is active")


class ComplianceControlResponse(BaseModel):
    """Schema for compliance control response"""
    id: uuid.UUID = Field(..., description="Control unique identifier")
    framework_id: uuid.UUID = Field(..., description="Framework ID")
    control_id: str = Field(..., description="Control identifier")
    title: str = Field(..., description="Control title")
    description: str = Field(..., description="Control description")
    category: str = Field(..., description="Control category")
    subcategory: Optional[str] = Field(None, description="Control subcategory")
    control_type: ControlType = Field(..., description="Control type")
    severity: str = Field(..., description="Control severity")
    risk_rating: Optional[int] = Field(None, description="Risk rating (1-10)")
    compliance_weight: int = Field(..., description="Weight in compliance score")
    implementation_guidance: Optional[str] = Field(None, description="Implementation guidance")
    remediation_steps: Optional[str] = Field(None, description="Remediation steps")
    remediation_cost: Optional[str] = Field(None, description="Remediation cost")
    remediation_effort: Optional[str] = Field(None, description="Remediation effort")
    check_script: Optional[str] = Field(None, description="Automated check script")
    check_parameters: Optional[Dict[str, Any]] = Field(None, description="Check parameters")
    resource_types: Optional[List[str]] = Field(None, description="Target resource types")
    references: Optional[List[str]] = Field(None, description="Reference URLs/documents")
    tags: Optional[List[str]] = Field(None, description="Control tags")
    is_active: bool = Field(..., description="Whether control is active")
    order_index: int = Field(..., description="Order within framework")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


# Template Schemas
class CustomScanTemplateCreate(BaseModel):
    """Schema for creating a custom scan template"""
    name: str = Field(..., description="Template name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Template description")
    framework_id: uuid.UUID = Field(..., description="Framework ID")
    selected_controls: List[str] = Field(..., description="Selected control IDs")
    scan_config: Optional[Dict[str, Any]] = Field(None, description="Additional scan configuration")
    is_public: bool = Field(False, description="Whether template is public")


class CustomScanTemplateUpdate(BaseModel):
    """Schema for updating a custom scan template"""
    name: Optional[str] = Field(None, description="Template name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Template description")
    selected_controls: Optional[List[str]] = Field(None, description="Selected control IDs")
    scan_config: Optional[Dict[str, Any]] = Field(None, description="Additional scan configuration")
    is_public: Optional[bool] = Field(None, description="Whether template is public")


class CustomScanTemplateResponse(BaseModel):
    """Schema for custom scan template response"""
    id: uuid.UUID = Field(..., description="Template unique identifier")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    framework_id: uuid.UUID = Field(..., description="Framework ID")
    framework_name: Optional[str] = Field(None, description="Framework name")
    selected_controls: List[str] = Field(..., description="Selected control IDs")
    scan_config: Optional[Dict[str, Any]] = Field(None, description="Additional scan configuration")
    created_by: uuid.UUID = Field(..., description="Creator user ID")
    organization_id: uuid.UUID = Field(..., description="Organization ID")
    is_public: bool = Field(..., description="Whether template is public")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


# List Response Schemas
class ComplianceFrameworkListResponse(BaseModel):
    """Schema for framework list response"""
    frameworks: List[ComplianceFrameworkResponse] = Field(..., description="List of frameworks")
    total: int = Field(..., description="Total number of frameworks")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")


class ComplianceControlListResponse(BaseModel):
    """Schema for control list response"""
    controls: List[ComplianceControlResponse] = Field(..., description="List of controls")
    total: int = Field(..., description="Total number of controls")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")


class CustomScanTemplateListResponse(BaseModel):
    """Schema for template list response"""
    templates: List[CustomScanTemplateResponse] = Field(..., description="List of templates")
    total: int = Field(..., description="Total number of templates")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    has_next: bool = Field(..., description="Whether there are more pages")


# Bulk Operations
class BulkControlCreate(BaseModel):
    """Schema for bulk control creation"""
    framework_id: uuid.UUID = Field(..., description="Framework ID")
    controls: List[ComplianceControlCreate] = Field(..., description="List of controls to create")


class FrameworkImport(BaseModel):
    """Schema for importing a framework from external source"""
    source_type: str = Field(..., description="Source type (json, csv, xml)")
    source_data: str = Field(..., description="Source data content")
    framework_name: str = Field(..., description="Framework name")
    framework_display_name: str = Field(..., description="Framework display name")
    merge_strategy: str = Field("replace", description="Merge strategy (replace, append, update)")