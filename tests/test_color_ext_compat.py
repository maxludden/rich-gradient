"""Compatibility tests for the rich-color-ext (>= 3.0.0) integration."""

import sys

import pytest
import rich_color_ext
from rich.color import Color, ColorParseError

from rich_gradient import Gradient, Text
from rich_gradient._color_ext import ensure_installed, get_css_map, parse_color


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


# Names that Rich itself defines are resolved by Rich first (ANSI palette), not by
# the CSS map, matching rich-color-ext >= 3.0 (e.g. "red" -> #800000, not #ff0000).
@pytest.mark.parametrize(
    "name, rich_hex",
    [
        ("red", "#800000"),
        ("blue", "#000080"),
        ("yellow", "#808000"),
        ("cyan", "#008080"),
        ("magenta", "#800080"),
        ("white", "#c0c0c0"),
        ("purple", "#af00ff"),
        ("violet", "#d787ff"),
        ("orchid", "#d75fd7"),
        ("tan", "#d7af87"),
    ],
)
def test_parse_color_is_rich_first(name, rich_hex):
    assert parse_color(name).get_truecolor().hex == rich_hex
    text = Text("hello", colors=[name, "#000"])
    assert text.colors[0].get_truecolor().hex == rich_hex
    assert Gradient._to_color_triplets([name])[0].hex == rich_hex


def test_parse_color_matches_color_parse_for_every_css_name():
    """parse_color agrees with the patched Color.parse, with or without the patch."""
    names = list(get_css_map())
    expected = {name: Color.parse(name) for name in names}
    for name in names:
        assert parse_color(name) == expected[name], name
    rich_color_ext.uninstall()
    try:
        for name in names:
            assert parse_color(name) == expected[name], name
    finally:
        rich_color_ext.install()


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
