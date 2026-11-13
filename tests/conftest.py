"""Test configuration for rich-gradient."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the src/ directory is on sys.path so `import rich_gradient` works in tests.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if SRC_PATH.is_dir():
    sys.path.insert(0, str(SRC_PATH))


import dataclasses  # noqa: E402
import importlib  # noqa: E402

import pytest  # noqa: E402


@pytest.fixture
def animation_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the global config to allow animation for one test.

    The config's ``animate`` setting is a kill switch that wins over
    ``animate=True``, so tests that need live animation pin it on rather than
    depend on the caller's environment (e.g. ``RICH_GRADIENT_ANIMATE=0``).

    Args:
        monkeypatch: The pytest monkeypatch fixture.
    """
    config_module = importlib.import_module("rich_gradient.config")
    monkeypatch.setattr(
        config_module, "config", dataclasses.replace(config_module.config, animate=True)
    )
