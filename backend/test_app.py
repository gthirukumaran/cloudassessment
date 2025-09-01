"""
Simple test script to run the FastAPI app without database dependencies
"""
import os
import sys
from unittest.mock import patch

# Set environment variables for testing
os.environ['DATABASE_URL'] = 'sqlite:///./test.db'
os.environ['SECRET_KEY'] = 'test-secret-key'
os.environ['AZURE_CLIENT_ID'] = 'test-client-id'
os.environ['AZURE_CLIENT_SECRET'] = 'test-client-secret'
os.environ['AZURE_TENANT_ID'] = 'test-tenant-id'
os.environ['AZURE_REDIRECT_URI'] = 'http://localhost:3000/auth/callback'
os.environ['OPENAI_API_KEY'] = 'test-openai-key'
os.environ['DEBUG'] = 'true'

# Mock the database initialization
def mock_init_db():
    print("Mocked database initialization - skipping for testing")
    return True

# Import and patch the app
from app.main import app

# Patch the startup event to skip database initialization
@app.on_event("startup")
async def test_startup_event():
    """Test startup event without database"""
    print("Starting Securra application in test mode")
    print("Database initialization skipped for testing")

if __name__ == "__main__":
    import uvicorn
    print("Starting Securra Backend in Test Mode")
    print("Access the API at: http://127.0.0.1:8000")
    print("API Documentation at: http://127.0.0.1:8000/docs")
    print("Health Check at: http://127.0.0.1:8000/health")
    uvicorn.run(
        "test_app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
