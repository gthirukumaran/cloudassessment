# Securra Architecture & Component Design

This document describes Securra’s backend architecture, core components, data model, and end‑to‑end request flows. It also explains operational modes, security posture, and how report generation ties to the `reports_output.json` structure.

## 1) High‑Level Overview

Securra is an AI‑assisted cloud security assessment platform. It provides APIs to:

- Authenticate users (Azure OAuth2 or demo test auth)
- Discover cloud subscriptions/resources (Azure)
- Execute and track security scans (CIS/SOC2/NIST/ISO27001)
- Analyze findings with LLM assistance
- Generate compliance reports (PDF and JSON)
- Offer a chatbot for interactive security assistance

The codebase currently offers two backend modes:

1. Modular FastAPI app (production‑oriented): `backend/app/*`
2. Enhanced demo backend (self‑contained features): `backend/enhanced_backend.py`


## 2) Core Components

### 2.1 FastAPI Application (Modular)

- Entrypoint: `backend/app/main.py`
  - App instance, CORS, Trusted Hosts, structured logging, exception handlers
  - Routes mounted from `backend/app/api/v1/api.py`
  - Startup initializes database via `app.database.init_db()`

- API Router: `backend/app/api/v1/api.py`
  - Aggregates endpoint modules under `/api/v1/*`

- Endpoints: `backend/app/api/v1/endpoints/*.py`
  - `auth.py`: Azure OAuth2 login, refresh, logout, `GET /me`
  - `scans.py`, `reports.py`, `dashboard.py`, `subscriptions.py`, `users.py`, `chatbot.py`, `compliance.py` (stubs/logic via services)

- Dependencies: `backend/app/core/dependencies.py`
  - Injects Auth/Scan/Chatbot/Report/Compliance services
  - Enforces `Authorization` header and role/permission checks

### 2.2 Services (Business Logic)

- `AuthService` (`backend/app/services/auth_service.py`)
  - Azure OAuth2 code exchange and MS Graph user info
  - JWT generation/verification (`python-jose` based)
  - User provisioning and organization mapping

- `ScanService`, `ReportService`, `ChatbotService`, `ComplianceService`
  - Placeholders or thin wrappers to orchestrate scanning, reporting, chat, and compliance logic

- `AzureService` (`backend/azure_service.py`)
  - Handles Azure credentials, subscription discovery, resource introspection
  - Uses real clients when credentials exist, falls back to mock data otherwise
  - Optional OpenAI client for AI recommendations (if configured)

- Enhanced/auxiliary services (demo mode, if present in workspace):
  - `agentic_langgraph_service.py`, `pdf_config_service.py`, `validation_service.py`, `llm_email_service.py`

### 2.3 Data Layer

- SQLAlchemy setup: `backend/app/database.py`
  - Engine from `DATABASE_URL` (supports SQLite dev/test and pooled Postgres)
  - `SessionLocal` and `Base`

- Models: `backend/app/models/*.py`
  - `User`: identity, Azure linkage, role, activity flags
  - `Organization`: multi‑tenant boundary, quotas
  - `Scan`, `Report`, `ChatSession`, `Compliance` (present in repo, not all shown here)

### 2.4 Configuration

- Pydantic settings: `backend/app/config.py`
  - App/server, DB, Redis, security, Azure OAuth2, OpenAI, CORS, storage, logging, rate limiting, email, scan config
  - Env file template: `backend/env.example`

### 2.5 Enhanced Demo Backend (Self‑Contained)

- File: `backend/enhanced_backend.py`
  - All‑in‑one FastAPI app for demos: test users/roles, Azure subscription façade, AI remediation, PDF generation
  - CORS regex for dev ports; JWT via `python-jose`
  - Direct integration with `azure_service.py` and optional OpenAI calls

### 2.6 Test Auth Service (Mock)

- File: `backend/test_auth.py`
  - Provides test login endpoint and canned data for scans, subscriptions, users
  - Useful for front‑end dev without Azure/OAuth


## 3) End‑to‑End Flows

### 3.1 Authentication (Azure OAuth2)

1. Frontend obtains `authorization_code` from Azure login
2. `POST /api/v1/auth/login` with `{ azure_code, redirect_uri }`
3. `AuthService._exchange_code_for_token()` calls Azure token endpoint
4. `AuthService._get_azure_user_info()` calls MS Graph `/me`
5. `AuthService.get_or_create_user()` links/creates `User` and `Organization`
6. `AuthService.create_token_response()` returns `{ access_token, refresh_token, user, expires_in }`
7. Subsequent requests include `Authorization: Bearer <access_token>`

Refresh token:
- `POST /api/v1/auth/refresh` → verifies refresh JWT (`type=refresh`), mints new pair

Who‑am‑I:
- `GET /api/v1/auth/me` → verifies access JWT, returns current user context

Demo mode:
- `backend/test_auth.py` exposes `POST /api/v1/auth/login` with static credentials

### 3.2 Subscription Discovery (Azure)

1. Frontend calls `/api/v1/subscriptions`
2. Service uses `AzureService`:
   - If env credentials (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`) present: real SDK clients enumerate subscriptions and resource groups
   - Else: returns mock subscriptions with informative flags (`spn_configured` etc.)

### 3.3 Scan Orchestration

Two patterns exist in the repo:

- Modular API (intended): `ScanService` would create a `Scan` row, enqueue background workers (Celery/Redis planned), poll/report status, persist findings
- Demo API (current): endpoints in `test_auth.py` or `enhanced_backend.py` construct mock scan objects in memory and return progress snapshots

### 3.4 AI‑Assisted Analysis

1. For a finding (title, severity, resource, category), service constructs a structured prompt
2. If `OPENAI_API_KEY` is configured:
   - Preferred modern client: `from openai import AsyncOpenAI; client = AsyncOpenAI(api_key=...)`
   - Create completion via `client.chat.completions.create(...)`
3. On failure or if not configured: fall back to rule‑based recommendations

Output includes remediation steps, commands, effort estimate, and compliance impact.

### 3.5 Report Generation

Two output forms:

- JSON: Structured data similar to `reports_output.json` (see Section 6)
- PDF: Using `reportlab` and/or `weasyprint` to render CIS/SOC2 style reports for download

Flow:
1. Frontend requests report generation with a `scan_id` and framework (`CIS`, `SOC2`, etc.)
2. Service compiles scan results, AI insights, KPIs
3. Service emits a report entity (JSON) and optionally a PDF artifact stored in configured storage

### 3.6 Chatbot

1. Frontend posts a user query to `/api/v1/chatbot/query`
2. Service enriches query with context (subscriptions, recent scans, findings)
3. AI answers with references and actionable steps
4. Session context persisted to `ChatSession` (planned)


## 4) Data Model (Essentials)

Entity highlights (SQLAlchemy):

- `User` (`backend/app/models/user.py`)
  - `id (UUID)`, `email`, `azure_id`, `first_name`, `last_name`, `role`, `is_active`
  - `organization_id` FK → `Organization`
  - Relationships: `organization`, `scans`, `reports`, `chat_sessions`

- `Organization` (`backend/app/models/organization.py`)
  - `id (UUID)`, `name`, `domain`, `subscription_tier`, quota fields
  - Relationships: `users`, `scans`

- `Scan`, `Report`, `ChatSession`, `Compliance` (present in `backend/app/models/`)
  - Store scan metadata, findings summary, generated reports, chat threads


## 5) Security & Compliance

- Authentication: JWT (access/refresh) with `python-jose`; short‑lived access, longer refresh
- Authorization: role- and permission‑aware helpers in `dependencies.py`
- CORS: restricted to dev origins (regex in enhanced backend) or `settings.cors_origins`
- Trusted Hosts: `localhost`, `127.0.0.1`, domain allowlist (prod)
- Secrets: `.env` loaded by settings; recommend Vault/Key Vault in production
- Rate limiting & audit logging: listed in README roadmap; not fully implemented in modular app yet

Hardening recommendations:
- Rotate any secrets committed accidentally
- Enforce HTTPS and secure cookies on the frontend/proxy
- Add rate limiting (e.g., SlowAPI) and audit trail sinks
- Implement token revocation/blacklist for logout


## 6) Report JSON Contract (`reports_output.json`)

Example structure (root fields):

```json
{
  "reports": [ { ... } ],
  "total": 3,
  "available_types": ["CIS", "SOC2", "NIST", "ISO27001"],
  "generated_from_scans": 0
}
```

Per‑report fields:

- `id` / `report_id`: unique identifier
- `name`: human‑readable title (e.g., "CIS Compliance Report - Security Scan")
- `type` / `framework`: compliance framework
- `status`: generation status (e.g., `generated`)
- `environment`: e.g., `production`
- `created_at` / `generated_at`: timestamps
- `scan_id`: associated scan
- `compliance_score`: aggregate score (0‑100)
- `executive_summary`: high‑level narrative
- `recommendations`: array of actionable items
- `findings_summary`: `{ total_findings, critical, high, medium, low }`
- `scan_details`: `{ total_checks, passed_checks, failed_checks, scan_duration, target_resources[] }`

Mapping to flows:
- Created by Report Generation (Section 3.5) from scan results and AI analysis
- Serves as source for PDF rendering and frontend dashboards


## 7) Operational Modes & Local Development

Modular app (recommended):
- Dev server: `uvicorn app.main:app --reload` in `backend/`
- Configure `.env` from `backend/env.example`
- API docs: `http://localhost:8000/docs`

Enhanced demo backend:
- Run: `python backend/start_backend.py`
- Demo auth and subscriptions without Azure/OAuth
- API: `http://127.0.0.1:9099`

Test auth service:
- Run: `python backend/test_auth.py`
- Test logins for admin/demo users; simple scans/subscriptions/users endpoints


## 8) Sequence Diagrams (Textual)

Auth (Azure OAuth2):

```
Frontend → /auth/login (code) → AuthService
AuthService → Azure Token API → access_token
AuthService → MS Graph /me → user profile
AuthService → DB → get_or_create_user
AuthService → Frontend → JWTs + user
```

Subscription Discovery:

```
Frontend → /subscriptions → AzureService
AzureService → (Azure SDK or mock) → subscriptions list
AzureService → Frontend → subscriptions payload
```

Report Generation:

```
Frontend → /reports (scan_id, framework) → ReportService
ReportService → DB/ScanService → scan results
ReportService → (AI optional) → remediation insights
ReportService → storage → JSON/PDF artifacts
ReportService → Frontend → report metadata/URL
```


## 9) Deployment Topology

- Frontend (React) → Nginx (static) and proxy → Backend (FastAPI)
- Backend → Postgres (SQLAlchemy), Redis (caching/queue, planned), Azure APIs, OpenAI APIs
- Docker Compose (per README), with networks for frontend/backend/db/cache

Environment variables (selected):
- `DATABASE_URL`, `SECRET_KEY`, `AZURE_*`, `OPENAI_*`, `CORS_ORIGINS`, `LOG_LEVEL`


## 10) Gaps & Roadmap

- Rate limiting and audit logging plumbing in modular app
- Background job processing (Celery/Redis) for long scans
- Modernize OpenAI usage to `openai>=1.x` client across all files
- Tighten role/permission model and persist permissions per role
- Add comprehensive tests and CI pipelines


## 11) How to Extend

- New compliance framework:
  - Add framework constants and checks
  - Extend ReportService to aggregate scoring rules
  - Add PDF/JSON templates for the framework

- New cloud provider (AWS/GCP):
  - Create `aws_service.py` / `gcp_service.py` mirroring `AzureService`
  - Add endpoints under `/api/v1/providers/{provider}`
  - Abstract ScanService to provider‑agnostic interface

- Observability:
  - Add request IDs, structured logs shipping to ELK/Datadog
  - Expose Prometheus metrics and health endpoints per service


---

This design reflects the current repository state and intended production architecture. Demo helpers remain available for rapid UI development while the modular app evolves toward full feature parity and operations readiness.

