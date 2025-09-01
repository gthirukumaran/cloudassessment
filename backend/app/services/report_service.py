"""
Report service for generating security assessment reports
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
import uuid

from app.models.report import Report, ReportStatus, ReportType
from app.models.scan import Scan, Finding
from app.models.user import User
from app.schemas.report import ReportCreate, ReportGenerationRequest
from app.core.exceptions import ResourceNotFoundError, AuthorizationError


class ReportService:
    """Service for managing security assessment reports"""
    
    def __init__(self):
        pass
    
    def create_report(self, db: Session, report_data: ReportCreate, user: User) -> Report:
        """Create a new report"""
        report = Report(
            user_id=user.id,
            organization_id=user.organization_id,
            report_type=report_data.report_type,
            scan_id=report_data.scan_id,
            title=report_data.title,
            description=report_data.description,
            status=ReportStatus.PENDING
        )
        
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return report
    
    def get_report(self, db: Session, report_id: str, user: User) -> Report:
        """Get a report by ID"""
        report = db.query(Report).filter(
            and_(
                Report.id == report_id,
                Report.user_id == user.id
            )
        ).first()
        
        if not report:
            raise ResourceNotFoundError(f"Report {report_id} not found")
        
        return report
    
    def get_user_reports(
        self, 
        db: Session, 
        user: User, 
        skip: int = 0, 
        limit: int = 100,
        report_type: Optional[ReportType] = None
    ) -> List[Report]:
        """Get reports for a user"""
        query = db.query(Report).filter(Report.user_id == user.id)
        
        if report_type:
            query = query.filter(Report.report_type == report_type)
        
        return query.order_by(desc(Report.created_at)).offset(skip).limit(limit).all()
    
    async def generate_report(
        self, 
        db: Session, 
        report_id: str, 
        generation_data: ReportGenerationRequest, 
        user: User
    ) -> Dict[str, Any]:
        """Generate a security assessment report"""
        report = self.get_report(db, report_id, user)
        
        if report.status != ReportStatus.PENDING:
            raise AuthorizationError("Report can only be generated if it's in pending status")
        
        # Update status to generating
        report.status = ReportStatus.GENERATING
        report.generation_started_at = datetime.utcnow()
        db.commit()
        
        try:
            # Get scan data if report is scan-based
            scan_data = None
            findings = []
            
            if report.scan_id:
                scan = db.query(Scan).filter(Scan.id == report.scan_id).first()
                if scan:
                    scan_data = {
                        "id": str(scan.id),
                        "name": scan.name,
                        "description": scan.description,
                        "scan_type": scan.scan_type.value,
                        "status": scan.status.value,
                        "created_at": scan.created_at.isoformat(),
                        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None
                    }
                    
                    # Get findings
                    findings = db.query(Finding).filter(Finding.scan_id == scan.id).all()
            
            # Generate report content based on type
            if report.report_type == ReportType.CIS_COMPLIANCE:
                report_content = await self._generate_cis_report(
                    scan_data, findings, generation_data.template_options
                )
            elif report.report_type == ReportType.EXECUTIVE_SUMMARY:
                report_content = await self._generate_executive_summary(
                    scan_data, findings, generation_data.template_options
                )
            else:
                report_content = await self._generate_detailed_report(
                    scan_data, findings, generation_data.template_options
                )
            
            # Update report with generated content
            report.content = report_content
            report.file_path = f"reports/{report.id}.pdf"
            report.file_size_bytes = len(str(report_content).encode('utf-8'))
            report.status = ReportStatus.COMPLETED
            report.generation_completed_at = datetime.utcnow()
            
            db.commit()
            db.refresh(report)
            
            return {
                "report_id": str(report.id),
                "status": report.status.value,
                "file_path": report.file_path,
                "file_size_bytes": report.file_size_bytes
            }
            
        except Exception as e:
            # Update status to failed
            report.status = ReportStatus.FAILED
            report.error_message = str(e)
            db.commit()
            
            raise e
    
    async def _generate_cis_report(
        self, 
        scan_data: Optional[Dict[str, Any]], 
        findings: List[Finding], 
        template_options: Optional[Dict[str, Any]]
    ) -> str:
        """Generate CIS compliance report"""
        # TODO: Implement CIS report generation
        return f"CIS Compliance Report for {scan_data['name'] if scan_data else 'Security Assessment'}"
    
    async def _generate_executive_summary(
        self, 
        scan_data: Optional[Dict[str, Any]], 
        findings: List[Finding], 
        template_options: Optional[Dict[str, Any]]
    ) -> str:
        """Generate executive summary report"""
        # TODO: Implement executive summary generation
        return f"Executive Summary for {scan_data['name'] if scan_data else 'Security Assessment'}"
    
    async def _generate_detailed_report(
        self, 
        scan_data: Optional[Dict[str, Any]], 
        findings: List[Finding], 
        template_options: Optional[Dict[str, Any]]
    ) -> str:
        """Generate detailed technical report"""
        # TODO: Implement detailed report generation
        return f"Detailed Report for {scan_data['name'] if scan_data else 'Security Assessment'}"
    
    def download_report(self, db: Session, report_id: str, user: User) -> Dict[str, Any]:
        """Get report download information"""
        report = self.get_report(db, report_id, user)
        
        if report.status != ReportStatus.COMPLETED:
            raise AuthorizationError("Report is not ready for download")
        
        return {
            "report_id": str(report.id),
            "file_path": report.file_path,
            "file_size_bytes": report.file_size_bytes,
            "content_type": "application/pdf",
            "filename": f"{report.title.replace(' ', '_')}.pdf"
        }
    
    def delete_report(self, db: Session, report_id: str, user: User) -> bool:
        """Delete a report"""
        report = self.get_report(db, report_id, user)
        
        if report.status == ReportStatus.GENERATING:
            raise AuthorizationError("Cannot delete a report that is being generated")
        
        db.delete(report)
        db.commit()
        
        return True
    
    def get_report_templates(self) -> List[Dict[str, Any]]:
        """Get available report templates"""
        return [
            {
                "type": ReportType.CIS_COMPLIANCE.value,
                "name": "CIS Compliance Report",
                "description": "Comprehensive compliance report following CIS benchmarks",
                "features": ["Compliance scoring", "Remediation steps", "Executive summary"]
            },
            {
                "type": ReportType.EXECUTIVE_SUMMARY.value,
                "name": "Executive Summary",
                "description": "High-level summary for executive stakeholders",
                "features": ["Risk overview", "Key findings", "Business impact"]
            },
            {
                "type": ReportType.DETAILED_TECHNICAL.value,
                "name": "Detailed Technical Report",
                "description": "Comprehensive technical analysis and recommendations",
                "features": ["Technical details", "Code examples", "Detailed remediation"]
            }
        ]
