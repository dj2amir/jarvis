@echo off
REM ============================================================
REM  JARVIS — Windows Run Script (Development Mode)
REM  Runs JARVIS from source with virtual environment
REM ============================================================
echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     JARVIS — Starting Up...               ║
echo  ╚═══════════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+.
    pause
    exit /b 1
)

REM Create venv if needed
if not exist venv\ (
    echo [*] First run: setting up virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Check if .env exists
if not exist .env (
    echo.
    echo [WARNING] No .env file found!
    echo [INFO]    Copying .env.example to .env
    echo [INFO]    Edit .env and add your API keys before using voice/AI features.
    copy /Y .env.example .env >nul
    echo.
)

echo [*] Launching JARVIS...
echo.
python main.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] JARVIS crashed. Check the error above.
    pause
)
