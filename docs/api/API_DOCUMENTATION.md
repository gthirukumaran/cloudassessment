# SecurityA API Documentation

## Overview

The SecurityA API provides comprehensive endpoints for cloud security assessment, AI-powered analysis, and report generation. The API follows RESTful principles and uses JSON for data exchange.

**Base URL**: `https://api.securitya.com/v1`  
**Authentication**: Bearer Token (JWT)  
**Content-Type**: `application/json`

## Authentication

### Azure OAuth2 Flow

SecurityA uses Azure OAuth2 for authentication. The flow involves:

1. **Authorization Request**: Redirect user to Azure AD
2. **Authorization Code**: Azure redirects back with authorization code
3. **Token Exchange**: Exchange code for access token
4. **API Access**: Use access token for API requests

### Token Management

```http
Authorization: Bearer <jwt_token>
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/login
Exchange Azure authorization code for JWT token.

**Request:**
```json
{
  "azure_code": "M.R3_BAY.c0...",
  "redirect_uri": "https://securitya.com/auth/callback"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "john.doe@company.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "security_admin",
    "organization_id": "550e8400-e29b-41d4-a716-446655440001"
  }
}
```

#### POST /auth/refresh
Refresh expired access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### POST /auth/logout
Invalidate current session.

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### User Management

#### GET /user/profile
Get current user profile.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "john.doe@company.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": "security_admin",
  "organization": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "name": "Acme Corporation",
    "azure_tenant_id": "12345678-1234-1234-1234-123456789012"
  },
  "preferences": {
    "notifications": {
      "email": true,
      "high_priority_alerts": true,
      "weekly_summaries": false
    },
    "timezone": "America/New_York"
  },
  "created_at": "2024-01-15T10:00:00Z",
  "last_login": "2024-01-15T14:30:00Z"
}
```

#### PUT /user/profile
Update user profile.

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "preferences": {
    "notifications": {
      "email": true,
      "high_priority_alerts": true,
      "weekly_summaries": true
    },
    "timezone": "America/New_York"
  }
}
```

### Scan Management

#### GET /scans
List all scans for the authenticated user.

**Query Parameters:**
- `status` (optional): Filter by status (`pending`, `running`, `completed`, `failed`)
- `cloud_provider` (optional): Filter by cloud provider (`azure`, `aws`, `gcp`)
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "scans": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "cloud_provider": "azure",
      "scan_type": "comprehensive",
      "status": "completed",
      "risk_score": 75,
      "findings_count": 23,
      "high_severity": 2,
      "medium_severity": 15,
      "low_severity": 6,
      "started_at": "2024-01-15T10:00:00Z",
      "completed_at": "2024-01-15T10:05:00Z",
      "created_at": "2024-01-15T09:55:00Z"
    }
  ],
  "pagination": {
    "total": 45,
    "limit": 20,
    "offset": 0,
    "has_next": true
  }
}
```

#### POST /scans
Create a new security scan.

**Request:**
```json
{
  "cloud_provider": "azure",
  "scan_type": "comprehensive",
  "config": {
    "include_vms": true,
    "include_storage": true,
    "include_networking": true,
    "include_key_vaults": true,
    "include_app_services": false,
    "include_sql_databases": false
  },
  "options": {
    "enable_ai_analysis": true,
    "generate_pdf_report": true,
    "send_email_notifications": true
  }
}
```

**Response:**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "initiated",
  "estimated_duration": 300,
  "message": "Scan initiated successfully",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### GET /scans/{scan_id}
Get detailed information about a specific scan.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "550e8400-e29b-41d4-a716-446655440001",
  "cloud_provider": "azure",
  "scan_type": "comprehensive",
  "status": "completed",
  "config": {
    "include_vms": true,
    "include_storage": true,
    "include_networking": true,
    "include_key_vaults": true
  },
  "results": {
    "total_resources": 45,
    "compliant_resources": 22,
    "non_compliant_resources": 23,
    "scan_duration": 300
  },
  "risk_score": 75,
  "findings_count": 23,
  "high_severity": 2,
  "medium_severity": 15,
  "low_severity": 6,
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:05:00Z",
  "created_at": "2024-01-15T09:55:00Z"
}
```

#### GET /scans/{scan_id}/progress
Get real-time scan progress.

**Response:**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440002",
  "status": "running",
  "progress": 65,
  "current_step": "Scanning Network Security Groups",
  "estimated_remaining": 120,
  "resources_scanned": 30,
  "total_resources": 45,
  "started_at": "2024-01-15T10:00:00Z"
}
```

#### DELETE /scans/{scan_id}
Cancel a running scan or delete a completed scan.

**Response:**
```json
{
  "message": "Scan cancelled successfully"
}
```

### Security Findings

#### GET /scans/{scan_id}/findings
Get all findings for a specific scan.

**Query Parameters:**
- `severity` (optional): Filter by severity (`high`, `medium`, `low`)
- `status` (optional): Filter by status (`open`, `fixed`, `ignored`)
- `resource_type` (optional): Filter by resource type
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "findings": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440003",
      "scan_id": "550e8400-e29b-41d4-a716-446655440002",
      "finding_type": "network_security",
      "severity": "high",
      "title": "Overly Permissive Network Security Rule",
      "description": "This finding indicates that a network security rule allows traffic from any source or to any destination port, which poses a significant security risk.",
      "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/rg-network/providers/Microsoft.Network/networkSecurityGroups/nsg-web",
      "resource_type": "Network Security Group",
      "resource_name": "nsg-web",
      "remediation_steps": [
        {
          "step": 1,
          "description": "Identify the overly permissive network security rule",
          "command": "az network nsg rule list --resource-group rg-network --nsg-name nsg-web"
        },
        {
          "step": 2,
          "description": "Modify the rule to restrict access to only necessary IP addresses and ports",
          "command": "az network nsg rule update --resource-group rg-network --nsg-name nsg-web --name AllowAll --access Deny"
        }
      ],
      "compliance_frameworks": ["CIS", "NIST"],
      "created_at": "2024-01-15T10:05:00Z"
    }
  ],
  "pagination": {
    "total": 23,
    "limit": 20,
    "offset": 0,
    "has_next": true
  }
}
```

#### GET /findings/{finding_id}
Get detailed information about a specific finding.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "scan_id": "550e8400-e29b-41d4-a716-446655440002",
  "finding_type": "network_security",
  "severity": "high",
  "title": "Overly Permissive Network Security Rule",
  "description": "This finding indicates that a network security rule allows traffic from any source or to any destination port, which poses a significant security risk.",
  "resource_id": "/subscriptions/12345678-1234-1234-1234-123456789012/resourceGroups/rg-network/providers/Microsoft.Network/networkSecurityGroups/nsg-web",
  "resource_type": "Network Security Group",
  "resource_name": "nsg-web",
  "resource_group": "rg-network",
  "location": "East US",
  "remediation_steps": [
    {
      "step": 1,
      "description": "Identify the overly permissive network security rule",
      "command": "az network nsg rule list --resource-group rg-network --nsg-name nsg-web",
      "powershell_command": "Get-AzNetworkSecurityRuleConfig -NetworkSecurityGroup $nsg"
    },
    {
      "step": 2,
      "description": "Modify the rule to restrict access to only necessary IP addresses and ports",
      "command": "az network nsg rule update --resource-group rg-network --nsg-name nsg-web --name AllowAll --access Deny",
      "powershell_command": "Set-AzNetworkSecurityRuleConfig -NetworkSecurityGroup $nsg -Name AllowAll -Access Deny"
    }
  ],
  "compliance_frameworks": ["CIS", "NIST"],
  "risk_assessment": {
    "impact": "High",
    "likelihood": "Medium",
    "overall_risk": "High"
  },
  "created_at": "2024-01-15T10:05:00Z"
}
```

#### PUT /findings/{finding_id}/status
Update finding status.

**Request:**
```json
{
  "status": "fixed",
  "notes": "Fixed by updating NSG rule configuration"
}
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "status": "fixed",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### AI Analysis

#### GET /scans/{scan_id}/ai-analysis
Get AI-powered analysis for a scan.

**Response:**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440002",
  "ai_insights": [
    {
      "finding_id": "550e8400-e29b-41d4-a716-446655440003",
      "analysis": "This finding indicates a critical security vulnerability that could expose your network infrastructure to unauthorized access. The overly permissive rule allows traffic from any source IP address, which significantly increases the attack surface.",
      "recommendations": [
        "Immediately restrict network access to only necessary IP addresses",
        "Enable network security group flow logs for monitoring",
        "Implement proper network segmentation",
        "Consider using Azure Firewall for additional protection"
      ],
      "priority": "high",
      "estimated_fix_time": "2 hours",
      "business_impact": "High risk of data breach and compliance violations",
      "confidence_score": 0.95
    }
  ],
  "overall_assessment": "Your infrastructure has several critical vulnerabilities that require immediate attention. The most concerning issues are related to network security and access controls.",
  "trend_analysis": "Security posture has improved 15% compared to last scan, but critical network vulnerabilities remain.",
  "compliance_gap_analysis": {
    "cis_compliance": 78,
    "nist_compliance": 82,
    "missing_controls": ["AC-3", "SC-7", "SC-8"]
  },
  "generated_at": "2024-01-15T10:10:00Z"
}
```

### Chatbot

#### POST /chatbot/query
Send a query to the AI chatbot.

**Request:**
```json
{
  "query": "How do I fix the overly permissive network security rule?",
  "context": {
    "scan_id": "550e8400-e29b-41d4-a716-446655440002",
    "finding_id": "550e8400-e29b-41d4-a716-446655440003"
  },
  "session_id": "session-123"
}
```

**Response:**
```json
{
  "response": "To fix the overly permissive network security rule, follow these steps:\n\n1. **Identify the problematic rule**: Use Azure CLI to list all NSG rules\n2. **Modify the rule**: Update the rule to deny access or restrict to specific IP ranges\n3. **Verify the changes**: Test connectivity to ensure legitimate traffic is not blocked\n\nHere are the specific commands:\n\n**Azure CLI:**\n```bash\naz network nsg rule update --resource-group <resource-group-name> --nsg-name <nsg-name> --name <rule-name> --access Deny\n```\n\n**PowerShell:**\n```powershell\nSet-AzNetworkSecurityRuleConfig -NetworkSecurityGroup <nsg> -Name <rule-name> -Access Deny\n```\n\nWould you like me to help you with anything else?",
  "recommendations": [
    {
      "action": "Update NSG rule",
      "command": "az network nsg rule update --resource-group <rg> --nsg-name <nsg> --name <rule> --access Deny",
      "description": "Deny access to the overly permissive rule"
    }
  ],
  "related_findings": ["550e8400-e29b-41d4-a716-446655440004"],
  "confidence_score": 0.95,
  "session_id": "session-123",
  "timestamp": "2024-01-15T10:15:00Z"
}
```

#### GET /chatbot/history
Get conversation history for the current user.

**Query Parameters:**
- `session_id` (optional): Filter by session ID
- `limit` (optional): Number of results (default: 50, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "conversations": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440005",
      "session_id": "session-123",
      "query": "How do I fix the overly permissive network security rule?",
      "response": "To fix the overly permissive network security rule...",
      "context": {
        "scan_id": "550e8400-e29b-41d4-a716-446655440002",
        "finding_id": "550e8400-e29b-41d4-a716-446655440003"
      },
      "created_at": "2024-01-15T10:15:00Z"
    }
  ],
  "pagination": {
    "total": 25,
    "limit": 50,
    "offset": 0,
    "has_next": false
  }
}
```

### Reports

#### GET /reports/templates
Get available report templates.

**Response:**
```json
{
  "templates": [
    {
      "id": "executive_summary",
      "name": "Executive Summary",
      "description": "High-level overview for executives and stakeholders",
      "estimated_generation_time": 30,
      "sections": ["executive_summary", "risk_overview", "key_findings", "recommendations"]
    },
    {
      "id": "technical_report",
      "name": "Technical Report",
      "description": "Detailed technical findings and remediation steps",
      "estimated_generation_time": 60,
      "sections": ["executive_summary", "methodology", "detailed_findings", "remediation_steps", "compliance_mapping"]
    },
    {
      "id": "compliance_report",
      "name": "Compliance Report",
      "description": "CIS, NIST, and industry compliance mapping",
      "estimated_generation_time": 45,
      "sections": ["compliance_overview", "control_mapping", "gap_analysis", "remediation_plan"]
    }
  ]
}
```

#### POST /reports/generate
Generate a new report.

**Request:**
```json
{
  "scan_id": "550e8400-e29b-41d4-a716-446655440002",
  "template_id": "executive_summary",
  "options": {
    "include_ai_analysis": true,
    "include_remediation_steps": true,
    "include_compliance_mapping": true,
    "custom_sections": ["custom_section_1", "custom_section_2"]
  }
}
```

**Response:**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440006",
  "status": "generating",
  "estimated_completion": "2024-01-15T10:20:00Z",
  "message": "Report generation started"
}
```

#### GET /reports/{report_id}
Get report status and details.

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440006",
  "scan_id": "550e8400-e29b-41d4-a716-446655440002",
  "template_id": "executive_summary",
  "status": "completed",
  "file_url": "https://storage.blob.core.windows.net/reports/report-550e8400-e29b-41d4-a716-446655440006.pdf",
  "file_size": 2048576,
  "expires_at": "2024-01-22T10:20:00Z",
  "generated_at": "2024-01-15T10:20:00Z"
}
```

#### GET /reports
List all reports for the authenticated user.

**Query Parameters:**
- `scan_id` (optional): Filter by scan ID
- `template_id` (optional): Filter by template ID
- `status` (optional): Filter by status (`generating`, `completed`, `failed`)
- `limit` (optional): Number of results (default: 20, max: 100)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "reports": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440006",
      "scan_id": "550e8400-e29b-41d4-a716-446655440002",
      "template_id": "executive_summary",
      "template_name": "Executive Summary",
      "status": "completed",
      "file_size": 2048576,
      "generated_at": "2024-01-15T10:20:00Z"
    }
  ],
  "pagination": {
    "total": 15,
    "limit": 20,
    "offset": 0,
    "has_next": false
  }
}
```

### Analytics

#### GET /analytics/dashboard
Get dashboard analytics data.

**Response:**
```json
{
  "overview": {
    "total_scans": 45,
    "active_scans": 3,
    "total_findings": 156,
    "high_priority_findings": 12,
    "average_risk_score": 68
  },
  "trends": {
    "security_posture": [
      {"date": "2024-01-10", "score": 65},
      {"date": "2024-01-11", "score": 68},
      {"date": "2024-01-12", "score": 72},
      {"date": "2024-01-13", "score": 70},
      {"date": "2024-01-14", "score": 75}
    ]
  },
  "findings_by_severity": {
    "high": 12,
    "medium": 89,
    "low": 55
  },
  "findings_by_type": {
    "network_security": 34,
    "storage_security": 28,
    "identity_access": 22,
    "monitoring": 18,
    "other": 54
  },
  "compliance_overview": {
    "cis_compliance": 78,
    "nist_compliance": 82,
    "iso_compliance": 75
  }
}
```

#### GET /analytics/trends
Get security trends over time.

**Query Parameters:**
- `period` (optional): Time period (`7d`, `30d`, `90d`, `1y`)
- `metric` (optional): Metric to analyze (`risk_score`, `findings_count`, `compliance_score`)

**Response:**
```json
{
  "period": "30d",
  "metric": "risk_score",
  "data": [
    {
      "date": "2024-01-01",
      "value": 65,
      "change": 0
    },
    {
      "date": "2024-01-02",
      "value": 68,
      "change": 3
    }
  ],
  "summary": {
    "average": 70.2,
    "trend": "improving",
    "change_percentage": 8.5
  }
}
```

### Cloud Connections

#### GET /cloud/connections
Get cloud provider connection status.

**Response:**
```json
{
  "connections": [
    {
      "provider": "azure",
      "status": "connected",
      "tenant_id": "12345678-1234-1234-1234-123456789012",
      "subscription_id": "87654321-4321-4321-4321-210987654321",
      "connected_at": "2024-01-10T09:00:00Z",
      "last_sync": "2024-01-15T10:00:00Z"
    },
    {
      "provider": "aws",
      "status": "configured",
      "account_id": "123456789012",
      "connected_at": null,
      "last_sync": null
    },
    {
      "provider": "gcp",
      "status": "not_configured",
      "project_id": null,
      "connected_at": null,
      "last_sync": null
    }
  ]
}
```

#### POST /cloud/connections/azure/connect
Connect Azure subscription.

**Request:**
```json
{
  "tenant_id": "12345678-1234-1234-1234-123456789012",
  "subscription_id": "87654321-4321-4321-4321-210987654321",
  "permissions": ["Reader", "Security Reader"]
}
```

**Response:**
```json
{
  "status": "connected",
  "message": "Azure connection established successfully",
  "connected_at": "2024-01-15T10:30:00Z"
}
```

## Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": [
      {
        "field": "cloud_provider",
        "message": "Cloud provider must be one of: azure, aws, gcp"
      }
    ],
    "timestamp": "2024-01-15T10:00:00Z",
    "request_id": "req-12345678-1234-1234-1234-123456789012"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing authentication token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

## Rate Limiting

API requests are rate-limited to ensure fair usage:

- **Authentication endpoints**: 10 requests per minute
- **Scan management**: 5 requests per minute
- **AI analysis**: 20 requests per minute
- **Report generation**: 3 requests per minute
- **General endpoints**: 100 requests per minute

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

## Webhooks

SecurityA supports webhooks for real-time notifications:

### Webhook Events

- `scan.completed` - Scan completed
- `scan.failed` - Scan failed
- `finding.created` - New finding detected
- `report.generated` - Report generation completed

### Webhook Configuration

```json
{
  "url": "https://your-app.com/webhooks/securitya",
  "events": ["scan.completed", "finding.created"],
  "secret": "webhook-secret-key"
}
```

### Webhook Payload Example

```json
{
  "event": "scan.completed",
  "timestamp": "2024-01-15T10:05:00Z",
  "data": {
    "scan_id": "550e8400-e29b-41d4-a716-446655440002",
    "status": "completed",
    "risk_score": 75,
    "findings_count": 23
  }
}
```

## SDKs and Libraries

### Python SDK

```python
from securitya import SecurityAClient

client = SecurityAClient(api_key="your-api-key")

# Start a new scan
scan = client.scans.create(
    cloud_provider="azure",
    scan_type="comprehensive"
)

# Get scan results
results = client.scans.get(scan_id=scan.id)
```

### JavaScript SDK

```javascript
import { SecurityAClient } from '@securitya/sdk';

const client = new SecurityAClient({ apiKey: 'your-api-key' });

// Start a new scan
const scan = await client.scans.create({
  cloudProvider: 'azure',
  scanType: 'comprehensive'
});

// Get scan results
const results = await client.scans.get(scan.id);
```

## Support

For API support and questions:

- **Documentation**: https://docs.securitya.com
- **API Status**: https://status.securitya.com
- **Support Email**: api-support@securitya.com
- **Developer Community**: https://community.securitya.com
