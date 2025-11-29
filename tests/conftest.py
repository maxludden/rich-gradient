"""Test configuration for rich-gradient."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the src/ directory is on sys.path so `import rich_gradient` works in tests.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.is_dir():
    sys.path.insert(0, str(SRC_PATH))

