# Securra - Cloud Security Assessment AI Tool

A comprehensive, AI-powered cloud security assessment platform that provides real-time scanning, intelligent analysis, and automated remediation recommendations for multi-cloud environments.

## 🚀 Features

- **Real-time Cloud Security Scanning**: Comprehensive security assessments for Azure, AWS, and GCP
- **AI-Powered Analysis**: GPT-4 integration for intelligent security analysis and remediation
- **CIS-Style Reports**: Professional PDF report generation with compliance frameworks
- **Interactive Chatbot**: AI assistant for security queries and guidance
- **Multi-Cloud Support**: Azure (active), AWS/GCP (roadmap)
- **Enterprise UI/UX**: Modern, responsive interface built with Material-UI
- **Role-Based Access Control**: Secure authentication with Azure OAuth2

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Frontend│    │   FastAPI Backend│    │   Cloud Services│
│                 │    │                  │    │                 │
│ - Dashboard     │◄──►│ - API Gateway    │◄──►│ - Azure         │
│ - Reports       │    │ - Auth Service   │    │ - AWS           │
│ - Chatbot       │    │ - Scan Engine    │    │ - GCP           │
│ - Analytics     │    │ - AI Analysis    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                               │
                      ┌──────────────────┐
                      │   Data Layer     │
                      │                  │
                      │ - PostgreSQL     │
                      │ - Redis Cache    │
                      │ - File Storage   │
                      └──────────────────┘
```

## 🛠️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **Material-UI (MUI)** for enterprise UI components
- **React Query** for state management and caching
- **React Router v6** for navigation
- **Chart.js** for data visualization
- **Vite** for fast development and building

### Backend
- **FastAPI** with Python 3.11+
- **SQLAlchemy ORM** with PostgreSQL
- **Redis** for caching and session management
- **Celery** for background tasks
- **Azure OAuth2** for authentication
- **OpenAI GPT-4** for AI analysis

### Infrastructure
- **Docker & Docker Compose** for containerization
- **PostgreSQL** for primary database
- **Redis** for caching and message queuing
- **Nginx** for frontend serving and API proxying

## 📋 Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **Azure App Registration** (for OAuth2)
- **OpenAI API Key** (for AI features)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd security-assessment
```

### 2. Set Up Environment Variables
```bash
# Copy the environment template
cp backend/env.example backend/.env

# Edit the .env file with your credentials
nano backend/.env
```

**Required Environment Variables:**
```env
# Azure OAuth2 Configuration
AZURE_CLIENT_ID=your-azure-client-id
AZURE_CLIENT_SECRET=your-azure-client-secret
AZURE_TENANT_ID=your-azure-tenant-id
AZURE_REDIRECT_URI=http://localhost:3000/auth/callback

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Security
SECRET_KEY=your-super-secret-key-here
```

### 3. Start the Application
```bash
# Make the startup script executable
chmod +x start.sh

# Run the startup script
./start.sh
```

Or manually:
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Development Setup

### Backend Development
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp env.example .env
# Edit .env with your credentials

# Run the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## 📊 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Azure OAuth2 login
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout user

### Scans
- `GET /api/v1/scans` - List all scans
- `POST /api/v1/scans` - Create new scan
- `GET /api/v1/scans/{scan_id}` - Get scan details
- `PUT /api/v1/scans/{scan_id}` - Update scan
- `DELETE /api/v1/scans/{scan_id}` - Delete scan

### Chatbot
- `POST /api/v1/chatbot/query` - Send chat query
- `GET /api/v1/chatbot/sessions` - List chat sessions
- `GET /api/v1/chatbot/sessions/{session_id}` - Get chat history

### Reports
- `GET /api/v1/reports` - List all reports
- `POST /api/v1/reports` - Generate new report
- `GET /api/v1/reports/{report_id}` - Get report details
- `GET /api/v1/reports/{report_id}/download` - Download PDF report

## 🐳 Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild and start
docker-compose up -d --build

# Access specific service logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f postgres
```

## 🔒 Security Features

- **Azure OAuth2 Authentication**: Enterprise-grade SSO
- **JWT Token Management**: Secure session handling
- **Role-Based Access Control**: Granular permissions
- **CORS Protection**: Cross-origin request security
- **Input Validation**: Comprehensive request validation
- **Rate Limiting**: API abuse prevention
- **Audit Logging**: Complete activity tracking

## 📈 Monitoring & Logging

- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Health Checks**: Service health monitoring
- **Metrics**: Performance and usage metrics
- **Error Tracking**: Comprehensive error handling and reporting

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📝 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AZURE_CLIENT_ID` | Azure App Registration Client ID | Yes | - |
| `AZURE_CLIENT_SECRET` | Azure App Registration Client Secret | Yes | - |
| `AZURE_TENANT_ID` | Azure Tenant ID | Yes | - |
| `AZURE_REDIRECT_URI` | OAuth2 Redirect URI | Yes | - |
| `OPENAI_API_KEY` | OpenAI API Key | Yes | - |
| `SECRET_KEY` | JWT Secret Key | Yes | - |
| `DATABASE_URL` | PostgreSQL Connection String | Yes | - |
| `REDIS_URL` | Redis Connection String | No | `redis://localhost:6379` |
| `DEBUG` | Debug Mode | No | `false` |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)

## 🗺️ Roadmap

- [ ] AWS Cloud Provider Support
- [ ] GCP Cloud Provider Support
- [ ] Advanced AI Models Integration
- [ ] Real-time Notifications
- [ ] Mobile Application
- [ ] Advanced Reporting Features
- [ ] Compliance Framework Expansion
- [ ] Multi-language Support

---

**Securra** - Empowering organizations with AI-driven cloud security assessment and remediation.
