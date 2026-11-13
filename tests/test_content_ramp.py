"""Gradients that do not expand spread their ramp over the content, not the line."""

import pytest
from rich.console import Console
from rich.text import Text as RichText

from rich_gradient import Gradient, Panel

RED, BLUE = (255, 0, 0), (0, 0, 255)


def _glyph_colors(
    renderable: object, width: int = 80
) -> list[tuple[int, int, int] | None]:
    """Return the foreground RGB of every non-space cell, left to right.

    Unstyled cells are kept as ``None`` so a missing endpoint color fails the
    assertions instead of being skipped.
    """
    console = Console(width=width, force_terminal=True, color_system="truecolor")
    colors: list[tuple[int, int, int] | None] = []
    for segment in console.render(renderable, console.options):  # type: ignore[arg-type]
        color = segment.style.color if segment.style else None
        rgb = tuple(color.get_truecolor()) if color is not None else None
        colors.extend(rgb for ch in segment.text if not ch.isspace())  # type: ignore[misc]
    return colors


def _is_reddish(rgb: tuple[int, int, int] | None) -> bool:
    return rgb is not None and rgb[0] > 200 and rgb[2] < 80


def _is_bluish(rgb: tuple[int, int, int] | None) -> bool:
    return rgb is not None and rgb[2] > 200 and rgb[0] < 80


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
    """The border of a content-width panel shows both end colors on its corners."""
    panel = Panel("hello world", colors=["#ff0000", "#0000ff"], expand=False)
    console = Console(width=80, force_terminal=True, color_system="truecolor")
    first_line = next(iter(console.render_lines(panel, console.options)))
    cells = [
        (ch, segment.style.color if segment.style else None)
        for segment in first_line
        for ch in segment.text
        if not ch.isspace()
    ]
    assert cells[0][0] == "╭" and cells[-1][0] == "╮"
    first, last = cells[0][1], cells[-1][1]
    assert first is not None and last is not None
    assert _is_reddish(tuple(first.get_truecolor()))  # type: ignore[arg-type]
    assert _is_bluish(tuple(last.get_truecolor()))  # type: ignore[arg-type]


def test_centered_block_stays_centered() -> None:
    """Changing the ramp span does not move a centered block."""
    console = Console(width=40, record=True, force_terminal=True, color_system="truecolor")
    console.print(Gradient(RichText("abcd"), expand=False, justify="center"))
    line = console.export_text().splitlines()[0]
    assert line.index("abcd") == 18


def test_expanding_gradient_is_unchanged() -> None:
    """With ``expand=True`` the ramp spans the whole 80-cell line.

    "hello world" covers only the first 11 cells, so it moves from red a short
    way toward blue: each glyph is bluer than the last but none reaches blue.
    """
    colors = _glyph_colors(
        Gradient(RichText("hello world"), colors=["#ff0000", "#0000ff"], expand=True)
    )
    assert all(c is not None for c in colors)
    blues = [c[2] for c in colors if c is not None]
    assert _is_reddish(colors[0])
    assert blues == sorted(blues) and blues[-1] > blues[0]
    assert not _is_bluish(colors[-1])
    assert blues[-1] < 128


def test_gradient_accepts_rich_cast() -> None:
    """Objects that only implement ``__rich__`` are valid gradient content."""

    class Cast:
        def __rich__(self) -> RichText:
            return RichText("cast")

    console = Console(width=20, record=True)
    console.print(Gradient(Cast()))
    assert "cast" in console.export_text()
