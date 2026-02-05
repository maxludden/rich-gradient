"""Tests covering configuration discovery and integration."""

from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import rich_gradient as rg_pkg
import rich_gradient.animated_gradient as ag_module


def _reload_with_home(temp_home: Path) -> None:
    # Set the runtime home dir env var used by RichGradientConfig.load
    os.environ["RICH_GRADIENT_HOME_DIR"] = str(temp_home)
    # Use the package helper to refresh cached configuration objects.
    rg_pkg.reload_config()
    # Refresh animated_gradient module so its config reference updates.
    importlib.reload(ag_module)


def test_config_json_override_and_integration() -> None:
    """Write a simple JSON config and ensure the package-level config and
    AnimatedGradient pick up the overridden animation_enabled value and
    spectrum colors.
    """
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        # Create a config.json in the provided home directory. The loader
        # expects a file named `config.json` at the configured home path.
        cfg = {
            "animate": False,
            "colors": {"white": "#FFFFFF", "black": "#000000"},
        }
        config_path = tmp_path / "config.json"
        config_path.write_text(json.dumps(cfg), encoding="utf-8")

        _reload_with_home(tmp_path)

        # The package exposes a top-level `config` instance with the runtime values
        pkg_config = getattr(rg_pkg, "config")
        assert pkg_config.animation_enabled is False
        assert isinstance(pkg_config.spectrum_colors, list)
        assert pkg_config.home_dir == tmp_path

        # AnimatedGradient should consult the package config when animate is None
        gradient = ag_module.AnimatedGradient(renderables="Sample")
        assert gradient.animate is False
