@echo off
REM ============================================================
REM  JARVIS — Windows Build Script (PyInstaller)
REM  Creates JARVIS.exe in deploy/windows/dist/
REM ============================================================
echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     JARVIS — Windows Build Tool           ║
echo  ╚═══════════════════════════════════════════╝
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.10+ from:
    echo         https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if venv exists, create if not
if not exist venv\ (
    echo [*] Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install requirements
echo [*] Installing dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q pyinstaller

REM Clean previous build
echo [*] Cleaning previous builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

REM Build with PyInstaller
echo [*] Building JARVIS.exe (this may take a few minutes)...
pyinstaller --onedir ^
    --name "JARVIS" ^
    --add-data "config;config" ^
    --add-data "core;core" ^
    --add-data ".env.example;." ^
    --hidden-import openai ^
    --hidden-import anthropic ^
    --hidden-import sounddevice ^
    --hidden-import edge_tts ^
    --hidden-import pygame ^
    --hidden-import cv2 ^
    --hidden-import mediapipe ^
    --hidden-import chromadb ^
    --hidden-import sentence_transformers ^
    --hidden-import psutil ^
    --hidden-import yaml ^
    --hidden-import rich ^
    --collect-all ultralytics ^
    main.py

if %errorlevel% neq 0 (
    echo [ERROR] Build failed! Check the output above.
    pause
    exit /b 1
)

REM Copy config files
echo [*] Copying configuration files...
xcopy /E /I /Y config dist\JARVIS\config >nul
copy /Y .env.example dist\JARVIS\.env.example >nul

echo.
echo  ╔═══════════════════════════════════════════╗
echo  ║     BUILD SUCCESSFUL!                     ║
echo  ║     Location: dist\JARVIS\JARVIS.exe      ║
echo  ╚═══════════════════════════════════════════╝
echo.
echo  To run: dist\JARVIS\JARVIS.exe
echo  To create shortcut: Right-click JARVIS.exe ^> Send to Desktop
echo.

pause
