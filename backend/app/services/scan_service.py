"""
Scan service for handling security assessments
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.models.scan import Scan, ScanResult, Finding, ScanStatus, ScanType, SeverityLevel
from app.models.user import User
from app.schemas.scan import ScanCreate, ScanUpdate, ScanResponse, FindingResponse
from app.services.ai_service import AIService
from app.core.exceptions import ResourceNotFoundError, AuthorizationError


class ScanService:
    """Service for managing security scans"""
    
    def __init__(self):
        self.ai_service = AIService()
    
    def create_scan(self, db: Session, scan_data: ScanCreate, user: User) -> Scan:
        """Create a new security scan"""
        scan = Scan(
            user_id=user.id,
            organization_id=user.organization_id,
            name=scan_data.name,
            description=scan_data.description,
            scan_type=scan_data.scan_type,
            target_resources=scan_data.target_resources,
            scan_config=scan_data.scan_config,
            status=ScanStatus.PENDING
        )
        
        db.add(scan)
        db.commit()
        db.refresh(scan)
        
        return scan
    
    def get_scan(self, db: Session, scan_id: str, user: User) -> Scan:
        """Get a scan by ID"""
        scan = db.query(Scan).filter(
            and_(
                Scan.id == scan_id,
                Scan.user_id == user.id
            )
        ).first()
        
        if not scan:
            raise ResourceNotFoundError(f"Scan {scan_id} not found")
        
        return scan
    
    def get_user_scans(
        self, 
        db: Session, 
        user: User, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[ScanStatus] = None
    ) -> List[Scan]:
        """Get scans for a user"""
        query = db.query(Scan).filter(Scan.user_id == user.id)
        
        if status:
            query = query.filter(Scan.status == status)
        
        return query.order_by(desc(Scan.created_at)).offset(skip).limit(limit).all()
    
    def update_scan(self, db: Session, scan_id: str, scan_data: ScanUpdate, user: User) -> Scan:
        """Update a scan"""
        scan = self.get_scan(db, scan_id, user)
        
        for field, value in scan_data.dict(exclude_unset=True).items():
            setattr(scan, field, value)
        
        db.commit()
        db.refresh(scan)
        
        return scan
    
    def delete_scan(self, db: Session, scan_id: str, user: User) -> bool:
        """Delete a scan"""
        scan = self.get_scan(db, scan_id, user)
        
        if scan.status in [ScanStatus.RUNNING, ScanStatus.PENDING]:
            raise AuthorizationError("Cannot delete a scan that is running or pending")
        
        db.delete(scan)
        db.commit()
        
        return True
    
    def start_scan(self, db: Session, scan_id: str, user: User) -> Scan:
        """Start a security scan"""
        scan = self.get_scan(db, scan_id, user)
        
        if scan.status != ScanStatus.PENDING:
            raise AuthorizationError("Scan can only be started if it's in pending status")
        
        scan.status = ScanStatus.RUNNING
        scan.started_at = datetime.utcnow()
        
        db.commit()
        db.refresh(scan)
        
        # TODO: Trigger actual scan execution (background task)
        
        return scan
    
    def complete_scan(self, db: Session, scan_id: str, results: Dict[str, Any]) -> Scan:
        """Complete a scan with results"""
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        
        if not scan:
            raise ResourceNotFoundError(f"Scan {scan_id} not found")
        
        scan.status = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow()
        
        # Create scan result
        scan_result = ScanResult(
            scan_id=scan.id,
            summary=results.get("summary", ""),
            total_findings=results.get("total_findings", 0),
            critical_findings=results.get("critical_findings", 0),
            high_findings=results.get("high_findings", 0),
            medium_findings=results.get("medium_findings", 0),
            low_findings=results.get("low_findings", 0),
            scan_duration_seconds=results.get("duration_seconds", 0),
            raw_results=results.get("raw_results", {})
        )
        
        db.add(scan_result)
        db.commit()
        db.refresh(scan_result)
        
        # Process findings
        findings = results.get("findings", [])
        for finding_data in findings:
            finding = Finding(
                scan_id=scan.id,
                title=finding_data.get("title", ""),
                description=finding_data.get("description", ""),
                severity=SeverityLevel(finding_data.get("severity", "low")),
                category=finding_data.get("category", ""),
                resource_id=finding_data.get("resource_id", ""),
                resource_type=finding_data.get("resource_type", ""),
                location=finding_data.get("location", ""),
                recommendation=finding_data.get("recommendation", ""),
                raw_data=finding_data.get("raw_data", {})
            )
            db.add(finding)
        
        db.commit()
        db.refresh(scan)
        
        return scan
    
    def get_scan_findings(self, db: Session, scan_id: str, user: User) -> List[Finding]:
        """Get findings for a scan"""
        scan = self.get_scan(db, scan_id, user)
        
        return db.query(Finding).filter(Finding.scan_id == scan.id).all()
    
    def analyze_finding(self, db: Session, finding_id: str, user: User) -> Dict[str, Any]:
        """Analyze a finding with AI"""
        finding = db.query(Finding).filter(Finding.id == finding_id).first()
        
        if not finding:
            raise ResourceNotFoundError(f"Finding {finding_id} not found")
        
        # Get scan context
        scan = db.query(Scan).filter(Scan.id == finding.scan_id).first()
        
        # Analyze with AI
        analysis = self.ai_service.analyze_finding(finding, {
            "scan_type": scan.scan_type.value if scan else None,
            "target_resources": scan.target_resources if scan else None
        })
        
        return analysis
    
    def get_scan_stats(self, db: Session, user: User) -> Dict[str, Any]:
        """Get scan statistics for a user"""
        total_scans = db.query(Scan).filter(Scan.user_id == user.id).count()
        completed_scans = db.query(Scan).filter(
            and_(Scan.user_id == user.id, Scan.status == ScanStatus.COMPLETED)
        ).count()
        running_scans = db.query(Scan).filter(
            and_(Scan.user_id == user.id, Scan.status == ScanStatus.RUNNING)
        ).count()
        
        # Get finding statistics
        scan_ids = [scan.id for scan in db.query(Scan).filter(Scan.user_id == user.id).all()]
        total_findings = db.query(Finding).filter(Finding.scan_id.in_(scan_ids)).count()
        critical_findings = db.query(Finding).filter(
            and_(Finding.scan_id.in_(scan_ids), Finding.severity == SeverityLevel.CRITICAL)
        ).count()
        high_findings = db.query(Finding).filter(
            and_(Finding.scan_id.in_(scan_ids), Finding.severity == SeverityLevel.HIGH)
        ).count()
        
        return {
            "total_scans": total_scans,
            "completed_scans": completed_scans,
            "running_scans": running_scans,
            "total_findings": total_findings,
            "critical_findings": critical_findings,
            "high_findings": high_findings
        }
