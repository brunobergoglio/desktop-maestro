"""
Configuration module for DesktopMaestro.

Supports YAML and JSON formats with automatic validation,
default values, and comment-preserving defaults file generation.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any

try:
    import yaml

    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .categories import (
    DEFAULT_LANGUAGE,
    SUPPORTED_LANGUAGES,
    Category,
    get_category_folder_name,
)

# ─── Default paths (macOS) ───
DEFAULT_DESKTOP_PATH = os.path.expanduser("~/Desktop")
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/desktopmaestro")
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, "config.yaml")
DEFAULT_LOG_DIR = os.path.expanduser("~/Library/Logs/DesktopMaestro")


@dataclass
class DesktopMaestroConfig:
    """
    Complete configuration for DesktopMaestro.

    All settings have sensible defaults. Configuration is stored
    as YAML (or JSON) in ~/.config/desktopmaestro/config.yaml.
    """

    # ─── Paths ───
    desktop_path: str = DEFAULT_DESKTOP_PATH
    """Path to the desktop (or folder) to organize."""
    config_dir: str = DEFAULT_CONFIG_DIR
    """Directory where configuration and undo snapshots are stored."""
    log_dir: str = DEFAULT_LOG_DIR
    """Directory for log files."""

    # ─── Language ───
    language: str = DEFAULT_LANGUAGE
    """Language for folder names: 'en' (English) or 'es' (Español)."""

    # ─── Behavior ───
    dry_run: bool = False
    """If True, simulate without moving any files."""
    verbose: bool = True
    """Show detailed information during execution."""
    auto_organize: bool = False
    """Run organization automatically on startup."""
    organize_on_startup: bool = False
    """Run organization when user logs in."""
    create_icon_macos: bool = True
    """Create custom folder icons on macOS (via .localized files)."""

    # ─── Filters ───
    include_extensions: list[str] = field(default_factory=list)
    """Only include these extensions (empty = all)."""
    exclude_extensions: list[str] = field(default_factory=list)
    """Extensions to always skip."""
    exclude_files: list[str] = field(
        default_factory=lambda: [
            ".DS_Store",
            ".localized",
            "Desktop DB",
            "Desktop DF",
        ]
    )
    """Specific filenames to never touch."""
    exclude_patterns: list[str] = field(
        default_factory=lambda: [
            r"^\._.*",  # Apple Double files
            r"^\..*\.icloud$",  # iCloud placeholder files
        ]
    )
    """Regex patterns for files to exclude."""

    # ─── Custom Categories ───
    custom_categories: list[dict[str, Any]] = field(default_factory=list)
    """User-defined categories (see docs for format)."""
    disabled_categories: list[str] = field(default_factory=list)
    """Names of built-in categories to disable."""
    category_folder_names: dict[str, str] = field(default_factory=dict)
    """Custom folder name overrides for any category."""

    # ─── Organization ───
    max_folder_depth: int = 1
    """Maximum subfolder depth (1 = flat structure)."""
    sort_into_subfolders: bool = False
    """Create subfolders for sub-categories."""
    date_based_folders: bool = False
    """Group files by date (YYYY/MM structure)."""
    preserve_original_filenames: bool = True
    """Keep original filenames when moving."""
    lowercase_extensions: bool = True
    """Normalize extensions to lowercase (e.g., .JPG → .jpg)."""
    remove_conflicting_chars: bool = True
    """Remove characters invalid for macOS/Linux filenames."""

    # ─── Safety ───
    create_undo_snapshot: bool = True
    """Save an undo snapshot for every organization."""
    max_undo_snapshots: int = 50
    """Maximum number of undo snapshots to retain."""
    min_file_age_minutes: int = 0
    """Skip files newer than this many minutes (0 = any age)."""
    skip_locked_files: bool = True
    """Skip files that cannot be opened for reading."""
    skip_files_in_use: bool = True
    """Skip files that appear to be in use by another process."""

    # ─── Scheduling ───
    schedule_enabled: bool = False
    """Whether automatic organization is enabled."""
    schedule_interval_hours: int = 6
    """Interval in hours between automatic runs."""
    schedule_time: str | None = None
    """Specific time of day for scheduling (HH:MM)."""

    # ─── Notifications ───
    show_notifications: bool = True
    """Show macOS native notifications."""
    notification_on_complete: bool = True
    """Notify when organization completes."""
    notification_on_error: bool = True
    """Notify on errors during organization."""

    # ─── macOS Specific ───
    hide_dmg_volumes: bool = True
    """Hide mounted DMG volumes from organization."""
    skip_system_directories: bool = True
    """Skip macOS system directories."""
    respect_spotlight_tags: bool = False
    """Use Spotlight tags for categorization."""
    add_tags_to_folders: bool = False
    """Add color tags to category folders (requires 'brew install tag')."""

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to a plain dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DesktopMaestroConfig:
        """
        Create configuration from a dictionary.

        Only valid keys are used; unknown keys are silently ignored.

        Args:
            data: Dictionary with configuration values.

        Returns:
            A new DesktopMaestroConfig instance.
        """
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def __post_init__(self):
        """Validate language setting."""
        if self.language not in SUPPORTED_LANGUAGES:
            self.language = DEFAULT_LANGUAGE

    def resolve_category_folder(self, category: Category) -> str:
        """
        Resolve the folder name for a category, respecting language.

        Checks user-customized names first, then falls back to defaults
        with the configured language.

        Args:
            category: The Category instance.

        Returns:
            The folder display name (e.g., "🖼️ Images" or "🖼️ Imágenes").
        """
        # First check for user-customized names (these override language)
        if category.name in self.category_folder_names:
            return self.category_folder_names[category.name]
        # Use language-aware folder name
        return get_category_folder_name(category, lang=self.language)


# ─── Config Load / Save ───


def load_config(config_path: str | None = None) -> DesktopMaestroConfig:
    """
    Load configuration from a YAML or JSON file.

    If no path is provided, uses the default location
    (~/.config/desktopmaestro/config.yaml). If the file doesn't exist,
    a default configuration is created and saved automatically.

    Args:
        config_path: Path to the configuration file.

    Returns:
        DesktopMaestroConfig with loaded settings.

    Raises:
        ImportError: If the file is YAML but PyYAML is not installed.
        ValueError: If the file format is not supported.
    """
    path = config_path or DEFAULT_CONFIG_FILE
    path = os.path.expanduser(path)

    if not os.path.exists(path):
        config = DesktopMaestroConfig()
        save_config(config, path)
        return config

    with open(path, encoding="utf-8") as f:
        content = f.read()

    if path.endswith(".json"):
        data = json.loads(content)
    elif path.endswith((".yaml", ".yml")):
        if not HAS_YAML:
            raise ImportError(
                "PyYAML is required to read YAML config files. "
                "Install it: pip install pyyaml"
            )
        data = yaml.safe_load(content)
    else:
        raise ValueError(f"Unsupported config format: {path}")

    if data is None:
        return DesktopMaestroConfig()

    return DesktopMaestroConfig.from_dict(data)


def save_config(config: DesktopMaestroConfig, path: str | None = None) -> str:
    """
    Save configuration to a file.

    Creates the parent directory if it doesn't exist.

    Args:
        config: The configuration to save.
        path: Target file path (default: ~/.config/desktopmaestro/config.yaml).

    Returns:
        The path where the config was saved.
    """
    path = path or DEFAULT_CONFIG_FILE
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = config.to_dict()

    if path.endswith(".json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    else:
        if not HAS_YAML:
            # Fall back to JSON if PyYAML is not available
            path = path.rsplit(".", 1)[0] + ".json"
            return save_config(config, path)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

    return path


def create_default_config(config_path: str | None = None) -> str:
    """
    Create a commented default configuration file.

    Args:
        config_path: Target path (default: ~/.config/desktopmaestro/config.yaml).

    Returns:
        The path where the config was created.
    """
    path = config_path or DEFAULT_CONFIG_FILE
    path = os.path.expanduser(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    if path.endswith(".json"):
        config = DesktopMaestroConfig()
        return save_config(config, path)

    yaml_content = rf"""# ─── DesktopMaestro Configuration ───
# Smart desktop organizer for macOS
# Documentation: https://github.com/brunitobe/desktopmaestro#readme

# ─── Paths ───
desktop_path: "{DEFAULT_DESKTOP_PATH}"
config_dir: "{DEFAULT_CONFIG_DIR}"
log_dir: "{DEFAULT_LOG_DIR}"

# ─── Language ───
language: "en"                # Folder names: "en" (English) or "es" (Español)

# ─── Behavior ───
dry_run: false              # Simulate without moving files
verbose: true               # Show detailed information
auto_organize: false        # Organize automatically on startup
create_icon_macos: true     # Create custom folder icons

# ─── Filters ───
# Extensions to include (empty = all)
include_extensions: []
# Extensions to exclude
exclude_extensions: [".part", ".crdownload", ".tmp", ".temp"]
# Files to exclude by name
exclude_files:
  - .DS_Store
  - .localized
  - Desktop DB
  - Desktop DF
# Regex patterns to exclude
exclude_patterns:
  - '^\._.*'            # Apple Double files
  - '^\..*\.icloud$'    # iCloud placeholder files

# ─── Categories ───
# Disabled categories (no folders created for these)
disabled_categories:
  # - Temporary

# Custom folder names for categories
category_folder_names:
  # 🖼️ Images: "My Photos"
  # 📄 Documents: "Docs"

# ─── Organization ───
max_folder_depth: 1
sort_into_subfolders: false
date_based_folders: false
preserve_original_filenames: true
lowercase_extensions: true
remove_conflicting_chars: true

# ─── Safety ───
create_undo_snapshot: true
max_undo_snapshots: 50
min_file_age_minutes: 0     # Don't move files newer than this
skip_locked_files: true
skip_files_in_use: true

# ─── Scheduling ───
schedule_enabled: false
schedule_interval_hours: 6
# schedule_time: "03:00"    # Specific time (optional)

# ─── Notifications ───
show_notifications: true
notification_on_complete: true
notification_on_error: true

# ─── macOS ───
hide_dmg_volumes: true
skip_system_directories: true
respect_spotlight_tags: false
add_tags_to_folders: false    # Requires: brew install tag
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(yaml_content)

    return path
