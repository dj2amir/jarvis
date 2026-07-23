#!/usr/bin/env bash
# ============================================================
#  JARVIS — Linux Run Script (Development Mode)
#  Runs JARVIS from source with virtual environment
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."  # Go to project root

echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║     JARVIS — Starting Up...               ║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 not found! Install it:"
    echo "        sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "[*] First run: setting up virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
else
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "[WARNING] No .env file found!"
    echo "[INFO]    Copying .env.example to .env"
    echo "[INFO]    Edit .env and add your API keys."
    cp .env.example .env
    echo ""
fi

echo "[*] Launching JARVIS..."
echo ""
python3 main.py

echo ""
echo "[*] JARVIS has stopped."
