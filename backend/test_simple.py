#!/usr/bin/env python3
"""
Simple test script to check backend startup
"""
import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("🔍 Testing backend import...")
    import enhanced_backend
    print("✅ Backend import successful")
    
    print("🚀 Starting backend server...")
    uvicorn.run("enhanced_backend:app", host="127.0.0.1", port=9099, reload=False)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()



