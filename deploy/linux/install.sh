#!/usr/bin/env bash
# ============================================================
#  JARVIS — Linux Install Script
#  Sets up everything and creates a desktop entry
# ============================================================

set -e

echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║     JARVIS — Linux Installer              ║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."  # Go to project root
PROJECT_DIR="$(pwd)"

# 1. Install system dependencies
echo "[*] Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq \
        python3 python3-pip python3-venv \
        portaudio19-dev python3-pyaudio \
        espeak espeak-ng ffmpeg
elif command -v dnf &> /dev/null; then
    sudo dnf install -y python3 python3-pip portaudio-devel espeak ffmpeg
elif command -v pacman &> /dev/null; then
    sudo pacman -Sy --noconfirm python python-pip portaudio espeak ffmpeg
else
    echo "[WARNING] Unknown package manager. Install dependencies manually."
    echo "          Required: python3, python3-pip, portaudio, espeak"
fi

# 2. Create virtual environment
echo "[*] Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 3. Copy .env.example if .env doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[*] Created .env — add your API keys to enable AI features."
fi

# 4. Create desktop entry
echo "[*] Creating desktop entry..."
DESKTOP_FILE="$HOME/.local/share/applications/jarvis.desktop"
mkdir -p "$HOME/.local/share/applications"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Name=JARVIS
Comment=Self-Evolving AI Assistant
Exec=${PROJECT_DIR}/deploy/linux/run.sh
Icon=${PROJECT_DIR}/assets/face/jarvis-icon.png
Terminal=true
Type=Application
Categories=Utility;ArtificialIntelligence;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"
chmod +x "$SCRIPT_DIR/run.sh"

echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║     INSTALLATION COMPLETE!                ║"
echo "  ║                                           ║"
echo "  ║  Run JARVIS:                              ║"
echo "  ║    ./deploy/linux/run.sh                  ║"
echo "  ║    or search 'JARVIS' in your app menu    ║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""
