# SecurityA Architecture Documentation

## System Overview

SecurityA is designed as a microservices-based architecture with clear separation of concerns, ensuring scalability, maintainability, and security. The system follows a layered architecture pattern with event-driven communication for real-time capabilities.

## Architecture Layers

### 1. Presentation Layer (Frontend)
- **Technology**: React 18 with TypeScript
- **UI Framework**: Material-UI (MUI) v5
- **State Management**: React Query + Zustand
- **Routing**: React Router v6
- **Build Tool**: Vite

### 2. API Gateway Layer
- **Technology**: FastAPI with Uvicorn
- **Authentication**: Azure OAuth2 with JWT tokens
- **Rate Limiting**: Redis-based rate limiting
- **CORS**: Configured for cross-origin requests
- **Documentation**: Auto-generated OpenAPI/Swagger docs

### 3. Business Logic Layer
- **Core Services**: Modular service architecture
- **Background Tasks**: Celery with Redis broker
- **Event Handling**: Async event processing
- **Caching**: Redis for performance optimization

### 4. Data Access Layer
- **ORM**: SQLAlchemy 2.0 with async support
- **Database**: PostgreSQL 15+
- **Migrations**: Alembic
- **Connection Pooling**: SQLAlchemy connection pooling

### 5. External Services Layer
- **Cloud Providers**: Azure, AWS, GCP APIs
- **AI Services**: OpenAI GPT-4 API
- **Storage**: Azure Blob Storage
- **Secrets**: Azure Key Vault

## Component Architecture

### Core Components

#### 1. Authentication Service
```python
# Handles Azure OAuth2 authentication and JWT token management
class AuthService:
    - authenticate_user(credentials)
    - validate_token(token)
    - refresh_token(refresh_token)
    - get_user_permissions(user_id)
```

#### 2. Scan Engine
```python
# Multi-cloud security scanning orchestration
class ScanEngine:
    - initiate_scan(cloud_provider, scan_config)
    - monitor_scan_progress(scan_id)
    - process_scan_results(scan_data)
    - generate_scan_summary(scan_id)
```

#### 3. AI Analysis Service
```python
# AI-powered security analysis and recommendations
class AIAnalysisService:
    - analyze_security_findings(findings)
    - generate_remediation_recommendations(finding)
    - assess_risk_score(scan_results)
    - provide_chatbot_response(query)
```

#### 4. Report Generation Service
```python
# CIS-style PDF report generation
class ReportService:
    - generate_executive_summary(scan_id)
    - create_detailed_report(scan_id)
    - export_pdf_report(scan_id)
    - send_email_report(scan_id, recipients)
```

#### 5. Chatbot Service
```python
# AI-powered chatbot for user queries
class ChatbotService:
    - process_user_query(query, context)
    - save_conversation_history(user_id, conversation)
    - provide_recommendations(query)
    - integrate_with_scan_data(query)
```

## Database Schema

### Core Tables

#### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    azure_id VARCHAR(255) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Organizations
```sql
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    azure_tenant_id VARCHAR(255),
    subscription_id VARCHAR(255),
    settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Scans
```sql
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    organization_id UUID REFERENCES organizations(id),
    cloud_provider VARCHAR(50) NOT NULL,
    scan_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    config JSONB,
    results JSONB,
    risk_score INTEGER,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Security Findings
```sql
CREATE TABLE security_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id),
    finding_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    resource_id VARCHAR(255),
    resource_type VARCHAR(100),
    remediation_steps JSONB,
    ai_analysis JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Chatbot Conversations
```sql
CREATE TABLE chatbot_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    query TEXT NOT NULL,
    response TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Reports
```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id),
    report_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Design

### Authentication Endpoints

#### POST /api/auth/login
```json
{
  "azure_code": "string",
  "redirect_uri": "string"
}
```

Response:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": "uuid",
    "email": "string",
    "name": "string",
    "role": "string"
  }
}
```

### Scan Management Endpoints

#### POST /api/scans
```json
{
  "cloud_provider": "azure",
  "scan_type": "comprehensive",
  "config": {
    "include_vms": true,
    "include_storage": true,
    "include_networking": true
  }
}
```

Response:
```json
{
  "scan_id": "uuid",
  "status": "initiated",
  "estimated_duration": 300,
  "message": "Scan initiated successfully"
}
```

#### GET /api/scans/{scan_id}
Response:
```json
{
  "id": "uuid",
  "status": "completed",
  "risk_score": 75,
  "findings_count": 23,
  "high_severity": 2,
  "medium_severity": 15,
  "low_severity": 6,
  "started_at": "2024-01-15T10:00:00Z",
  "completed_at": "2024-01-15T10:05:00Z",
  "summary": {
    "total_resources": 45,
    "compliant_resources": 22,
    "non_compliant_resources": 23
  }
}
```

### AI Analysis Endpoints

#### GET /api/ai-analysis/{scan_id}
Response:
```json
{
  "scan_id": "uuid",
  "ai_insights": [
    {
      "finding_id": "uuid",
      "analysis": "This finding indicates a critical security vulnerability...",
      "recommendations": [
        "Immediately restrict network access",
        "Enable encryption at rest",
        "Implement proper IAM policies"
      ],
      "priority": "high",
      "estimated_fix_time": "2 hours"
    }
  ],
  "overall_assessment": "Your infrastructure has several critical vulnerabilities that require immediate attention.",
  "trend_analysis": "Security posture has improved 15% compared to last scan."
}
```

### Chatbot Endpoints

#### POST /api/chatbot/query
```json
{
  "query": "How do I fix the overly permissive network security rule?",
  "context": {
    "scan_id": "uuid",
    "finding_id": "uuid"
  }
}
```

Response:
```json
{
  "response": "To fix the overly permissive network security rule, follow these steps...",
  "recommendations": [
    {
      "action": "Update NSG rule",
      "command": "az network nsg rule update --resource-group <rg> --nsg-name <nsg> --name <rule> --access Deny",
      "description": "Deny access to the overly permissive rule"
    }
  ],
  "related_findings": ["uuid1", "uuid2"],
  "confidence_score": 0.95
}
```

### Report Endpoints

#### GET /api/reports/{scan_id}/pdf
Response:
```json
{
  "report_url": "https://storage.blob.core.windows.net/reports/report-uuid.pdf",
  "expires_at": "2024-01-16T10:00:00Z",
  "file_size": 2048576
}
```

## Security Considerations

### Authentication & Authorization
- Azure OAuth2 integration with JWT tokens
- Role-based access control (RBAC)
- Token refresh mechanism
- Session management with Redis

### Data Protection
- All sensitive data encrypted at rest
- TLS 1.3 for data in transit
- Azure Key Vault for secret management
- Data anonymization for analytics

### API Security
- Rate limiting per user/IP
- Input validation and sanitization
- CORS configuration
- API versioning

### Cloud Security
- Least privilege access principles
- Managed identities for Azure resources
- Network security groups
- Audit logging enabled

## Performance Considerations

### Caching Strategy
- Redis for session storage
- API response caching
- Database query result caching
- Static asset caching

### Database Optimization
- Connection pooling
- Indexed queries
- Partitioned tables for large datasets
- Read replicas for analytics

### Scalability
- Horizontal scaling with load balancers
- Microservices architecture
- Event-driven communication
- Background task processing

## Monitoring & Observability

### Logging
- Structured logging with correlation IDs
- Centralized log aggregation
- Error tracking and alerting
- Performance metrics collection

### Health Checks
- Application health endpoints
- Database connectivity checks
- External service availability
- Automated alerting

### Metrics
- API response times
- Error rates
- User activity tracking
- Resource utilization

## Deployment Architecture

### Development Environment
- Docker Compose for local development
- Hot reload for frontend and backend
- Local PostgreSQL and Redis
- Mock external services

### Production Environment
- Azure Container Registry
- Azure App Service for web apps
- Azure Database for PostgreSQL
- Azure Redis Cache
- Azure Application Insights

### CI/CD Pipeline
- GitHub Actions for automation
- Automated testing
- Security scanning
- Blue-green deployment strategy
