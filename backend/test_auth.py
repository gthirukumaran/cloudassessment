"""
Simple test authentication endpoint for development/demo purposes
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="Securra Test Auth", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3016", "http://127.0.0.1:3016", "http://localhost:3017", "http://127.0.0.1:3017", "http://localhost:3018", "http://127.0.0.1:3018"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Test credentials
TEST_USERS = {
    "admin@securra.com": {
        "password": "admin123",
        "user_data": {
            "id": "test-user-1",
            "email": "admin@securra.com",
            "firstName": "Securra",
            "lastName": "Admin",
            "role": "admin",
            "isActive": True
        }
    },
    "demo@securra.com": {
        "password": "demo123",
        "user_data": {
            "id": "test-user-2",
            "email": "demo@securra.com",
            "firstName": "Demo",
            "lastName": "User",
            "role": "user",
            "isActive": True
        }
    }
}

SECRET_KEY = "test-secret-key-for-demo"

# Dynamic scan storage
SCAN_LIST = [
    {
        "scan_id": "scan-001",
        "subscription_id": "sub-001",
        "framework": "CIS",
        "status": "completed",
        "start_time": "2025-08-13T13:25:58.089226",
        "end_time": "2025-08-13T15:25:58.089226",
        "progress": 100,
        "total_checks": 50,
        "passed_checks": 45,
        "failed_checks": 5,
        "compliance_score": 90
    },
    {
        "scan_id": "scan-002",
        "subscription_id": "sub-001",
        "framework": "SOC2",
        "status": "in_progress",
        "start_time": "2025-08-12T13:25:58.089226",
        "end_time": None,
        "progress": 65,
        "total_checks": 50,
        "passed_checks": 32,
        "failed_checks": 0,
        "compliance_score": None
    },
    {
        "scan_id": "scan-003",
        "subscription_id": "sub-001",
        "framework": "NIST",
        "status": "failed",
        "start_time": "2025-08-11T13:25:58.089226",
        "end_time": "2025-08-11T15:25:58.089226",
        "progress": 100,
        "total_checks": 50,
        "passed_checks": 36,
        "failed_checks": 14,
        "compliance_score": 72
    },
    {
        "scan_id": "scan-004",
        "subscription_id": "sub-001",
        "framework": "CIS",
        "status": "completed",
        "start_time": "2025-08-10T13:25:58.089226",
        "end_time": "2025-08-10T15:25:58.089226",
        "progress": 100,
        "total_checks": 50,
        "passed_checks": 42,
        "failed_checks": 8,
        "compliance_score": 85
    },
    {
        "scan_id": "scan-005",
        "subscription_id": "sub-001",
        "framework": "SOC2",
        "status": "in_progress",
        "start_time": "2025-08-09T13:25:58.089226",
        "end_time": None,
        "progress": 50,
        "total_checks": 50,
        "passed_checks": 25,
        "failed_checks": 0,
        "compliance_score": None
    }
]

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Securra Test Auth Service",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/auth/login")
async def test_login(login_data: dict):
    """Test login endpoint for demo purposes"""
    email = login_data.get("email")
    password = login_data.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    # Check test credentials
    if email in TEST_USERS and TEST_USERS[email]["password"] == password:
        user_data = TEST_USERS[email]["user_data"]
        
        # Create JWT token
        token_data = {
            "sub": user_data["email"],
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow(),
            "user_id": user_data["id"],
            "role": user_data["role"]
        }
        
        access_token = jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 86400,  # 24 hours
            "user": user_data
        }
    
    raise HTTPException(status_code=401, detail="Invalid email or password")

@app.get("/api/v1/test")
async def test_endpoint():
    return {"message": "API is working", "status": "success"}

@app.get("/api/v1/scans")
async def test_scans():
    return {
        "scans": SCAN_LIST,
        "total": len(SCAN_LIST),
        "frameworks": ["CIS", "SOC2", "NIST", "ISO27001"],
        "statuses": ["completed", "in_progress", "failed", "pending"]
    }

@app.post("/api/v1/scans")
async def create_scan(scan_data: dict):
    """Create a new security scan"""
    import uuid
    
    scan_id = f"scan-{str(uuid.uuid4())[:8]}"
    
    # Simulate scan creation
    new_scan = {
        "scan_id": scan_id,
        "subscription_id": scan_data.get("subscription_id", "sub-001"),
        "framework": scan_data.get("framework", "CIS"),
        "status": "in_progress",
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "progress": 0,
        "total_checks": 50,
        "passed_checks": 0,
        "failed_checks": 0,
        "compliance_score": None
    }
    
    # Add the new scan to the beginning of the list (most recent first)
    SCAN_LIST.insert(0, new_scan)
    
    return {
        "message": "Scan created successfully",
        "scan": new_scan,
        "scan_id": scan_id,
        "status": "initiated"
    }

@app.get("/api/v1/subscriptions")
async def get_subscriptions():
    """Get Azure subscriptions with SPN configuration details from .env file"""
    
    # Read actual .env configuration
    azure_client_id = os.getenv('AZURE_CLIENT_ID')
    azure_client_secret = os.getenv('AZURE_CLIENT_SECRET')
    azure_tenant_id = os.getenv('AZURE_TENANT_ID')
    azure_subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    
    # Determine SPN configuration status
    spn_configured = bool(azure_client_id and azure_client_secret and azure_tenant_id)
    
    # Create status message based on configuration
    if spn_configured:
        env_status = "active"
        env_name = "Production Azure (.env configured)"
        error_message = None
    else:
        env_status = "inactive"
        env_name = "Production Azure (.env missing SPN details)"
        missing_fields = []
        if not azure_client_id:
            missing_fields.append("AZURE_CLIENT_ID")
        if not azure_client_secret:
            missing_fields.append("AZURE_CLIENT_SECRET")
        if not azure_tenant_id:
            missing_fields.append("AZURE_TENANT_ID")
        error_message = f"Missing .env variables: {', '.join(missing_fields)}"
    
    return {
        "subscriptions": [
            {
                "id": azure_subscription_id or "12345678-1234-1234-1234-123456789012",
                "name": env_name,
                "provider": "azure",
                "status": env_status,
                "state": "Enabled" if spn_configured else "Disabled",
                "tenant_id": azure_tenant_id or "Not configured",
                "resource_groups_count": 15 if spn_configured else 0,
                "last_scan": "2025-08-11T13:25:58.089226" if spn_configured else None,
                "compliance_score": 85 if spn_configured else 0,
                "critical_findings": 3 if spn_configured else 0,
                "subscription_type": "Pay-As-You-Go",
                "cost_center": "IT-001",
                "environment": "production",
                "spn_configured": spn_configured,
                "error_message": error_message
            },
            {
                "id": "87654321-4321-4321-4321-210987654321",
                "name": "Development Environment",
                "provider": "azure",
                "status": "active",
                "state": "Enabled",
                "tenant_id": azure_tenant_id or "64b85bc1-b5cf-4169-9b23-8addcc72c198",
                "resource_groups_count": 8,
                "last_scan": "2025-08-08T13:25:58.089226",
                "compliance_score": 92,
                "critical_findings": 1,
                "subscription_type": "Pay-As-You-Go",
                "cost_center": "IT-002",
                "environment": "development",
                "spn_configured": True
            },
            {
                "id": "11111111-2222-3333-4444-555555555555",
                "name": "Third Subscription (SPN Required)",
                "provider": "azure",
                "status": "inactive",
                "state": "Disabled",
                "tenant_id": "64b85bc1-b5cf-4169-9b23-8addcc72c198",
                "resource_groups_count": 0,
                "last_scan": None,
                "compliance_score": 0,
                "critical_findings": 0,
                "subscription_type": "Pay-As-You-Go",
                "cost_center": "IT-003",
                "environment": "staging",
                "spn_configured": False,
                "error_message": "Service Principal Name (SPN) credentials not configured for this subscription"
            }
        ],
        "total_subscriptions": 3,
        "active_subscriptions": 2 if spn_configured else 1,
        "azure_config": {
            "tenant_id": azure_tenant_id or "Not configured",
            "client_id": azure_client_id or "Not configured",
            "subscription_id": azure_subscription_id or "Not configured",
            "spn_status": "configured" if spn_configured else "missing",
            "env_file_status": "loaded",
            "missing_spn_subscriptions": [] if spn_configured else ["12345678-1234-1234-1234-123456789012"]
        }
    }

@app.get("/api/v1/dashboard/analytics")
async def get_dashboard_analytics():
    """Get dashboard analytics data"""
    return {
        "total_resources": 156,
        "compliance_score": 85,
        "critical_findings": 3,
        "recent_scans": 5,
        "security_metrics": {
            "overall_score": 87,
            "vulnerabilities": {
                "critical": 2,
                "high": 8,
                "medium": 15,
                "low": 23
            },
            "compliance_scores": {
                "cis": 88,
                "nist": 85,
                "soc2": 92
            }
        }
    }

@app.get("/api/v1/reports")
async def test_reports():
    return {
        "reports": [
            {
                "id": "report-001",
                "scan_id": "scan-001",
                "title": "CIS Benchmark Report",
                "created_at": "2025-08-13T15:25:58.089226",
                "status": "completed"
            }
        ]
    }

@app.get("/api/v1/users")
async def get_users():
    """Get all users for settings page"""
    users_list = []
    for email, user_info in TEST_USERS.items():
        user_data = user_info["user_data"].copy()
        # Remove sensitive data and add additional fields for UI
        # Add permissions based on role
        permissions = []
        if user_data["role"] == "admin":
            permissions = ["read", "write", "delete", "manage_users", "manage_settings"]
        else:
            permissions = ["read"]
        
        users_list.append({
            "id": user_data["id"],
            "email": user_data["email"],
            "firstName": user_data["firstName"],
            "lastName": user_data["lastName"],
            "role": user_data["role"],
            "permissions": permissions,
            "status": "active",
            "createdAt": "2025-01-01T00:00:00.000Z",
            "lastLogin": "2025-01-15T10:30:00.000Z"
        })
    
    return {
        "users": users_list,
        "total": len(users_list)
    }

@app.post("/api/v1/users")
async def create_user(user_data: dict):
    """Create a new user (mock endpoint)"""
    import uuid
    
    new_user = {
        "id": str(uuid.uuid4()),
        "email": user_data.get("email"),
        "firstName": user_data.get("firstName"),
        "lastName": user_data.get("lastName"),
        "role": user_data.get("role", "user"),
        "status": "active",
        "createdAt": datetime.now().isoformat(),
        "lastLogin": None
    }
    
    return {
        "message": "User created successfully",
        "user": new_user
    }

@app.put("/api/v1/users/{user_email}")
async def update_user(user_email: str, user_data: dict):
    """Update user (mock endpoint)"""
    return {
        "message": f"User {user_email} updated successfully",
        "user": user_data
    }

@app.delete("/api/v1/users/{user_email}")
async def delete_user(user_email: str):
    """Delete user (mock endpoint)"""
    return {
        "message": f"User {user_email} deleted successfully"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Securra Test Auth Service")
    print("📍 URL: http://127.0.0.1:9099")
    print("📋 Test Credentials:")
    print("   Admin: admin@securra.com / admin123")
    print("   Demo:  demo@securra.com / demo123")
    uvicorn.run("test_auth:app", host="127.0.0.1", port=9099, reload=True)
