"""
Test suite for edge cases in Gradient and Text, including long text, unicode, empty input, no colors, background, quit panel, and invalid color inputs.
"""

import pytest
from rich.color import ColorParseError
from rich.console import Console
from rich.panel import Panel
from rich.segment import Segment
from rich_color_ext import install

from rich_gradient import Gradient, Text

install()  # Ensure rich_color_ext is installed for color support

console = Console()


def render_to_text(renderable):
    """
    Render a Rich renderable to plain text for assertion.
    """
    console.begin_capture()
    console.print(renderable)
    return console.end_capture()


@pytest.mark.parametrize("length", [1_000, 10_000])
def test_gradient_long_text(length):
    """
    Test that rendering a long text with Gradient outputs at least as many characters as input.
    """
    txt = "X" * length
    grad = Gradient(txt, colors=["#9f0", "#0f0", "#0f9", "#0ff"])
    out = render_to_text(grad)
    assert len(out) >= length  # ensure all characters output
    assert isinstance(out, str)


def test_unicode_input():
    """
    Test that Gradient correctly renders unicode and emoji characters.
    """
    s = "こんにちは世界"  # Japanese
    grad = Gradient(Text(s + "🌟"), colors=["#9f0", "#0f0", "#0f9", "#0ff"])
    out = render_to_text(grad)
    assert "こんにちは世界" in out and "🌟" in out


def test_gradient_empty_string():
    """
    Test that Gradient with empty string input produces no output but does not error.
    """
    grad = Gradient("", colors=["#f00", "#0f0"])
    out = render_to_text(grad)
    assert out.strip().replace('\n', '') == ""


def test_text_empty_string():
    """
    Test that Text with empty string input produces no output but does not error.
    """
    txt = Text("")
    out = render_to_text(txt)
    assert out == ""


def test_gradient_no_colors():
    """
    Test that Gradient with no colors falls back to default spectrum and produces output.
    """
    grad = Gradient("No colors fallback")
    out = render_to_text(grad)
    assert "No colors fallback" in out


def test_text_no_colors():
    """
    Test that Text with no colors falls back to default spectrum and produces output.
    """
    txt = Text("No colors fallback")
    out = render_to_text(txt)
    assert "No colors fallback" in out


def test_gradient_background_true():
    """
    Test that Gradient with background=True applies background color and produces output.
    """
    grad = Gradient("BG", colors=["#f00", "#0f0"], background=True)
    out = render_to_text(grad)
    assert "BG" in out


def test_gradient_show_quit_panel():
    """
    Test that Gradient with show_quit_panel=True includes quit panel text in output.
    """
    grad = Gradient("Quit", colors=["#f00", "#0f0"], show_quit_panel=True)
    out = render_to_text(grad)
    assert "Press [bold]Ctrl+C[/bold] to stop." in out


def test_gradient_hide_quit_panel():
    """
    Test that Gradient with show_quit_panel=False does not include quit panel text in output.
    """
    grad = Gradient("No Quit", colors=["#f00", "#0f0"], show_quit_panel=False)
    out = render_to_text(grad)
    assert "Press [bold]Ctrl+C[/bold] to stop." not in out


def test_gradient_animated_static():
    """
    Test that Gradient with animated=True can be constructed and produces output (static test).
    """
    grad = Gradient("Animated", colors=["#f00", "#0f0"], animated=True)
    out = render_to_text(grad)
    assert "Animated" in out


def test_gradient_panel_render():
    """
    Test that rendering a Panel with Gradient produces output containing the panel text.
    """
    grad = Gradient(
        Panel("Panel Content", title="Panel Title"), colors=["#f00", "#0f0"]
    )
    out = render_to_text(grad)
    assert "Panel Content" in out and "Panel Title" in out


def test_gradient_single_color():
    """
    Test that Gradient with a single color produces a smooth gradient (two stops).
    """
    grad = Gradient("Single", colors=["#f00"])
    assert len(grad._active_stops) == 2
    out = render_to_text(grad)
    assert "Single" in out


@pytest.mark.parametrize(
    "colors",
    [
        # Invalid hex codes
        ["#GGGGGG", "blue"],
        ["#12345", "red"],  # too short
        ["#1234567", "green"],  # too long
        ["#12G45F", "yellow"],  # invalid character
        # Named colors that don't exist
        ["notacolor", "blue"],
        ["bluish", "red"],
        ["reddish", "green"],
        # Invalid rgb/rgba strings
        ["rgb(300,0,0)", "blue"],  # out of range
        ["rgb(-1,0,0)", "blue"],  # negative value
        ["rgb(0,0)", "blue"],  # too few components
        ["rgb(0,0,0,0,0)", "blue"],  # too many components
        ["rgba(0,0,0,2)", "blue"],  # alpha out of range
        ["rgba(0,0,0,-1)", "blue"],  # negative alpha
        ["rgba(0,0,0)", "blue"],  # missing alpha
        # Completely invalid strings
        ["", "blue"],
        [None, "blue"],
        [123, "blue"],
        ["#FFF", None],
        ["#FFF", ""],
        ["#FFF", 123],
    ],
)
def test_invalid_color_raises_all_cases(colors):
    """
    Test that invalid color inputs to Text raise ColorParseError, TypeError, or ValueError.
    """
    text = "Testing invalid color input"
    with pytest.raises((ColorParseError, TypeError, ValueError)):
        console.begin_capture()
        console.print(Text(text, colors=colors))
        console.end_capture()
