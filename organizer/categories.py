"""
Intelligent file categorization system for macOS.

Defines categories, extensions, patterns, and classification rules
used by DesktopMaestro to organize files into themed folders.
Supports English and Spanish via language translations.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

# ─── Supported languages ───
SUPPORTED_LANGUAGES = ["en", "es"]
DEFAULT_LANGUAGE = "en"

# ─── Category name translations (English → Spanish) ───
CATEGORY_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        "Images": "Images",
        "Documents": "Documents",
        "Archives": "Archives",
        "Videos": "Videos",
        "Audio": "Audio",
        "Code": "Code",
        "Presentations": "Presentations",
        "Spreadsheets": "Spreadsheets",
        "PDFs": "PDFs",
        "Design": "Design",
        "Torrents": "Torrents",
        "Fonts": "Fonts",
        "Disks & ISOs": "Disks & ISOs",
        "Executables": "Executables",
        "Databases": "Databases",
        "Configuration": "Configuration",
        "Emails": "Emails",
        "Books": "Books",
        "Backups": "Backups",
        "Scripts": "Scripts",
        "Temporary": "Temporary",
        "Others": "Others",
        "macOS System": "macOS System",
    },
    "es": {
        "Images": "Imágenes",
        "Documents": "Documentos",
        "Archives": "Archivos",
        "Videos": "Videos",
        "Audio": "Audio",
        "Code": "Código",
        "Presentations": "Presentaciones",
        "Spreadsheets": "Hojas de Cálculo",
        "PDFs": "PDFs",
        "Design": "Diseño",
        "Torrents": "Torrents",
        "Fonts": "Fuentes",
        "Disks & ISOs": "Discos e ISOs",
        "Executables": "Ejecutables",
        "Databases": "Bases de Datos",
        "Configuration": "Configuración",
        "Emails": "Correos",
        "Books": "Libros",
        "Backups": "Respaldos",
        "Scripts": "Scripts",
        "Temporary": "Temporal",
        "Others": "Otros",
        "macOS System": "Sistema macOS",
    },
}

# Cache for translated names to avoid repeated lookups
_translation_cache: Dict[str, Dict[str, str]] = {"en": {}, "es": {}}


def translate_name(english_name: str, lang: str = "en") -> str:
    """Translate a category name from English to the target language.

    Args:
        english_name: The English category name.
        lang: Target language code ("en" or "es").

    Returns:
        Translated category name.
    """
    if lang not in CATEGORY_TRANSLATIONS:
        lang = "en"
    return CATEGORY_TRANSLATIONS[lang].get(english_name, english_name)


def translate_folder_name(english_name: str, icon: str, lang: str = "en") -> str:
    """Build a folder name with icon and translated name.

    Args:
        english_name: The English category name.
        icon: Emoji icon for the category.
        lang: Target language code.

    Returns:
        Folder name like "🖼️ Imágenes" or "🖼️ Images".
    """
    translated = translate_name(english_name, lang)
    return f"{icon} {translated}"


# ─── Icon map for all categories (macOS emoji-friendly) ───
CATEGORY_ICONS: Dict[str, str] = {
    "Images": "🖼️",
    "Documents": "📄",
    "Archives": "🗜️",
    "Videos": "🎬",
    "Audio": "🎵",
    "Code": "💻",
    "Presentations": "📊",
    "Spreadsheets": "📈",
    "PDFs": "📕",
    "Design": "🎨",
    "Torrents": "🧲",
    "Fonts": "🔤",
    "Disks & ISOs": "💿",
    "Executables": "⚡",
    "Databases": "🗄️",
    "Configuration": "⚙️",
    "Emails": "✉️",
    "Books": "📚",
    "Backups": "💾",
    "Scripts": "📜",
    "Temporary": "🗑️",
    "Others": "📦",
    "macOS System": "🍎",
}


@dataclass(unsafe_hash=True)
class Category:
    """
    Defines a file category with its matching rules.

    Each category has a name, icon, set of file extensions, regex patterns,
    and a priority level. Files are classified into the highest-priority
    matching category.

    Attributes:
        name: Human-readable category name (e.g., "Images").
        icon: Emoji icon displayed in folder names (e.g., "🖼️").
        extensions: Set of file extensions (e.g., {".jpg", ".png"}).
        patterns: List of regex patterns for filename matching.
        folder_name: Custom folder name override. Defaults to "{icon} {name}".
        priority: Higher priority = matched first (default: 0).
    """

    name: str
    icon: str
    extensions: Set[str] = field(default_factory=set, hash=False)
    patterns: List[str] = field(default_factory=list, hash=False)
    folder_name: Optional[str] = None
    """Custom folder name override. If None, computed dynamically from name + icon + language."""
    priority: int = 0
    language: str = "en"

    def get_localized_name(self, lang: Optional[str] = None) -> str:
        """Get the category name in the specified language.

        Args:
            lang: Language code. Defaults to the category's language setting.

        Returns:
            Translated category name.
        """
        return translate_name(self.name, lang or self.language)

    def get_localized_folder(self, lang: Optional[str] = None) -> str:
        """Get the folder name in the specified language.

        If a custom folder_name is set (user override), returns that.
        Otherwise computes dynamically: "{icon} {translated_name}".

        Args:
            lang: Language code. Defaults to the category's language setting.

        Returns:
            Folder name with icon and translated text.
        """
        if self.folder_name is not None:
            return self.folder_name
        target_lang = lang or self.language
        return translate_folder_name(self.name, self.icon, target_lang)

    def matches(self, filename: str, extension: str) -> bool:
        """
        Check whether a file belongs to this category.

        Matching is performed by:
        1. Extension check (case-insensitive)
        2. Regex pattern matching against the full filename

        Args:
            filename: The full filename (e.g., "photo.jpg").
            extension: The lowercase file extension (e.g., ".jpg").

        Returns:
            True if the file matches this category's rules.
        """
        # Check by extension (case-insensitive)
        if extension.lower() in self.extensions:
            return True
        # Check by regex pattern
        for pattern in self.patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        return False


# ─── Predefined categories ───

# macOS system files that must NEVER be touched
MACOS_SYSTEM_FILES: Set[str] = {
    ".DS_Store",
    ".localized",
    ".Spotlight-V100",
    ".Trashes",
    ".fseventsd",
    ".metadata_never_index",
    "Desktop DB",
    "Desktop DF",
    ".apdisk",
}

# macOS hidden files that are always ignored
MACOS_HIDDEN_FILES: Set[str] = {
    ".DS_Store",
    ".localized",
}

IMAGES = Category(
    name="Images",
    icon="🖼️",
    extensions={
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
        ".svg",
        ".webp",
        ".ico",
        ".heic",
        ".heif",
        ".raw",
        ".cr2",
        ".nef",
        ".arw",
        ".dng",
        ".psd",
        ".ai",
        ".eps",
        ".xcf",
        ".jfif",
        ".pjpeg",
        ".pjp",
        ".avif",
        ".jxl",
    },
    priority=10,
)

DOCUMENTS = Category(
    name="Documents",
    icon="📄",
    extensions={
        ".txt",
        ".md",
        ".markdown",
        ".rtf",
        ".odt",
        ".doc",
        ".docx",
        ".tex",
        ".log",
        ".pages",
        ".wpd",
        ".wps",
        ".csv",
    },
    priority=5,
)

PDFS = Category(
    name="PDFs",
    icon="📕",
    extensions={".pdf"},
    priority=15,  # Higher priority so PDFs go to PDFs, not Documents
)

SPREADSHEETS = Category(
    name="Spreadsheets",
    icon="📈",
    extensions={".xls", ".xlsx", ".xlsm", ".xlsb", ".ods", ".numbers", ".gsheet"},
    priority=8,
)

PRESENTATIONS = Category(
    name="Presentations",
    icon="📊",
    extensions={".ppt", ".pptx", ".pptm", ".ppsx", ".odp", ".key", ".gslides"},
    priority=8,
)

ARCHIVES = Category(
    name="Archives",
    icon="🗜️",
    extensions={
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".zst",
        ".tgz",
        ".tbz2",
        ".tzst",
        ".lz",
        ".lzma",
        ".z",
        ".arj",
        ".cab",
        ".lha",
        ".ace",
        ".dmg",
        ".iso",
        ".img",
        ".vcd",
        ".toast",
        ".pkg",
        ".war",
        ".ear",
        ".jar",
    },
    priority=10,
)

VIDEOS = Category(
    name="Videos",
    icon="🎬",
    extensions={
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wmv",
        ".flv",
        ".webm",
        ".m4v",
        ".mpg",
        ".mpeg",
        ".m2ts",
        ".ts",
        ".vob",
        ".3gp",
        ".3g2",
        ".ogv",
        ".rm",
        ".rmvb",
        ".swf",
        ".avchd",
        ".divx",
        ".xvid",
        ".h264",
        ".h265",
        ".hevc",
        ".srt",
        ".sub",
        ".idx",
        ".ass",  # subtitles
    },
    priority=10,
)

AUDIO = Category(
    name="Audio",
    icon="🎵",
    extensions={
        ".mp3",
        ".wav",
        ".flac",
        ".aac",
        ".ogg",
        ".wma",
        ".m4a",
        ".opus",
        ".aiff",
        ".alac",
        ".ac3",
        ".dts",
        ".mid",
        ".midi",
        ".pcm",
        ".wv",
        ".tta",
        ".ape",
        ".dsf",
        ".dff",
        ".au",
        ".snd",
    },
    priority=10,
)

CODE = Category(
    name="Code",
    icon="💻",
    extensions={
        ".py",
        ".js",
        ".ts",
        ".jsx",
        ".tsx",
        ".html",
        ".htm",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".java",
        ".kt",
        ".kts",
        ".swift",
        ".go",
        ".rs",
        ".rb",
        ".php",
        ".pl",
        ".pm",
        ".lua",
        ".r",
        ".sql",
        ".graphql",
        ".gql",
        ".dockerfile",
        ".makefile",
        ".cmake",
        ".env",
        ".gitignore",
        ".gitkeep",
        ".gitattributes",
        ".vue",
        ".svelte",
        ".astro",
        ".ejs",
        ".hbs",
        ".pug",
        ".ipynb",
        ".jl",
        ".scala",
        ".clj",
        ".cljs",
        ".ex",
        ".exs",
        ".erl",
        ".hs",
        ".ml",
        ".mli",
        ".fs",
        ".fsx",
        ".dart",
        ".coffee",
        ".litcoffee",
        ".mjs",
        ".cjs",
        ".wasm",
    },
    patterns=[
        r"^Makefile$",
        r"^Dockerfile$",
        r"^docker-compose\.",
        r"^\.env",
        r"^\.git",
        r"^requirements\.",
        r"^package\.json$",
        r"^tsconfig\.",
        r"^webpack\.",
        r"^vite\.config",
        r"^next\.config",
        r"^nuxt\.config",
        r"^tailwind\.config",
        r"^babel\.config",
        r"^\.babelrc",
        r"^\.eslint",
        r"^\.prettier",
        r"^Gemfile",
        r"^Podfile",
        r"^Cargo\.",
        r"^go\.mod$",
        r"^go\.sum$",
    ],
    priority=8,
)

DESIGN = Category(
    name="Design",
    icon="🎨",
    extensions={
        ".psd",
        ".ai",
        ".eps",
        ".sketch",
        ".fig",
        ".xd",
        ".afdesign",
        ".afphoto",
        ".afpub",
        ".indd",
        ".idml",
        ".indb",
        ".cdr",
        ".dwg",
        ".dxf",
        ".blend",
        ".fbx",
        ".obj",
        ".3ds",
        ".max",
        ".ma",
        ".mb",
        ".glb",
        ".gltf",
        ".usdz",
        ".stl",
        ".ae",
        ".aep",
        ".prproj",
        ".fcpxml",
        ".drp",
        ".lottie",
        ".tga",
    },
    priority=8,
)

TORRENTS = Category(
    name="Torrents",
    icon="🧲",
    extensions={".torrent", ".magnet"},
    priority=15,
)

FONTS = Category(
    name="Fonts",
    icon="🔤",
    extensions={
        ".ttf",
        ".otf",
        ".woff",
        ".woff2",
        ".eot",
        ".fnt",
        ".fon",
        ".pfa",
        ".pfb",
        ".gsf",
    },
    priority=12,
)

DISKS_ISOS = Category(
    name="Disks & ISOs",
    icon="💿",
    extensions={
        ".iso",
        ".dmg",
        ".img",
        ".vcd",
        ".toast",
        ".bin",
        ".cue",
        ".nrg",
        ".mdf",
        ".mds",
        ".ccd",
    },
    priority=10,
)

EXECUTABLES = Category(
    name="Executables",
    icon="⚡",
    extensions={
        ".app",
        ".exe",
        ".msi",
        ".bat",
        ".cmd",
        ".command",
        ".tool",
        ".workflow",
        ".apk",
        ".ipa",
        ".run",
        ".bin",
    },
    patterns=[r"^.*\.app$"],
    priority=10,
)

DATABASES = Category(
    name="Databases",
    icon="🗄️",
    extensions={
        ".db",
        ".sqlite",
        ".sqlite3",
        ".db3",
        ".mdb",
        ".accdb",
        ".fdb",
        ".bak",
        ".sql",
        ".dump",
        ".rdb",
        ".aof",
        ".mongodb",
    },
    priority=5,
)

CONFIG_FILES = Category(
    name="Configuration",
    icon="⚙️",
    extensions={
        ".plist",
        ".config",
        ".desktop",
        ".service",
        ".timer",
        ".profile",
        ".bash_profile",
        ".bashrc",
        ".zshrc",
        ".editorconfig",
        ".stylelintrc",
    },
    patterns=[
        r"^\.\w+rc$",
        r"^\.\w+_profile$",
    ],
    priority=5,
)

EMAILS = Category(
    name="Emails",
    icon="✉️",
    extensions={
        ".eml",
        ".msg",
        ".pst",
        ".ost",
        ".mbox",
    },
    priority=5,
)

BOOKS = Category(
    name="Books",
    icon="📚",
    extensions={
        ".epub",
        ".mobi",
        ".azw",
        ".azw3",
        ".fb2",
        ".djvu",
        ".djv",
        ".cbr",
        ".cbz",
        ".chm",
        ".ibooks",
        ".pdb",
    },
    priority=10,
)

SCRIPTS = Category(
    name="Scripts",
    icon="📜",
    extensions={
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".csh",
        ".tcsh",
        ".py",
        ".rb",
        ".pl",
        ".pm",
        ".lua",
        ".tcl",
        ".awk",
        ".sed",
        ".expect",
        ".applescript",
        ".scpt",
        ".scptd",
        ".automator",
        ".workflow",
        ".js",
        ".mjs",
    },
    patterns=[r"^.*\.command$"],
    priority=8,
)

TEMPORARY = Category(
    name="Temporary",
    icon="🗑️",
    extensions={
        ".tmp",
        ".temp",
        ".swp",
        ".swo",
        ".bak",
        ".backup",
        ".cache",
        ".log",
        ".log1",
        ".log2",
        ".part",
        ".crdownload",
        ".download",
        ".~lock.",
    },
    patterns=[
        r"^~\$",  # Office temporary files
        r"\.\d{3}$",  # Backup suffixes
        r"\.tmp\d*$",
    ],
    priority=0,
)

# ─── macOS system category (invisible, never touched) ───
MACOS_SYSTEM_CATEGORY = Category(
    name="macOS System",
    icon="🍎",
    extensions=set(),
    patterns=[
        r"^\.DS_Store$",
        r"^\.localized$",
        r"^\.Spotlight-V100$",
        r"^\.Trashes$",
    ],
    priority=999,  # Maximum priority so these are never moved
    folder_name=".System",
)

# ─── Category ordering (most specific → most general) ───
DEFAULT_CATEGORIES: List[Category] = [
    MACOS_SYSTEM_CATEGORY,  # System first (maximum priority)
    TEMPORARY,  # Trash
    TORRENTS,
    PDFS,  # Specific before Documents
    IMAGES,
    VIDEOS,
    AUDIO,
    ARCHIVES,
    DISKS_ISOS,
    EXECUTABLES,
    FONTS,
    BOOKS,
    SCRIPTS,
    CODE,
    DESIGN,
    SPREADSHEETS,
    PRESENTATIONS,
    DOCUMENTS,
    DATABASES,
    CONFIG_FILES,
    EMAILS,
]

# ─── "Others" category (catch-all) ───
OTHERS = Category(
    name="Others",
    icon="📦",
    extensions=set(),
    priority=-999,
)


def smart_categorize(
    filename: str,
    custom_categories: Optional[List[Category]] = None,
) -> Category:
    """
    Classify a file into the best-matching category.

    Uses a priority system to ensure specific categories (e.g., PDFs)
    take precedence over general ones (e.g., Documents).

    The matching order is:
    1. Custom categories (sorted by priority descending)
    2. Default categories (in predefined order)
    3. "Others" (catch-all)

    Args:
        filename: The file name (with or without extension).
        custom_categories: Optional list of user-defined categories.

    Returns:
        The Category that best describes the file.
    """
    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    # Handle hidden files without extensions (.bashrc, .zshrc, etc.)
    if not ext and filename.startswith("."):
        for cat in custom_categories or DEFAULT_CATEGORIES:
            if isinstance(cat, Category) and cat.matches(filename, ext):
                return cat

    # Check custom categories first (they have priority)
    if custom_categories:
        sorted_cats = sorted(
            custom_categories,
            key=lambda c: c.priority,
            reverse=True,
        )
        for cat in sorted_cats:
            if isinstance(cat, Category) and cat.matches(filename, ext):
                return cat

    # Check default categories in order
    for cat in DEFAULT_CATEGORIES:
        if isinstance(cat, Category) and cat.matches(filename, ext):
            return cat

    return OTHERS


def get_category_folder_name(category: Category, lang: Optional[str] = None) -> str:
    """
    Get the folder name for a category, respecting language.

    If no custom folder_name is set, dynamically computes
    "{icon} {translated_name}" based on the target language.

    Args:
        category: The Category instance.
        lang: Language code ("en" or "es"). Defaults to category.language.

    Returns:
        str: The folder display name in the specified language.
    """
    if category.folder_name is not None:
        return category.folder_name
    target_lang = lang or category.language
    return translate_folder_name(category.name, category.icon, target_lang)


def is_macos_system_file(filename: str) -> bool:
    """
    Check if a file is a macOS system file that should never be moved.

    Args:
        filename: The file name to check.

    Returns:
        True if the file is a macOS system/protected file.
    """
    return filename in MACOS_SYSTEM_FILES or filename in MACOS_HIDDEN_FILES


def is_directory_safe_to_process(dirpath: str) -> bool:
    """
    Check if a directory is safe to process (not a macOS system directory).

    Args:
        dirpath: The full directory path.

    Returns:
        True if the directory is safe to process.
    """
    basename = os.path.basename(dirpath)
    return basename not in MACOS_SYSTEM_FILES


def get_supported_languages() -> Dict[str, str]:
    """Get a dict of supported language codes to their display names.

    Returns:
        Dict like {"en": "English", "es": "Español"}.
    """
    return {
        "en": "English",
        "es": "Español",
    }


def build_extension_map(
    categories: Optional[List[Category]] = None,
) -> Dict[str, Category]:
    """
    Build a fast lookup map from file extension to Category.

    Args:
        categories: List of categories to index. Defaults to DEFAULT_CATEGORIES.

    Returns:
        Dict mapping lowercase extensions (e.g., ".jpg") to Category instances.
    """
    ext_map: Dict[str, Category] = {}
    for cat in categories or DEFAULT_CATEGORIES:
        for ext in cat.extensions:
            ext_map[ext.lower()] = cat
    return ext_map
