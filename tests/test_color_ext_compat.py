"""Compatibility tests for the rich-color-ext (>= 3.0.0) integration."""

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


# Names that rich-color-ext >= 3.0 leaves to Rich's ANSI palette in Color.parse
# (e.g. "red" -> #800000). Gradient stops must still get the exact CSS value.
@pytest.mark.parametrize(
    "name, css_hex",
    [
        ("red", "#ff0000"),
        ("blue", "#0000ff"),
        ("yellow", "#ffff00"),
        ("cyan", "#00ffff"),
        ("magenta", "#ff00ff"),
        ("white", "#ffffff"),
        ("purple", "#800080"),
        ("violet", "#ee82ee"),
        ("orchid", "#da70d6"),
        ("tan", "#d2b48c"),
    ],
)
def test_parse_color_prefers_css_over_ansi(name, css_hex):
    assert parse_color(name).get_truecolor().hex == css_hex
    text = Text("hello", colors=[name, "#000"])
    assert text.colors[0].get_truecolor().hex == css_hex
    assert Gradient._to_color_triplets([name])[0].hex == css_hex


def test_parse_color_rejects_invalid():
    with pytest.raises(ColorParseError):
        parse_color("notacolor")
    with pytest.raises(ColorParseError):
        parse_color("#abcd")
    with pytest.raises(ColorParseError):
        parse_color("#ggg")


def test_gradient_and_text_survive_uninstall(uninstalled):
    with pytest.raises(ColorParseError):
        Color.parse("tomato")  # confirms the patch really is gone

    text = Text("hello", colors=["tomato", "#abc"])
    assert [c.get_truecolor().hex for c in text.colors] == ["#ff6347", "#aabbcc"]

    triplets = Gradient._to_color_triplets(["tomato", "#abc"])
    assert [t.hex for t in triplets] == ["#ff6347", "#aabbcc"]
