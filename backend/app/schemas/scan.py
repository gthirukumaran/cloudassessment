"""
Scan-related Pydantic schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
from enum import Enum

from app.models.scan import ScanStatus, ScanType, SeverityLevel


class ScanCreate(BaseModel):
    """Scan creation request schema"""
    name: str = Field(..., description="Scan name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Scan description")
    scan_type: ScanType = Field(..., description="Type of cloud scan")
    scan_config: Optional[Dict[str, Any]] = Field(None, description="Scan configuration")
    target_resources: Optional[List[str]] = Field(None, description="Target resources to scan")


class ScanUpdate(BaseModel):
    """Scan update request schema"""
    name: Optional[str] = Field(None, description="Scan name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Scan description")
    scan_config: Optional[Dict[str, Any]] = Field(None, description="Scan configuration")
    target_resources: Optional[List[str]] = Field(None, description="Target resources to scan")


class ScanResponse(BaseModel):
    """Scan response schema"""
    id: uuid.UUID = Field(..., description="Scan unique identifier")
    name: str = Field(..., description="Scan name")
    description: Optional[str] = Field(None, description="Scan description")
    scan_type: ScanType = Field(..., description="Type of cloud scan")
    status: ScanStatus = Field(..., description="Scan status")
    user_id: uuid.UUID = Field(..., description="User who created the scan")
    organization_id: uuid.UUID = Field(..., description="Organization identifier")
    
    # Scan configuration
    scan_config: Optional[Dict[str, Any]] = Field(None, description="Scan configuration")
    target_resources: Optional[List[str]] = Field(None, description="Target resources")
    
    # Scan results
    total_findings: int = Field(..., description="Total number of findings")
    critical_findings: int = Field(..., description="Number of critical findings")
    high_findings: int = Field(..., description="Number of high severity findings")
    medium_findings: int = Field(..., description="Number of medium severity findings")
    low_findings: int = Field(..., description="Number of low severity findings")
    
    # Timestamps
    started_at: Optional[datetime] = Field(None, description="Scan start time")
    completed_at: Optional[datetime] = Field(None, description="Scan completion time")
    created_at: datetime = Field(..., description="Scan creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    class Config:
        from_attributes = True


class ScanListResponse(BaseModel):
    """Scan list response schema"""
    scans: List[ScanResponse] = Field(..., description="List of scans")
    total: int = Field(..., description="Total number of scans")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class FindingResponse(BaseModel):
    """Finding response schema"""
    id: uuid.UUID = Field(..., description="Finding unique identifier")
    scan_id: uuid.UUID = Field(..., description="Associated scan identifier")
    
    # Finding details
    title: str = Field(..., description="Finding title")
    description: str = Field(..., description="Finding description")
    severity: SeverityLevel = Field(..., description="Finding severity level")
    category: str = Field(..., description="Finding category")
    
    # Resource information
    resource_type: str = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource identifier")
    resource_name: str = Field(..., description="Resource name")
    
    # Technical details
    finding_type: str = Field(..., description="Type of finding")
    compliance_framework: Optional[str] = Field(None, description="Compliance framework")
    compliance_control: Optional[str] = Field(None, description="Compliance control")
    
    # Remediation
    remediation_steps: Optional[str] = Field(None, description="Remediation steps")
    remediation_cost: Optional[str] = Field(None, description="Remediation cost")
    remediation_effort: Optional[str] = Field(None, description="Remediation effort")
    
    # AI Analysis
    ai_analysis: Optional[str] = Field(None, description="AI analysis of the finding")
    ai_confidence: Optional[int] = Field(None, description="AI confidence score")
    
    # Status
    is_false_positive: bool = Field(..., description="Whether finding is false positive")
    is_resolved: bool = Field(..., description="Whether finding is resolved")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    resolved_by: Optional[uuid.UUID] = Field(None, description="User who resolved the finding")
    
    # Metadata
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw finding data")
    created_at: datetime = Field(..., description="Finding creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    class Config:
        from_attributes = True


class ScanResultResponse(BaseModel):
    """Scan result response schema"""
    id: uuid.UUID = Field(..., description="Result unique identifier")
    scan_id: uuid.UUID = Field(..., description="Associated scan identifier")
    
    # Result data
    resource_type: str = Field(..., description="Resource type")
    resource_id: str = Field(..., description="Resource identifier")
    resource_name: str = Field(..., description="Resource name")
    compliance_status: str = Field(..., description="Compliance status")
    risk_score: Optional[int] = Field(None, description="Risk score")
    
    # Detailed results
    findings_count: int = Field(..., description="Number of findings")
    compliance_checks: Optional[Dict[str, Any]] = Field(None, description="Compliance check results")
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Raw result data")
    
    created_at: datetime = Field(..., description="Result creation time")
    
    class Config:
        from_attributes = True


class ScanStatsResponse(BaseModel):
    """Scan statistics response schema"""
    total_scans: int = Field(..., description="Total number of scans")
    completed_scans: int = Field(..., description="Number of completed scans")
    running_scans: int = Field(..., description="Number of running scans")
    failed_scans: int = Field(..., description="Number of failed scans")
    
    total_findings: int = Field(..., description="Total number of findings")
    critical_findings: int = Field(..., description="Number of critical findings")
    high_findings: int = Field(..., description="Number of high severity findings")
    medium_findings: int = Field(..., description="Number of medium severity findings")
    low_findings: int = Field(..., description="Number of low severity findings")
    
    average_scan_duration: Optional[float] = Field(None, description="Average scan duration in minutes")
    compliance_rate: Optional[float] = Field(None, description="Overall compliance rate percentage")
