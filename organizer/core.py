"""
Core engine — the heart of DesktopMaestro.

Handles desktop scanning, file categorization, safe file movement,
undo snapshots, and macOS-specific operations.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from .categories import (
    DEFAULT_CATEGORIES,
    MACOS_SYSTEM_FILES,
    OTHERS,
    Category,
    get_category_folder_name,
    is_macos_system_file,
    smart_categorize,
)
from .config import DEFAULT_CONFIG_DIR, DesktopMaestroConfig, load_config


# ─── Events / Callbacks ───


class OrganizerEvents:
    """
    Callback container for organization events.

    Subscribe by setting the corresponding attribute to your callback.
    All callbacks are optional (can be None).
    """

    def __init__(self) -> None:
        self.on_start: Optional[Callable[[], None]] = None
        """Called when organization begins."""
        self.on_file_moved: Optional[Callable[[str, str, str], None]] = None
        """Called for each file moved: (source, destination, category)."""
        self.on_file_skipped: Optional[Callable[[str, str], None]] = None
        """Called when a file is skipped: (path, reason)."""
        self.on_category_created: Optional[Callable[[str], None]] = None
        """Called when a category folder is created."""
        self.on_error: Optional[Callable[[str, Exception], None]] = None
        """Called on error: (path, exception)."""
        self.on_complete: Optional[Callable[[int, int, int], None]] = None
        """Called when organization finishes: (moved, skipped, errors)."""
        self.on_progress: Optional[Callable[[int, int, str], None]] = None
        """Progress callback: (current, total, current_filename)."""
        self.on_undo_created: Optional[Callable[[str], None]] = None
        """Called when an undo snapshot is saved."""

    def fire_start(self) -> None:
        """Fire the on_start event."""
        if self.on_start:
            self.on_start()

    def fire_file_moved(self, src: str, dst: str, category: str) -> None:
        """Fire the on_file_moved event."""
        if self.on_file_moved:
            self.on_file_moved(src, dst, category)

    def fire_file_skipped(self, path: str, reason: str) -> None:
        """Fire the on_file_skipped event."""
        if self.on_file_skipped:
            self.on_file_skipped(path, reason)

    def fire_category_created(self, folder: str) -> None:
        """Fire the on_category_created event."""
        if self.on_category_created:
            self.on_category_created(folder)

    def fire_error(self, path: str, error: Exception) -> None:
        """Fire the on_error event."""
        if self.on_error:
            self.on_error(path, error)

    def fire_complete(self, moved: int, skipped: int, errors: int) -> None:
        """Fire the on_complete event."""
        if self.on_complete:
            self.on_complete(moved, skipped, errors)

    def fire_progress(self, current: int, total: int, filename: str) -> None:
        """Fire the on_progress event."""
        if self.on_progress:
            self.on_progress(current, total, filename)

    def fire_undo_created(self, undo_path: str) -> None:
        """Fire the on_undo_created event."""
        if self.on_undo_created:
            self.on_undo_created(undo_path)


@dataclass
class OrganizeResult:
    """
    Result of an organization operation.

    Contains lists of moved/skipped/errored files, created folders,
    timing information, and a human-readable summary.
    """

    moved_files: List[Tuple[str, str, str]] = field(default_factory=list)
    """List of (source, destination, category_name) for each moved file."""
    skipped_files: List[Tuple[str, str]] = field(default_factory=list)
    """List of (path, reason) for skipped files."""
    errors: List[Tuple[str, str]] = field(default_factory=list)
    """List of (path, error_message) for errors."""
    categories_created: List[str] = field(default_factory=list)
    """Names of category folders that were created."""
    start_time: float = 0.0
    """Unix timestamp when the operation started."""
    end_time: float = 0.0
    """Unix timestamp when the operation ended."""
    total_files_found: int = 0
    """Total files discovered on the desktop."""
    dry_run: bool = False
    """Whether this was a dry-run (simulation) operation."""

    @property
    def duration_seconds(self) -> float:
        """Total duration of the operation in seconds."""
        return self.end_time - self.start_time

    @property
    def success_count(self) -> int:
        """Number of files successfully moved."""
        return len(self.moved_files)

    def summary(self) -> str:
        """Generate a human-readable summary of the operation."""
        lines = []
        lines.append("=" * 50)
        if self.dry_run:
            lines.append("🔍 DRY RUN - No files were moved")
        lines.append("📊 Organization Summary:")
        lines.append(f"   • Files found:     {self.total_files_found}")
        lines.append(f"   • Files moved:     {self.success_count}")
        lines.append(f"   • Files skipped:   {len(self.skipped_files)}")
        lines.append(f"   • Errors:          {len(self.errors)}")
        lines.append(f"   • Folders created: {len(self.categories_created)}")
        lines.append(f"   • Time elapsed:    {self.duration_seconds:.2f}s")

        if self.categories_created:
            lines.append(f"\n📁 Folders created:")
            for folder in self.categories_created:
                lines.append(f"   • {folder}")

        if self.moved_files:
            lines.append(f"\n📦 Files organized:")
            for src, dst, cat in self.moved_files[:10]:
                lines.append(f"   • {os.path.basename(src)} → {cat}")
            if len(self.moved_files) > 10:
                lines.append(f"   ... and {len(self.moved_files) - 10} more")

        if self.errors:
            lines.append(f"\n❌ Errors:")
            for path, error in self.errors[:5]:
                lines.append(f"   • {os.path.basename(path)}: {error}")
            if len(self.errors) > 5:
                lines.append(f"   ... and {len(self.errors) - 5} more")

        lines.append("=" * 50)
        return "\n".join(lines)


@dataclass
class UndoEntry:
    """A single entry in the undo history."""

    timestamp: str
    """ISO-formatted timestamp of the operation."""
    source_path: str
    """Original file path before organization."""
    destination_path: str
    """File path after organization."""
    file_hash: str
    """SHA-256 hash of the file content for integrity verification."""
    file_size: int
    """File size in bytes."""

    def to_dict(self) -> Dict[str, object]:
        """Serialize to a plain dictionary for JSON storage."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> UndoEntry:
        """Deserialize from a dictionary."""
        return cls(**data)


class UndoManager:
    """
    Manages undo history for organization operations.

    Each organization creates a JSON snapshot containing file paths,
    hashes, and metadata, allowing full reversal of operations.
    """

    def __init__(self, config_dir: str = DEFAULT_CONFIG_DIR) -> None:
        """
        Initialize the undo manager.

        Args:
            config_dir: Directory where configuration and undo data are stored.
        """
        self.config_dir = config_dir
        self.undo_dir = os.path.join(config_dir, "undo")
        os.makedirs(self.undo_dir, exist_ok=True)

    def _get_snapshot_path(self, timestamp: str) -> str:
        """Get the file path for a snapshot by timestamp."""
        return os.path.join(self.undo_dir, f"undo_{timestamp}.json")

    def create_snapshot(
        self,
        entries: List[UndoEntry],
        description: str = "",
    ) -> str:
        """
        Create an undo snapshot file.

        Args:
            entries: List of UndoEntry instances for each moved file.
            description: Human-readable description of the operation.

        Returns:
            Path to the created snapshot file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        snapshot = {
            "timestamp": timestamp,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "entries": [e.to_dict() for e in entries],
        }

        path = self._get_snapshot_path(timestamp)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)

        self._cleanup_old_snapshots()
        return path

    def restore_snapshot(
        self, snapshot_path: str
    ) -> List[Tuple[str, str, bool]]:
        """
        Restore a snapshot (undo an organization).

        Before restoring, verifies file integrity via SHA-256 hashes.

        Args:
            snapshot_path: Path to the snapshot JSON file.

        Returns:
            List of (path, status_message, success) tuples.
        """
        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshot = json.load(f)

        results: List[Tuple[str, str, bool]] = []
        entries = [UndoEntry.from_dict(e) for e in snapshot["entries"]]

        # Restore in reverse order (last moved → first restored)
        for entry in reversed(entries):
            try:
                if os.path.exists(entry.destination_path):
                    # Integrity check
                    if os.path.isfile(entry.destination_path):
                        current_hash = self._compute_hash(
                            entry.destination_path
                        )
                        if current_hash != entry.file_hash:
                            results.append((
                                entry.destination_path,
                                "⚠️ File has changed since organization",
                                False,
                            ))
                            continue

                    # Move back to original location
                    os.makedirs(
                        os.path.dirname(entry.source_path), exist_ok=True
                    )
                    shutil.move(entry.destination_path, entry.source_path)
                    results.append((
                        entry.destination_path,
                        f"✅ Restored to {entry.source_path}",
                        True,
                    ))
                else:
                    results.append((
                        entry.destination_path,
                        "❌ File no longer exists",
                        False,
                    ))
            except Exception as exc:
                results.append((
                    entry.destination_path,
                    f"❌ Error: {exc}",
                    False,
                ))

        # Clean up empty folders left after restoration
        if entries:
            self._cleanup_empty_folders(
                os.path.dirname(entries[0].destination_path)
            )

        return results

    def list_snapshots(self) -> List[Dict]:
        """
        List all available undo snapshots, sorted newest first.

        Returns:
            List of dicts with keys: file, path, timestamp, description,
            created_at, entries_count, error (if unreadable).
        """
        snapshots: List[Dict] = []
        if not os.path.exists(self.undo_dir):
            return snapshots

        for f in sorted(os.listdir(self.undo_dir), reverse=True):
            if f.startswith("undo_") and f.endswith(".json"):
                path = os.path.join(self.undo_dir, f)
                try:
                    with open(path, "r", encoding="utf-8") as fp:
                        data = json.load(fp)
                    snapshots.append({
                        "file": f,
                        "path": path,
                        "timestamp": data.get("timestamp", ""),
                        "description": data.get("description", ""),
                        "created_at": data.get("created_at", ""),
                        "entries_count": len(data.get("entries", [])),
                    })
                except Exception:
                    snapshots.append({
                        "file": f,
                        "path": path,
                        "error": "Could not read snapshot",
                    })

        return snapshots

    def _compute_hash(self, filepath: str) -> str:
        """Compute SHA-256 hash of a file."""
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def _cleanup_old_snapshots(self, max_snapshots: int = 50) -> None:
        """Remove oldest snapshots when exceeding the limit."""
        snapshots = sorted([
            os.path.join(self.undo_dir, f)
            for f in os.listdir(self.undo_dir)
            if f.startswith("undo_") and f.endswith(".json")
        ])

        while len(snapshots) > max_snapshots:
            oldest = snapshots.pop(0)
            try:
                os.remove(oldest)
            except OSError:
                pass

    def _cleanup_empty_folders(self, base_path: str) -> None:
        """Remove empty folders after a restore operation."""
        if not os.path.exists(base_path):
            return
        for root, dirs, _files in os.walk(base_path, topdown=False):
            for d in dirs:
                dirpath = os.path.join(root, d)
                try:
                    if not os.listdir(dirpath):
                        os.rmdir(dirpath)
                except OSError:
                    pass


class DesktopOrganizer:
    """
    The main organizer engine.

    Scans the desktop, categorizes files, creates category folders,
    and moves files with safety guarantees and undo support.
    """

    def __init__(
        self,
        config: Optional[DesktopMaestroConfig] = None,
        config_path: Optional[str] = None,
    ) -> None:
        """
        Initialize the organizer.

        Args:
            config: A pre-built configuration instance. If None, loads
                    from config_path or the default location.
            config_path: Alternative path to the configuration file.
        """
        if config:
            self.config = config
        else:
            self.config = load_config(config_path)

        self.events = OrganizerEvents()
        self.undo_manager = UndoManager(self.config.config_dir)
        self._abort_flag = False

    # ─── Properties ───

    @property
    def desktop(self) -> str:
        """Expanded path to the desktop directory."""
        return os.path.expanduser(self.config.desktop_path)

    @property
    def is_dry_run(self) -> bool:
        """Whether the organizer is in simulation mode."""
        return self.config.dry_run

    # ─── Public API ───

    def organize(self) -> OrganizeResult:
        """
        Run a full desktop organization.

        Scans, categorizes, creates folders, and moves files.
        Returns a detailed result object.

        Returns:
            OrganizeResult with details about all operations.

        Raises:
            NotADirectoryError: If the configured desktop path doesn't exist.
            PermissionError: If macOS Full Disk Access is denied.
        """
        result = OrganizeResult()
        result.start_time = time.time()
        result.dry_run = self.is_dry_run

        self.events.fire_start()

        desktop_path = self.desktop

        if not os.path.isdir(desktop_path):
            raise NotADirectoryError(
                f"Directory '{desktop_path}' does not exist."
            )

        # Verify read permissions (macOS Full Disk Access)
        try:
            os.listdir(desktop_path)
        except PermissionError:
            self.events.fire_error(
                desktop_path,
                PermissionError("macOS blocks access to the desktop"),
            )
            from .utils import send_macos_notification, show_macos_dialog

            send_macos_notification(
                title="DesktopMaestro",
                message="Cannot read the desktop — need Full Disk Access",
                subtitle="Permission Required",
            )

            dialog_result = show_macos_dialog(
                "DesktopMaestro – Permissions",
                "DesktopMaestro cannot access your desktop.\n\n"
                "Would you like to see how to fix this?",
                buttons=["Show Instructions", "Cancel"],
                default_button="Show Instructions",
                icon="caution",
            )

            if dialog_result == "Show Instructions":
                DesktopOrganizer._show_permissions_guide()

            raise PermissionError(
                "🧹 DesktopMaestro needs Full Disk Access to read your desktop.\n\n"
                "   macOS blocks this for security. To grant access:\n\n"
                "   1. Open System Settings / System Preferences\n"
                "   2. Go to Privacy & Security\n"
                "   3. Select 'Full Disk Access'\n"
                "   4. Click the 🔒 lock and enter your password\n"
                "   5. Add your terminal app (Terminal.app, iTerm2, etc.)\n"
                "   6. Restart your terminal and try again\n\n"
                "   Or try: desktopmaestro organize --path ~/Downloads"
            )

        # 1. Collect files from desktop
        files_to_process = self._scan_desktop(desktop_path)
        result.total_files_found = len(files_to_process)

        if not files_to_process:
            self.events.fire_complete(0, 0, 0)
            result.end_time = time.time()
            return result

        # 2. Categorize files
        categorized = self._categorize_files(files_to_process)

        # 3. Create destination folders
        target_categories = self._ensure_category_folders(
            desktop_path, categorized, result
        )

        # 4. Move files
        undo_entries = []
        total = len(files_to_process)
        processed = 0

        for category, files in categorized.items():
            if self._abort_flag:
                break

            category_folder = target_categories.get(category.name)
            if not category_folder:
                continue

            for filepath in files:
                if self._abort_flag:
                    break

                processed += 1
                filename = os.path.basename(filepath)
                self.events.fire_progress(processed, total, filename)

                try:
                    dst = self._move_file(
                        filepath, category_folder, category
                    )
                    if dst:
                        result.moved_files.append((
                            filepath, dst, category.name
                        ))
                        undo_entries.append(UndoEntry(
                            timestamp=datetime.now().isoformat(),
                            source_path=filepath,
                            destination_path=dst,
                            file_hash=self._compute_hash(filepath),
                            file_size=os.path.getsize(filepath),
                        ))
                        self.events.fire_file_moved(
                            filepath, dst, category.name
                        )
                    else:
                        # File was skipped (already in destination, etc.)
                        pass
                except Exception as e:
                    result.errors.append((filepath, str(e)))
                    self.events.fire_error(filepath, e)

        # 5. Create undo snapshot
        if undo_entries and self.config.create_undo_snapshot and not self.is_dry_run:
            try:
                undo_path = self.undo_manager.create_snapshot(
                    undo_entries,
                    description=(
                        f"Desktop organization "
                        f"({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})"
                    ),
                )
                self.events.fire_undo_created(undo_path)
            except Exception:
                # Non-critical — undo snapshot is best-effort
                pass

        result.end_time = time.time()
        self.events.fire_complete(
            len(result.moved_files),
            len(result.skipped_files),
            len(result.errors),
        )

        return result

    def undo(
        self, snapshot_path: Optional[str] = None
    ) -> List[Tuple[str, str, bool]]:
        """
        Undo the last organization operation.

        Args:
            snapshot_path: Specific snapshot file to restore (optional).

        Returns:
            List of (path, status_message, success) tuples.
        """
        if snapshot_path:
            return self.undo_manager.restore_snapshot(snapshot_path)

        snapshots = self.undo_manager.list_snapshots()
        if not snapshots:
            return [("", "No operations to undo", False)]

        return self.undo_manager.restore_snapshot(snapshots[0]["path"])

    def abort(self) -> None:
        """Safely abort the current organization operation."""
        self._abort_flag = True

    # ─── Internal Methods ───

    def _scan_desktop(self, desktop_path: str) -> List[str]:
        """
        Scan the desktop and collect eligible files.

        Rules:
        - Skips directories
        - Skips macOS system files
        - Skips files in exclude_files list
        - Skips files matching exclude_patterns
        - Respects include_extensions and exclude_extensions
        - Respects min_file_age_minutes

        Args:
            desktop_path: Path to the desktop directory.

        Returns:
            List of full file paths eligible for organization.
        """
        files = []

        try:
            entries = sorted(os.listdir(desktop_path))
        except PermissionError:
            return files

        for entry in entries:
            full_path = os.path.join(desktop_path, entry)

            # Saltar directorios
            if os.path.isdir(full_path):
                continue

            # Skip macOS system files
            if is_macos_system_file(entry):
                continue

            # Skip files excluded by name
            if entry in self.config.exclude_files:
                continue

            # Skip files matching regex patterns
            if self._matches_exclude_pattern(entry):
                continue

            # Check minimum file age
            if self.config.min_file_age_minutes > 0:
                try:
                    file_age = time.time() - os.path.getmtime(full_path)
                    if file_age < self.config.min_file_age_minutes * 60:
                        continue
                except OSError:
                    pass

            # Verificar extensiones
            _, ext = os.path.splitext(entry)
            ext = ext.lower()

            if self.config.include_extensions:
                if ext not in self.config.include_extensions:
                    continue

            if ext in self.config.exclude_extensions:
                continue

            files.append(full_path)

        return files

    def _matches_exclude_pattern(self, filename: str) -> bool:
        """Check if a filename matches any exclude regex patterns."""
        for pattern in self.config.exclude_patterns:
            try:
                if re.search(pattern, filename):
                    return True
            except re.error:
                pass
        return False

    def _categorize_files(
        self, files: List[str]
    ) -> Dict[Category, List[str]]:
        """
        Classify files into categories.

        Args:
            files: List of file paths to categorize.

        Returns:
            Dict mapping Category to list of file paths.
        """
        # Build custom categories from config
        custom_cats = None
        if self.config.custom_categories:
            custom_cats = []
            for cat_data in self.config.custom_categories:
                cat = Category(**cat_data)
                custom_cats.append(cat)

        # Disabled categories fall through to "Others"
        disabled = set(self.config.disabled_categories)

        categorized: Dict[Category, List[str]] = {}
        for filepath in files:
            filename = os.path.basename(filepath)
            category = smart_categorize(filename, custom_cats)

            if category.name in disabled:
                category = OTHERS

            if category not in categorized:
                categorized[category] = []
            categorized[category].append(filepath)

        return categorized

    def _ensure_category_folders(
        self,
        desktop_path: str,
        categorized: Dict[Category, List[str]],
        result: OrganizeResult,
    ) -> Dict[str, str]:
        """
        Create category folders on the desktop.

        Args:
            desktop_path: Path to the desktop.
            categorized: Dict of Category to files.
            result: OrganizeResult to record created folders.

        Returns:
            Dict mapping category name to folder path.
        """
        target_folders: Dict[str, str] = {}

        for category, files in categorized.items():
            if not files:
                continue

            folder_name = self.config.resolve_category_folder(category)
            folder_path = os.path.join(desktop_path, folder_name)

            if not os.path.exists(folder_path):
                if self.is_dry_run:
                    result.categories_created.append(folder_name)
                else:
                    try:
                        os.makedirs(folder_path, exist_ok=True)
                        result.categories_created.append(folder_name)
                        self.events.fire_category_created(folder_path)

                        # Create .localized file so Finder displays emoji names correctly
                        self._create_localized_file(folder_path, folder_name)

                        # Add macOS color tag (optional)
                        if self.config.add_tags_to_folders:
                            self._add_macos_tag(folder_path, category.name)

                    except OSError as exc:
                        result.errors.append((folder_path, str(exc)))
                        continue

            target_folders[category.name] = folder_path

        return target_folders

    def _move_file(
        self,
        src: str,
        dst_folder: str,
        category: Category,
    ) -> Optional[str]:
        """
        Safely move a file to its destination folder.

        Handles name sanitization, conflict resolution, and locked files.

        Args:
            src: Source file path.
            dst_folder: Destination folder path.
            category: The file category (for logging).

        Returns:
            Destination path if moved, None if skipped.
        """
        filename = os.path.basename(src)

        # Don't move if already in destination
        if os.path.dirname(src) == dst_folder:
            return None

        # Sanitize filename
        if self.config.remove_conflicting_chars:
            filename = self._sanitize_filename(filename)
        if self.config.lowercase_extensions:
            name, ext = os.path.splitext(filename)
            filename = f"{name}{ext.lower()}"

        dst = os.path.join(dst_folder, filename)

        # Resolve name conflicts
        if os.path.exists(dst):
            dst = self._resolve_conflict(dst_folder, filename)

        if self.is_dry_run:
            return dst

        # Skip locked/inaccessible files
        if self.config.skip_locked_files and not self._is_file_accessible(src):
            self.events.fire_file_skipped(src, "File locked or in use")
            return None

        # Move with fallback (copy + delete for cross-device)
        try:
            shutil.move(src, dst)
            return dst
        except shutil.Error:
            shutil.copy2(src, dst)
            os.remove(src)
            return dst

    def _resolve_conflict(self, folder: str, filename: str) -> str:
        """
        Resolve filename conflicts by appending a numeric suffix.

        E.g., "file.txt" -> "file (1).txt" -> "file (2).txt" ...
        """
        name, ext = os.path.splitext(filename)
        counter = 1
        while True:
            new_name = f"{name} ({counter}){ext}"
            new_path = os.path.join(folder, new_name)
            if not os.path.exists(new_path):
                return new_path
            counter += 1

    def _sanitize_filename(self, filename: str) -> str:
        """
        Remove problematic characters for macOS/Linux.
        """
        # Replace problematic characters
        sanitized = filename
        # Forbidden characters on macOS: : and /
        sanitized = sanitized.replace(":", " -")
        sanitized = sanitized.replace("/", "⁄")
        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
        # Remove multiple spaces
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        return sanitized

    def _is_file_accessible(self, filepath: str) -> bool:
        """Check whether a file is readable and not locked."""
        try:
            with open(filepath, "rb") as f:
                f.read(1)
            return True
        except (IOError, OSError):
            return False

    def _compute_hash(self, filepath: str) -> str:
        """Compute SHA-256 hash of a file for integrity verification."""
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()

    def _create_localized_file(
        self, folder_path: str, display_name: str
    ) -> None:
        """
        Create a .localized file so Finder displays emoji folder names correctly.
        """
        try:
            localized_path = os.path.join(folder_path, ".localized")
            if not os.path.exists(localized_path):
                Path(localized_path).touch()
        except OSError:
            pass

    def _add_macos_tag(self, folder_path: str, category_name: str) -> None:
        """
        Add a macOS Finder color tag to a folder.

        Requires the `tag` CLI: brew install tag

        Color mapping:
            Images -> Orange, Videos -> Purple, Audio -> Pink,
            Documents/PDFs -> Blue, Archives -> Gray, Code -> Green,
            Torrents -> Red
        """
        if not shutil.which("tag"):
            return

        color_map = {
            "Images": "Orange",
            "Videos": "Purple",
            "Audio": "Pink",
            "Documents": "Blue",
            "PDFs": "Blue",
            "Archives": "Gray",
            "Code": "Green",
            "Torrents": "Red",
        }

        color = color_map.get(category_name)
        if color:
            try:
                subprocess.run(
                    ["tag", "-a", color, folder_path],
                    capture_output=True, timeout=5,
                )
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

    @staticmethod
    def _show_permissions_guide() -> None:
        """Display a visual guide for granting Full Disk Access on macOS."""
        guide = (
            "\n"
            + "╔══════════════════════════════════════════════════════════════╗\n"
            + "║                                                              ║\n"
            + "║    🔒  macOS needs your permission                          ║\n"
            + "║    ─────────────────────────────                             ║\n"
            + "║                                                              ║\n"
            + "║    DesktopMaestro cannot read your desktop because            ║\n"
            + "║    macOS protects it for security.                           ║\n"
            + "║                                                              ║\n"
            + "║    To fix this:                                               ║\n"
            + "║                                                              ║\n"
            + "║    1.  Open System Settings → Privacy & Security             ║\n"
            + "║    2.  Go to Full Disk Access                               ║\n"
            + "║    3.  Click the lock and enter your password                ║\n"
            + "║    4.  Add your terminal (Terminal.app, iTerm2, etc.)       ║\n"
            + "║    5.  Restart terminal and run again                       ║\n"
            + "║        desktopmaestro organize                               ║\n"
            + "║                                                              ║\n"
            + "║    Or try: desktopmaestro organize --path ~/Downloads         ║\n"
            + "║                                                              ║\n"
            + "╚══════════════════════════════════════════════════════════════╝"
        )
        print(guide)
        try:
            subprocess.run(
                [
                    "open",
                    "x-apple.systempreferences:com.apple.preference.security"
                    "?Privacy_AllFiles",
                ],
                timeout=5,
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
    @staticmethod
    def request_full_disk_access() -> bool:
        """
        Open macOS System Settings to the Full Disk Access pane via AppleScript.

        Returns:
            True if the dialog was opened successfully.
        """
        if not shutil.which("osascript"):
            return False

        script = """
        tell application "System Settings"
            activate
            set current pane to pane id "com.apple.preference.security"
            reveal (first anchor of current pane whose name is "Privacy_AllFiles")
        end tell
        """

        try:
            subprocess.run(["osascript", "-e", script], timeout=10)
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False


# ─── High-level convenience function ───

def organize_desktop(
    config_path: Optional[str] = None,
    dry_run: bool = False,
    **kwargs,
) -> OrganizeResult:
    """
    Convenience function to organize the desktop in one call.

    Args:
        config_path: Path to a custom configuration file.
        dry_run: If True, simulate without moving files.
        **kwargs: Additional configuration attributes to override.

    Returns:
        OrganizeResult with the operation details.
    """
    config = load_config(config_path)
    if dry_run:
        config.dry_run = True
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)

    organizer = DesktopOrganizer(config=config)
    return organizer.organize()
