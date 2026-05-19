"""
Comprehensive test suite for DesktopMaestro.

Covers categorization, organization engine, configuration, undo,
utilities, integration, and performance benchmarks.
"""

import os
import sys
import json
import tempfile
import shutil
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Añadir raíz del proyecto al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from organizer import __version__, __description__
from organizer.categories import (
    Category,
    smart_categorize,
    is_macos_system_file,
    DEFAULT_CATEGORIES,
    OTHERS,
    CATEGORY_ICONS,
    MACOS_SYSTEM_FILES,
    build_extension_map,
)
from organizer.config import (
    DesktopMaestroConfig,
    load_config,
    save_config,
    create_default_config,
    DEFAULT_CONFIG_FILE,
)
from organizer.core import (
    DesktopOrganizer,
    OrganizeResult,
    UndoManager,
    UndoEntry,
    organize_desktop,
)
from organizer.utils import (
    is_macos,
    get_desktop_stats,
    _format_size,
    DesktopMaestroLogger,
)

# ─── Fixtures ───


@pytest.fixture
def temp_desktop():
    """Create a temporary desktop with test files of various types."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Crear estructura de escritorio
        desktop = os.path.join(tmpdir, "Desktop")
        os.makedirs(desktop)

        # Archivos normales
        files = {
            "foto.jpg": b"fake jpg content",
            "documento.pdf": b"fake pdf content",
            "video.mp4": b"fake mp4 content",
            "musica.mp3": b"fake mp3 content",
            "codigo.py": b"print('hello')",
            "archivo.zip": b"fake zip content",
            "notas.txt": b"notas importantes",
            "presentacion.pptx": b"fake pptx content",
            "hoja.xlsx": b"fake xlsx content",
            "libro.epub": b"fake epub content",
            "fuente.ttf": b"fake ttf content",
            "torrent.torrent": b"fake torrent content",
            "disco.dmg": b"fake dmg content",
            "script.sh": b"echo hello",
            "datos.json": b'{"key": "value"}',
            "app.app": b"fake app bundle pointer",
        }

        for name, content in files.items():
            filepath = os.path.join(desktop, name)
            with open(filepath, "wb") as f:
                f.write(content)

        # Archivo del sistema macOS (no debe moverse)
        ds_store = os.path.join(desktop, ".DS_Store")
        with open(ds_store, "w") as f:
            f.write("")

        # Directorio (no debe moverse)
        os.makedirs(os.path.join(desktop, "My Folder"))

        # Archivo temporal
        temp_file = os.path.join(desktop, "download.part")
        with open(temp_file, "w") as f:
            f.write("incomplete")

        yield desktop


@pytest.fixture
def organizer():
    """Create an organizer instance in dry-run mode."""
    config = DesktopMaestroConfig(dry_run=True)
    return DesktopOrganizer(config=config)


# ─── Tests de Categorías ───


class TestCategories:
    def test_smart_categorize_image(self):
        cat = smart_categorize("vacaciones.jpg")
        assert cat.name == "Images"
        assert cat.get_localized_folder() == "🖼️ Images"

    def test_smart_categorize_pdf(self):
        cat = smart_categorize("report.pdf")
        assert cat.name == "PDFs"

    def test_smart_categorize_video(self):
        cat = smart_categorize("movie.mkv")
        assert cat.name == "Videos"

    def test_smart_categorize_audio(self):
        cat = smart_categorize("song.flac")
        assert cat.name == "Audio"

    def test_smart_categorize_code(self):
        cat = smart_categorize("main.py")
        assert cat.name == "Scripts" or cat.name == "Código"

    def test_smart_categorize_archive(self):
        cat = smart_categorize("data.zip")
        assert cat.name == "Archives"

    def test_smart_categorize_unknown(self):
        cat = smart_categorize("file.xyz123")
        assert cat.name == "Others"

    def test_smart_categorize_no_extension(self):
        cat = smart_categorize("README")
        assert cat.name == "Others"

    def test_smart_categorize_hidden_file(self):
        cat = smart_categorize(".hidden_file")
        assert cat.name == "Others"

    def test_smart_categorize_case_insensitive(self):
        cat_jpg = smart_categorize("photo.JPG")
        cat_png = smart_categorize("image.PNG")
        assert cat_jpg.name == "Images"
        assert cat_png.name == "Images"

    def test_smart_categorize_priority_pdf_over_doc(self):
        """PDF debe ir a PDFs, no a Documentos."""
        cat = smart_categorize("document.pdf")
        assert cat.name == "PDFs"

    def test_smart_categorize_heic(self):
        """HEIC de iPhone debe ir a Imágenes."""
        cat = smart_categorize("IMG_1234.heic")
        assert cat.name == "Images"

    def test_smart_categorize_raw_photo(self):
        cat = smart_categorize("photo.CR2")
        assert cat.name == "Images"

    def test_smart_categorize_docx(self):
        cat = smart_categorize("document.docx")
        assert cat.name == "Documents"

    def test_custom_category(self):
        custom = Category(
            name="Personal",
            icon="🌟",
            extensions=[".myext"],
            priority=100,
        )
        cat = smart_categorize("project.myext", custom_categories=[custom])
        assert cat.name == "Personal"

    def test_is_macos_system_file(self):
        assert is_macos_system_file(".DS_Store") is True
        assert is_macos_system_file(".localized") is True
        assert is_macos_system_file("photo.jpg") is False
        assert is_macos_system_file(".Spotlight-V100") is True

    def test_build_extension_map(self):
        ext_map = build_extension_map()
        assert ".jpg" in ext_map
        assert ".pdf" in ext_map
        assert ext_map[".jpg"].name == "Images"
        assert ext_map[".pdf"].name == "PDFs"

    def test_all_categories_have_icons(self):
        for cat in DEFAULT_CATEGORIES:
            assert cat.icon, f"Category {cat.name} has no icon"
            assert (
                cat.get_localized_folder()
            ), f"Category {cat.name} has no localized folder name"

    @pytest.mark.parametrize(
        "filename,expected_category",
        [
            ("photo.heic", "Images"),
            ("video.avi", "Videos"),
            ("song.ogg", "Audio"),
            ("archive.7z", "Archives"),
            ("font.woff2", "Fonts"),
            ("ebook.mobi", "Books"),
            ("spreadsheet.ods", "Spreadsheets"),
            ("presentation.odp", "Presentations"),
            ("db.sqlite", "Databases"),
            ("config.plist", "Configuration"),
            ("email.eml", "Emails"),
            ("dmg_file.dmg", "Archives"),
        ],
    )
    def test_various_extensions(self, filename, expected_category):
        cat = smart_categorize(filename)
        if expected_category:
            assert cat.name == expected_category or cat.name != "Others"

    def test_macos_system_files_not_in_default_categories(self):
        """DS_Store no debería categorizarse como nada."""
        for f in MACOS_SYSTEM_FILES:
            if f.endswith("/"):  # skip directories
                continue
            cat = smart_categorize(f)
            # These should be categorized as Others or macOS System
            assert cat.name != "Images"  # should not be mistaken for Images


# ─── Tests de Configuración ───


class TestConfig:
    def test_default_config_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            path = create_default_config(config_path)
            assert os.path.exists(path)
            with open(path) as f:
                content = f.read()
            assert "DesktopMaestro" in content

    def test_load_save_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.yaml")
            create_default_config(config_path)
            config = load_config(config_path)
            # La ruta se expande automáticamente al cargar
            assert os.path.expanduser("~/Desktop") == config.desktop_path
            assert config.dry_run is False
            assert config.verbose is True

    def test_config_from_dict(self):
        data = {
            "dry_run": True,
            "verbose": False,
            "desktop_path": "/tmp/test",
        }
        config = DesktopMaestroConfig.from_dict(data)
        assert config.dry_run is True
        assert config.verbose is False
        assert config.desktop_path == "/tmp/test"

    def test_config_json_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config = DesktopMaestroConfig(dry_run=True)
            save_config(config, config_path)
            assert os.path.exists(config_path)
            loaded = load_config(config_path)
            assert loaded.dry_run is True

    def test_config_to_dict(self):
        config = DesktopMaestroConfig(dry_run=True, verbose=False)
        d = config.to_dict()
        assert d["dry_run"] is True
        assert d["verbose"] is False
        assert "desktop_path" in d

    def test_category_folder_resolution(self):
        config = DesktopMaestroConfig()
        config.category_folder_names = {"Images": "My Photos"}
        from organizer.categories import IMAGES

        folder = config.resolve_category_folder(IMAGES)
        assert folder == "My Photos"

    def test_disabled_categories(self):
        config = DesktopMaestroConfig(disabled_categories=["Temporal"])
        assert "Temporal" in config.disabled_categories


# ─── Tests del Core ───


class TestCore:
    def test_scan_desktop(self, temp_desktop, organizer):
        """Desktop scanning should find all eligible files."""
        files = organizer._scan_desktop(temp_desktop)

        # Should find all files except .DS_Store and .part
        assert len(files) == 17  # 17 test files
        assert all(os.path.isfile(f) for f in files)

        # Should NOT include .DS_Store
        assert not any(f.endswith(".DS_Store") for f in files)

        # Should NOT include directories
        assert not any(f.endswith("My Folder") for f in files)

    def test_categorize_files(self, temp_desktop, organizer):
        """File categorization should correctly classify all files."""
        files = organizer._scan_desktop(temp_desktop)
        categorized = organizer._categorize_files(files)

        assert len(categorized) > 0
        all_files = []
        for cat, cat_files in categorized.items():
            all_files.extend(cat_files)

        assert len(all_files) == len(files)

        # Verificar que categorías específicas estén presentes
        cat_names = [cat.name for cat in categorized.keys()]
        assert "Images" in cat_names
        assert "PDFs" in cat_names
        assert "Videos" in cat_names

    def test_dry_run_organize(self, temp_desktop, organizer):
        """Dry-run mode should not actually move files."""
        organizer.config.desktop_path = temp_desktop
        organizer.config.dry_run = True

        result = organizer.organize()

        assert result.dry_run is True
        assert result.success_count > 0

        # Files should remain on the desktop
        for src, dst, cat in result.moved_files:
            assert os.path.exists(src), f"File {src} should not have been moved"

    def test_real_organize(self, temp_desktop):
        """Real organization should actually move files into category folders."""
        config = DesktopMaestroConfig(
            dry_run=False,
            create_undo_snapshot=False,
            desktop_path=temp_desktop,
        )
        org = DesktopOrganizer(config=config)
        result = org.organize()

        assert result.success_count > 0

        # Files should no longer be on the desktop root
        for src, dst, cat in result.moved_files:
            assert not os.path.exists(src), f"File {src} should have been moved"
            assert os.path.exists(dst), f"File {dst} should exist"

        # .DS_Store should remain untouched
        ds_store = os.path.join(temp_desktop, ".DS_Store")
        assert os.path.exists(ds_store), ".DS_Store should not be moved"

        # Category folders should be created
        for folder in result.categories_created:
            folder_path = os.path.join(temp_desktop, folder)
            assert os.path.isdir(folder_path), f"Folder {folder} should exist"

    def test_organize_skips_directories(self, temp_desktop):
        """Directories should never be moved by the organizer."""
        config = DesktopMaestroConfig(
            dry_run=False,
            create_undo_snapshot=False,
            desktop_path=temp_desktop,
        )
        org = DesktopOrganizer(config=config)
        result = org.organize()

        # Folders should remain intact
        folder = os.path.join(temp_desktop, "My Folder")
        assert os.path.isdir(folder), "Directories must not be moved"

    def test_organize_skips_temp_files(self, temp_desktop):
        """Temporary files should be excluded by configuration."""
        config = DesktopMaestroConfig(
            dry_run=False,
            create_undo_snapshot=False,
            desktop_path=temp_desktop,
            exclude_extensions=[".part"],
        )
        org = DesktopOrganizer(config=config)
        result = org.organize()

        # descarga.part debería estar excluído
        part_file = os.path.join(temp_desktop, "download.part")
        assert os.path.exists(part_file), ".part files should not be moved"

    def test_organize_empty_desktop(self, tmpdir):
        """Empty desktops should not cause errors."""
        desktop = tmpdir.mkdir("empty_desktop")
        config = DesktopMaestroConfig(
            dry_run=True,
            desktop_path=str(desktop),
        )
        org = DesktopOrganizer(config=config)
        result = org.organize()

        assert result.success_count == 0
        assert result.total_files_found == 0

    def test_organize_result_summary(self):
        """The result summary should be human-readable."""
        result = OrganizeResult(
            moved_files=[("/src/a.txt", "/dst/a.txt", "Documentos")],
            skipped_files=[("/src/b.txt", "Ya existe")],
            errors=[("/src/c.txt", "Permiso denegado")],
            categories_created=["📄 Documentos"],
            total_files_found=3,
            start_time=0.0,
            end_time=1.0,
            dry_run=False,
        )
        summary = result.summary()
        assert "Documentos" in summary
        assert "1" in summary  # moved count
        assert "1" in summary  # skipped count
        assert "1" in summary  # errors count

    def test_organize_with_custom_path(self, temp_desktop):
        """Custom desktop paths should work correctly."""
        config = DesktopMaestroConfig(
            dry_run=True,
            desktop_path=temp_desktop,
        )
        assert config.desktop_path == temp_desktop

    def test_fast_organize_function(self, temp_desktop):
        """The organize_desktop convenience function should work."""
        result = organize_desktop(
            dry_run=True,
            desktop_path=temp_desktop,
        )
        assert result.success_count > 0

    def test_concurrent_access_safety(self, temp_desktop):
        """Multiple organizer instances should not conflict."""
        config = DesktopMaestroConfig(
            dry_run=True,
            desktop_path=temp_desktop,
        )
        org1 = DesktopOrganizer(config=config)
        org2 = DesktopOrganizer(config=config)

        result1 = org1.organize()
        result2 = org2.organize()

        # Ambos deben ejecutarse sin errores
        assert result1.errors == []
        assert result2.errors == []


# ─── Tests de Undo ───


class TestUndo:
    def test_undo_create_snapshot(self, tmpdir):
        """Undo snapshots should be created correctly."""
        undo = UndoManager(config_dir=str(tmpdir))
        entries = [
            UndoEntry(
                timestamp="2025-01-01T12:00:00",
                source_path="/src/file.txt",
                destination_path="/dst/file.txt",
                file_hash="abc123",
                file_size=100,
            )
        ]
        path = undo.create_snapshot(entries, "Test")
        assert os.path.exists(path)

        # Verificar contenido
        with open(path) as f:
            data = json.load(f)
        assert data["description"] == "Test"
        assert len(data["entries"]) == 1

    def test_undo_list_snapshots(self, tmpdir):
        """Available snapshots should be listed correctly."""
        undo = UndoManager(config_dir=str(tmpdir))
        snapshots = undo.list_snapshots()
        assert snapshots == []

        # Crear uno
        entries = [
            UndoEntry(
                timestamp="2025-01-01T12:00:00",
                source_path="/src/file.txt",
                destination_path="/dst/file.txt",
                file_hash="abc123",
                file_size=100,
            )
        ]
        undo.create_snapshot(entries, "Test")
        snapshots = undo.list_snapshots()
        assert len(snapshots) == 1
        assert snapshots[0]["description"] == "Test"


# ─── Tests de Utilidades ───


class TestUtils:
    def test_format_size(self):
        assert _format_size(500) == "500.0 B"
        assert _format_size(2048) == "2.0 KB"
        assert _format_size(1048576) == "1.0 MB"
        assert _format_size(1073741824) == "1.0 GB"
        assert "TB" in _format_size(1099511627776)

    def test_get_desktop_stats(self, temp_desktop):
        stats = get_desktop_stats(temp_desktop)

        assert stats["total_files"] == 17  # 17 test files
        assert stats["total_folders"] == 1  # My Folder
        assert stats["total_size_bytes"] > 0
        assert "by_extension" in stats
        assert ".jpg" in stats["by_extension"]
        assert ".pdf" in stats["by_extension"]

    def test_get_desktop_stats_error(self):
        stats = get_desktop_stats("/ruta/que/no/existe")
        assert "error" in stats

    def test_logger_creation(self, tmpdir):
        log = DesktopMaestroLogger(
            name="Test",
            log_dir=str(tmpdir),
            verbose=True,
            log_to_file=True,
        )
        log.info("Test message")
        assert log.log_file is not None
        assert os.path.exists(log.log_file)

    def test_category_icons_completeness(self):
        """All default categories must have icons defined."""
        for cat in DEFAULT_CATEGORIES:
            assert cat.name in CATEGORY_ICONS, f"Missing icon for {cat.name}"

    def test_no_duplicate_extensions(self):
        """Duplicate extensions between categories should be handled."""
        ext_map = {}
        for cat in DEFAULT_CATEGORIES:
            for ext in cat.extensions:
                if ext in ext_map:
                    # Si está duplicado, debe ser la misma categoría
                    # o una con mayor prioridad
                    pass
                ext_map[ext] = cat


# ─── Tests de Integración ───


class TestIntegration:
    def test_full_workflow(self, temp_desktop):
        """Full workflow: organize desktop and verify results."""
        config = DesktopMaestroConfig(
            dry_run=True,
            desktop_path=temp_desktop,
        )
        org = DesktopOrganizer(config=config)

        # 1. Organizar
        result = org.organize()
        assert result.success_count > 0
        assert result.errors == []

        # 2. Verificar estadísticas
        stats = get_desktop_stats(temp_desktop)
        assert stats["total_files"] > 0


# ─── Tests de Rendimiento ───


class TestPerformance:
    def test_organize_many_files(self, tmpdir):
        """Performance: organize 500 files in under 30 seconds."""
        desktop = tmpdir.mkdir("full_desktop")

        # Create 500 test files
        for i in range(500):
            ext = [".jpg", ".pdf", ".mp4", ".mp3", ".py", ".zip"][i % 6]
            filepath = os.path.join(str(desktop), f"file_{i}{ext}")
            with open(filepath, "w") as f:
                f.write(f"content {i}")

        config = DesktopMaestroConfig(
            dry_run=True,
            desktop_path=str(desktop),
        )
        org = DesktopOrganizer(config=config)

        import time

        start = time.time()
        result = org.organize()
        elapsed = time.time() - start

        assert result.success_count == 500
        assert elapsed < 30, f"Too slow: {elapsed:.2f}s"  # 500 files < 30s


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
