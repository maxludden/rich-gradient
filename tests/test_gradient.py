"""
Test suite for Gradient class and color interpolation logic.
Covers color computation, style merging, rendering, and quit panel logic.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, TypeGuard

import pytest
from rich.color import Color, ColorParseError
from rich.color_triplet import ColorTriplet
from rich.console import Console
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style
from rich.text import Text as RichText

from rich_gradient.gradient import Gradient


def _is_segment(value: object) -> TypeGuard[Segment]:
    return isinstance(value, Segment)


def _segments_only(segments: Iterable[object]) -> list[Segment]:
    return [seg for seg in segments if _is_segment(seg)]


@pytest.mark.parametrize("rainbow", [True, False])
def test_gradient_color_computation(rainbow: bool) -> None:
    """Test that Gradient._color_at returns a valid hex color string for
    both rainbow and non-rainbow modes.
    """
    gradient = Gradient("Hello", rainbow=rainbow)
    color = gradient._color_at(5, 1, 10)
    assert color.startswith("#") and len(color) == 7


def test_gradient_styled_foreground() -> None:
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


def test_gradient_styled_background() -> None:
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


def test_gradient_single_bg_color_accepts_color_types() -> None:
    """Single bg color should accept Color and ColorTriplet inputs."""
    color = Color.parse("#0000ff")
    gradient_color = Gradient("Test", colors=["#f00", "#0f0"], bg_colors=[color])
    assert len(gradient_color.bg_colors) == gradient_color.hues
    assert all(bg == color.get_truecolor() for bg in gradient_color.bg_colors)

    triplet = ColorTriplet(0, 255, 255)
    gradient_triplet = Gradient("Test", colors=["#f00", "#0f0"], bg_colors=[triplet])
    assert len(gradient_triplet.bg_colors) == gradient_triplet.hues
    assert all(bg == triplet for bg in gradient_triplet.bg_colors)


def test_gradient_accepts_rgb_tuple_colors() -> None:
    """Gradient should accept RGB tuples like Text does."""
    gradient = Gradient("Tuple", colors=[(255, 0, 0), (0, 255, 0)])
    assert gradient.colors[:2] == [ColorTriplet(255, 0, 0), ColorTriplet(0, 255, 0)]


@pytest.mark.parametrize("color", [(256, 0, 0), (-1, 0, 0)])
def test_gradient_rejects_out_of_range_rgb_tuple(color: tuple[int, int, int]) -> None:
    """RGB tuple channels must stay inside truecolor bounds."""
    with pytest.raises(ColorParseError):
        Gradient("Tuple", colors=[color, (0, 0, 0)])


def test_gradient_render_static() -> None:
    """
    Test that static gradient rendering produces only Segment objects.
    """
    console = Console()
    gradient = Gradient(
        Panel("Static Gradient Test", title="Test"), colors=["#f00", "#0f0"]
    )
    segments = list(gradient.__rich_console__(console, console.options))
    assert all(isinstance(seg, Segment) for seg in segments)


def test_gradient_with_single_color() -> None:
    """
    Test that a single color input produces two identical stops for smooth gradient.
    """
    gradient = Gradient("Single Color", colors=["#f00"])
    assert len(gradient._active_stops) == 2
    assert all(isinstance(c, tuple) and len(c) == 3 for c in gradient._active_stops)


def test_gradient_color_interpolation_boundaries() -> None:
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


def test_gradient_style_position_reuses_cached_ramp() -> None:
    """Repeated style lookups for the same span should reuse one gradient ramp."""
    gradient = Gradient("Interp", colors=["#000000", "#ffffff"])

    first_style = gradient._get_style_at_position(0, 1, 10)
    first_ramp = gradient._gradient_ramp
    second_style = gradient._get_style_at_position(1, 1, 10)

    assert first_ramp is not None
    assert gradient._gradient_ramp is first_ramp
    assert first_style.color is not None
    assert second_style.color is not None


def test_gradient_ramp_invalidates_when_color_stops_change() -> None:
    """Updating color stops should force a new gradient ramp to be built."""
    gradient = Gradient("Interp", colors=["#000000", "#ffffff"])

    gradient._get_style_at_position(0, 1, 10)
    first_ramp = gradient._gradient_ramp

    gradient_any: Any = gradient
    gradient_any.colors = ["#ff0000", "#00ff00"]
    gradient._get_style_at_position(0, 1, 10)

    assert first_ramp is not None
    assert gradient._gradient_ramp is not first_ramp


def test_gradient_highlight_words_applies_style() -> None:
    """
    Test that highlight_words overlays styles after gradient rendering.
    """
    console = Console()
    gradient = Gradient("Hello World", colors=["#f00", "#0f0"])
    gradient.highlight_words(["World"], style="bold")
    segments = list(gradient.__rich_console__(console, console.options))
    segment_list = _segments_only(segments)
    characters: list[tuple[str, Style | None]] = []
    for seg in segment_list:
        for ch in seg.text:
            if ch == "\n":
                continue
            characters.append((ch, seg.style))
    plain = "".join(ch for ch, _ in characters)
    start = plain.find("World")
    assert start != -1, "Highlight target word not found in rendered output."
    world_chars = characters[start : start + 5]
    assert all(style is not None and style.bold for _, style in world_chars)


def test_gradient_highlight_words_case_insensitive_override() -> None:
    """
    Test that case-insensitive matching remains available when requested.
    """
    console = Console()
    gradient = Gradient("Hello World", colors=["#f00", "#0f0"])
    gradient.highlight_words(["world"], style="bold", case_sensitive=False)
    segments = list(gradient.__rich_console__(console, console.options))
    segment_list = _segments_only(segments)
    characters: list[tuple[str, Style | None]] = []
    for seg in segment_list:
        for ch in seg.text:
            if ch == "\n":
                continue
            characters.append((ch, seg.style))
    plain = "".join(ch for ch, _ in characters)
    start = plain.find("World")
    assert start != -1, "Highlight target word not found in rendered output."
    world_chars = characters[start : start + 5]
    assert all(style is not None and style.bold for _, style in world_chars)


def test_gradient_highlight_regex_applies_style() -> None:
    """
    Test that highlight_regex overlays styles using compiled regex patterns.
    """
    console = Console()
    gradient = Gradient("Numbers: 12345", colors=["#f00", "#0f0"])
    gradient.highlight_regex(r"\d+", Style(underline=True))
    segments = list(gradient.__rich_console__(console, console.options))
    segment_list = _segments_only(segments)
    digit_segments = [seg for seg in segment_list if seg.text and seg.text.isdigit()]
    assert digit_segments, "Expected to find digit segments for regex highlight."
    assert all(seg.style is not None and seg.style.underline for seg in digit_segments)


def test_gradient_init_highlight_words_mapping() -> None:
    """
    Test that highlight words supplied via __init__ mapping are applied.
    """
    console = Console()
    highlight_words: Any = {"Beta": {"style": "bold", "case_sensitive": True}}
    gradient = Gradient(
        "Alpha Beta",
        colors=["#f00", "#0f0"],
        highlight_words=highlight_words,
    )
    segments = list(gradient.__rich_console__(console, console.options))
    segment_list = _segments_only(segments)
    characters: list[tuple[str, Style | None]] = []
    for seg in segment_list:
        for ch in seg.text:
            if ch == "\n":
                continue
            characters.append((ch, seg.style))
    plain = "".join(ch for ch, _ in characters)
    start = plain.find("Beta")
    assert start != -1
    beta_chars = characters[start : start + 4]
    assert all(style is not None and style.bold for _, style in beta_chars)


def test_gradient_init_highlight_regex_sequence() -> None:
    """
    Test that highlight regex supplied via __init__ sequence is applied.
    """
    console = Console()
    highlight_regex: Any = [(r"\d+", Style(italic=True))]
    gradient = Gradient(
        "Value: 123",
        colors=["#f00", "#0f0"],
        highlight_regex=highlight_regex,
    )
    segments = list(gradient.__rich_console__(console, console.options))
    segment_list = _segments_only(segments)
    digit_segments = [seg for seg in segment_list if seg.text and seg.text.isdigit()]
    assert digit_segments
    assert all(seg.style is not None and seg.style.italic for seg in digit_segments)


def _first_line_from_segments(segments: Iterable[Segment]) -> str:
    """Helper to extract the first rendered line of text from segments."""
    line_parts: list[str] = []
    for segment in segments:
        if segment.text == "\n":
            break
        line_parts.append(segment.text)
    return "".join(line_parts)


def test_gradient_justify_left_no_leading_padding() -> None:
    """
    Test that left justification does not insert leading spaces.
    """
    console = Console(width=10)
    gradient = Gradient("Hi", colors=["#f00", "#0f0"], justify="left")
    segments = list(gradient.__rich_console__(console, console.options))
    segment_list = _segments_only(segments)
    first_line = _first_line_from_segments(segment_list)
    assert first_line.startswith("Hi")


def test_gradient_justify_center_centers_text() -> None:
    """
    Test that center justification inserts symmetric padding.
    """
    console = Console(width=10)
    gradient = Gradient("Hi", colors=["#f00", "#0f0"], justify="center")
    segments = list(gradient.__rich_console__(console, console.options))
    segment_list: list[Segment] = [seg for seg in segments if isinstance(seg, Segment)]
    first_line = _first_line_from_segments(segment_list)
    assert first_line.startswith(" " * 4)
    assert first_line.strip() == "Hi"


def _plain(gradient: Gradient) -> list[str]:
    """Return the plain text of each stored renderable."""
    return [getattr(r, "plain", "") for r in gradient.renderables]


def test_gradient_accepts_tuple_of_renderables() -> None:
    """A tuple is treated as several renderables."""
    gradient = Gradient((RichText("a"), RichText("b")), colors=["red", "blue"])
    assert _plain(gradient) == ["a", "b"]
    assert list(gradient.__rich_console__(Console(), Console().options))


def test_gradient_accepts_generator_of_renderables() -> None:
    """A generator is consumed once and stored as a stable list."""
    gradient = Gradient((RichText(ch) for ch in "ab"), colors=["red", "blue"])
    assert _plain(gradient) == ["a", "b"]
    assert _plain(gradient) == ["a", "b"]  # still there on a second read


def test_gradient_accepts_list_of_renderables() -> None:
    """Lists keep working."""
    gradient = Gradient([RichText("a"), RichText("b")], colors=["red", "blue"])
    assert _plain(gradient) == ["a", "b"]


def test_gradient_single_renderable_is_not_split() -> None:
    """A single renderable stays whole, even though rich Text is iterable."""
    gradient = Gradient(RichText("abc"), colors=["red", "blue"])
    assert _plain(gradient) == ["abc"]


def test_gradient_string_is_one_renderable() -> None:
    """A string is a single renderable, not a sequence of characters."""
    gradient = Gradient("abc", colors=["red", "blue"])
    assert _plain(gradient) == ["abc"]


def test_gradient_empty_tuple_has_no_renderables() -> None:
    """An empty tuple yields no renderables instead of raising."""
    gradient = Gradient((), colors=["red", "blue"])
    assert gradient.renderables == []


def test_gradient_renderables_setter_accepts_tuple() -> None:
    """The renderables setter normalizes tuples too."""
    gradient = Gradient("x", colors=["red", "blue"])
    gradient.renderables = (RichText("a"), "b")
    assert _plain(gradient) == ["a", "b"]


def _printed(renderable: object) -> str:
    """Return exactly what Console.print writes for ``renderable``."""
    import io

    console = Console(file=io.StringIO(), width=10, force_terminal=False)
    console.print(renderable)
    return console.file.getvalue()  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "build",
    [
        lambda: "",
        lambda: RichText(""),
        lambda: RichText("", end=""),
        lambda: RichText("", end="!\n"),
    ],
)
def test_empty_gradient_matches_rich(build) -> None:
    """An empty Gradient prints exactly what Rich prints for the same input."""
    source = build()
    assert _printed(Gradient(source, colors=["red", "blue"])) == _printed(source)


def test_empty_gradient_prints_a_newline() -> None:
    """``Gradient("")`` prints a blank line, like ``console.print("")``."""
    assert _printed(Gradient("", colors=["red", "blue"])) == "\n"


def test_gradient_without_renderables_prints_nothing() -> None:
    """No renderables at all still prints nothing, like an empty Rich Group."""
    assert _printed(Gradient((), colors=["red", "blue"])) == ""


def test_non_empty_gradient_is_unchanged() -> None:
    """Non-empty content still renders through the gradient path."""
    assert "hi" in _printed(Gradient("hi", colors=["red", "blue"]))


def test_multiple_empty_renderables_print_one_newline_each() -> None:
    """Two empty texts print two blank lines, like a Rich Group of empty Text."""
    from rich.console import Group

    expected = _printed(Group(RichText(""), RichText("")))
    assert _printed(Gradient(["", ""], colors=["red", "blue"])) == expected == "\n\n"
