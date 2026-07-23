#!/usr/bin/env bash
# ============================================================
#  JARVIS — Self-Bootstrapping Dependency Installer (Linux/Mac)
#  Installs all required packages automatically.
#  The only external dependency you need is an LLM API.
# ============================================================

set -e

DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$DIR")"
VENV_DIR="$PROJECT_DIR/venv"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     JARVIS — Bootstrap Installer          ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════╝${NC}"
echo ""

# ── Detect OS ──
OS="$(uname -s)"
case "$OS" in
    Linux*)   MACHINE=linux ;;
    Darwin*)  MACHINE=mac ;;
    *)        MACHINE=unknown ;;
esac
echo -e "${BLUE}  ⟳ Detected OS:${NC} $MACHINE"
echo ""

# ── Check Python ──
PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        PYTHON="$cmd"
        break
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}  ✗ Python 3 is not installed!${NC}"
    echo "  Please install Python 3.10+ first:"
    echo "    https://www.python.org/downloads/"
    exit 1
fi

PY_VER=$("$PYTHON" --version 2>&1 | grep -oP '\d+\.\d+')
echo -e "${BLUE}  ⟳ Python:${NC} $("$PYTHON" --version)"
echo ""

# ── Check pip ──
if ! "$PYTHON" -m pip --version &>/dev/null; then
    echo -e "${YELLOW}  ⚠ pip not found — installing...${NC}"
    curl -sS https://bootstrap.pypa.io/get-pip.py | "$PYTHON"
fi
echo -e "${BLUE}  ⟳ pip:${NC} $("$PYTHON" -m pip --version)"
echo ""

# ── Upgrade pip ──
"$PYTHON" -m pip install --quiet --upgrade pip

# ── Optional: Create virtualenv ──
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}  ⚠ No virtualenv found.${NC}"
    echo -n "  Create one? [Y/n]: "
    read -r answer
    if [[ "$answer" =~ ^[Yy]?$ ]]; then
        "$PYTHON" -m venv "$VENV_DIR"
        echo -e "${GREEN}  ✓ Virtualenv created at $VENV_DIR${NC}"
        echo "  Activate it: source $VENV_DIR/bin/activate"
        PYTHON="$VENV_DIR/bin/$PYTHON"
    fi
fi

# ── Install dependencies ──
echo ""
echo -e "${BLUE}  ⟳ Installing JARVIS dependencies...${NC}"
echo ""

# Install from requirements (this respects --find-links if vendor dir has wheels)
VENDOR_PACKAGES="$DIR/packages"
if [ -d "$VENDOR_PACKAGES" ] && [ "$(ls -A "$VENDOR_PACKAGES" 2>/dev/null)" ]; then
    echo -e "${BLUE}  ⟳ Using vendored packages from vendor/packages/${NC}"
    "$PYTHON" -m pip install --no-index --find-links "$VENDOR_PACKAGES" -r "$PROJECT_DIR/requirements.txt" 2>&1 | while IFS= read -r line; do
        if [[ "$line" == *"Successfully installed"* ]]; then
            echo -e "  ${GREEN}✓${NC} $line"
        elif [[ "$line" == *"already satisfied"* ]]; then
            echo -e "  ${GREEN}✓${NC} $line"
        elif [[ "$line" == *"ERROR"* ]]; then
            echo -e "  ${RED}✗${NC} $line"
        else
            echo "  $line"
        fi
    done
else
    # Normal pip install (downloads from PyPI)
    echo -e "${YELLOW}  ⚠ No vendored packages found — downloading from PyPI${NC}"
    "$PYTHON" -m pip install -r "$PROJECT_DIR/requirements.txt" 2>&1 | tail -20
fi

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ JARVIS dependencies installed!        ║${NC}"
echo -e "${GREEN}║  Run: cd .. && python main.py             ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BLUE}Only LLM connection needed:${NC}"
echo -e "    - Set OPENAI_API_KEY in .env"
echo -e "    - Or use local LM Studio at http://localhost:1234"
echo ""
