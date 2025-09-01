"""\nCompliance service for managing custom frameworks and controls\n"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import uuid
import json

from app.models.compliance import ComplianceFramework, ComplianceControl, CustomScanTemplate, FrameworkType, ControlType
from app.models.user import User
from app.schemas.compliance import (
    ComplianceFrameworkCreate, ComplianceFrameworkUpdate, ComplianceFrameworkResponse,
    ComplianceControlCreate, ComplianceControlUpdate, ComplianceControlResponse,
    CustomScanTemplateCreate, CustomScanTemplateUpdate, CustomScanTemplateResponse
)
from app.core.exceptions import ResourceNotFoundError, AuthorizationError, ValidationError


class ComplianceService:
    """Service for managing compliance frameworks and controls"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # Framework Management
    async def create_framework(self, framework_data: ComplianceFrameworkCreate, user: User) -> ComplianceFrameworkResponse:
        """Create a new compliance framework"""
        # Check if framework name already exists
        existing = self.db.query(ComplianceFramework).filter(
            and_(
                ComplianceFramework.name == framework_data.name,
                ComplianceFramework.organization_id == user.organization_id
            )
        ).first()
        
        if existing:
            raise ValidationError(f"Framework with name '{framework_data.name}' already exists")
        
        # Create new framework
        framework = ComplianceFramework(
            name=framework_data.name,
            display_name=framework_data.display_name,
            description=framework_data.description,
            version=framework_data.version,
            framework_type=framework_data.framework_type,
            industry=framework_data.industry,
            region=framework_data.region,
            tags=framework_data.tags,
            created_by=user.id,
            organization_id=user.organization_id,
            is_public=framework_data.is_public
        )
        
        self.db.add(framework)
        self.db.commit()
        self.db.refresh(framework)
        
        return ComplianceFrameworkResponse.from_orm(framework)
    
    async def get_framework(self, framework_id: uuid.UUID, user: User) -> ComplianceFrameworkResponse:
        """Get a specific framework"""
        framework = self.db.query(ComplianceFramework).filter(
            and_(
                ComplianceFramework.id == framework_id,
                ComplianceFramework.is_active == True,
                # User can access if it's their org's framework or if it's public
                (ComplianceFramework.organization_id == user.organization_id) |
                (ComplianceFramework.is_public == True)
            )
        ).first()
        
        if not framework:
            raise ResourceNotFoundError("Framework not found")
        
        # Add controls count
        controls_count = self.db.query(func.count(ComplianceControl.id)).filter(
            and_(
                ComplianceControl.framework_id == framework_id,
                ComplianceControl.is_active == True
            )
        ).scalar()
        
        response = ComplianceFrameworkResponse.from_orm(framework)
        response.controls_count = controls_count
        return response
    
    async def list_frameworks(self, user: User, page: int = 1, per_page: int = 20, 
                            framework_type: Optional[FrameworkType] = None,
                            industry: Optional[str] = None) -> Tuple[List[ComplianceFrameworkResponse], int]:
        """List frameworks accessible to the user"""
        query = self.db.query(ComplianceFramework).filter(
            and_(
                ComplianceFramework.is_active == True,
                # User can access if it's their org's framework or if it's public
                (ComplianceFramework.organization_id == user.organization_id) |
                (ComplianceFramework.is_public == True)
            )
        )
        
        # Apply filters
        if framework_type:
            query = query.filter(ComplianceFramework.framework_type == framework_type)
        if industry:
            query = query.filter(ComplianceFramework.industry == industry)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        frameworks = query.order_by(desc(ComplianceFramework.created_at)).\
                          offset((page - 1) * per_page).\
                          limit(per_page).all()
        
        # Add controls count for each framework
        framework_responses = []
        for framework in frameworks:
            controls_count = self.db.query(func.count(ComplianceControl.id)).filter(
                and_(
                    ComplianceControl.framework_id == framework.id,
                    ComplianceControl.is_active == True
                )
            ).scalar()
            
            response = ComplianceFrameworkResponse.from_orm(framework)
            response.controls_count = controls_count
            framework_responses.append(response)
        
        return framework_responses, total
    
    async def update_framework(self, framework_id: uuid.UUID, framework_data: ComplianceFrameworkUpdate, 
                             user: User) -> ComplianceFrameworkResponse:
        """Update a framework"""
        framework = self.db.query(ComplianceFramework).filter(
            and_(
                ComplianceFramework.id == framework_id,
                ComplianceFramework.organization_id == user.organization_id,
                ComplianceFramework.is_active == True
            )
        ).first()
        
        if not framework:
            raise ResourceNotFoundError("Framework not found or access denied")
        
        # Update fields
        update_data = framework_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(framework, field, value)
        
        self.db.commit()
        self.db.refresh(framework)
        
        return ComplianceFrameworkResponse.from_orm(framework)
    
    async def delete_framework(self, framework_id: uuid.UUID, user: User) -> bool:
        """Soft delete a framework"""
        framework = self.db.query(ComplianceFramework).filter(
            and_(
                ComplianceFramework.id == framework_id,
                ComplianceFramework.organization_id == user.organization_id,
                ComplianceFramework.is_active == True
            )
        ).first()
        
        if not framework:
            raise ResourceNotFoundError("Framework not found or access denied")
        
        # Soft delete framework and its controls
        framework.is_active = False
        self.db.query(ComplianceControl).filter(
            ComplianceControl.framework_id == framework_id
        ).update({ComplianceControl.is_active: False})
        
        self.db.commit()
        return True
    
    # Control Management
    async def create_control(self, framework_id: uuid.UUID, control_data: ComplianceControlCreate, 
                           user: User) -> ComplianceControlResponse:
        """Create a new control in a framework"""
        # Verify framework access
        framework = self.db.query(ComplianceFramework).filter(
            and_(
                ComplianceFramework.id == framework_id,
                ComplianceFramework.organization_id == user.organization_id,
                ComplianceFramework.is_active == True
            )
        ).first()
        
        if not framework:
            raise ResourceNotFoundError("Framework not found or access denied")
        
        # Check if control ID already exists in this framework
        existing = self.db.query(ComplianceControl).filter(
            and_(
                ComplianceControl.framework_id == framework_id,
                ComplianceControl.control_id == control_data.control_id,
                ComplianceControl.is_active == True
            )
        ).first()
        
        if existing:
            raise ValidationError(f"Control with ID '{control_data.control_id}' already exists in this framework")
        
        # Create new control
        control = ComplianceControl(
            framework_id=framework_id,
            **control_data.dict()
        )
        
        self.db.add(control)
        self.db.commit()
        self.db.refresh(control)
        
        return ComplianceControlResponse.from_orm(control)
    
    async def get_control(self, control_id: uuid.UUID, user: User) -> ComplianceControlResponse:
        """Get a specific control"""
        control = self.db.query(ComplianceControl).join(ComplianceFramework).filter(
            and_(
                ComplianceControl.id == control_id,
                ComplianceControl.is_active == True,
                ComplianceFramework.is_active == True,
                # User can access if it's their org's framework or if it's public
                (ComplianceFramework.organization_id == user.organization_id) |
                (ComplianceFramework.is_public == True)
            )
        ).first()
        
        if not control:
            raise ResourceNotFoundError("Control not found")
        
        return ComplianceControlResponse.from_orm(control)
    
    async def list_controls(self, framework_id: uuid.UUID, user: User, page: int = 1, per_page: int = 50,
                          category: Optional[str] = None, severity: Optional[str] = None) -> Tuple[List[ComplianceControlResponse], int]:
        """List controls in a framework"""
        # Verify framework access
        framework = self.db.query(ComplianceFramework).filter(
            and_(
                ComplianceFramework.id == framework_id,
                ComplianceFramework.is_active == True,
                # User can access if it's their org's framework or if it's public
                (ComplianceFramework.organization_id == user.organization_id) |
                (ComplianceFramework.is_public == True)
            )
        ).first()
        
        if not framework:
            raise ResourceNotFoundError("Framework not found or access denied")
        
        query = self.db.query(ComplianceControl).filter(
            and_(
                ComplianceControl.framework_id == framework_id,
                ComplianceControl.is_active == True
            )
        )
        
        # Apply filters
        if category:
            query = query.filter(ComplianceControl.category == category)
        if severity:
            query = query.filter(ComplianceControl.severity == severity)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        controls = query.order_by(ComplianceControl.order_index, ComplianceControl.control_id).\
                        offset((page - 1) * per_page).\
                        limit(per_page).all()
        
        return [ComplianceControlResponse.from_orm(control) for control in controls], total
    
    async def update_control(self, control_id: uuid.UUID, control_data: ComplianceControlUpdate, 
                           user: User) -> ComplianceControlResponse:
        """Update a control"""
        control = self.db.query(ComplianceControl).join(ComplianceFramework).filter(
            and_(
                ComplianceControl.id == control_id,
                ComplianceControl.is_active == True,
                ComplianceFramework.organization_id == user.organization_id,
                ComplianceFramework.is_active == True
            )
        ).first()
        
        if not control:
            raise ResourceNotFoundError("Control not found or access denied")
        
        # Update fields
        update_data = control_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(control, field, value)
        
        self.db.commit()
        self.db.refresh(control)
        
        return ComplianceControlResponse.from_orm(control)
    
    async def delete_control(self, control_id: uuid.UUID, user: User) -> bool:
        """Soft delete a control"""
        control = self.db.query(ComplianceControl).join(ComplianceFramework).filter(
            and_(
                ComplianceControl.id == control_id,
                ComplianceControl.is_active == True,
                ComplianceFramework.organization_id == user.organization_id,
                ComplianceFramework.is_active == True
            )
        ).first()
        
        if not control:
            raise ResourceNotFoundError("Control not found or access denied")
        
        control.is_active = False
        self.db.commit()
        return True
    
    # Bulk Operations
    async def create_bulk_controls(self, framework_id: uuid.UUID, controls_data: List[ComplianceControlCreate], 
                                 user: User) -> List[ComplianceControlResponse]:
        """Create multiple controls in a framework"""
        # Verify framework access
        framework = self.db.query(ComplianceFramework).filter(
            and_(
                ComplianceFramework.id == framework_id,
                ComplianceFramework.organization_id == user.organization_id,
                ComplianceFramework.is_active == True
            )
        ).first()
        
        if not framework:
            raise ResourceNotFoundError("Framework not found or access denied")
        
        # Check for duplicate control IDs
        control_ids = [control.control_id for control in controls_data]
        existing_controls = self.db.query(ComplianceControl.control_id).filter(
            and_(
                ComplianceControl.framework_id == framework_id,
                ComplianceControl.control_id.in_(control_ids),
                ComplianceControl.is_active == True
            )
        ).all()
        
        if existing_controls:
            existing_ids = [control.control_id for control in existing_controls]
            raise ValidationError(f"Controls with IDs {existing_ids} already exist in this framework")
        
        # Create controls
        created_controls = []
        for control_data in controls_data:
            control = ComplianceControl(
                framework_id=framework_id,
                **control_data.dict()
            )
            self.db.add(control)
            created_controls.append(control)
        
        self.db.commit()
        
        # Refresh and return
        for control in created_controls:
            self.db.refresh(control)
        
        return [ComplianceControlResponse.from_orm(control) for control in created_controls]
    
    # Template Management
    async def create_scan_template(self, template_data: CustomScanTemplateCreate, 
                                 user: User) -> CustomScanTemplateResponse:
        """Create a custom scan template"""
        # Verify framework access
        framework = self.db.query(ComplianceFramework).filter(
            and_(
                ComplianceFramework.id == template_data.framework_id,
                ComplianceFramework.is_active == True,
                # User can access if it's their org's framework or if it's public
                (ComplianceFramework.organization_id == user.organization_id) |
                (ComplianceFramework.is_public == True)
            )
        ).first()
        
        if not framework:
            raise ResourceNotFoundError("Framework not found or access denied")
        
        # Verify selected controls exist
        existing_controls = self.db.query(ComplianceControl.control_id).filter(
            and_(
                ComplianceControl.framework_id == template_data.framework_id,
                ComplianceControl.control_id.in_(template_data.selected_controls),
                ComplianceControl.is_active == True
            )
        ).all()
        
        existing_control_ids = [control.control_id for control in existing_controls]
        invalid_controls = set(template_data.selected_controls) - set(existing_control_ids)
        
        if invalid_controls:
            raise ValidationError(f"Invalid control IDs: {list(invalid_controls)}")
        
        # Create template
        template = CustomScanTemplate(
            name=template_data.name,
            description=template_data.description,
            framework_id=template_data.framework_id,
            selected_controls=template_data.selected_controls,
            scan_config=template_data.scan_config,
            created_by=user.id,
            organization_id=user.organization_id,
            is_public=template_data.is_public
        )
        
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        
        response = CustomScanTemplateResponse.from_orm(template)
        response.framework_name = framework.display_name
        return response
    
    # Utility Methods
    async def get_framework_statistics(self, framework_id: uuid.UUID, user: User) -> Dict[str, Any]:
        """Get statistics for a framework"""
        # Verify framework access
        framework = self.db.query(ComplianceFramework).filter(
            and_(
                ComplianceFramework.id == framework_id,
                ComplianceFramework.is_active == True,
                # User can access if it's their org's framework or if it's public
                (ComplianceFramework.organization_id == user.organization_id) |
                (ComplianceFramework.is_public == True)
            )
        ).first()
        
        if not framework:
            raise ResourceNotFoundError("Framework not found or access denied")
        
        # Get control statistics
        controls_query = self.db.query(ComplianceControl).filter(
            and_(
                ComplianceControl.framework_id == framework_id,
                ComplianceControl.is_active == True
            )
        )
        
        total_controls = controls_query.count()
        
        # Count by severity
        severity_counts = {}
        for severity in ['critical', 'high', 'medium', 'low']:
            count = controls_query.filter(ComplianceControl.severity == severity).count()
            severity_counts[severity] = count
        
        # Count by category
        category_counts = self.db.query(
            ComplianceControl.category,
            func.count(ComplianceControl.id)
        ).filter(
            and_(
                ComplianceControl.framework_id == framework_id,
                ComplianceControl.is_active == True
            )
        ).group_by(ComplianceControl.category).all()
        
        # Count by control type
        type_counts = self.db.query(
            ComplianceControl.control_type,
            func.count(ComplianceControl.id)
        ).filter(
            and_(
                ComplianceControl.framework_id == framework_id,
                ComplianceControl.is_active == True
            )
        ).group_by(ComplianceControl.control_type).all()
        
        return {
            "framework_id": str(framework_id),
            "framework_name": framework.display_name,
            "total_controls": total_controls,
            "severity_distribution": severity_counts,
            "category_distribution": {category: count for category, count in category_counts},
            "type_distribution": {str(control_type): count for control_type, count in type_counts},
            "created_at": framework.created_at.isoformat(),
            "updated_at": framework.updated_at.isoformat()
        }