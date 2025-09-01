"""
Scan endpoints for security assessment management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.scan import ScanStatus
from app.schemas.scan import ScanCreate, ScanUpdate, ScanResponse, ScanListResponse, ScanStatsResponse
from app.services.scan_service import ScanService
from app.core.dependencies import get_current_active_user, get_scan_service

router = APIRouter()


@router.post("/", response_model=ScanResponse)
async def create_scan(
    scan_data: ScanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    scan_service: ScanService = Depends(get_scan_service)
):
    """Create a new security scan"""
    scan = scan_service.create_scan(db, scan_data, current_user)
    return ScanResponse.from_orm(scan)


@router.get("/", response_model=ScanListResponse)
async def get_scans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[ScanStatus] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    scan_service: ScanService = Depends(get_scan_service)
):
    """Get user's scans"""
    scans = scan_service.get_user_scans(db, current_user, skip, limit, status)
    return ScanListResponse(
        scans=[ScanResponse.from_orm(scan) for scan in scans],
        total=len(scans),
        skip=skip,
        limit=limit
    )


@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    scan_service: ScanService = Depends(get_scan_service)
):
    """Get a specific scan"""
    scan = scan_service.get_scan(db, scan_id, current_user)
    return ScanResponse.from_orm(scan)


@router.put("/{scan_id}", response_model=ScanResponse)
async def update_scan(
    scan_id: str,
    scan_data: ScanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    scan_service: ScanService = Depends(get_scan_service)
):
    """Update a scan"""
    scan = scan_service.update_scan(db, scan_id, scan_data, current_user)
    return ScanResponse.from_orm(scan)


@router.delete("/{scan_id}")
async def delete_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    scan_service: ScanService = Depends(get_scan_service)
):
    """Delete a scan"""
    scan_service.delete_scan(db, scan_id, current_user)
    return {"message": "Scan deleted successfully"}


@router.post("/{scan_id}/start", response_model=ScanResponse)
async def start_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    scan_service: ScanService = Depends(get_scan_service)
):
    """Start a scan"""
    scan = scan_service.start_scan(db, scan_id, current_user)
    return ScanResponse.from_orm(scan)


@router.get("/stats", response_model=ScanStatsResponse)
async def get_scan_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    scan_service: ScanService = Depends(get_scan_service)
):
    """Get scan statistics"""
    stats = scan_service.get_scan_stats(db, current_user)
    return ScanStatsResponse(**stats)
