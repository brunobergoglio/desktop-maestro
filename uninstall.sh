#!/usr/bin/env bash
# =============================================================================
# 🧹 DesktopMaestro – Desinstalador oficial
# =============================================================================
# Uso: bash uninstall.sh
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                          ║${NC}"
echo -e "${BLUE}║     🧹  DesktopMaestro — Desinstalador                   ║${NC}"
echo -e "${BLUE}║                                                          ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Confirmar
echo -e "${YELLOW}⚠️   Esto eliminará DesktopMaestro y toda su configuración.${NC}"
echo -e "${YELLOW}    Los archivos organizados en tu escritorio NO se tocan.${NC}"
echo ""
read -p "  ¿Continuar? [s/N]: " CONFIRM
if [[ ! "$CONFIRM" =~ ^[sS]$ ]]; then
    echo -e "${BLUE}  ❌ Desinstalación cancelada${NC}"
    exit 0
fi

echo ""

# 1. Detener y eliminar LaunchAgent
PLIST="$HOME/Library/LaunchAgents/com.desktopmaestro.plist"
if [[ -f "$PLIST" ]]; then
    echo -e "${BLUE}  ⏹️   Deteniendo LaunchAgent…${NC}"
    launchctl unload "$PLIST" 2>/dev/null || true
    rm -f "$PLIST"
    echo -e "${GREEN}  ✅  LaunchAgent eliminado${NC}"
fi

# 2. Desinstalar paquete pip
echo -e "${BLUE}  📦  Desinstalando paquete Python…${NC}"
pip3 uninstall desktopmaestro -y 2>/dev/null || true
pip uninstall desktopmaestro -y 2>/dev/null || true
echo -e "${GREEN}  ✅  Paquete desinstalado${NC}"

# 3. Eliminar configuración
CONFIG_DIR="$HOME/.config/desktopmaestro"
if [[ -d "$CONFIG_DIR" ]]; then
    echo -e "${YELLOW}  ⚙️   Eliminando configuración…${NC}"
    rm -rf "$CONFIG_DIR"
    echo -e "${GREEN}  ✅  Configuración eliminada${NC}"
fi

# 4. Eliminar logs
LOG_DIR="$HOME/Library/Logs/DesktopMaestro"
if [[ -d "$LOG_DIR" ]]; then
    echo -e "${BLUE}  🗑️   Eliminando logs…${NC}"
    rm -rf "$LOG_DIR"
    echo -e "${GREEN}  ✅  Logs eliminados${NC}"
fi

# 5. Eliminar alias del shell
for rc in "$HOME/.zshrc" "$HOME/.bashrc" "$HOME/.bash_profile"; do
    if [[ -f "$rc" ]]; then
        sed -i '' '/# DesktopMaestro alias/d' "$rc" 2>/dev/null || true
        sed -i '' '/alias dmaestro/d' "$rc" 2>/dev/null || true
    fi
done

echo ""
echo -e "${GREEN}${BOLD}  ✅  DesktopMaestro desinstalado correctamente${NC}"
echo -e "${BLUE}  📝  Los archivos de tu escritorio no fueron modificados${NC}"
echo -e "${CYAN}  💡  Volvé a instalar cuando quieras:${NC}"
echo -e "${CYAN}      bash <(curl -sSL https://desktopmaestro.dev/install.sh)${NC}"
echo ""
