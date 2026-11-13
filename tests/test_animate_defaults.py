"""Tests for the ``animate`` argument's defaults, pass-through, and config kill switch."""

from __future__ import annotations

import dataclasses
import importlib
from collections.abc import Callable
from typing import Any

import pytest
from rich.console import Console

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.animated_markdown import AnimatedMarkdown
from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.animated_rule import AnimatedRule
from rich_gradient.animated_text import AnimatedText
from rich_gradient.columns import Columns
from rich_gradient.gradient import Gradient
from rich_gradient.json import JSON
from rich_gradient.markdown import Markdown
from rich_gradient.panel import Panel
from rich_gradient.pretty import Pretty
from rich_gradient.rule import Rule
from rich_gradient.syntax import Syntax
from rich_gradient.table import Table
from rich_gradient.tree import Tree

# ``import rich_gradient.config`` would bind the package attribute, which the
# package rebinds to the config instance, so fetch the module by name.
config_module = importlib.import_module("rich_gradient.config")

StaticFactory = Callable[..., Gradient]
AnimatedFactory = Callable[..., AnimatedGradient]

STATIC_FACTORIES: dict[str, StaticFactory] = {
    "Gradient": lambda **kw: Gradient("text", **kw),
    "Columns": lambda **kw: Columns(["a", "b"], **kw),
    "JSON": lambda **kw: JSON('{"a": 1}', **kw),
    "Markdown": lambda **kw: Markdown("# Title", **kw),
    "Panel": lambda **kw: Panel("text", **kw),
    "Pretty": lambda **kw: Pretty({"a": 1}, **kw),
    "Rule": lambda **kw: Rule("title", **kw),
    "Syntax": lambda **kw: Syntax("x = 1", "python", **kw),
    "Table": lambda **kw: Table("col", **kw),
    "Tree": lambda **kw: Tree("root", **kw),
}

ANIMATED_FACTORIES: dict[str, AnimatedFactory] = {
    "AnimatedGradient": lambda **kw: AnimatedGradient("text", console=Console(), **kw),
    "AnimatedMarkdown": lambda **kw: AnimatedMarkdown("# Title", console=Console(), **kw),
    "AnimatedPanel": lambda **kw: AnimatedPanel("text", console=Console(), **kw),
    "AnimatedRule": lambda **kw: AnimatedRule("title", console=Console(), **kw),
    "AnimatedText": lambda **kw: AnimatedText("text", console=Console(), **kw),
}


def _set_animation_enabled(monkeypatch: pytest.MonkeyPatch, enabled: bool) -> None:
    """Swap in a config with ``animate`` set to ``enabled`` for this test.

    Args:
        monkeypatch: The pytest monkeypatch fixture.
        enabled: Whether the global config allows animation.
    """
    patched = dataclasses.replace(config_module.config, animate=enabled)
    monkeypatch.setattr(config_module, "config", patched)


@pytest.mark.parametrize("name", STATIC_FACTORIES)
def test_static_classes_default_to_not_animating(name: str) -> None:
    """Every Gradient-based static class defaults to ``animate=False``."""
    assert STATIC_FACTORIES[name]().animate is False


@pytest.mark.parametrize("name", STATIC_FACTORIES)
def test_static_classes_pass_animate_through(name: str) -> None:
    """``animate=True`` reaches the Gradient base, which then skips the highlight cache."""
    renderable = STATIC_FACTORIES[name](animate=True)
    assert renderable.animate is True


@pytest.mark.parametrize("name", ANIMATED_FACTORIES)
def test_animated_classes_default_to_animating(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """Animated classes animate by default when the config allows it."""
    _set_animation_enabled(monkeypatch, True)
    assert ANIMATED_FACTORIES[name]().animate is True


@pytest.mark.parametrize("name", ANIMATED_FACTORIES)
def test_config_kill_switch_overrides_explicit_true(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """With animation disabled in the config, even ``animate=True`` stays static."""
    _set_animation_enabled(monkeypatch, False)
    assert ANIMATED_FACTORIES[name]().animate is False
    assert ANIMATED_FACTORIES[name](animate=True).animate is False


@pytest.mark.parametrize("name", ANIMATED_FACTORIES)
def test_animated_classes_honor_explicit_false(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """``animate=False`` turns animation off even when the config allows it."""
    _set_animation_enabled(monkeypatch, True)
    assert ANIMATED_FACTORIES[name](animate=False).animate is False


def test_animate_none_is_treated_as_true(monkeypatch: pytest.MonkeyPatch) -> None:
    """``animate=None`` (the pre-0.4.4 default) still means "animate if allowed"."""
    _set_animation_enabled(monkeypatch, True)
    assert AnimatedGradient("text", console=Console(), animate=None).animate is True
    _set_animation_enabled(monkeypatch, False)
    assert AnimatedGradient("text", console=Console(), animate=None).animate is False


def test_kill_switch_is_read_at_call_time(monkeypatch: pytest.MonkeyPatch) -> None:
    """A config change after import is honored without reloading the module."""
    _set_animation_enabled(monkeypatch, False)
    assert AnimatedGradient("text", console=Console()).animate is False
    _set_animation_enabled(monkeypatch, True)
    assert AnimatedGradient("text", console=Console()).animate is True


def test_gradient_animated_alias_is_deprecated() -> None:
    """``Gradient(animated=...)`` still works but warns, and ``.animated`` mirrors ``.animate``."""
    with pytest.warns(DeprecationWarning, match="animate"):
        gradient: Any = Gradient("text", animated=True)
    assert gradient.animate is True
    assert gradient.animated is True
