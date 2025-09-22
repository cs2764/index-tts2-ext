@echo off
REM Enhanced IndexTTS2 WebUI Setup Script for Windows
REM This script automates the setup process

echo Enhanced IndexTTS2 WebUI Setup
echo ================================

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 or higher.
    pause
    exit /b 1
)

echo Python found. Checking version...
python -c "import sys; exit(0 if sys.version_info >= (3, 10) else 1)"
if errorlevel 1 (
    echo ERROR: Python 3.10 or higher required.
    pause
    exit /b 1
)

echo Python version OK.

REM Run the Python setup script
echo Running setup script...
python scripts/setup_enhanced_webui.py %*

if errorlevel 1 (
    echo Setup failed. Check the output above for errors.
    pause
    exit /b 1
)

echo.
echo Setup completed successfully!
echo.
echo Next steps:
echo 1. Review configuration in config/user_config.yaml
echo 2. Add voice samples to the samples/ directory  
echo 3. Run the WebUI: uv run webui.py
echo.
pause