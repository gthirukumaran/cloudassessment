@echo off
echo 🚀 Starting Securra - Local Development Mode
echo ================================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ Python is not installed. Please install Python 3.8+ first.
        pause
        exit /b 1
    )
)

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ first.
    pause
    exit /b 1
)

echo ✅ Python and Node.js are available

REM Set up backend
echo 📦 Setting up Python backend...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

REM Set up frontend
echo 📦 Setting up React frontend...
cd ..\frontend

REM Install Node.js dependencies
echo Installing Node.js dependencies...
npm install

echo.
echo 🎉 Setup complete!
echo.
echo To start the application:
echo 1. Backend: cd backend ^&^& venv\Scripts\activate ^&^& uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
echo 2. Frontend: cd frontend ^&^& npm start
echo.
echo Note: You'll need to set up PostgreSQL and Redis separately, or update the .env file to use cloud services.
echo.
echo For now, you can test the backend API at: http://localhost:8000/docs
pause
