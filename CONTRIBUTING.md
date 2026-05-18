# 🤝 Contributing to DesktopMaestro

First off, thank you for considering contributing! Every contribution helps make DesktopMaestro better for everyone.

## 🧭 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)
- [Ideas for Contributions](#ideas-for-contributions)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/desktopmaestro.git`
3. Create a branch: `git checkout -b feature/your-feature-name`

## Development Setup

```bash
# Clone and enter directory
git clone https://github.com/your-username/desktopmaestro.git
cd desktopmaestro

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (optional but recommended)
pip install pre-commit
pre-commit install
```

## Coding Standards

### Style

- **Formatter**: [Black](https://github.com/psf/black) — default settings
- **Linter**: [Ruff](https://github.com/astral-sh/ruff) — configured in `pyproject.toml`
- **Line length**: 88 characters (Black default)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants

Run both before committing:

```bash
make lint    # ruff check
make format  # black
```

### Type Hints

All public functions **must** have type hints:

```python
def organize_desktop(
    config_path: Optional[str] = None,
    dry_run: bool = False,
    **kwargs: Any,
) -> OrganizeResult:
    ...
```

### Docstrings

Use Google-style docstrings:

```python
def load_config(config_path: Optional[str] = None) -> DesktopMaestroConfig:
    """
    Load configuration from a YAML or JSON file.

    Args:
        config_path: Path to the config file. If None, uses default location.

    Returns:
        DesktopMaestroConfig with the loaded configuration.

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError: If the format is not supported.
    """
```

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for HEIC images
fix: resolve crash on empty desktop
docs: improve README installation section
test: add tests for custom categories
refactor: simplify file scanning logic
```

## Testing

We use `pytest` with coverage tracking.

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test
pytest tests/ -v -k "test_smart_categorize"

# Run tests with print statements visible
pytest tests/ -v -s
```

### Writing Tests

- Place tests in `tests/test_organizer.py`
- Use `pytest` fixtures for reusable setup (see `temp_desktop` and `organizer` fixtures)
- Aim for > 90% coverage
- Test both success and error paths

```python
def test_smart_categorize_image():
    """Images should be categorized correctly."""
    cat = smart_categorize("vacation.jpg")
    assert cat.name == "Images"
```

## Pull Request Process

1. **Ensure tests pass**: `make test`
2. **Ensure linting passes**: `make lint`
3. **Update documentation** if you're changing behavior
4. **Add tests** for new features
5. **Keep PRs focused** — one feature/fix per PR
6. **Link related issues**: `Fixes #123`
7. **Describe your changes** in the PR description

### PR Checklist

Before submitting, make sure:

- [ ] Code follows Black + Ruff style
- [ ] Type hints are added
- [ ] Tests are added/updated
- [ ] Documentation is updated
- [ ] All tests pass
- [ ] No linting errors

## Project Structure

```
desktopmaestro/
├── organizer/              # Main package
│   ├── __init__.py         # Package metadata
│   ├── cli.py              # CLI entry point (argparse)
│   ├── core.py             # Organization engine
│   ├── categories.py       # File categorization system
│   ├── config.py           # Configuration management
│   └── utils.py            # Utilities (logging, notifications, etc.)
├── config/
│   └── default_config.yaml # Default configuration file
├── tests/
│   ├── __init__.py
│   └── test_organizer.py   # Test suite
├── installer/              # Distribution installer
├── maestro_assets/         # Brand assets
└── run.py                  # Alternative entry point
```

## Ideas for Contributions

| Idea | Difficulty | Area |
|---|---|---|
| ➕ More file categories | 🟢 Easy | `categories.py` |
| 🧪 Additional tests | 🟢 Easy | `tests/` |
| 🌐 Localization/i18n | 🟢 Easy | `cli.py` |
| 🪟 Windows support | 🔴 Hard | Core |
| 🐧 Linux support | 🔴 Hard | Core |
| 📊 Menu bar app (macOS) | 🟡 Medium | New |
| 🌐 Local web UI | 🟡 Medium | New |
| 🎨 Native macOS app (SwiftUI) | 🔴 Hard | New |
| ⚡ Conditional rules (by size/date) | 🟡 Medium | `core.py` |
| 🔍 Spotlight integration | 🟡 Medium | New |

---

**Thank you for contributing!** 🧹✨
