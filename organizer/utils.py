"""
Utility module for DesktopMaestro.

Provides logging, macOS notifications, LaunchAgent management,
desktop statistics, and system information helpers.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import plistlib
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .config import DEFAULT_LOG_DIR

# ─── OS Detection ───


def is_macos() -> bool:
    """Check whether the current system is macOS (Darwin)."""
    return platform.system() == "Darwin"


def is_macos_ventura_or_above() -> bool:
    """
    Check whether macOS version is 13+ (Ventura or later).

    Returns:
        True if running on macOS 13 or higher.
    """
    if not is_macos():
        return False
    version = platform.mac_ver()[0]
    try:
        major = int(version.split(".")[0])
        return major >= 13
    except (ValueError, IndexError):
        return False


def get_macos_version() -> str:
    """Get a human-readable macOS version string."""
    if not is_macos():
        return platform.system()
    return f"macOS {platform.mac_ver()[0]}"


# ─── Logging ───


class ColoredFormatter:
    """Format log messages with colors and emoji icons for the terminal."""

    colors: Dict[str, str] = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[41m",
        "RESET": "\033[0m",
    }
    icons: Dict[str, str] = {
        "DEBUG": "🐛",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🔥",
    }

    @classmethod
    def format(cls, level: str, message: str, use_color: bool = True) -> str:
        """
        Format a message with timestamp and optional ANSI colors.

        Args:
            level: Log level name (e.g., "INFO", "ERROR").
            message: The log message text.
            use_color: Whether to include ANSI color codes.

        Returns:
            Formatted string.
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = cls.icons.get(level, "")
        if use_color and sys.stdout.isatty():
            color = cls.colors.get(level, cls.colors["RESET"])
            reset = cls.colors["RESET"]
            return f"{color}{icon} [{timestamp}] {message}{reset}"
        return f"{icon} [{timestamp}] {message}"


class DesktopMaestroLogger:
    """
    Logger with terminal colors and file output support.

    Writes colorized output to stdout for interactive use and
    structured logs to a daily log file in the configured log directory.
    """

    def __init__(
        self,
        name: str = "DesktopMaestro",
        log_dir: str = DEFAULT_LOG_DIR,
        verbose: bool = True,
        log_to_file: bool = True,
    ):
        """
        Initialize the logger.

        Args:
            name: Logger name.
            log_dir: Directory for log files.
            verbose: Show debug-level messages.
            log_to_file: Write logs to a daily file.
        """
        self.name = name
        self.verbose = verbose
        self.log_dir = log_dir
        self.log_file: Optional[str] = None
        self._formatter = ColoredFormatter()

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG if verbose else logging.INFO)

        if log_to_file:
            self._setup_file_logging()

    def _setup_file_logging(self) -> None:
        """Configure logging to a daily file."""
        os.makedirs(self.log_dir, exist_ok=True)
        log_file = os.path.join(
            self.log_dir,
            f"desktopmaestro_{datetime.now().strftime('%Y%m%d')}.log",
        )

        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.log_file = log_file

    def debug(self, message: str) -> None:
        """Log a debug message."""
        self.logger.debug(message)
        if self.verbose:
            print(ColoredFormatter.format("DEBUG", message))

    def info(self, message: str) -> None:
        """Log an info message."""
        self.logger.info(message)
        print(ColoredFormatter.format("INFO", message))

    def warning(self, message: str) -> None:
        """Log a warning message."""
        self.logger.warning(message)
        print(ColoredFormatter.format("WARNING", message))

    def error(self, message: str) -> None:
        """Log an error message."""
        self.logger.error(message)
        print(ColoredFormatter.format("ERROR", message))

    def critical(self, message: str) -> None:
        """Log a critical message."""
        self.logger.critical(message)
        print(ColoredFormatter.format("CRITICAL", message))

    def success(self, message: str) -> None:
        """Log a success message with a checkmark icon."""
        self.logger.info(message)
        print(f"✅ {message}")

    def section(self, title: str) -> None:
        """Print a prominent section header."""
        width = 60
        self.logger.info(f"=== {title} ===")
        print(f"\n{'=' * width}")
        print(f"  {title}")
        print(f"{'=' * width}")


# ─── macOS Native Notifications ───


def send_macos_notification(
    title: str,
    message: str,
    subtitle: str = "",
    sound: bool = True,
) -> bool:
    """
    Send a native macOS notification via osascript.

    Args:
        title: Notification title.
        message: Notification body text.
        subtitle: Optional subtitle.
        sound: Play the default notification sound.

    Returns:
        True if the notification was sent successfully.
    """
    if not is_macos():
        return False

    script = f'display notification "{message}" with title "{title}"'

    if subtitle:
        script = (
            f'display notification "{message}" '
            f'with title "{title}" subtitle "{subtitle}"'
        )
    if sound:
        script += ' sound name "default"'

    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            timeout=5,
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def show_macos_dialog(
    title: str,
    message: str,
    buttons: Optional[List[str]] = None,
    default_button: str = "OK",
    icon: str = "note",
) -> Optional[str]:
    """
    Show a native macOS dialog window via osascript.

    Args:
        title: Dialog window title.
        message: Dialog message text.
        buttons: List of button labels (default: ["OK"]).
        default_button: Which button is selected by default.
        icon: Icon style: 'note', 'stop', or 'caution'.

    Returns:
        The label of the button pressed, or None if canceled.
    """
    if not is_macos():
        return None

    buttons = buttons or ["OK"]
    buttons_str = '", "'.join(buttons)
    script = (
        f'display dialog "{message}" '
        f'with title "{title}" '
        f'buttons {{"{buttons_str}"}} '
        f'default button "{default_button}" '
        f"with icon {icon}"
    )

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            for line in result.stdout.split(","):
                if "button returned:" in line:
                    return line.split(":")[1].strip()
        return None
    except (subprocess.SubprocessError, FileNotFoundError):
        return None


# ─── LaunchAgent (macOS auto-start) ───


def create_launch_agent(
    plist_path: str = "~/Library/LaunchAgents/com.desktopmaestro.plist",
    interval_hours: int = 6,
    python_path: Optional[str] = None,
) -> str:
    """
    Create a macOS LaunchAgent to run DesktopMaestro on a schedule.

    Uses launchd for zero-overhead background execution.

    Args:
        plist_path: Path for the .plist file.
        interval_hours: Interval in hours between runs.
        python_path: Python interpreter path (auto-detected if None).

    Returns:
        Path to the created .plist file.
    """
    plist_path = os.path.expanduser(plist_path)
    os.makedirs(os.path.dirname(plist_path), exist_ok=True)

    if python_path is None:
        python_path = sys.executable

    script_path = os.path.join(os.path.dirname(__file__), "cli.py")

    plist_data = {
        "Label": "com.desktopmaestro",
        "ProgramArguments": [python_path, script_path, "organize", "--headless"],
        "StartInterval": interval_hours * 3600,
        "RunAtLoad": True,
        "StandardOutPath": os.path.expanduser(
            "~/Library/Logs/DesktopMaestro/launchd.stdout.log"
        ),
        "StandardErrorPath": os.path.expanduser(
            "~/Library/Logs/DesktopMaestro/launchd.stderr.log"
        ),
        "EnvironmentVariables": {
            "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
        },
    }

    with open(plist_path, "wb") as f:
        plistlib.dump(plist_data, f)

    subprocess.run(
        ["launchctl", "load", plist_path],
        capture_output=True,
    )

    return plist_path


def remove_launch_agent(
    plist_path: str = "~/Library/LaunchAgents/com.desktopmaestro.plist",
) -> bool:
    """
    Remove and unload the DesktopMaestro LaunchAgent.

    Args:
        plist_path: Path to the .plist file.

    Returns:
        True if the agent was removed, False if it didn't exist.
    """
    plist_path = os.path.expanduser(plist_path)

    if os.path.exists(plist_path):
        subprocess.run(
            ["launchctl", "unload", plist_path],
            capture_output=True,
        )
        os.remove(plist_path)
        return True
    return False


# ─── Desktop Statistics ───


def get_desktop_stats(desktop_path: str = "~/Desktop") -> Dict:
    """
    Analyze a desktop directory and return detailed statistics.

    Includes file counts, size distribution, extension breakdown,
    and oldest/newest files.

    Args:
        desktop_path: Path to the desktop directory.

    Returns:
        Dict with keys: total_files, total_folders, total_size_bytes,
        total_size_human, by_extension, by_size_category, oldest_file,
        newest_file, and error (if applicable).
    """
    desktop_path = os.path.expanduser(desktop_path)

    if not os.path.isdir(desktop_path):
        return {"error": "Directory not found"}

    stats: Dict = {
        "total_files": 0,
        "total_folders": 0,
        "total_size_bytes": 0,
        "by_extension": {},
        "by_size_category": {
            "tiny": 0,  # < 10 KB
            "small": 0,  # 10 KB – 1 MB
            "medium": 0,  # 1 MB – 100 MB
            "large": 0,  # 100 MB – 1 GB
            "huge": 0,  # > 1 GB
        },
        "oldest_file": None,
        "newest_file": None,
    }

    oldest_time = float("inf")
    newest_time = 0.0
    oldest_name: Optional[str] = None
    newest_name: Optional[str] = None

    try:
        for entry in os.listdir(desktop_path):
            full_path = os.path.join(desktop_path, entry)

            if entry.startswith("."):
                continue

            if os.path.isdir(full_path):
                stats["total_folders"] += 1
                continue

            stats["total_files"] += 1

            try:
                file_size = os.path.getsize(full_path)
                stats["total_size_bytes"] += file_size

                _, ext = os.path.splitext(entry)
                ext = ext.lower() or "(no extension)"
                stats["by_extension"][ext] = stats["by_extension"].get(ext, 0) + 1

                # Size category
                if file_size < 10_240:
                    stats["by_size_category"]["tiny"] += 1
                elif file_size < 1_048_576:
                    stats["by_size_category"]["small"] += 1
                elif file_size < 104_857_600:
                    stats["by_size_category"]["medium"] += 1
                elif file_size < 1_073_741_824:
                    stats["by_size_category"]["large"] += 1
                else:
                    stats["by_size_category"]["huge"] += 1

                # Track dates
                mtime = os.path.getmtime(full_path)
                if mtime < oldest_time:
                    oldest_time = mtime
                    oldest_name = entry
                if mtime > newest_time:
                    newest_time = mtime
                    newest_name = entry

            except OSError:
                continue

        if oldest_name:
            stats["oldest_file"] = {
                "name": oldest_name,
                "date": datetime.fromtimestamp(oldest_time).isoformat(),
            }
        if newest_name:
            stats["newest_file"] = {
                "name": newest_name,
                "date": datetime.fromtimestamp(newest_time).isoformat(),
            }

        stats["total_size_human"] = _format_size(stats["total_size_bytes"])

    except PermissionError:
        stats["error"] = "Permission denied — macOS Full Disk Access required"

    return stats


def _format_size(size_bytes: int) -> str:
    """Format a byte count into a human-readable string."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


# ─── System Information ───


def get_system_info() -> Dict[str, str]:
    """
    Collect system information for diagnostics.

    Returns:
        Dict with keys: os, os_version, os_release, macos_version,
        python_version, hostname, architecture, processor.
    """
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "os_release": platform.release(),
        "macos_version": get_macos_version(),
        "python_version": platform.python_version(),
        "hostname": platform.node(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
    }
