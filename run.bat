@echo off
REM NX88 Casino - Backend Startup Script (Windows)

echo.
echo 🎰 NX88 Casino Backend - Startup
echo ==================================
echo.

REM Check if .env exists
if not exist .env (
    echo ⚠️  .env file not found!
    echo Creating .env from .env.example...
    copy .env.example .env
    echo ✏️  Please edit .env with your Discord OAuth credentials
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment if it doesn't exist
if not exist venv (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📚 Installing dependencies...
pip install -q -r requirements.txt

echo.
echo 🚀 Starting NX88 Casino API Server...
echo 📍 Server: http://localhost:8000
echo 📚 Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop
echo.

REM Start the server
python main.py

pause
