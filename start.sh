#!/usr/bin/env bash
# =============================================================================
# 🧹 DesktopMaestro – Quick Start (API server + Frontend)
# =============================================================================
# This script starts both the API server and the Next.js frontend.
# Usage: bash start.sh
# =============================================================================

set -euo pipefail

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     🧹  DesktopMaestro                                      ║${NC}"
echo -e "${BLUE}║     Starting API server + Frontend                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Check dependencies ───
if ! command -v desktopmaestro &>/dev/null; then
    echo -e "${YELLOW}📦 Installing DesktopMaestro...${NC}"
    pip install -e "$SCRIPT_DIR" 2>/dev/null || pip3 install -e "$SCRIPT_DIR"
fi

# ─── Start API server in background ───
echo -e "${CYAN}🌐 Starting API server on http://127.0.0.1:7899...${NC}"
desktopmaestro web &
API_PID=$!
echo -e "${GREEN}✅ API server PID: $API_PID${NC}"

# ─── Start frontend ───
if command -v node &>/dev/null && [ -f "$SCRIPT_DIR/frontend/package.json" ]; then
    echo -e "${CYAN}📱 Starting frontend on http://localhost:3000...${NC}"
    cd "$SCRIPT_DIR/frontend"
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing frontend dependencies...${NC}"
        npm install --silent
    fi
    npm run dev &
    FE_PID=$!
    echo -e "${GREEN}✅ Frontend PID: $FE_PID${NC}"
    cd "$SCRIPT_DIR"
else
    echo -e "${YELLOW}⚠️  Frontend not available (Node.js or package.json missing)${NC}"
    echo -e "${YELLOW}   Install manually: cd frontend && npm install && npm run dev${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  🧹  DesktopMaestro is running!                             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}📊  API:${NC}         http://127.0.0.1:7899/api/health"
echo -e "  ${CYAN}📱  Frontend:${NC}    http://localhost:3000"
echo -e "  ${CYAN}🧹  CLI:${NC}         desktopmaestro organize --dry-run"
echo -e "  ${CYAN}🌐  Español:${NC}     desktopmaestro organize --dry-run --lang es"
echo -e "  ${CYAN}🛑  Stop:${NC}        Press Ctrl+C"
echo ""

# ─── Wait for Ctrl+C ───
trap "echo ''; echo -e '${YELLOW}🛑 Stopping...${NC}'; kill $API_PID $FE_PID 2>/dev/null; exit 0" SIGINT SIGTERM
wait
