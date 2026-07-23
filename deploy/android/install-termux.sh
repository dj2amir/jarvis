#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  JARVIS — Android Termux Install Script
#  Runs JARVIS on your Android phone via Termux
# ============================================================
#
# REQUIREMENTS:
#   1. Install Termux from F-Droid (not Google Play!)
#      https://f-droid.org/packages/com.termux/
#
#   2. Run this script:
#      bash install-termux.sh
#
# ============================================================

set -e

echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║     JARVIS — Android Installer            ║"
echo "  ║     (Termux Edition)                      ║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""

# 1. Update Termux packages
echo "[*] Updating Termux packages..."
pkg update -y -qq
pkg upgrade -y -qq

# 2. Install system dependencies
echo "[*] Installing system dependencies..."
pkg install -y -qq \
    python \
    python-pip \
    clang \
    make \
    cmake \
    portaudio \
    espeak \
    ffmpeg \
    git \
    opencv \
    rust

# 3. Install Python packages
echo "[*] Installing Python packages..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 4. Create .env from example
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[*] Created .env — add your API keys!"
fi

# 5. Create launcher script
echo "[*] Creating launcher..."
cat > ~/.shortcuts/jarvis << 'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd ~/storage/shared/jarvis
source venv/bin/activate
python main.py
EOF
chmod +x ~/.shortcuts/jarvis 2>/dev/null || true

echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║     INSTALLATION COMPLETE!                ║"
echo "  ║                                           ║"
echo "  ║  Run JARVIS:                              ║"
echo "  ║    cd jarvis-core && python main.py       ║"
echo "  ║                                           ║"
echo "  ║  Voice may need Termux:API:               ║"
echo "  ║    pkg install termux-api                 ║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""
