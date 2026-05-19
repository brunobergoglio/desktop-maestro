# =============================================================================
# 🧹 DesktopMaestro – Makefile
# =============================================================================
# Commands:
#   make install        → Install Python package (editable)
#   make install-dev    → Install with dev dependencies
#   make install-all    → Install everything (Python + Frontend)
#   make uninstall      → Uninstall
#   make test           → Run tests
#   make test-cov       → Tests with coverage
#   make lint           → Lint code
#   make format         → Format code (black)
#   make clean          → Clean temp files
#   make build          → Build distributable package
#   make dmg            → Create .dmg for distribution
#   make run            → Simulate organization (dry-run)
#   make run-es         → Simulate with Spanish folder names
#   make demo           → Create demo test folder
#   make undo           → Undo last organization
#   make schedule       → Enable scheduled organization
#   make web            → Start web UI server
#   make frontend       → Start Next.js frontend (dev mode)
#   make help           → Show this help
# =============================================================================

.PHONY: install install-dev install-all uninstall test test-cov lint format clean build dmg run run-es demo undo schedule web frontend docker-build docker-up docker-down docker-logs docker-restart docker-dev help

VERSION := $(shell grep 'version =' pyproject.toml | head -1 | cut -d'"' -f2)
APP_NAME := DesktopMaestro
BUNDLE_ID := com.desktopmaestro

# ─── Colors ─────────────────────────────────────────────────────────────────
GREEN  := \033[0;32m
BLUE   := \033[0;34m
YELLOW := \033[1;33m
RED    := \033[0;31m
CYAN   := \033[0;36m
BOLD   := \033[1m
NC     := \033[0m

# ─── Installation ────────────────────────────────────────────────────────────

install:
	@echo "$(BLUE)📦 Instalando DesktopMaestro...$(NC)"
	@pip install -e .
	@echo "$(GREEN)✅ DesktopMaestro v$(VERSION) instalado$(NC)"
	@echo "$(CYAN)💡 Usá: desktopmaestro organize --dry-run$(NC)"

install-dev:
	@echo "$(BLUE)📦 Instalando con dependencias de desarrollo...$(NC)"
	@pip install -e ".[dev]"
	@echo "$(GREEN)✅ DesktopMaestro + dev dependencies instalados$(NC)"

uninstall:
	@echo "$(YELLOW)🗑️  Desinstalando DesktopMaestro...$(NC)"
	@pip uninstall desktopmaestro -y 2>/dev/null || true
	@rm -rf $(HOME)/.config/desktopmaestro 2>/dev/null || true
	@echo "$(GREEN)✅ DesktopMaestro desinstalado$(NC)"

reinstall: uninstall install

install-all: install
	@echo "$(BLUE)📦 Installing frontend dependencies...$(NC)"
	@cd frontend && npm install 2>/dev/null || echo "$(YELLOW)⚠️  npm not found. Install Node.js first: brew install node$(NC)"
	@echo "$(GREEN)✅ All dependencies installed$(NC)"

# ─── Tests ───────────────────────────────────────────────────────────────────

test:
	@echo "$(BLUE)🧪 Ejecutando tests...$(NC)"
	@python -m pytest tests/ -v
	@echo "$(GREEN)✅ Tests completados$(NC)"

test-cov:
	@echo "$(BLUE)📊 Ejecutando tests con cobertura...$(NC)"
	@python -m pytest tests/ -v --cov=organizer --cov-report=term --cov-report=html
	@echo "$(GREEN)✅ Cobertura generada en htmlcov/$(NC)"

# ─── Linting ─────────────────────────────────────────────────────────────────

lint:
	@echo "$(BLUE)🔍 Verificando estilo de código...$(NC)"
	@python -m ruff check organizer/ tests/
	@echo "$(GREEN)✅ Sin problemas de estilo$(NC)"

format:
	@echo "$(BLUE)✨ Formateando código...$(NC)"
	@python -m black organizer/ tests/
	@echo "$(GREEN)✅ Código formateado$(NC)"

# ─── Cleanup ────────────────────────────────────────────────────────────────

clean:
	@echo "$(YELLOW)🧹 Limpiando archivos temporales...$(NC)"
	@rm -rf build/ dist/ *.egg-info/ .eggs/
	@rm -rf __pycache__/ organizer/__pycache__/ tests/__pycache__/
	@rm -rf .pytest_cache/ htmlcov/ .coverage
	@rm -rf *.dmg *.app
	@find . -name '*.pyc' -delete
	@find . -name '__pycache__' -type d -delete
	@echo "$(GREEN)✅ Cleanup complete$(NC)"

# ─── Build ───────────────────────────────────────────────────────────────────

build:
	@echo "$(BLUE)📦 Construyendo paquete...$(NC)"
	@python -m build
	@echo "$(GREEN)✅ Paquete creado en dist/$(NC)"
	@ls -lh dist/

# ─── DMG (disk image) ────────────────────────────────────────────────────────

dmg: build
	@echo "$(BLUE)💿 Creando DMG...$(NC)"
	@mkdir -p dist/dmg
	@cp dist/desktopmaestro-$(VERSION)-py3-none-any.whl dist/dmg/
	@cp install.sh dist/dmg/
	@cp README.md dist/dmg/
	@cp LICENSE dist/dmg/
	@cp config/default_config.yaml dist/dmg/
	@printf '\342\225\224\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\342\225\220\n' > dist/dmg/INSTALL.txt
	@echo "🧹 DesktopMaestro - Manual Installation" >> dist/dmg/INSTALL.txt
	@echo "========================================" >> dist/dmg/INSTALL.txt
	@echo "" >> dist/dmg/INSTALL.txt
	@echo "1. Abrí Terminal (está en Aplicaciones/Utilidades)" >> dist/dmg/INSTALL.txt
	@echo "2. Ejecutá: bash install.sh" >> dist/dmg/INSTALL.txt
	@echo "3. Seguí las instrucciones en pantalla" >> dist/dmg/INSTALL.txt
	@echo "" >> dist/dmg/INSTALL.txt
	@echo "O instalá manualmente:" >> dist/dmg/INSTALL.txt
	@echo "   pip install desktopmaestro-$(VERSION)-py3-none-any.whl" >> dist/dmg/INSTALL.txt
	@hdiutil create -volname "$(APP_NAME) $(VERSION)" \
		-srcfolder dist/dmg/ \
		-ov -format UDZO \
		"dist/DesktopMaestro-$(VERSION).dmg"
	@rm -rf dist/dmg/
	@echo "$(GREEN)✅ DMG creado: dist/DesktopMaestro-$(VERSION).dmg$(NC)"

# ─── Homebrew Formula ────────────────────────────────────────────────────────

homebrew:
	@echo "$(BLUE)🍺 Creando Homebrew formula...$(NC)"
	@mkdir -p dist/homebrew
	@SHA256=$$(shasum -a 256 dist/desktopmaestro-$(VERSION)-py3-none-any.whl 2>/dev/null | cut -d' ' -f1 || echo "REPLACE_WITH_ACTUAL_SHA256"); \
	formula="dist/homebrew/desktopmaestro.rb"; \
	echo '# typed: false' > $$formula; \
	echo '# frozen_string_literal: true' >> $$formula; \
	echo '' >> $$formula; \
	echo 'class Desktopmaestro < Formula' >> $$formula; \
	echo '  desc "Smart desktop organizer for macOS"' >> $$formula; \
	echo '  homepage "https://github.com/brunitobe/desktopmaestro"' >> $$formula; \
	echo "  url \"https://github.com/brunitobe/desktopmaestro/releases/download/v$(VERSION)/desktopmaestro-$(VERSION)-py3-none-any.whl\"" >> $$formula; \
	echo "  sha256 \"$$SHA256\"" >> $$formula; \
	echo '  license "MIT"' >> $$formula; \
	echo '' >> $$formula; \
	echo '  depends_on "python@3"' >> $$formula; \
	echo '' >> $$formula; \
	echo '  def install' >> $$formula; \
	echo '    system "pip3", "install", *std_pip_args(build_isolation: true), "."' >> $$formula; \
	echo '  end' >> $$formula; \
	echo '' >> $$formula; \
	echo '  test do' >> $$formula; \
	echo "    assert_match \"v$(VERSION)\", shell_output(\"#{bin}/desktopmaestro --version\")" >> $$formula; \
	echo '  end' >> $$formula; \
	echo 'end' >> $$formula
	@echo "$(GREEN)✅ Formula creada: dist/homebrew/desktopmaestro.rb$(NC)"

# ─── .app Bundle (macOS) ─────────────────────────────────────────────────────

app:
	@echo "$(BLUE)📱 Creando $(APP_NAME).app...$(NC)"
	@mkdir -p "dist/$(APP_NAME).app/Contents/MacOS"
	@mkdir -p "dist/$(APP_NAME).app/Contents/Resources"
	@plist_path="dist/$(APP_NAME).app/Contents/Info.plist"; \
	printf '<?xml version="1.0" encoding="UTF-8"?>\n' > $$plist_path; \
	printf '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n' >> $$plist_path; \
	printf '<plist version="1.0">\n<dict>\n' >> $$plist_path; \
	printf '\t<key>CFBundleExecutable</key>\n\t<string>DesktopMaestro</string>\n' >> $$plist_path; \
	printf '\t<key>CFBundleIdentifier</key>\n\t<string>$(BUNDLE_ID)</string>\n' >> $$plist_path; \
	printf '\t<key>CFBundleName</key>\n\t<string>$(APP_NAME)</string>\n' >> $$plist_path; \
	printf '\t<key>CFBundleVersion</key>\n\t<string>$(VERSION)</string>\n' >> $$plist_path; \
	printf '\t<key>CFBundleShortVersionString</key>\n\t<string>$(VERSION)</string>\n' >> $$plist_path; \
	printf '\t<key>CFBundlePackageType</key>\n\t<string>APPL</string>\n' >> $$plist_path; \
	printf '\t<key>LSMinimumSystemVersion</key>\n\t<string>11.0</string>\n' >> $$plist_path; \
	printf '\t<key>NSHighResolutionCapable</key>\n\t<true/>\n' >> $$plist_path; \
	printf '\t<key>NSHumanReadableCopyright</key>\n\t<string>MIT License</string>\n' >> $$plist_path; \
	printf '</dict>\n</plist>\n' >> $$plist_path
	@launcher_path="dist/$(APP_NAME).app/Contents/MacOS/DesktopMaestro"; \
	printf '#!/bin/bash\n' > $$launcher_path; \
	printf '# DesktopMaestro macOS App Launcher\n' >> $$launcher_path; \
	printf 'open -a Terminal "$(BUNDLE_ID)" 2>/dev/null || desktopmaestro --help\n' >> $$launcher_path
	@chmod +x "dist/$(APP_NAME).app/Contents/MacOS/DesktopMaestro"
	@echo "$(GREEN)✅ $(APP_NAME).app creado en dist/$(NC)"

# ─── Run ─────────────────────────────────────────────────────────────────────

run:
	@echo "$(BLUE)🧹 Running DesktopMaestro (dry-run)...$(NC)"
	@desktopmaestro organize --dry-run

run-es:
	@echo "$(BLUE)🧹 Running DesktopMaestro (dry-run, Español)...$(NC)"
	@desktopmaestro organize --dry-run --lang es

run-real:
	@echo "$(YELLOW)⚠️  Running actual organization...$(NC)"
	@desktopmaestro organize

undo:
	@echo "$(BLUE)↩️  Deshaciendo última organización...$(NC)"
	@desktopmaestro undo

demo:
	@echo "$(BLUE)📁 Creando carpeta demo...$(NC)"
	@mkdir -p /tmp/DesktopMaestro-demo
	@touch /tmp/DesktopMaestro-demo/foto.jpg
	@touch /tmp/DesktopMaestro-demo/foto2.png
	@touch /tmp/DesktopMaestro-demo/documento.pdf
	@touch /tmp/DesktopMaestro-demo/informe.pdf
	@touch /tmp/DesktopMaestro-demo/video.mp4
	@touch /tmp/DesktopMaestro-demo/pelicula.mkv
	@touch /tmp/DesktopMaestro-demo/musica.mp3
	@touch /tmp/DesktopMaestro-demo/cancion.flac
	@touch /tmp/DesktopMaestro-demo/codigo.py
	@touch /tmp/DesktopMaestro-demo/app.js
	@touch /tmp/DesktopMaestro-demo/archivo.zip
	@touch /tmp/DesktopMaestro-demo/backup.tar.gz
	@touch /tmp/DesktopMaestro-demo/notas.txt
	@touch /tmp/DesktopMaestro-demo/presentacion.pptx
	@touch /tmp/DesktopMaestro-demo/hoja.xlsx
	@touch /tmp/DesktopMaestro-demo/libro.epub
	@touch /tmp/DesktopMaestro-demo/fuente.ttf
	@touch /tmp/DesktopMaestro-demo/torrent.torrent
	@touch /tmp/DesktopMaestro-demo/instalador.dmg
	@touch /tmp/DesktopMaestro-demo/script.sh
	@touch /tmp/DesktopMaestro-demo/datos.json
	@echo "$(GREEN)✅ Demo creada en /tmp/DesktopMaestro-demo/$(NC)"
	@echo "$(CYAN)🧪 Ejecutá: make demo-run$(NC)"

demo-run:
	@echo "$(BLUE)🧹 Organizando demo...$(NC)"
	@desktopmaestro organize --dry-run --path /tmp/DesktopMaestro-demo

schedule:
	@echo "$(BLUE)⏰ Activando organización programada...$(NC)"
	@desktopmaestro schedule enable

schedule-stop:
	@echo "$(YELLOW)⏹️  Disabling scheduled organization...$(NC)"
	@desktopmaestro schedule disable

# ─── Web UI ─────────────────────────────────────────────────────────────────

web:
	@echo "$(BLUE)🌐 Starting DesktopMaestro web server...$(NC)"
	@desktopmaestro web

# ─── Docker ─────────────────────────────────────────────────────────────────

docker-build:
		@echo "$(BLUE)\U0001f40e Building Docker images...$(NC)"
		@docker compose build
		@echo "$(GREEN)\u2705 Docker images built$(NC)"

docker-up:
		@echo "$(BLUE)\U0001f40e Starting DesktopMaestro with Docker...$(NC)"
		@docker compose up -d
		@echo "$(GREEN)\u2705 Running at http://localhost:3000$(NC)"

docker-down:
		@echo "$(YELLOW)\U0001f40e Stopping Docker containers...$(NC)"
		@docker compose down
		@echo "$(GREEN)\u2705 Stopped$(NC)"

docker-logs:
		@docker compose logs -f

docker-restart: docker-down docker-up


docker-dev:
		@echo "$(BLUE)🐳 Starting in DEV mode (hot reload)...$(NC)"
		@docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build frontend
		@echo "$(GREEN)✅ Dev mode running at http://localhost:3000$(NC)"
		@echo "$(YELLOW)💡 Code changes auto-reload (no rebuild needed)$(NC)"



# ─── Help ────────────────────────────────────────────────────────────────────

help:
	@echo ""
	@echo "$(BOLD)🧹 DesktopMaestro – Commands$(NC)"
	@echo ""
	@echo "  $(GREEN)INSTALLATION$(NC)"
	@echo "  make install         Install DesktopMaestro (pip)"
	@echo "  make install-all     Install Python + Frontend"
	@echo "  make install-dev     Install with dev tools"
	@echo "  make uninstall       Uninstall"
	@echo "  make reinstall       Reinstall"
	@echo ""
	@echo "  $(GREEN)DEVELOPMENT$(NC)"
	@echo "  make test            Run tests"
	@echo "  make test-cov        Tests with coverage"
	@echo "  make lint            Lint code"
	@echo "  make format          Format code"
	@echo "  make clean           Clean temp files"
	@echo ""
	@echo "  $(GREEN)PACKAGING$(NC)"
	@echo "  make build           Build pip package"
	@echo "  make dmg             Create DMG"
	@echo "  make homebrew        Create Homebrew formula"
	@echo "  make app             Create .app bundle"
	@echo ""
	@echo "  $(GREEN)USAGE$(NC)"
	@echo "  make run             Simulate (dry-run, English)"
	@echo "  make run-es          Simulate (dry-run, Español)"
	@echo "  make run-real        Organize for real"
	@echo "  make undo            Undo last organization"
	@echo "  make schedule        Enable auto organization"
	@echo "  make demo            Create test folder"
	@echo "  make demo-run        Organize test folder"
	@echo ""
	@echo "  $(GREEN)WEB UI$(NC)"
	@echo "  make web             Start API server"
	@echo "  make frontend        Start Next.js (dev)"
	@echo "  make install-all     Install everything"
	@echo ""
	@echo ""
	@echo "  $(GREEN)DOCKER$(NC)"
	@echo "  make docker-up       Start with Docker Compose"
	@echo "  make docker-dev      Start in dev mode (hot reload)"
	@echo "  make docker-down     Stop Docker containers"
	@echo "  make docker-build    Rebuild Docker images"
	@echo "  make docker-logs     Show container logs"
	@echo ""
