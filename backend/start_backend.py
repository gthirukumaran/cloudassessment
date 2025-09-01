#!/usr/bin/env python3
"""
Simple startup script for Securra Backend
"""
import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting Securra Enhanced Backend")
    print("📍 URL: http://127.0.0.1:9099")
    print("📋 Features: Subscription Management, CIS/SOC Reports, AI Assistant, User Management")
    print("🔐 Test Credentials:")
    print("   Admin: admin@securra.com / admin123")
    print("   Analyst: analyst@securra.com / analyst123")
    print("   Demo: demo@securra.com / demo123")
    
    uvicorn.run("enhanced_backend:app", host="127.0.0.1", port=9099, reload=True)
