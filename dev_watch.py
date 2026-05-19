"""
DesktopMaestro Dev Watch — Auto-reloads the API server on file changes.
Used by docker compose in development mode.
"""

import os
import sys
import time
import signal
import subprocess
from pathlib import Path

WATCH_DIRS = [
    Path(__file__).parent / "organizer",
    Path(__file__).parent / "config",
]

IGNORE_PATTERNS = ("__pycache__", ".pyc", ".pyo", ".swp", "~")
SERVER_ARGS = sys.argv[1:] if len(sys.argv) > 1 else ["web", "--port", "7899"]
SERVER_PROCESS = None


def should_watch(path: str) -> bool:
    for p in IGNORE_PATTERNS:
        if p in path:
            return False
    return path.endswith(".py") or path.endswith(".yaml") or path.endswith(".yml")


def start_server():
    global SERVER_PROCESS
    if SERVER_PROCESS:
        SERVER_PROCESS.terminate()
        try:
            SERVER_PROCESS.wait(timeout=5)
        except subprocess.TimeoutExpired:
            SERVER_PROCESS.kill()

    print(f"\n{'=' * 50}")
    print(f"🚀 Starting DesktopMaestro API (dev mode)...")
    print(f"{'=' * 50}\n")

    SERVER_PROCESS = subprocess.Popen(
        [sys.executable, "-m", "organizer.cli"] + SERVER_ARGS,
        cwd=Path(__file__).parent,
    )


def watch():
    """Poll for file changes and restart server."""
    last_mtimes = {}

    for watch_dir in WATCH_DIRS:
        if watch_dir.exists():
            for f in watch_dir.rglob("*"):
                if f.is_file() and should_watch(str(f)):
                    last_mtimes[str(f)] = f.stat().st_mtime

    print(f"👀 Watching {len(last_mtimes)} files for changes...")
    print(f"   Change a .py file and the server auto-restarts ✨\n")

    while True:
        time.sleep(0.8)
        changed = False

        for watch_dir in WATCH_DIRS:
            if not watch_dir.exists():
                continue
            for f in watch_dir.rglob("*"):
                if not f.is_file() or not should_watch(str(f)):
                    continue
                try:
                    new_mtime = f.stat().st_mtime
                    old_mtime = last_mtimes.get(str(f))
                    if old_mtime is None:
                        last_mtimes[str(f)] = new_mtime
                    elif new_mtime > old_mtime:
                        last_mtimes[str(f)] = new_mtime
                        rel_path = f.relative_to(Path(__file__).parent)
                        print(f"\n📝 Changed: {rel_path}")
                        changed = True
                except OSError:
                    pass

        if changed:
            start_server()


if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def cleanup(sig, frame):
        if SERVER_PROCESS:
            SERVER_PROCESS.terminate()
        print("\n👋 Dev watch stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    start_server()
    watch()
