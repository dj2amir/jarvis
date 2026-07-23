@echo off
REM ============================================================
REM  JARVIS — Self-Bootstrapping Dependency Installer (Windows)
REM  Installs all required packages automatically.
REM  The only external dependency you need is an LLM API.
REM ============================================================

setlocal enabledelayedexpansion

echo.
echo === JARVIS Bootstrap Installer (Windows) ===
echo.

REM ── Check Python ──
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ✗ Python 3 is not installed!
    echo   Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo.

REM ── Upgrade pip ──
python -m pip install --quiet --upgrade pip

REM ── Install dependencies ──
echo Installing JARVIS dependencies...

set VENDOR_DIR=%~dp0packages
if exist "%VENDOR_DIR%" (
    dir "%VENDOR_DIR%" /b >nul 2>&1
    if not errorlevel 1 (
        echo Using vendored packages from vendor/packages/
        python -m pip install --no-index --find-links "%VENDOR_DIR%" -r "%~dp0..\requirements.txt"
        goto :done
    )
)

echo No vendored packages found - downloading from PyPI...
python -m pip install -r "%~dp0..\requirements.txt"

:done
echo.
echo ===========================================
echo  ✓ JARVIS dependencies installed!
echo  Run: python main.py
echo ===========================================
echo.
echo Only LLM connection needed:
echo   - Set OPENAI_API_KEY in .env
echo   - Or use local LM Studio at http://localhost:1234
echo.
pause
