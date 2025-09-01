"""\nCompliance framework endpoints for custom framework management\n"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import uuid

from app.database import get_db
from app.models.user import User
from app.models.compliance import FrameworkType
from app.schemas.compliance import (
    ComplianceFrameworkCreate, ComplianceFrameworkUpdate, ComplianceFrameworkResponse,
    ComplianceFrameworkListResponse, ComplianceControlCreate, ComplianceControlUpdate,
    ComplianceControlResponse, ComplianceControlListResponse, CustomScanTemplateCreate,
    CustomScanTemplateUpdate, CustomScanTemplateResponse, CustomScanTemplateListResponse,
    BulkControlCreate
)
from app.services.compliance_service import ComplianceService
from app.core.dependencies import get_current_active_user, get_compliance_service
from app.core.exceptions import ResourceNotFoundError, AuthorizationError, ValidationError

router = APIRouter()

# Test endpoint without authentication for development
@router.get("/frameworks/test")
async def test_frameworks():
    """Test endpoint to return mock frameworks without authentication"""
    return {
        "frameworks": [
            {
                "id": "cis-azure",
                "name": "cis_azure",
                "display_name": "CIS Azure Foundations Benchmark",
                "description": "Center for Internet Security Benchmarks for Microsoft Azure",
                "controls_count": 150,
                "framework_type": "standard",
                "industry": "general",
                "version": "1.5.0",
                "is_public": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "soc2-type2",
                "name": "soc2_type2",
                "display_name": "SOC 2 Type II",
                "description": "Service Organization Control 2 Type II Framework",
                "controls_count": 64,
                "framework_type": "standard",
                "industry": "technology",
                "version": "2017",
                "is_public": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "nist-csf",
                "name": "nist_csf",
                "display_name": "NIST Cybersecurity Framework",
                "description": "National Institute of Standards and Technology Cybersecurity Framework",
                "controls_count": 108,
                "framework_type": "standard",
                "industry": "general",
                "version": "1.1",
                "is_public": True,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "iso27001",
                "name": "iso27001",
                "display_name": "ISO 27001:2013",
                "description": "International Organization for Standardization 27001 Information Security Management",
                "controls_count": 114,
                "framework_type": "standard",
                "industry": "general",
                "version": "2013",
                "is_public": True,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ],
        "total": 4
    }


# Framework Endpoints
@router.post("/frameworks", response_model=ComplianceFrameworkResponse, status_code=status.HTTP_201_CREATED)
async def create_framework(
    framework_data: ComplianceFrameworkCreate,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Create a new compliance framework"""
    try:
        return await compliance_service.create_framework(framework_data, current_user)
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create framework")


@router.get("/frameworks", response_model=ComplianceFrameworkListResponse)
async def list_frameworks(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    framework_type: Optional[FrameworkType] = Query(None, description="Filter by framework type"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """List compliance frameworks"""
    try:
        frameworks, total = await compliance_service.list_frameworks(
            current_user, page, per_page, framework_type, industry
        )
        
        return ComplianceFrameworkListResponse(
            frameworks=frameworks,
            total=total,
            page=page,
            per_page=per_page,
            has_next=(page * per_page) < total
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list frameworks")


@router.get("/frameworks/{framework_id}", response_model=ComplianceFrameworkResponse)
async def get_framework(
    framework_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Get a specific compliance framework"""
    try:
        return await compliance_service.get_framework(framework_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get framework")


@router.put("/frameworks/{framework_id}", response_model=ComplianceFrameworkResponse)
async def update_framework(
    framework_id: uuid.UUID,
    framework_data: ComplianceFrameworkUpdate,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Update a compliance framework"""
    try:
        return await compliance_service.update_framework(framework_id, framework_data, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update framework")


@router.delete("/frameworks/{framework_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_framework(
    framework_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Delete a compliance framework"""
    try:
        await compliance_service.delete_framework(framework_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete framework")


@router.get("/frameworks/{framework_id}/statistics")
async def get_framework_statistics(
    framework_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Get framework statistics"""
    try:
        return await compliance_service.get_framework_statistics(framework_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get statistics")


# Control Endpoints
@router.post("/frameworks/{framework_id}/controls", response_model=ComplianceControlResponse, status_code=status.HTTP_201_CREATED)
async def create_control(
    framework_id: uuid.UUID,
    control_data: ComplianceControlCreate,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Create a new control in a framework"""
    try:
        return await compliance_service.create_control(framework_id, control_data, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create control")


@router.post("/frameworks/{framework_id}/controls/bulk", response_model=List[ComplianceControlResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_controls(
    framework_id: uuid.UUID,
    bulk_data: BulkControlCreate,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Create multiple controls in a framework"""
    try:
        return await compliance_service.create_bulk_controls(framework_id, bulk_data.controls, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create controls")


@router.get("/frameworks/{framework_id}/controls", response_model=ComplianceControlListResponse)
async def list_controls(
    framework_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """List controls in a framework"""
    try:
        controls, total = await compliance_service.list_controls(
            framework_id, current_user, page, per_page, category, severity
        )
        
        return ComplianceControlListResponse(
            controls=controls,
            total=total,
            page=page,
            per_page=per_page,
            has_next=(page * per_page) < total
        )
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to list controls")


@router.get("/controls/{control_id}", response_model=ComplianceControlResponse)
async def get_control(
    control_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Get a specific control"""
    try:
        return await compliance_service.get_control(control_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get control")


@router.put("/controls/{control_id}", response_model=ComplianceControlResponse)
async def update_control(
    control_id: uuid.UUID,
    control_data: ComplianceControlUpdate,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Update a control"""
    try:
        return await compliance_service.update_control(control_id, control_data, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update control")


@router.delete("/controls/{control_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_control(
    control_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Delete a control"""
    try:
        await compliance_service.delete_control(control_id, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete control")


# Template Endpoints
@router.post("/templates", response_model=CustomScanTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_scan_template(
    template_data: CustomScanTemplateCreate,
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Create a custom scan template"""
    try:
        return await compliance_service.create_scan_template(template_data, current_user)
    except ResourceNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create template")


# Utility Endpoints
@router.get("/categories")
async def get_control_categories(
    framework_id: Optional[uuid.UUID] = Query(None, description="Filter by framework"),
    current_user: User = Depends(get_current_active_user),
    compliance_service: ComplianceService = Depends(get_compliance_service)
):
    """Get available control categories"""
    # This would return predefined categories or categories from existing controls
    categories = [
        "Identity and Access Management",
        "Data Protection",
        "Network Security",
        "Logging and Monitoring",
        "Incident Response",
        "Asset Management",
        "Vulnerability Management",
        "Configuration Management",
        "Backup and Recovery",
        "Compliance and Governance",
        "Cryptography",
        "Application Security",
        "Physical Security",
        "Business Continuity",
        "Risk Management"
    ]
    
    return {"categories": categories}


@router.get("/resource-types")
async def get_azure_resource_types(
    current_user: User = Depends(get_current_active_user)
):
    """Get available Azure resource types for controls"""
    resource_types = [
        "Microsoft.Compute/virtualMachines",
        "Microsoft.Storage/storageAccounts",
        "Microsoft.Network/networkSecurityGroups",
        "Microsoft.Network/virtualNetworks",
        "Microsoft.KeyVault/vaults",
        "Microsoft.Sql/servers",
        "Microsoft.Sql/servers/databases",
        "Microsoft.Web/sites",
        "Microsoft.ContainerService/managedClusters",
        "Microsoft.Security/securityContacts",
        "Microsoft.Security/pricings",
        "Microsoft.Authorization/roleAssignments",
        "Microsoft.Authorization/policyAssignments",
        "Microsoft.Insights/activityLogAlerts",
        "Microsoft.Insights/logProfiles",
        "Microsoft.OperationalInsights/workspaces",
        "Microsoft.Resources/resourceGroups",
        "Microsoft.Resources/subscriptions"
    ]
    
    return {"resource_types": resource_types}