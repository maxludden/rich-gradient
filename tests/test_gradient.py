"""
Test suite for Gradient class and color interpolation logic.
Covers color computation, style merging, rendering, and quit panel logic.
"""

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style

from rich_gradient.gradient import Gradient


@pytest.mark.parametrize("rainbow", [True, False])
def test_gradient_color_computation(rainbow):
    """
    Test that Gradient._color_at returns a valid hex color string for both rainbow and non-rainbow modes.
    """
    gradient = Gradient("Hello", rainbow=rainbow)
    color = gradient._color_at(5, 1, 10)
    assert color.startswith("#") and len(color) == 7


def test_gradient_styled_foreground():
    """
    Test that _styled correctly merges foreground color and preserves style attributes.
    """
    original = Style(bold=True)
    gradient = Gradient("Test", colors=["#f00", "#0f0"])
    color = "#00ff00"
    styled = gradient._styled(original, color)
    assert styled.bold
    assert styled.color is not None
    assert styled.color.get_truecolor().hex.lower() == color.lower()


def test_gradient_styled_background():
    """
    Test that _styled correctly merges background color and preserves style attributes.
    """
    original = Style(dim=True)
    gradient = Gradient("Test", colors=["#f00", "#0f0"], bg_colors=["#00f", "#0ff"])
    color = "#00ff00"
    styled = gradient._styled(original, color)
    assert styled.dim
    assert styled.bgcolor is not None
    assert styled.bgcolor.get_truecolor().hex.lower() == color.lower()


def test_gradient_render_static():
    """
    Test that static gradient rendering produces only Segment objects.
    """
    console = Console()
    gradient = Gradient(
        Panel("Static Gradient Test", title="Test"), colors=["#f00", "#0f0"]
    )
    segments = list(gradient.__rich_console__(console, console.options))
    assert all(isinstance(seg, Segment) for seg in segments)


def test_gradient_with_single_color():
    """
    Test that a single color input produces two identical stops for smooth gradient.
    """
    gradient = Gradient("Single Color", colors=["#f00"])
    assert len(gradient._active_stops) == 2
    assert all(isinstance(c, tuple) and len(c) == 3 for c in gradient._active_stops)


def test_gradient_color_interpolation_boundaries():
    """
    Test that color interpolation at boundaries returns correct RGB values.
    """
    gradient = Gradient("Interp", colors=["#000000", "#ffffff"])
    assert gradient._interpolated_color(
        0.0, gradient._active_stops, len(gradient._active_stops)
    ) == (
        0,
        0,
        0,
    )
    assert gradient._interpolated_color(
        1.0, gradient._active_stops, len(gradient._active_stops)
    ) == (
        255,
        255,
        255,
    )


def test_gradient_highlight_words_applies_style():
    """
    Test that highlight_words overlays styles after gradient rendering.
    """
    console = Console()
    gradient = Gradient("Hello World", colors=["#f00", "#0f0"])
    gradient.highlight_words(["world"], style="bold", case_sensitive=False)
    segments = list(gradient.__rich_console__(console, console.options))
    characters: list[tuple[str, Style | None]] = []
    for seg in segments:
        for ch in seg.text:
            if ch == "\n":
                continue
            characters.append((ch, seg.style))
    plain = "".join(ch for ch, _ in characters).lower()
    start = plain.find("world")
    assert start != -1, "Highlight target word not found in rendered output."
    world_chars = characters[start : start + 5]
    assert all(style is not None and style.bold for _, style in world_chars)


def test_gradient_highlight_regex_applies_style():
    """
    Test that highlight_regex overlays styles using compiled regex patterns.
    """
    console = Console()
    gradient = Gradient("Numbers: 12345", colors=["#f00", "#0f0"])
    gradient.highlight_regex(r"\d+", Style(underline=True))
    segments = list(gradient.__rich_console__(console, console.options))
    digit_segments = [seg for seg in segments if seg.text and seg.text.isdigit()]
    assert digit_segments, "Expected to find digit segments for regex highlight."
    assert all(seg.style is not None and seg.style.underline for seg in digit_segments)


def test_gradient_init_highlight_words_mapping():
    """
    Test that highlight words supplied via __init__ mapping are applied.
    """
    console = Console()
    gradient = Gradient(
        "Alpha Beta",
        colors=["#f00", "#0f0"],
        highlight_words={"Beta": {"style": "bold", "case_sensitive": True}},
    )
    segments = list(gradient.__rich_console__(console, console.options))
    characters: list[tuple[str, Style | None]] = []
    for seg in segments:
        for ch in seg.text:
            if ch == "\n":
                continue
            characters.append((ch, seg.style))
    plain = "".join(ch for ch, _ in characters)
    start = plain.find("Beta")
    assert start != -1
    beta_chars = characters[start : start + 4]
    assert all(style is not None and style.bold for _, style in beta_chars)


def test_gradient_init_highlight_regex_sequence():
    """
    Test that highlight regex supplied via __init__ sequence is applied.
    """
    console = Console()
    gradient = Gradient(
        "Value: 123",
        colors=["#f00", "#0f0"],
        highlight_regex=[(r"\d+", Style(italic=True))],
    )
    segments = list(gradient.__rich_console__(console, console.options))
    digit_segments = [seg for seg in segments if seg.text and seg.text.isdigit()]
    assert digit_segments
    assert all(seg.style is not None and seg.style.italic for seg in digit_segments)


def _first_line_from_segments(segments):
    """Helper to extract the first rendered line of text from segments."""
    line_parts: list[str] = []
    for segment in segments:
        if segment.text == "\n":
            break
        line_parts.append(segment.text)
    return "".join(line_parts)


def test_gradient_justify_left_no_leading_padding():
    """
    Test that left justification does not insert leading spaces.
    """
    console = Console(width=10)
    gradient = Gradient("Hi", colors=["#f00", "#0f0"], justify="left")
    segments = list(gradient.__rich_console__(console, console.options))
    first_line = _first_line_from_segments(segments)
    assert first_line.startswith("Hi")


def test_gradient_justify_center_centers_text():
    """
    Test that center justification inserts symmetric padding.
    """
    console = Console(width=10)
    gradient = Gradient("Hi", colors=["#f00", "#0f0"], justify="center")
    segments = list(gradient.__rich_console__(console, console.options))
    first_line = _first_line_from_segments(segments)
    assert first_line.startswith(" " * 4)
    assert first_line.strip() == "Hi"
