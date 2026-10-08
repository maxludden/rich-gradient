"""Tests covering configuration discovery and integration."""

from __future__ import annotations

import importlib
import json
from collections.abc import Iterator
from pathlib import Path

import pytest

import rich_gradient as rg_pkg
import rich_gradient.animated_gradient as ag_module
from rich_gradient.config import RichGradientConfig

ENV_VARS = (
    "RICH_GRADIENT_HOME_DIR",
    "RICH_GRADIENT_ANIMATE",
    "RICH_GRADIENT_COLORS",
    "RICH_GRADIENT_EXE",
)


@pytest.fixture(autouse=True)
def clean_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Start every test without RICH_GRADIENT_* variables and restore config after."""
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    yield
    monkeypatch.undo()
    rg_pkg.reload_config()
    importlib.reload(ag_module)


def _write(tmp_path: Path, data: object) -> Path:
    path = tmp_path / "config.json"
    path.write_text(
        data if isinstance(data, str) else json.dumps(data), encoding="utf-8"
    )
    return path


def _reload_with_home(monkeypatch: pytest.MonkeyPatch, home: Path) -> None:
    monkeypatch.setenv("RICH_GRADIENT_HOME_DIR", str(home))
    rg_pkg.reload_config()
    importlib.reload(ag_module)


def test_config_json_override_and_integration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A JSON config reaches the package config and AnimatedGradient."""
    _write(tmp_path, {"animate": False, "colors": {"white": "#FFFFFF"}})
    _reload_with_home(monkeypatch, tmp_path)

    pkg_config = rg_pkg.config
    assert pkg_config.animation_enabled is False
    assert isinstance(pkg_config.spectrum_colors, list)
    assert pkg_config.home_dir == tmp_path
    assert ag_module.AnimatedGradient(renderables="Sample").animate is False


def test_defaults_without_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """With no file or env, the built-in defaults are used."""
    monkeypatch.setenv("RICH_GRADIENT_HOME_DIR", str(tmp_path))
    cfg = RichGradientConfig.load()
    assert cfg.animate is True
    assert cfg.colors == RichGradientConfig.DEFAULT_CONFIG["colors"]
    assert len(cfg.spectrum_colors) == 17


def test_file_colors_merge_with_defaults(tmp_path: Path) -> None:
    """Overriding one color keeps the rest of the default palette."""
    path = _write(tmp_path, {"colors": {"red": "#111111"}})
    cfg = RichGradientConfig.load(path)
    assert cfg.colors["red"] == "#111111"
    assert cfg.colors["tomato"] == RichGradientConfig.DEFAULT_CONFIG["colors"]["tomato"]
    assert len(cfg.colors) == 17


def test_env_overrides_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Environment variables win over the config file."""
    path = _write(tmp_path, {"animate": True, "colors": {"red": "#111111"}})
    monkeypatch.setenv("RICH_GRADIENT_ANIMATE", "off")
    monkeypatch.setenv("RICH_GRADIENT_COLORS", json.dumps({"red": "#222222"}))
    cfg = RichGradientConfig.load(path)
    assert cfg.animate is False
    assert cfg.colors["red"] == "#222222"


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1", True), ("true", True), ("YES", True), ("on", True),
     ("0", False), ("false", False), ("No", False), ("off", False)],
)
def test_animate_env_values(
    value: str, expected: bool, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Known truthy and falsy strings are understood, case-insensitively."""
    monkeypatch.setenv("RICH_GRADIENT_HOME_DIR", str(tmp_path))
    monkeypatch.setenv("RICH_GRADIENT_ANIMATE", value)
    assert RichGradientConfig.load().animate is expected


def test_unrecognised_animate_value_keeps_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A typo no longer silently disables animation."""
    monkeypatch.setenv("RICH_GRADIENT_HOME_DIR", str(tmp_path))
    monkeypatch.setenv("RICH_GRADIENT_ANIMATE", "maybe")
    assert RichGradientConfig.load().animate is True


def test_non_boolean_animate_in_file_keeps_default(tmp_path: Path) -> None:
    """A non-boolean ``animate`` in the file is ignored."""
    cfg = RichGradientConfig.load(_write(tmp_path, {"animate": 5}))
    assert cfg.animate is True


def test_invalid_colors_are_dropped(tmp_path: Path) -> None:
    """Bad entries are discarded; good ones in the same file still apply."""
    path = _write(
        tmp_path,
        {"colors": {"red": "notacolor", "teal": "#008080", "bad": 5, "ok": "tomato"}},
    )
    cfg = RichGradientConfig.load(path)
    assert cfg.colors["red"] == RichGradientConfig.DEFAULT_CONFIG["colors"]["red"]
    assert cfg.colors["teal"] == "#008080"
    assert cfg.colors["ok"] == "tomato"
    assert "bad" not in cfg.colors


def test_colors_must_be_an_object(tmp_path: Path) -> None:
    """A non-object ``colors`` value leaves the default palette alone."""
    cfg = RichGradientConfig.load(_write(tmp_path, {"colors": ["red"]}))
    assert cfg.colors == RichGradientConfig.DEFAULT_CONFIG["colors"]


def test_malformed_json_falls_back_to_defaults(tmp_path: Path) -> None:
    """A broken file does not raise."""
    cfg = RichGradientConfig.load(_write(tmp_path, "{not json"))
    assert cfg.animate is True
    assert cfg.colors == RichGradientConfig.DEFAULT_CONFIG["colors"]


def test_non_object_json_is_ignored(tmp_path: Path) -> None:
    """A JSON array at the top level is ignored."""
    cfg = RichGradientConfig.load(_write(tmp_path, "[1, 2]"))
    assert cfg.animate is True


def test_invalid_env_colors_json_is_ignored(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Unparseable RICH_GRADIENT_COLORS does not raise."""
    monkeypatch.setenv("RICH_GRADIENT_HOME_DIR", str(tmp_path))
    monkeypatch.setenv("RICH_GRADIENT_COLORS", "{nope")
    cfg = RichGradientConfig.load()
    assert cfg.colors == RichGradientConfig.DEFAULT_CONFIG["colors"]


def test_home_dir_expands_user(monkeypatch: pytest.MonkeyPatch) -> None:
    """``~`` in the home directory override is expanded."""
    monkeypatch.setenv("RICH_GRADIENT_HOME_DIR", "~/somewhere")
    assert RichGradientConfig.load().home_dir == Path("~/somewhere").expanduser()


def test_defaults_are_not_mutated_by_load(tmp_path: Path) -> None:
    """Loading with overrides never changes the class-level defaults."""
    before = json.dumps(RichGradientConfig.DEFAULT_CONFIG, sort_keys=True)
    RichGradientConfig.load(_write(tmp_path, {"colors": {"red": "#111111"}}))
    assert json.dumps(RichGradientConfig.DEFAULT_CONFIG, sort_keys=True) == before
