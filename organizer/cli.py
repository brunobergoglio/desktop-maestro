"""
CLI — DesktopMaestro command-line interface.

Provides a premium user experience with colored output, progress bars,
native macOS dialogs, and multiple subcommands for complete control.
"""

import os
import sys
import argparse
import time
from datetime import datetime
from typing import Optional

from . import __version__, __description__
from .core import DesktopOrganizer, organize_desktop
from .categories import SUPPORTED_LANGUAGES
from .config import (
    load_config, save_config, create_default_config,
    DesktopMaestroConfig, DEFAULT_CONFIG_FILE,
)
from .utils import (
    DesktopMaestroLogger, send_macos_notification,
    get_desktop_stats, get_system_info,
    create_launch_agent, remove_launch_agent,
    is_macos, show_macos_dialog,
)


# ─── Welcome Banner ───
BANNER = r"""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║     \U0001f9f9  DesktopMaestro  v{v}                   ║
║     ───────────────────────────────                      ║
║     Smart desktop organizer for macOS                    ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
""".format(v=__version__)


def build_parser() -> argparse.ArgumentParser:
    """Build the main argument parser."""
    parser = argparse.ArgumentParser(
        prog="desktopmaestro",
        description=f"🧹 {__description__} v{__version__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  desktopmaestro organize              Organize desktop now
  desktopmaestro organize --dry-run    Simulate organization (safe)
  desktopmaestro stats                 View desktop statistics
  desktopmaestro undo                  Undo last organization
  desktopmaestro config init           Create default configuration
  desktopmaestro config edit           Open config in editor
  desktopmaestro schedule enable       Enable automatic organization
  desktopmaestro schedule disable      Disable scheduling
        """,
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"DesktopMaestro v{__version__}",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help=f"Path to configuration file (default: {DEFAULT_CONFIG_FILE})",
    )
    parser.add_argument(
        "--verbose", "-V",
        action="store_true",
        default=False,
        help="Show detailed information",
    )
    parser.add_argument(
        "--lang", "--language",
        type=str,
        default=None,
        choices=SUPPORTED_LANGUAGES,
        help='Language for folder names: "en" (English) or "es" (Español)',
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Command to run",
    )

    # ─── organize ───
    org_parser = subparsers.add_parser(
        "organize", aliases=["org", "o"],
        help="Organize desktop files",
        description="Sorts and moves desktop files into organized category folders.",
    )
    org_parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        default=False,
        help="Simulate without moving files",
    )
    org_parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Non-interactive mode (for LaunchAgent)",
    )
    org_parser.add_argument(
        "--force", "-f",
        action="store_true",
        default=False,
        help="Force organization (skip warnings)",
    )
    org_parser.add_argument(
        "--path",
        type=str,
        default=None,
        help="Custom desktop path",
    )

    # ─── undo ───
    undo_parser = subparsers.add_parser(
        "undo", aliases=["u"],
        help="Undo last organization",
        description="Restores files to their original locations.",
    )
    undo_parser.add_argument(
        "--snapshot",
        type=str,
        default=None,
        help="Path to a specific snapshot to restore",
    )
    undo_parser.add_argument(
        "--list",
        action="store_true",
        default=False,
        help="List available snapshots",
    )

    # ─── stats ───
    stats_parser = subparsers.add_parser(
        "stats", aliases=["s", "status"],
        help="Show desktop statistics",
        description="Analyzes and displays detailed desktop information.",
    )
    stats_parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output as JSON",
    )

    # ─── config ───
    config_parser = subparsers.add_parser(
        "config", aliases=["c"],
        help="Manage configuration",
        description="Initialize, edit, or view configuration.",
    )
    config_sub = config_parser.add_subparsers(
        dest="config_action",
        help="Configuration action",
    )

    config_sub.add_parser("init", help="Create default configuration")
    config_sub.add_parser("edit", help="Open configuration in editor")
    config_sub.add_parser("show", help="Show current configuration")
    config_sub.add_parser("path", help="Show configuration path")

    reset_parser = config_sub.add_parser(
        "reset",
        help="Reset configuration to defaults",
    )
    reset_parser.add_argument(
        "--force", "-f",
        action="store_true",
        default=False,
        help="Reset without confirmation",
    )

    # ─── schedule ───
    sched_parser = subparsers.add_parser(
        "schedule",
        aliases=["timer"],
        help="Manage automatic organization",
        description="Schedule automatic organization runs.",
    )
    sched_sub = sched_parser.add_subparsers(
        dest="schedule_action",
        help="Schedule action",
    )

    enable_sched = sched_sub.add_parser(
        "enable",
        help="Enable scheduled organization",
    )
    enable_sched.add_argument(
        "--interval",
        type=int,
        default=6,
        help="Interval in hours (default: 6)",
    )

    sched_sub.add_parser("disable", help="Disable scheduled organization")
    sched_sub.add_parser("status", help="View scheduling status")

    # ─── system ───
    system_parser = subparsers.add_parser(
        "system", aliases=["info"],
        help="System information",
        description="Shows system information and diagnostics.",
    )

    # ─── web ───
    web_parser = subparsers.add_parser(
        "web", aliases=["ui", "gui", "frontend"],
        help="Launch web UI",
        description="Starts the DesktopMaestro web interface and API server.",
    )
    web_parser.add_argument(
        "--port", "-p",
        type=int,
        default=7899,
        help="Port for the API server (default: 7899)",
    )
    web_parser.add_argument(
        "--open", "-o",
        action="store_true",
        default=False,
        help="Open browser automatically",
    )

    return parser


# ─── Command Handlers ───

def cmd_organize(args, log: DesktopMaestroLogger):
    """Execute desktop organization."""
    log.section("🧹 ORGANIZING DESKTOP")

    config = load_config(args.config)

    if args.dry_run:
        config.dry_run = True
        log.info("🔍 DRY RUN MODE – No files will be moved")
        log.info("")

    if args.path:
        config.desktop_path = args.path
        log.info(f"📂 Using custom path: {config.desktop_path}")

    if args.verbose:
        config.verbose = True

    # Verificar escritorio
    desktop = os.path.expanduser(config.desktop_path)
    if not os.path.isdir(desktop):
        log.error(f"❌ Directory '{desktop}' does not exist or is not accessible")
        return 1

    # Show pre-execution summary
    if not args.headless:
        log.info(f"📂 Desktop: {desktop}")
        log.info(f"⏰ Start:     {datetime.now().strftime('%H:%M:%S')}")
        log.info("")

        if not args.dry_run and not args.force:
            dialog_result = show_macos_dialog(
                "DesktopMaestro",
                f"Organize {desktop}?",
                buttons=["Organize", "Simulate Only", "Cancel"],
                default_button="Organize",
                icon="note",
            )
            if dialog_result == "Cancel":
                log.info("⏹️  Operation cancelled by user")
                return 0
            elif dialog_result == "Simulate Only":
                config.dry_run = True
                log.info("🔍 Switching to simulation mode")

    # Ejecutar
    organizer = DesktopOrganizer(config=config)

    # Configurar eventos para progreso
    total_files = [0]

    def on_progress(current, total, filename):
        total_files[0] = total
        pct = (current / total) * 100 if total > 0 else 0
        bar = _progress_bar(pct)
        sys.stdout.write(
            f"\r   {bar} {current}/{total} ({pct:.0f}%) – {filename[:40]:40s}"
        )
        sys.stdout.flush()

    if not args.headless:
        organizer.events.on_progress = on_progress

    # Callback de error
    organizer.events.on_error = lambda path, err: log.error(
        f"   ❌ {os.path.basename(path)}: {err}"
    )

    start_time = time.time()

    try:
        result = organizer.organize()
    except KeyboardInterrupt:
        organizer.abort()
        log.warning("\n⏹️  Operation interrupted by user")
        return 130
    except Exception as e:
        log.critical(f"🔥 Critical error: {e}")
        return 1

    elapsed = time.time() - start_time

    # Resultados
    print()  # New line after progress bar
    log.section("📊 RESULTS")

    if result.dry_run:
        log.info(f"🔍 Dry run – {result.success_count} files ready to move")
    else:
        log.success(f"✅ {result.success_count} files organized successfully")

    if result.categories_created:
        log.info(f"📁 Folders created: {len(result.categories_created)}")
        for folder in result.categories_created:
            log.info(f"   • {folder}")

    if len(result.skipped_files) > 0:
        log.warning(f"⏭️  {len(result.skipped_files)} files skipped")

    if len(result.errors) > 0:
        log.error(f"❌ {len(result.errors)} errors")
        for path, error in result.errors[:5]:
            log.error(f"   • {os.path.basename(path)}: {error}")

    log.info(f"⏱️  Total time: {elapsed:.2f}s")

    # Notification
    if not args.headless and config.show_notifications and is_macos():
        send_macos_notification(
            title="DesktopMaestro",
            message=f"✅ {result.success_count} files organized in {elapsed:.1f}s",
            subtitle="Organization complete",
        )

    return 0


def cmd_undo(args, log: DesktopMaestroLogger):
    """Undo organization operations."""
    config = load_config(args.config)
    organizer = DesktopOrganizer(config=config)

    if args.list:
        log.section("📋 AVAILABLE SNAPSHOTS")
        snapshots = organizer.undo_manager.list_snapshots()
        if not snapshots:
            log.info("No snapshots available")
            return 0

        for snap in snapshots:
            log.info(f"  📄 {snap['file']}")
            log.info(f"     Date: {snap.get('created_at', '?')}")
            log.info(f"     Files: {snap.get('entries_count', 0)}")
            log.info(f"     Description: {snap.get('description', '—')}")
            log.info("")
        return 0

    log.section("↩️  UNDOING ORGANIZATION")

    if args.snapshot:
        log.info(f"Using snapshot: {args.snapshot}")

    if not args.force and is_macos():
        dialog_result = show_macos_dialog(
            "DesktopMaestro – Undo",
            "Restore files to their original locations?",
            buttons=["Restore", "Cancel"],
            default_button="Restore",
            icon="caution",
        )
        if dialog_result != "Restore":
            log.info("⏹️  Operation cancelled")
            return 0

    results = organizer.undo(snapshot_path=args.snapshot)

    success_count = sum(1 for _, _, ok in results if ok)
    error_count = sum(1 for _, _, ok in results if not ok)

    log.success(f"✅ {success_count} files restored")
    if error_count > 0:
        log.error(f"❌ {error_count} errors")
        for path, status, ok in results:
            if not ok:
                log.error(f"   • {path}: {status}")

    return 0


def cmd_stats(args, log: DesktopMaestroLogger):
    """Display desktop statistics."""
    config = load_config(args.config)

    log.section("📊 DESKTOP STATISTICS")

    stats = get_desktop_stats(config.desktop_path)

    if args.json:
        import json
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        return 0

    if "error" in stats:
        log.error(f"❌ {stats['error']}")
        return 1

    log.info(f"📂 Desktop:  {os.path.expanduser(config.desktop_path)}")
    log.info(f"📄 Files:    {stats['total_files']}")
    log.info(f"📁 Folders:    {stats['total_folders']}")
    log.info(f"💾 Size:      {stats['total_size_human']}")
    log.info("")

    # Most common extensions
    if stats["by_extension"]:
        log.info("🔤 Extensions:")
        sorted_ext = sorted(
            stats["by_extension"].items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]
        for ext, count in sorted_ext:
            log.info(f"   • {ext:15s} → {count} files")

    log.info("")

    # Size distribution
    log.info("📦 Size distribution:")
    size_labels = {
        "tiny": "🐜 < 10KB",
        "small": "📎 < 1MB",
        "medium": "📦 < 100MB",
        "large": "📀 < 1GB",
        "huge": "💿 > 1GB",
    }
    for key, label in size_labels.items():
        count = stats["by_size_category"].get(key, 0)
        if count > 0:
            log.info(f"   • {label:15s} → {count} files")

    if stats.get("oldest_file"):
        log.info(f"\n🐌 Oldest: {stats['oldest_file']['name']}")
    if stats.get("newest_file"):
        log.info(f"⚡ Newest: {stats['newest_file']['name']}")

    return 0


def cmd_config(args, log: DesktopMaestroLogger):
    """Manage configuration."""
    config_path = args.config or DEFAULT_CONFIG_FILE

    if args.config_action == "init":
        log.section("⚙️  INITIALIZING CONFIGURATION")
        path = create_default_config(config_path)
        log.success(f"✅ Configuration created at: {path}")
        return 0

    elif args.config_action == "edit":
        log.section("✏️  EDITING CONFIGURATION")
        config_path = os.path.expanduser(config_path)

        if not os.path.exists(config_path):
            create_default_config(config_path)
            log.info(f"📄 Created new file: {config_path}")

        # Intentar abrir con editor
        editors = [
            os.environ.get("EDITOR"),
            os.environ.get("VISUAL"),
            "code",
            "subl",
            "nano",
            "vim",
            "open",  # macOS: abre en TextEdit o Xcode
        ]

        for editor in editors:
            if editor:
                try:
                    import subprocess
                    subprocess.run(
                        [editor, config_path],
                        timeout=5,
                    )
                    log.success(f"✅ Opened with {editor}")
                    return 0
                except (subprocess.SubprocessError, FileNotFoundError, OSError):
                    continue

        log.info(f"📄 Open manually: {config_path}")
        return 0

    elif args.config_action == "show":
        log.section("⚙️  CURRENT CONFIGURATION")
        config = load_config(config_path)
        import json
        print(json.dumps(config.to_dict(), indent=2, ensure_ascii=False))
        return 0

    elif args.config_action == "path":
        print(os.path.expanduser(config_path))
        return 0

    elif args.config_action == "reset":
        log.section("🔄 RESETTING CONFIGURATION")

        if not args.force and is_macos():
            result = show_macos_dialog(
                "DesktopMaestro – Reset",
                "Reset configuration to defaults?\n"
                "Custom changes will be lost.",
                buttons=["Reset", "Cancel"],
                default_button="Cancel",
                icon="caution",
            )
            if result != "Reset":
                log.info("⏹️  Cancelled")
                return 0

        path = create_default_config(config_path)
        log.success(f"✅ Configuration reset at: {path}")
        return 0

    # Si no hay subcomando
    config_path_expanded = os.path.expanduser(config_path)
    exists = os.path.exists(config_path_expanded)
    log.info(f"📄 Path: {config_path_expanded}")
    log.info(f"📌 Status: {'✅ Exists' if exists else '❌ Does not exist'}")
    if not exists:
        log.info("💡 Create one: desktopmaestro config init")
    return 0


def cmd_schedule(args, log: DesktopMaestroLogger):
    """Manage scheduled organization."""
    if args.schedule_action == "enable":
        log.section("⏰ ENABLING SCHEDULED ORGANIZATION")

        interval = args.interval or 6
        log.info(f"⏰ Interval: every {interval} hours")

        try:
            path = create_launch_agent(interval_hours=interval)
            log.success(f"✅ LaunchAgent created: {path}")
            log.info("ℹ️  DesktopMaestro will run automatically")
            send_macos_notification(
                title="DesktopMaestro",
                message=f"Scheduled organization every {interval}h",
                subtitle="Scheduling enabled",
            )
        except Exception as e:
            log.error(f"❌ Error creating LaunchAgent: {e}")
            return 1

    elif args.schedule_action == "disable":
        log.section("⏹️  DISABLING SCHEDULED ORGANIZATION")

        if remove_launch_agent():
            log.success("✅ Scheduling disabled")
            send_macos_notification(
                title="DesktopMaestro",
                message="Scheduled organization disabled",
                subtitle="Scheduling disabled",
            )
        else:
            log.info("ℹ️  No scheduling was active")

    elif args.schedule_action == "status":
        log.section("⏰ SCHEDULING STATUS")

        plist_path = os.path.expanduser(
            "~/Library/LaunchAgents/com.desktopmaestro.plist"
        )
        if os.path.exists(plist_path):
            log.success("✅ Scheduling active")
            log.info(f"📄 {plist_path}")

            # Intentar leer intervalo
            try:
                import plistlib
                with open(plist_path, 'rb') as f:
                    plist = plistlib.load(f)
                interval = plist.get("StartInterval", 0)
                if interval:
                    hours = interval // 3600
                    log.info(f"⏰ Interval: every {hours} hours")
            except Exception:
                pass
        else:
            log.info("❌ Scheduling inactive")
            log.info("💡 Enable it: desktopmaestro schedule enable")

    else:
        log.info("❓ Use: desktopmaestro schedule enable|disable|status")

    return 0


def cmd_system(args, log: DesktopMaestroLogger):
    """Display system information."""
    log.section("💻 SYSTEM INFORMATION")

    info = get_system_info()
    for key, value in info.items():
        label = key.replace("_", " ").title()
        log.info(f"   • {label:20s} → {value}")

    log.info("")
    log.info(f"🐍 Python:     {sys.executable}")

    # Verificar dependencias
    log.info("")
    log.info("📦 Dependencies:")
    deps = {
        "PyYAML": False,
        "tag": False,
    }
    try:
        import yaml
        deps["PyYAML"] = True
    except ImportError:
        pass

    import shutil
    deps["tag"] = shutil.which("tag") is not None

    for dep, installed in deps.items():
        status = "✅" if installed else "❌"
        log.info(f"   {status} {dep}")

    if not deps["PyYAML"]:
        log.info("   💡 Instala: pip install pyyaml")
    if not deps["tag"]:
        log.info("   💡 Install: brew install tag (optional, for color tags)")

    return 0


def cmd_web(args, log: DesktopMaestroLogger):
    """Launch the web UI server."""
    from .server import run_server
    log.section("🌐 WEB UI")
    log.info(f"🚀 Starting API server on http://127.0.0.1:{args.port}")
    log.info(f"📱 Start frontend: cd frontend && npm run dev")
    log.info(f"💡 Or open: http://localhost:3000")
    log.info("")

    if args.open:
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{args.port}/api/health")

    run_server(port=args.port)
    return 0


# ─── Helper: Progress Bar ───

def _progress_bar(percentage: float, width: int = 30) -> str:
    """Generate a visual progress bar."""
    filled = int(width * percentage / 100)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}]"


# ─── Entry Point ───

def main(argv: Optional[list] = None) -> int:
    """Main entry point for DesktopMaestro."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Load configuration and apply language override
    config = load_config(args.config)
    if args.lang:
        config.language = args.lang

    log = DesktopMaestroLogger(
        verbose=args.verbose or config.verbose,
    )

    # Show banner
    if args.command != "config" or args.config_action != "path":
        print(BANNER)

    if not args.command:
        parser.print_help()
        return 0

    # Enrutar comandos
    command_handlers = {
        "organize": cmd_organize,
        "org": cmd_organize,
        "o": cmd_organize,
        "undo": cmd_undo,
        "u": cmd_undo,
        "stats": cmd_stats,
        "s": cmd_stats,
        "status": cmd_stats,
        "config": cmd_config,
        "c": cmd_config,
        "schedule": cmd_schedule,
        "timer": cmd_schedule,
        "system": cmd_system,
        "info": cmd_system,
        "web": cmd_web,
        "ui": cmd_web,
        "gui": cmd_web,
        "frontend": cmd_web,
    }

    handler = command_handlers.get(args.command)
    if handler:
        return handler(args, log)

    log.error(f"❌ Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
