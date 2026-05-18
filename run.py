#!/usr/bin/env python3
"""
🧹 DesktopMaestro — Direct entry point.

Usage:
    python run.py organize --dry-run
    python run.py stats
    python run.py --help
"""

from __future__ import annotations

import sys

from organizer.cli import main

if __name__ == "__main__":
    sys.exit(main())
