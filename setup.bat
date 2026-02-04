@echo off
REM Quick Start Script for AI Interview System (Windows)

echo ==================================================
echo AI Interview System - Quick Start Setup
echo ==================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3.10 or higher.
    exit /b 1
)

echo Python found
python --version
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)

echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install dependencies
    exit /b 1
)

echo Dependencies installed successfully
echo.

REM Check if .env file exists
if not exist ".env" (
    echo Creating .env file from template...
    copy .env.example .env
    echo .env file created
    echo.
    echo IMPORTANT: Please edit .env file with your API keys:
    echo    - GOOGLE_API_KEY
    echo    - LIVEKIT_URL
    echo    - LIVEKIT_API_KEY
    echo    - LIVEKIT_API_SECRET
    echo.
    echo Get your API keys from:
    echo    - Google Gemini: https://aistudio.google.com/app/apikey
    echo    - LiveKit: https://cloud.livekit.io
    echo.
) else (
    echo .env file already exists
    echo.
)

REM Create necessary directories
echo Creating directories...
if not exist "recordings" mkdir recordings
if not exist "transcripts" mkdir transcripts
if not exist "evaluations" mkdir evaluations
echo Directories created
echo.

REM Run setup test
echo Running setup verification test...
python tests\test_setup.py

echo.
echo ==================================================
echo Setup Complete!
echo ==================================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys (if not already done)
echo 2. Run the agent: python src\agent.py dev
echo 3. Connect a candidate to start an interview
echo.
echo For more information, see README.md
echo.

pause
