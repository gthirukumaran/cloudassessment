"""
Report-related Pydantic schemas
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from app.models.report import ReportStatus, ReportType


class ReportCreate(BaseModel):
    """Report creation request schema"""
    name: str = Field(..., description="Report name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Report description")
    report_type: ReportType = Field(..., description="Type of report")
    scan_id: Optional[uuid.UUID] = Field(None, description="Associated scan identifier")
    report_config: Optional[Dict[str, Any]] = Field(None, description="Report configuration")
    template_id: Optional[str] = Field(None, description="Report template identifier")


class ReportResponse(BaseModel):
    """Report response schema"""
    id: uuid.UUID = Field(..., description="Report unique identifier")
    name: str = Field(..., description="Report name")
    description: Optional[str] = Field(None, description="Report description")
    report_type: ReportType = Field(..., description="Type of report")
    status: ReportStatus = Field(..., description="Report generation status")
    
    # Associated entities
    user_id: uuid.UUID = Field(..., description="User who created the report")
    scan_id: Optional[uuid.UUID] = Field(None, description="Associated scan identifier")
    organization_id: uuid.UUID = Field(..., description="Organization identifier")
    
    # Report configuration
    report_config: Optional[Dict[str, Any]] = Field(None, description="Report configuration")
    template_id: Optional[str] = Field(None, description="Report template identifier")
    
    # File information
    file_path: Optional[str] = Field(None, description="Report file path")
    file_size: Optional[int] = Field(None, description="Report file size in bytes")
    file_url: Optional[str] = Field(None, description="Report download URL")
    
    # Generation metadata
    generation_started_at: Optional[datetime] = Field(None, description="Generation start time")
    generation_completed_at: Optional[datetime] = Field(None, description="Generation completion time")
    generation_duration_ms: Optional[int] = Field(None, description="Generation duration in milliseconds")
    
    # Report statistics
    total_pages: Optional[int] = Field(None, description="Total number of pages")
    total_findings: int = Field(..., description="Total number of findings")
    critical_findings: int = Field(..., description="Number of critical findings")
    high_findings: int = Field(..., description="Number of high severity findings")
    medium_findings: int = Field(..., description="Number of medium severity findings")
    low_findings: int = Field(..., description="Number of low severity findings")
    
    # Timestamps
    created_at: datetime = Field(..., description="Report creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Report list response schema"""
    reports: List[ReportResponse] = Field(..., description="List of reports")
    total: int = Field(..., description="Total number of reports")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


class ReportTemplateResponse(BaseModel):
    """Report template response schema"""
    id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    report_type: ReportType = Field(..., description="Supported report type")
    is_default: bool = Field(..., description="Whether this is the default template")
    preview_url: Optional[str] = Field(None, description="Template preview URL")
    created_at: datetime = Field(..., description="Template creation time")


class ReportGenerationRequest(BaseModel):
    """Report generation request schema"""
    report_id: uuid.UUID = Field(..., description="Report identifier")
    force_regenerate: bool = Field(default=False, description="Force regeneration of existing report")


class ReportDownloadResponse(BaseModel):
    """Report download response schema"""
    download_url: str = Field(..., description="Report download URL")
    expires_at: datetime = Field(..., description="Download URL expiration time")
    file_size: int = Field(..., description="Report file size in bytes")
    content_type: str = Field(..., description="File content type")
