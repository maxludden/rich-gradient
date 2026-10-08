"""Compatibility tests for the rich-color-ext (>= 2.0.0) integration."""

import sys

import pytest
import rich_color_ext
from rich.color import Color, ColorParseError

from rich_gradient import Gradient, Text
from rich_gradient._color_ext import ensure_installed, parse_color


@pytest.fixture
def uninstalled():
    """Run a test with the Color.parse patch removed, restoring it afterwards."""
    rich_color_ext.uninstall()
    try:
        yield
    finally:
        rich_color_ext.install()


def test_import_does_not_replace_excepthook():
    import importlib

    import rich_gradient

    hook = sys.excepthook
    importlib.reload(rich_gradient._color_ext)
    assert sys.excepthook is hook


def test_ensure_installed_is_idempotent(uninstalled):
    assert not rich_color_ext.is_installed()
    ensure_installed()
    ensure_installed()
    assert rich_color_ext.is_installed()


@pytest.mark.parametrize(
    "value, expected",
    [
        ("tomato", "#ff6347"),
        ("  RebeccaPurple ", "#663399"),
        ("#abc", "#aabbcc"),
        ("#ABC", "#aabbcc"),
        ("#336699", "#336699"),
    ],
)
def test_parse_color_with_and_without_patch(value, expected, uninstalled):
    assert parse_color(value).get_truecolor().hex == expected
    ensure_installed()
    assert parse_color(value).get_truecolor().hex == expected


def test_parse_color_rejects_invalid():
    with pytest.raises(ColorParseError):
        parse_color("notacolor")
    with pytest.raises(ColorParseError):
        parse_color("#abcd")


def test_gradient_and_text_survive_uninstall(uninstalled):
    with pytest.raises(ColorParseError):
        Color.parse("tomato")  # confirms the patch really is gone

    text = Text("hello", colors=["tomato", "#abc"])
    assert [c.get_truecolor().hex for c in text.colors] == ["#ff6347", "#aabbcc"]

    triplets = Gradient._to_color_triplets(["tomato", "#abc"])
    assert [t.hex for t in triplets] == ["#ff6347", "#aabbcc"]
