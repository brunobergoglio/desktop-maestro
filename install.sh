#!/usr/bin/env bash
# =============================================================================
# 🧹 DesktopMaestro – One-line installer
# =============================================================================
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/brunobergoglio/desktop-maestro/main/install.sh | bash
#   # or just:
#   bash install.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║     🧹  DesktopMaestro Installer                             ║${NC}"
echo -e "${BLUE}║     ─────────────────────────────                             ║${NC}"
echo -e "${BLUE}║     Smart desktop organizer for macOS                        ║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Check Python ───
echo -e "${CYAN}🔍 Checking requirements...${NC}"

PYTHON=""
for cmd in python3 python; do
    if command -v $cmd &>/dev/null; then
        VER=$($cmd -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")' 2>/dev/null || echo "0")
        MAJOR=$(echo $VER | cut -d. -f1)
        MINOR=$(echo $VER | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
            PYTHON=$cmd
            echo -e "  ✅ Python $VER found: $(which $cmd)"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo -e "${RED}❌ Python 3.9+ is required. Install it:${NC}"
    echo "   brew install python"
    exit 1
fi

# ─── Check pip ───
PIP=""
for cmd in pip3 pip; do
    if command -v $cmd &>/dev/null; then
        PIP=$cmd
        break
    fi
done

if [ -z "$PIP" ]; then
    echo -e "${YELLOW}⚠️  pip not found, installing...${NC}"
    $PYTHON -m ensurepip --upgrade 2>/dev/null || true
    PIP="pip3"
fi

# ─── Install Python package ───
echo ""
echo -e "${CYAN}📦 Installing DesktopMaestro...${NC}"
$PIP install -e . 2>/dev/null || $PIP install desktopmaestro 2>/dev/null || {
    echo -e "${YELLOW}📦 Installing from source...${NC}"
    $PYTHON -m pip install -e .
}

echo -e "${GREEN}✅ DesktopMaestro installed!${NC}"
echo ""

# ─── Verify installation ───
if command -v desktopmaestro &>/dev/null; then
    echo -e "${GREEN}✅ CLI ready: $(desktopmaestro --version 2>&1)${NC}"
else
    echo -e "${YELLOW}⚠️  CLI not in PATH. Add to your shell:${NC}"
    echo '   export PATH="$PATH:$HOME/.local/bin"'
fi

# ─── Frontend (optional) ───
if command -v node &>/dev/null; then
    echo ""
    echo -e "${CYAN}📱 Node.js found. Installing frontend dependencies...${NC}"
    cd "$(dirname "$0")/frontend" 2>/dev/null || true
    if [ -f "package.json" ]; then
        npm install --silent 2>/dev/null && echo -e "${GREEN}✅ Frontend dependencies installed${NC}" || echo -e "${YELLOW}⚠️  npm install failed (run manually: cd frontend && npm install)${NC}"
    fi
    cd - >/dev/null 2>&1 || true
fi

# ─── Done ───
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅  DesktopMaestro installed successfully!                  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}🧹  Simulate:${NC}     desktopmaestro organize --dry-run"
echo -e "  ${CYAN}🌐  English:${NC}      desktopmaestro organize --dry-run --lang en"
echo -e "  ${CYAN}🌐  Español:${NC}      desktopmaestro organize --dry-run --lang es"
echo -e "  ${CYAN}📊  Stats:${NC}        desktopmaestro stats"
echo -e "  ${CYAN}🌍  Web UI:${NC}       desktopmaestro web"
echo -e "  ${CYAN}❓  Help:${NC}         desktopmaestro --help"
echo ""
echo -e "  ${YELLOW}💡  Pro tip: Start with --dry-run to preview changes!${NC}"
echo ""
