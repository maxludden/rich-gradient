"""Gradients that do not expand spread their ramp over the content, not the line."""

import pytest
from rich.console import Console
from rich.text import Text as RichText

from rich_gradient import Gradient, Panel

RED, BLUE = (255, 0, 0), (0, 0, 255)


def _glyph_colors(renderable: object, width: int = 80) -> list[tuple[int, int, int]]:
    """Return the foreground RGB of every non-space cell, left to right."""
    console = Console(width=width, force_terminal=True, color_system="truecolor")
    colors = []
    for segment in console.render(renderable, console.options):  # type: ignore[arg-type]
        if not segment.text.strip() or segment.style is None or segment.style.color is None:
            continue
        triplet = segment.style.color.get_truecolor()
        colors.extend([tuple(triplet)] * len(segment.text.strip()))
    return colors


def _is_reddish(rgb: tuple[int, int, int]) -> bool:
    return rgb[0] > 200 and rgb[2] < 80


def _is_bluish(rgb: tuple[int, int, int]) -> bool:
    return rgb[2] > 200 and rgb[0] < 80


@pytest.mark.parametrize("justify", ["left", "center", "right"])
def test_non_expanding_gradient_reaches_last_color(justify: str) -> None:
    """A short line runs from the first color to the last whatever its alignment."""
    gradient = Gradient(
        RichText("hello world"), colors=["#ff0000", "#0000ff"], expand=False, justify=justify  # type: ignore[arg-type]
    )
    colors = _glyph_colors(gradient)
    assert _is_reddish(colors[0])
    assert _is_bluish(colors[-1])


def test_non_expanding_panel_border_spans_full_ramp() -> None:
    """The border of a content-width panel shows both end colors."""
    panel = Panel("hello world", colors=["#ff0000", "#0000ff"], expand=False)
    console = Console(width=80, force_terminal=True, color_system="truecolor")
    first_line = next(iter(console.render_lines(panel, console.options)))
    border = [s for s in first_line if s.text.strip() and s.style and s.style.color]
    assert _is_reddish(tuple(border[0].style.color.get_truecolor()))  # type: ignore[union-attr]
    assert _is_bluish(tuple(border[-1].style.color.get_truecolor()))  # type: ignore[union-attr]


def test_centered_block_stays_centered() -> None:
    """Changing the ramp span does not move a centered block."""
    console = Console(width=40, record=True, force_terminal=True, color_system="truecolor")
    console.print(Gradient(RichText("abcd"), expand=False, justify="center"))
    line = console.export_text().splitlines()[0]
    assert line.index("abcd") == 18


def test_expanding_gradient_is_unchanged() -> None:
    """With ``expand=True`` the ramp still spans the whole line (short text stays red)."""
    gradient = Gradient(RichText("hello world"), colors=["#ff0000", "#0000ff"], expand=True)
    colors = _glyph_colors(gradient)
    assert not _is_bluish(colors[-1])


def test_gradient_accepts_rich_cast() -> None:
    """Objects that only implement ``__rich__`` are valid gradient content."""

    class Cast:
        def __rich__(self) -> RichText:
            return RichText("cast")

    console = Console(width=20, record=True)
    console.print(Gradient(Cast()))
    assert "cast" in console.export_text()
