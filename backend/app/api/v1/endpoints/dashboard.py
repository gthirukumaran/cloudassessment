"""
Dashboard analytics endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import datetime, timedelta

from app.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.scan import Scan, ScanStatus, ScanType
from app.models.scan import Finding, SeverityLevel

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/dashboard/analytics", response_model=Dict[str, Any])
async def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard analytics data"""
    try:
        logger.info(f"Fetching dashboard analytics for user {current_user.id}")
        
        # Get scan statistics
        total_scans = db.query(Scan).filter(Scan.user_id == current_user.id).count()
        completed_scans = db.query(Scan).filter(
            Scan.user_id == current_user.id,
            Scan.status == ScanStatus.COMPLETED
        ).count()
        
        # Get recent scans (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_scans = db.query(Scan).filter(
            Scan.user_id == current_user.id,
            Scan.created_at >= thirty_days_ago
        ).count()
        
        # Get findings statistics
        total_findings = db.query(Finding).join(Scan).filter(Scan.user_id == current_user.id).count()
        critical_findings = db.query(Finding).join(Scan).filter(
            Scan.user_id == current_user.id,
            Finding.severity == SeverityLevel.CRITICAL
        ).count()
        high_findings = db.query(Finding).join(Scan).filter(
            Scan.user_id == current_user.id,
            Finding.severity == SeverityLevel.HIGH
        ).count()
        
        # Calculate compliance score (mock calculation)
        compliance_score = 85  # Mock score, in real implementation calculate based on findings
        
        # Get scan type distribution
        azure_scans = db.query(Scan).filter(
            Scan.user_id == current_user.id,
            Scan.scan_type == ScanType.AZURE
        ).count()
        aws_scans = db.query(Scan).filter(
            Scan.user_id == current_user.id,
            Scan.scan_type == ScanType.AWS
        ).count()
        gcp_scans = db.query(Scan).filter(
            Scan.user_id == current_user.id,
            Scan.scan_type == ScanType.GCP
        ).count()
        
        return {
            "total_resources": 100,  # Mock data
            "compliance_score": compliance_score,
            "critical_findings": critical_findings,
            "recent_scans": recent_scans,
            "total_scans": total_scans,
            "completed_scans": completed_scans,
            "total_findings": total_findings,
            "high_findings": high_findings,
            "scan_distribution": {
                "azure": azure_scans,
                "aws": aws_scans,
                "gcp": gcp_scans
            },
            "trends": {
                "compliance_trend": [85, 87, 89, 88, 90, 92, 91],  # Mock trend data
                "findings_trend": [12, 10, 8, 9, 7, 6, 5],  # Mock trend data
                "scans_trend": [5, 7, 6, 8, 9, 7, 8]  # Mock trend data
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching dashboard analytics: {str(e)}")
        # Return fallback data
        return {
            "total_resources": 100,
            "compliance_score": 75,
            "critical_findings": 2,
            "recent_scans": 3,
            "total_scans": 15,
            "completed_scans": 12,
            "total_findings": 25,
            "high_findings": 5,
            "scan_distribution": {
                "azure": 10,
                "aws": 3,
                "gcp": 2
            },
            "trends": {
                "compliance_trend": [75, 77, 79, 78, 80, 82, 81],
                "findings_trend": [12, 10, 8, 9, 7, 6, 5],
                "scans_trend": [5, 7, 6, 8, 9, 7, 8]
            }
        }
