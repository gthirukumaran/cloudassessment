"""
Report endpoints for security assessment reports
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.report import ReportType
from app.schemas.report import (
    ReportCreate, ReportResponse, ReportListResponse, 
    ReportGenerationRequest, ReportTemplateResponse
)
from app.services.report_service import ReportService
from app.core.dependencies import get_current_active_user, get_report_service

router = APIRouter()


@router.post("/", response_model=ReportResponse)
async def create_report(
    report_data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Create a new report"""
    report = report_service.create_report(db, report_data, current_user)
    return ReportResponse.from_orm(report)


@router.get("/", response_model=ReportListResponse)
async def get_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    report_type: Optional[ReportType] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Get user's reports"""
    reports = report_service.get_user_reports(db, current_user, skip, limit, report_type)
    return ReportListResponse(
        reports=[ReportResponse.from_orm(report) for report in reports],
        total=len(reports),
        skip=skip,
        limit=limit
    )


@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Get a specific report"""
    report = report_service.get_report(db, report_id, current_user)
    return ReportResponse.from_orm(report)


@router.post("/{report_id}/generate")
async def generate_report(
    report_id: str,
    generation_data: ReportGenerationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Generate a report"""
    result = await report_service.generate_report(db, report_id, generation_data, current_user)
    return result


@router.get("/{report_id}/download")
async def download_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Get report download information"""
    download_info = report_service.download_report(db, report_id, current_user)
    return download_info


@router.delete("/{report_id}")
async def delete_report(
    report_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    report_service: ReportService = Depends(get_report_service)
):
    """Delete a report"""
    report_service.delete_report(db, report_id, current_user)
    return {"message": "Report deleted successfully"}


@router.get("/templates", response_model=List[ReportTemplateResponse])
async def get_report_templates(
    report_service: ReportService = Depends(get_report_service)
):
    """Get available report templates"""
    templates = report_service.get_report_templates()
    return [ReportTemplateResponse(**template) for template in templates]
