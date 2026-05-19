<div align="center">

# 🧹 DesktopMaestro

### The smart folder organizer for **macOS**

*Organize any directory — Desktop, Downloads, Documents, or custom folders*

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![macOS](https://img.shields.io/badge/platform-macOS-black.svg?logo=apple)](https://www.apple.com/macos)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/brunobergoglio/desktop-maestro/pulls)
[![GitHub release](https://img.shields.io/github/v/release/brunobergoglio/desktop-maestro?logo=github)](https://github.com/brunobergoglio/desktop-maestro/releases)
[![CI](https://img.shields.io/github/actions/workflow/status/brunobergoglio/desktop-maestro/ci.yml?logo=githubactions)](https://github.com/brunobergoglio/desktop-maestro/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

---

[✨ Features](#✨-features) •
[📦 Installation](#📦-installation) •
[🚀 Quick Start](#🚀-quick-start) •
[📖 Commands](#📖-commands) •
[🧠 Categories](#🧠-category-system) •
[⚙️ Configuration](#⚙️-configuration) •
[🔐 Safety](#🔐-safety--undo) •
[⏰ Automation](#⏰-automation) •
[🏗️ Architecture](#🏗️-architecture) •
[🛠️ Development](#🛠️-development) •
[🤝 Contributing](#🤝-contributing)

---

</div>

## ✨ Features

DesktopMaestro instantly transforms any macOS folder into an organized space — Desktop, Downloads, Documents, or your own custom directory. No more hunting for files scattered everywhere.

### 🎯 Before → After

```
Before                                    After
┌──────────────────────────┐               ┌──────────────────────────┐
│ photo.jpg                │               │ 🖼️ Images/               │
│ document.pdf             │               │ 📕 PDFs/                 │
│ video.mp4                │               │ 🎬 Videos/               │
│ song.mp3                 │               │ 🎵 Audio/                │
│ code.py                  │     🧹        │ 💻 Code/                 │
│ presentation.pptx        │    ────►      │ 📊 Presentations/        │
│ archive.zip              │               │ 🗜️ Archives/             │
│ book.epub                │               │ 📚 Books/                │
│ .DS_Store                │               │ .DS_Store (untouched)    │
│ My Folder/               │               │ My Folder/ (untouched)   │
└──────────────────────────┘               └──────────────────────────┘
```

### 🌟 What makes DesktopMaestro special

| Feature | Benefit |
|---|---|
| 📂 **Any directory** | Organize Desktop, Downloads, Documents — or any custom path |
| 🧠 **Smart classification** | 400+ recognized extensions across **22 categories** with priority system |
| 🔒 **Safety first** | Dry-run mode, full undo snapshots with SHA-256 integrity verification |
| 🍎 **Made for macOS** | Respects `.DS_Store`, hidden files, system metadata, and Full Disk Access |
| ⚡ **Fast & efficient** | Processes hundreds of files in seconds with parallel processing |
| 🎨 **Premium experience** | Progress bar, colors, native dialogs, macOS notifications |
| ⚙️ **100% configurable** | Custom categories, rules, exclusions — all in YAML or JSON |
| 🔄 **Full undo** | Every operation saves a snapshot to restore everything as it was |
| 🌐 **Web UI** | Beautiful Next.js dashboard with file explorer, directory tree, and real-time HMR |
| ⏰ **Automatic** | Scheduled organization with native macOS LaunchAgent |

---

## 📦 Installation

### 🍺 Homebrew (recommended)

```bash
brew tap brunobergoglio/desktop-maestro
brew install desktopmaestro
```

### 🐍 pip (direct)

```bash
# Install from GitHub
pip install git+https://github.com/brunobergoglio/desktop-maestro.git

# Or from source
git clone https://github.com/brunobergoglio/desktop-maestro.git
cd desktopmaestro
pip install -e .
```

### 📥 Manual installer

```bash
curl -LO https://github.com/brunobergoglio/desktop-maestro/releases/latest/download/install.sh
chmod +x install.sh
./install.sh
```

### 📋 Optional dependencies

```bash
# For macOS color tags on folders
brew install tag

# For development
pip install -e ".[dev]"
```

### ✅ Verify installation

```bash
desktopmaestro --version
# → DesktopMaestro v1.0.0

desktopmaestro system
# → Shows system information and diagnostics
```

---

## 🚀 Quick Start

### 1️⃣ Simulate first (always recommended)

```bash
desktopmaestro organize --dry-run
```

This shows **exactly** what would happen without moving anything:
- Which files will be moved
- Which folders they'll go to
- Which new folders will be created

### 2️⃣ Execute

```bash
# You'll be asked to confirm with a native macOS dialog
desktopmaestro organize
```

### 3️⃣ View results

```bash
desktopmaestro stats
# → 📊 DESKTOP STATISTICS
#    📂 Desktop:  /Users/you/Desktop
#    📄 Files:    42
#    📁 Folders:  8
#    💾 Size:     1.2 GB
```

### 4️⃣ If something went wrong

```bash
# Undo instantly
desktopmaestro undo
```

> 💡 **Tip:** Always use `--dry-run` the first time. Zero risk, infinite peace of mind.

---



## 🐳 Docker

Run DesktopMaestro anywhere with Docker — perfect for servers, CI/CD, or if you just don't want to install Python locally.

### 🚀 Production mode

```bash
# Start everything
docker compose up -d

# Open the web UI
open http://localhost:3000

# API health check
curl http://localhost:7899/api/health

# Stop
docker compose down
```

### 🔥 Development mode (hot reload)

```bash
# Start with hot reload (make changes, see them instantly)
make docker-dev
# or: docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build frontend

# Open web UI
open http://localhost:3000
```

**What you get in dev mode:**

| Component | Changes | Behavior |
|---|---|---|
| 🖥️ **Frontend** | Edit `frontend/src/` | HMR — browser refreshes instantly |
| ⚙️ **API** | Edit `organizer/*.py` | Server auto-restarts via `dev_watch.py` |
| 📁 **Folders** | Your `~/Desktop`, `~/Downloads`, `~/Documents` | Mounted writable — organizer can move files |

> 💡 **No rebuilds needed.** Just save a file and see the result.

### 🏗️ Stack

| Service | Image | Size | Port |
|---|---|---|---|
| **API** (Python) | `python:3.12-alpine` | ~55 MB | `7899` |
| **Frontend** (Next.js) | `node:22-alpine` | ~150 MB | `3000` |

### 🛡️ Security

- **Non-root user** (`maestro`) in both containers
- **Read-only filesystem** (`read_only: true`) — only mounted volumes are writable
- **Resource limits** — CPU and memory caps prevent runaway containers
- **Healthchecks** — automatic restart on failure
- **Cache mounts** — pip and pnpm caches persist between builds

---

## 🌐 Web UI

DesktopMaestro includes a beautiful **Next.js web dashboard** for visual file management.

### 📸 Features

| Feature | Description |
|---|---|
| 📂 **Directory Tree** | VS Code-style collapsible tree to browse all folders |
| 📁 **File Explorer** | List or grid view with file type badges |
| 🏷️ **File Type Badges** | Color-coded badges for 30+ file formats (PDF, DOC, IMG, VIDEO, etc.) |
| 🔍 **Smart Folder Selector** | Autocomplete, bookmarks (Desktop, Downloads, Documents, Home), recent paths |
| 📊 **Dashboard** | Stats, file type distribution chart, category preview |
| 🔧 **Settings** | Configure language, dry-run, notifications, schedule |
| ↩️ **Undo** | View and restore organization snapshots |
| 🌐 **Bilingual** | English and Spanish UI |
| ⌨️ **Keyboard shortcuts** | `⌘K` focus folder input, `↑↓` navigate autocomplete, `Esc` dismiss |

### 🎨 File Type Recognition

The web UI recognizes **30+ file formats** with color-coded badges:

```
📕 PDF  🔴  📝 DOC  🔵  📊 XLS  🟢  🖼️ PNG  🟣  🎬 VIDEO  🟪
💻 CODE 🟠  🗜️ ZIP  🟣  🎵 AUDIO 🌹  📋 JSON 🟡  ⬇️ DMG  🔵
```

Every file in the explorer shows a **colored badge** with its format, inspired by Cursor/shadcn design.

---

## 📖 Commands

### 🧹 `organize` — The heart of DesktopMaestro

Organizes any folder into emoji-themed category folders. Works on Desktop, Downloads, Documents, or any custom path.

```bash
desktopmaestro organize                    # Organize Desktop (with confirmation)
desktopmaestro organize --path ~/Downloads # Organize Downloads folder
desktopmaestro organize --path ~/Documents # Organize Documents folder
desktopmaestro organize --path /any/path   # Organize any directory
desktopmaestro organize --dry-run          # Simulate without moving
desktopmaestro organize --force            # Skip confirmation dialog
desktopmaestro organize --headless         # No interaction (for scripts/LaunchAgent)
```

**Aliases:** `org`, `o`

**Flags:**
| Flag | Description |
|---|---|
| `-p`, `--path PATH` | **Target directory** (default: `~/Desktop`, can be any folder) |
| `-d`, `--dry-run` | Simulate only, don't move files |
| `-f`, `--force` | Skip confirmation dialog |
| `--headless` | No user interaction |
| `-V`, `--verbose` | Detailed information |

### 📊 `stats` — Desktop statistics

Analyzes your desktop and shows detailed information.

```bash
desktopmaestro stats                       # Overview with colors
desktopmaestro stats --json                # JSON output for scripting
```

**Aliases:** `s`, `status`

**Example output:**
```
📊 DESKTOP STATISTICS
   📂 Desktop:  /Users/you/Desktop
   📄 Files:    42
   📁 Folders:  8
   💾 Size:     1.2 GB

🔤 Extensions:
   • .pdf             → 12 files
   • .jpg             → 8 files
   • .py              → 5 files
   • .dmg             → 3 files

📦 Size distribution:
   • 🐜 < 10KB        → 15 files
   • 📎 < 1MB         → 18 files
   • 📦 < 100MB       → 7 files
   • 📀 < 1GB         → 2 files
```

### ↩️ `undo` — Revert changes

Restores your desktop to its state before organization.

```bash
desktopmaestro undo                        # Undo last organization
desktopmaestro undo --list                 # List all previous operations
desktopmaestro undo --snapshot <file>      # Restore a specific snapshot
```

**Aliases:** `u`

> 🔐 Every operation saves a snapshot with SHA-256 hashes to verify files haven't changed before restoring.

### ⚙️ `config` — Configuration management

```bash
desktopmaestro config init                 # Create default configuration
desktopmaestro config edit                 # Open config in your editor
desktopmaestro config show                 # View current configuration
desktopmaestro config path                 # Show config file path
desktopmaestro config reset                # Reset to defaults
desktopmaestro config reset --force        # Reset without confirmation
```

**Aliases:** `c`

### ⏰ `schedule` — Automatic organization

Schedule DesktopMaestro to keep your desktop tidy without you having to remember.

```bash
desktopmaestro schedule enable             # Enable (every 6h by default)
desktopmaestro schedule enable --interval 3 # Custom interval (every 3h)
desktopmaestro schedule disable            # Disable
desktopmaestro schedule status             # View status
```

**Aliases:** `timer`

> ⚡ Uses native macOS **LaunchAgent** — zero resource consumption, managed by `launchd`.

### 💻 `system` — System information

```bash
desktopmaestro system                      # Full diagnostics
desktopmaestro info                        # Same as system
```

Shows:
- macOS version and hardware
- Python version
- Dependency status (PyYAML, `tag` CLI)
- Permission diagnostics

---

## 🧠 Category System

DesktopMaestro uses an **intelligent priority-based categorization system**. A `.pdf` file always goes to `📕 PDFs/` instead of `📄 Documents/`, even though technically it's a document.

### 📋 Predefined categories

| Category | Key extensions | Priority |
|---|---|---|
| 🗑️ **Temporary** | `.tmp` `.swp` `.bak` `.cache` `.crdownload` | Highest |
| 🧲 **Torrents** | `.torrent` `.magnet` | High |
| 📕 **PDFs** | `.pdf` | High |
| 🖼️ **Images** | `.jpg` `.png` `.gif` `.svg` `.webp` `.heic` `.raw` `.psd` | High |
| 🎬 **Videos** | `.mp4` `.mov` `.avi` `.mkv` `.webm` + subtitles | High |
| 🎵 **Audio** | `.mp3` `.wav` `.flac` `.aac` `.m4a` `.opus` | High |
| 🗜️ **Archives** | `.zip` `.rar` `.7z` `.tar` `.gz` `.dmg` `.iso` | High |
| 💿 **Disks & ISOs** | `.iso` `.dmg` `.img` `.toast` | High |
| ⚡ **Executables** | `.app` `.exe` `.command` `.workflow` | High |
| 🔤 **Fonts** | `.ttf` `.otf` `.woff` `.woff2` | High |
| 📚 **Books** | `.epub` `.mobi` `.azw` `.djvu` `.cbr` | High |
| 📜 **Scripts** | `.sh` `.py` `.rb` `.applescript` `.workflow` | Medium |
| 💻 **Code** | `.py` `.js` `.ts` `.html` `.css` `.json` `.go` `.rs` +100 more | Medium |
| 🎨 **Design** | `.psd` `.ai` `.fig` `.sketch` `.blend` `.glb` | Medium |
| 📈 **Spreadsheets** | `.xls` `.xlsx` `.ods` `.numbers` | Medium |
| 📊 **Presentations** | `.ppt` `.pptx` `.key` `.odp` | Medium |
| 📄 **Documents** | `.txt` `.md` `.doc` `.docx` `.rtf` `.pages` | Medium |
| 🗄️ **Databases** | `.db` `.sqlite` `.mdb` | Low |
| ⚙️ **Configuration** | `.plist` `.config` `.bashrc` `.zshrc` | Low |
| ✉️ **Emails** | `.eml` `.msg` `.pst` `.mbox` | Low |
| 📦 **Others** | Any unrecognized extension | Minimum |

> 📌 **400+ extensions** recognized in total. And you can add your own!

### 🎨 Custom categories

Got unusual extensions or want a special folder for your project? Add them in the config:

```yaml
custom_categories:
  - name: "Project X"
    icon: "🚀"
    extensions: [".xproj", ".xsource", ".xbuild"]
    patterns:
      - "^project_x_"
      - ".*_final\\.pdf$"
    priority: 100             # Higher = matched first
    folder_name: "🚀 Project X"
```

---

## ⚙️ Configuration

Configuration lives at `~/.config/desktopmaestro/config.yaml`. It's auto-created the first time you run DesktopMaestro.

### Complete config file

```yaml
# ─── Paths ───
desktop_path: "~/Desktop"
log_dir: "~/Library/Logs/DesktopMaestro"

# ─── Behavior ───
dry_run: false
verbose: true
organize_on_startup: false

# ─── Filters ───
include_extensions: []                    # Empty = all extensions
exclude_extensions: [".part", ".crdownload", ".tmp"]
exclude_files:
  - .DS_Store
  - .localized
exclude_patterns:
  - '^\._.*'                              # Apple Double files
  - '^\..*\.icloud$'                      # iCloud placeholders

# ─── Categories ───
disabled_categories: []                   # Categories you don't want created
category_folder_names:
  # "Images": "My Photos"                 # Custom names

# ─── Safety ───
create_undo_snapshot: true
max_undo_snapshots: 50
min_file_age_minutes: 0                   # Don't move recent files
skip_locked_files: true
skip_files_in_use: true

# ─── Automation ───
schedule_enabled: false
schedule_interval_hours: 6
# schedule_time: "03:00"                  # Specific time

# ─── macOS ───
show_notifications: true
add_tags_to_folders: false                # Requires `brew install tag`
```

### 🔧 Common configuration scenarios

<details>
<summary><b>📁 Don't want folders for music and videos</b></summary>

```yaml
disabled_categories:
  - "Audio"
  - "Videos"
# Those files will go to "📦 Others"
```
</details>

<details>
<summary><b>🎯 Only organize images and PDFs</b></summary>

```yaml
include_extensions:
  - ".jpg"
  - ".jpeg"
  - ".png"
  - ".gif"
  - ".pdf"
```
</details>

<details>
<summary><b>🕒 Don't move files from the last 2 hours</b></summary>

```yaml
min_file_age_minutes: 120
```
</details>

<details>
<summary><b>📂 Custom folder names</b></summary>

```yaml
category_folder_names:
  Images: "01 - Images"
  PDFs: "02 - PDFs"
  Documents: "03 - Documents"
  Code: "04 - Code"
  Others: "99 - Others"
```
</details>

---

## 🔐 Safety & Undo

DesktopMaestro was designed with a **"first, do no harm"** philosophy. Every operation is protected by multiple safety layers.

### 🛡️ Multi-layer protection system

```
📂 Files on desktop
    │
    ├─ 1️⃣  Filter: Is it a macOS system file? → ❌ Leave it alone
    ├─ 2️⃣  Filter: Is it excluded by name/pattern? → ❌ Leave it alone
    ├─ 3️⃣  Filter: Is it locked or in use? → ❌ Leave it alone
    ├─ 4️⃣  Filter: Is it too recent? → ❌ Leave it alone (configurable)
    ├─ 5️⃣  Is it dry-run mode? → 🔍 Only show what would happen
    │
    └─ ✅  Move safely (with hash + snapshot)
```

### 📸 Undo snapshots

Every organization saves a **complete snapshot** including:

- **Original path** of every file
- **Destination path** where it was moved
- **SHA-256 hash** for integrity verification
- **Precise timestamp**
- **File size**

```bash
# View all available snapshots
desktopmaestro undo --list

# Restore a specific snapshot
desktopmaestro undo --snapshot ~/.config/desktopmaestro/undo/undo_20250101_120000_000000.json

# Undo the last operation
desktopmaestro undo
```

> 🔐 Before restoring, DesktopMaestro verifies that files **haven't changed** since they were moved. If the hash doesn't match, it warns you and doesn't touch anything.

### 🍎 Files that are NEVER touched

| File | Reason |
|---|---|
| `.DS_Store` | macOS folder metadata |
| `.localized` | Localized folder names |
| `.Spotlight-V100` | Spotlight index |
| `.Trashes` | macOS trash |
| `.fseventsd` | Filesystem event logs |
| `Desktop DB`, `Desktop DF` | Finder database (classic macOS) |

---

## ⏰ Automation

### With LaunchAgent (native macOS)

Uses macOS `launchd` — **zero resource consumption**, runs only when needed.

```bash
# Enable (every 6 hours)
desktopmaestro schedule enable

# Every 3 hours
desktopmaestro schedule enable --interval 3

# Check status
desktopmaestro schedule status
# → ✅ Scheduling active
#    ⏰ Interval: every 6 hours

# Disable
desktopmaestro schedule disable
```

### With cron (alternative)

```bash
# Every day at 3 AM
0 3 * * * /usr/local/bin/desktopmaestro organize --headless

# Every 4 hours
0 */4 * * * /usr/local/bin/desktopmaestro organize --headless
```

> 💡 The `--headless` flag prevents dialogs and notifications — ideal for automated execution.

---

## 🎯 Use Cases

### 🎨 Graphic Designer

> *"My desktop is full of `.psd`, `.ai`, `.sketch`, `.png`, `.jpg`... it's a mess."*

```bash
desktopmaestro organize --dry-run
# → 🎨 Design/     → mockup.psd, logo.ai, app.sketch
# → 🖼️ Images/    → photo.jpg, banner.png, icon.svg
# → 🔤 Fonts/     → Roboto.ttf, Inter.otf
```

### 💻 Developer

> *"My desktop is chaos: `.py`, `.json`, `.log`, `.dmg`, `.zip`..."*

```bash
desktopmaestro organize
# → 💻 Code/      → main.py, package.json, tsconfig.json
# → 🗜️ Archives/ → project.zip, library.tar.gz
# → 📄 Documents/ → notes.txt, api-docs.md
# → 💿 Disks/     → installer.dmg
```

### 🎓 Student

> *"I have PDFs, papers, presentations, and books all mixed up..."*

```bash
desktopmaestro organize
# → 📕 PDFs/      → thesis.pdf, paper-2024.pdf
# → 📚 Books/     → algorithm-design.epub, calculus.mobi
# → 📊 Presentations/ → presentation.pptx, project.key
```

### 👨‍💼 Office Worker

> *"Office documents, spreadsheets, and PDFs everywhere..."*

```bash
desktopmaestro organize
# → 📄 Documents/ → letter.docx, memo.rtf, minutes.txt
# → 📈 Spreadsheets/ → budget.xlsx, sales.numbers
# → 📕 PDFs/      → contract.pdf, report-2024.pdf
```

---

## 🏗️ Architecture

```
desktopmaestro/
├── organizer/
│   ├── __init__.py        # Package metadata (version, author)
│   ├── cli.py             # 🎛️  Full CLI with argparse, subcommands, banners
│   ├── core.py            # ⚙️  Engine: scanning, categorization, file movement
│   ├── categories.py      # 🧠  Category system (22 predefined + custom)
│   ├── config.py          # 📋  Configuration management (YAML/JSON)
│   ├── server.py          # 🌐  HTTP API server (REST endpoints)
│   └── utils.py           # 🔧  Logging, notifications, LaunchAgent, stats
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx   # 🖥️  Main dashboard (Next.js 14)
│   │   │   ├── layout.tsx #     Root layout
│   │   │   ├── globals.css #    Animations, glassmorphism, utilities
│   │   │   ├── components/
│   │   │   │   ├── FolderSelector.tsx  # 🔍 Smart path input + bookmarks
│   │   │   │   ├── DirectoryTree.tsx   # 🌳 Collapsible folder tree
│   │   │   │   └── FileTypeBadge.tsx   # 🏷️ Color-coded file badges
│   │   │   └── api/desktopmaestro/[...path]/route.ts  # API proxy
│   │   └── lib/api.ts      # 📡 API client (typed fetch wrappers)
│   ├── Dockerfile          # 🐳 Multi-stage (deps → build → runner)
│   ├── package.json
│   └── pnpm-lock.yaml
├── config/
│   └── default_config.yaml    # Default configuration with comments
├── tests/
│   ├── test_organizer.py      # 600+ lines of tests
│   └── __init__.py
├── Dockerfile.api             # 🐳 Python API image (Alpine, multi-stage)
├── docker-compose.yml         # 🐳 Production stack
├── docker-compose.dev.yml     # 🐳 Dev overrides (hot reload)
├── dev_watch.py               # 🔥 Auto-reload API on .py changes
├── installer/                 # Distribution installer (.dmg, install.sh)
├── maestro_assets/            # Brand assets
├── run.py                     # Alternative entry point
├── pyproject.toml             # Package build configuration
├── Makefile                   # 40+ development commands
├── requirements.txt           # Dependencies (just PyYAML)
├── CONTRIBUTING.md            # Contribution guidelines
└── CODE_OF_CONDUCT.md         # Code of conduct
```

### 🧩 Organization flow

```
1. CLI receives command → argparse
       │
2. Core: DesktopOrganizer.organize()
       │
       ├─ 3. _scan_desktop()     → List files, apply filters
       ├─ 4. _categorize_files() → Classify each file
       ├─ 5. _ensure_category_folders() → Create folders if needed
       ├─ 6. _move_file()        → Move with conflict resolution
       └─ 7. UndoManager.create_snapshot() → Save SHA-256 snapshot
       │
8. Results → console + macOS notification
```

### 📦 Just 1 dependency

DesktopMaestro has **only one required dependency**: `pyyaml`. Everything else is Python standard library:

- ✅ Lightweight, fast installation
- ✅ Minimal conflicts with other packages
- ✅ Easy to maintain

---

## 🛠️ Development

### Initial setup

```bash
# Clone
git clone https://github.com/brunobergoglio/desktop-maestro.git
cd desktopmaestro

# Virtualenv (recommended)
python -m venv venv
source venv/bin/activate

# Install editable + dev dependencies
pip install -e ".[dev]"

# Verify it works
desktopmaestro --version
```

### Makefile commands

```bash
make test           # Run tests
make test-cov       # Tests with coverage
make lint           # Check style (ruff)
make format         # Format code (black)
make build          # Build pip package
make dmg            # Create DMG for distribution
make demo           # Create test folder
make demo-run       # Organize test folder
make docker-dev     # 🐳 Start dev mode (hot reload)
make docker-up      # 🐳 Start production mode
make docker-down    # 🐳 Stop containers
make help           # View all commands
```

### Tests

The test suite has **600+ lines** covering:

- **Categories**: every extension, priorities, case-insensitive, custom categories
- **Configuration**: YAML/JSON load/save, defaults, custom overrides
- **Core**: scanning, categorization, dry-run, real organization, name conflicts
- **Undo**: snapshot creation and restoration, file integrity checks
- **Utils**: size formatting, stats, logging
- **Integration**: full workflow organization → statistics
- **Performance**: 500 files in under 30 seconds

```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=organizer --cov-report=html

# Specific tests
pytest tests/test_organizer.py -k "test_smart_categorize"
```

### Branch structure

| Branch | Purpose |
|---|---|
| `main` | Stable releases |
| `develop` | Feature integration |
| `feature/*` | New features |
| `fix/*` | Bug fixes |

---

## 🤝 Contributing

Contributions are very welcome! This project grows thanks to the community.

### 🌟 Ideas for contributing

| Idea | Difficulty | Area |
|---|---|---|
| 📦 More file categories | 🟢 Easy | `categories.py` |
| 🧪 Additional tests | 🟢 Easy | `tests/` |
| 🌐 Internationalization (i18n) | 🟢 Easy | `cli.py` |
| 📱 Native macOS app (SwiftUI) | 🔴 Hard | New |
| 🔍 Spotlight integration | 🟡 Medium | New |
| 🪟 Windows support | 🔴 Hard | Core |
| 🐧 Linux support | 🔴 Hard | Core |
| 🌐 Local web UI | 🟡 Medium | New |
| 📊 Menu bar app (macOS) | 🟡 Medium | New |
| ⚡ Conditional rules (by size/date) | 🟡 Medium | `core.py` |
| 🪞 Mirror mode (multi-folder) | 🟡 Medium | `core.py` |

### Process

1. **Fork** the project
2. Create a branch: `git checkout -b feature/your-feature-name`
3. Make your changes with **tests**
4. Run checks: `make lint && make test`
5. Commit with [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat: add RAW image category`
   - `fix: handle .heic files correctly`
   - `docs: improve README examples`
6. Push: `git push origin feature/your-feature-name`
7. Open a **Pull Request**

### Code conventions

- **Formatting**: Black (default settings, 88 chars)
- **Linting**: Ruff (configured in pyproject.toml)
- **Tests**: pytest with fixtures, coverage > 90%
- **Types**: Type hints on all public functions
- **Documentation**: Google-style docstrings

---

## 📄 License

**MIT** © [Bruno Bergoglio](https://github.com/brunobergoglio)

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

<div align="center">

### ⭐ Enjoying DesktopMaestro?

**Give us a star on [GitHub](https://github.com/brunobergoglio/desktop-maestro)!** ⭐

It helps more people discover this project.

---

**Made with ❤️ by Bruno Bergoglio**

[Report bug](https://github.com/brunobergoglio/desktop-maestro/issues) •
[Request feature](https://github.com/brunobergoglio/desktop-maestro/issues) •
[Contribute](https://github.com/brunobergoglio/desktop-maestro/pulls)

</div>
