"""
DesktopMaestro HTTP API Server.

Provides a REST API for the Next.js frontend to communicate with
the desktop organizer. Runs on http://127.0.0.1:7899.

Usage:
    desktopmaestro web           # Start the API server
    desktopmaestro web --port 7899  # Custom port
"""

from __future__ import annotations

import json
import os
import sys
import time
import signal
import shutil
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any, Dict, Optional
from dataclasses import asdict
from urllib.parse import urlparse, parse_qs

from . import __version__
from .core import DesktopOrganizer, organize_desktop
from .categories import (
    DEFAULT_CATEGORIES,
    OTHERS,
    CATEGORY_ICONS,
    translate_folder_name,
    get_supported_languages,
    SUPPORTED_LANGUAGES,
    smart_categorize,
)
from .config import load_config, save_config, DesktopMaestroConfig, DEFAULT_CONFIG_FILE
from .utils import get_desktop_stats, get_system_info


API_PORT = int(os.environ.get("DESKTOPMAESTRO_PORT", 7899))
API_HOST = os.environ.get("DESKTOPMAESTRO_HOST", "0.0.0.0")


class DesktopMaestroAPI(BaseHTTPRequestHandler):
    """HTTP request handler for the DesktopMaestro API."""

    # Silence per-request logs (we log manually)
    def log_message(self, format, *args):
        pass

    def _send_json(self, data: Any, status: int = 200):
        """Send a JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def _read_body(self) -> Dict[str, Any]:
        """Read and parse JSON request body."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        body = self.rfile.read(length)
        return json.loads(body.decode("utf-8"))

    def _get_lang(self) -> str:
        """Extract language from query params."""
        qs = parse_qs(urlparse(self.path).query)
        lang = qs.get("lang", ["en"])[0]
        return lang if lang in SUPPORTED_LANGUAGES else "en"

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format a byte count into a human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header(
            "Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS"
        )
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")

        if path == "/api/health" or path == "/health":
            return self._send_json(
                {
                    "status": "ok",
                    "version": __version__,
                    "language": self._get_lang(),
                    "languages": get_supported_languages(),
                }
            )

        if path == "/api/stats" or path == "/stats":
            config = load_config()
            stats = get_desktop_stats(config.desktop_path)
            return self._send_json(stats)

        if path == "/api/categories" or path == "/categories":
            lang = self._get_lang()
            cats = []
            for cat in DEFAULT_CATEGORIES:
                if cat.name == "macOS System":
                    continue
                cats.append(
                    {
                        "name": cat.name,
                        "icon": cat.icon,
                        "folder_name": cat.get_localized_folder(lang),
                        "extensions": sorted(cat.extensions),
                        "priority": cat.priority,
                    }
                )
            # Add "Others"
            cats.append(
                {
                    "name": "Others",
                    "icon": "📦",
                    "folder_name": translate_folder_name("Others", "📦", lang),
                    "extensions": [],
                    "priority": -999,
                }
            )
            return self._send_json(cats)

        if path == "/api/config" or path == "/config":
            config = load_config()
            return self._send_json(config.to_dict())

        if path == "/api/undo/snapshots" or path == "/undo/snapshots":
            organizer = DesktopOrganizer()
            snaps = organizer.undo_manager.list_snapshots()
            return self._send_json(snaps)

        if path == "/api/system" or path == "/system":
            info = get_system_info()
            return self._send_json(info)

        if path == "/api/folders" or path == "/folders":
            qs = parse_qs(urlparse(self.path).query)
            folder_path = qs.get("path", ["~"])[0]
            folder_path = os.path.expanduser(folder_path)
            try:
                items = []
                if os.path.isdir(folder_path):
                    for entry in sorted(os.listdir(folder_path)):
                        full = os.path.join(folder_path, entry)
                        if os.path.isdir(full) and not entry.startswith("."):
                            items.append(entry)
                parent = os.path.dirname(folder_path) if folder_path != "/" else None
                return self._send_json(
                    {
                        "path": folder_path,
                        "folders": items,
                        "parent": parent,
                    }
                )
            except PermissionError:
                return self._send_json(
                    {
                        "error": "Permission denied",
                        "path": folder_path,
                        "folders": [],
                        "parent": os.path.dirname(folder_path),
                    },
                    403,
                )
            except Exception as e:
                return self._send_json(
                    {
                        "error": str(e),
                        "path": folder_path,
                        "folders": [],
                    },
                    500,
                )

        if path == "/api/scan" or path == "/scan":
            qs = parse_qs(urlparse(self.path).query)
            folder_path = qs.get("path", ["~"])[0]
            folder_path = os.path.expanduser(folder_path)
            lang = self._get_lang()

            try:
                if not os.path.isdir(folder_path):
                    return self._send_json(
                        {
                            "error": "Directory not found",
                            "path": folder_path,
                            "items": [],
                            "total_files": 0,
                            "total_folders": 0,
                        },
                        404,
                    )

                items: list[Dict[str, Any]] = []
                total_files = 0
                total_size = 0
                by_extension: Dict[str, int] = {}
                by_category: Dict[str, int] = {}

                for entry in sorted(os.listdir(folder_path)):
                    if entry.startswith("."):
                        continue

                    full = os.path.join(folder_path, entry)
                    is_dir = os.path.isdir(full)

                    item: Dict[str, Any] = {
                        "name": entry,
                        "is_dir": is_dir,
                        "size": 0,
                        "size_human": "",
                        "extension": "",
                        "modified": "",
                        "category": None,
                    }

                    try:
                        st = os.stat(full)
                        item["size"] = st.st_size
                        item["size_human"] = self._format_size(st.st_size)
                        item["modified"] = datetime.fromtimestamp(st.st_mtime).strftime(
                            "%Y-%m-%d %H:%M"
                        )
                    except OSError:
                        pass

                    if not is_dir:
                        total_files += 1
                        total_size += item["size"]
                        _, ext = os.path.splitext(entry)
                        ext = ext.lower() or "(no extension)"
                        item["extension"] = ext

                        by_extension[ext] = by_extension.get(ext, 0) + 1

                        cat = smart_categorize(entry)
                        item["category"] = {
                            "name": cat.name,
                            "localized_name": cat.get_localized_name(lang),
                            "icon": cat.icon,
                            "folder_name": cat.get_localized_folder(lang),
                        }
                        by_category[cat.name] = by_category.get(cat.name, 0) + 1

                    items.append(item)

                # Folders first, then files
                items.sort(key=lambda i: (not i["is_dir"], i["name"].lower()))

                parent = os.path.dirname(folder_path) if folder_path != "/" else None

                return self._send_json(
                    {
                        "path": folder_path,
                        "name": os.path.basename(folder_path) or folder_path,
                        "parent": parent,
                        "items": items,
                        "total_files": total_files,
                        "total_folders": sum(1 for i in items if i["is_dir"]),
                        "total_size": total_size,
                        "total_size_human": self._format_size(total_size),
                        "by_extension": by_extension,
                        "by_category": by_category,
                    }
                )
            except PermissionError:
                return self._send_json(
                    {
                        "error": "Permission denied",
                        "path": folder_path,
                        "items": [],
                        "total_files": 0,
                        "total_folders": 0,
                    },
                    403,
                )
            except Exception as e:
                return self._send_json(
                    {
                        "error": str(e),
                        "path": folder_path,
                        "items": [],
                        "total_files": 0,
                        "total_folders": 0,
                    },
                    500,
                )

        if path == "/api/pick-folder" or path == "/pick-folder":
            """Show a native macOS folder picker dialog via osascript.

            Falls back to web-based folder selection when osascript
            is unavailable (e.g. Docker/Linux).
            """
            try:
                # Try native dialog via osascript (macOS only)
                if sys.platform == "darwin":
                    script = """
                    tell application "System Events"
                        activate
                    end tell
                    choose folder with prompt "Select a folder to organize"
                    """
                    result = subprocess.run(
                        ["osascript", "-e", script],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode == 0:
                        selected = result.stdout.strip()
                        # osascript returns "Macintosh HD:Users:..."
                        # Convert to POSIX path
                        selected = selected.replace(":", "/")
                        if selected.startswith("/"):
                            return self._send_json({"path": selected})

                # Fallback: return available common paths
                return self._send_json({
                    "path": None,
                    "suggestions": [
                        os.path.expanduser("~/Desktop"),
                        os.path.expanduser("~/Documents"),
                        os.path.expanduser("~/Downloads"),
                        os.path.expanduser("~"),
                    ],
                    "hint": "Use the web folder browser or type a path manually",
                })
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")
        body = self._read_body()

        if path == "/api/organize" or path == "/organize":
            dry_run = body.get("dry_run", False)
            lang = body.get("language", "en")
            custom_path = body.get("path")

            start = time.time()
            try:
                overrides: Dict[str, Any] = {"language": lang}
                if custom_path:
                    overrides["desktop_path"] = custom_path
                result = organize_desktop(dry_run=dry_run, **overrides)
                elapsed = time.time() - start
                return self._send_json(
                    {
                        "success_count": result.success_count,
                        "skipped_count": len(result.skipped_files),
                        "error_count": len(result.errors),
                        "categories_created": list(result.categories_created),
                        "dry_run": result.dry_run,
                        "duration": f"{elapsed:.2f}s",
                    }
                )
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if path == "/api/undo" or path == "/undo":
            snapshot = body.get("snapshot")
            config = load_config()
            organizer = DesktopOrganizer(config=config)
            try:
                results = organizer.undo(snapshot_path=snapshot)
                success = sum(1 for _, _, ok in results if ok)
                errors = sum(1 for _, _, ok in results if not ok)
                return self._send_json({"restored": success, "errors": errors})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        self._send_json({"error": "Not found"}, 404)

    def do_PUT(self):
        path = urlparse(self.path).path.rstrip("/")
        body = self._read_body()

        if path == "/api/config" or path == "/config":
            config = load_config()
            for key, value in body.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            save_config(config)
            return self._send_json(config.to_dict())

        self._send_json({"error": "Not found"}, 404)


def run_server(port: int = API_PORT, host: str = API_HOST):
    """Start the DesktopMaestro HTTP API server."""
    server = HTTPServer((host, port), DesktopMaestroAPI)

    # Handle shutdown gracefully
    def shutdown(sig, frame):
        print(f"\n🛑 Shutting down DesktopMaestro API server...")
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"🧹 DesktopMaestro API Server v{__version__}")
    print(f"🌐  http://{host}:{port}")
    print(f"📖  API docs: http://{host}:{port}/api/health")
    print(f"💡  Press Ctrl+C to stop")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


def start_web(args):
    """CLI handler for 'desktopmaestro web'."""
    port = getattr(args, "port", API_PORT)
    run_server(port=port)


if __name__ == "__main__":
    run_server()
