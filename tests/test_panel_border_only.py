"""Tests for the ``border_only`` flag on Panel and AnimatedPanel."""

from __future__ import annotations

import io
from collections.abc import Callable
from typing import Any

import pytest
from rich.console import Console
from rich.panel import Panel as RichPanel
from rich.segment import Segment
from rich.style import Style

from rich_gradient import AnimatedPanel, Panel

BORDER_CHARS = set("╭╮╰╯─│")
COLORS = ["#ff0000", "#0000ff"]
CONTENT = "[bold cyan]Hello[/] world"

PanelFactory = Callable[..., Any]
FACTORIES: dict[str, PanelFactory] = {
    "Panel": lambda content, **kw: Panel(content, expand=False, **kw),
    "AnimatedPanel": lambda content, **kw: AnimatedPanel(
        content, expand=False, animate=False, console=Console(), **kw
    ),
}


def _segments(renderable: object) -> list[Segment]:
    """Render with a quiet truecolor console.

    Args:
        renderable: What to render.

    Returns:
        The rendered segments.
    """
    console = Console(width=40, color_system="truecolor", file=io.StringIO())
    return list(console.render(renderable))


def _content_cells(segments: list[Segment]) -> list[tuple[str, Style | None]]:
    """Return the ``(char, style)`` pairs of the panel's content letters.

    Args:
        segments: Rendered segments of a panel titled ``"T"``.

    Returns:
        One pair per letter of ``"Helloworld"``, in order.
    """
    cells = [
        (ch, seg.style)
        for seg in segments
        if seg.text != "\n"
        for ch in seg.text
    ]
    # Content letters are the alphabetic cells other than the title "T".
    return [(ch, style) for ch, style in cells if ch.isalpha() and ch != "T"]


def _border_colors(segments: list[Segment]) -> set[str]:
    """Collect the distinct colors used on border characters.

    Args:
        segments: Rendered segments.

    Returns:
        Hex colors of border cells.
    """
    return {
        seg.style.color.get_truecolor().hex
        for seg in segments
        if seg.text and set(seg.text) <= BORDER_CHARS and seg.style and seg.style.color
    }


@pytest.mark.parametrize("name", FACTORIES)
def test_border_takes_the_gradient(name: str) -> None:
    """With ``border_only`` the border is still painted with the gradient."""
    segs = _segments(FACTORIES[name](CONTENT, title="T", colors=COLORS, border_only=True))
    assert len(_border_colors(segs)) > 5


@pytest.mark.parametrize("name", FACTORIES)
def test_content_matches_plain_rich_panel(name: str) -> None:
    """Content cells are styled exactly as a plain ``rich.panel.Panel`` styles them."""
    ours = _content_cells(_segments(FACTORIES[name](CONTENT, title="T", colors=COLORS, border_only=True)))
    rich = _content_cells(_segments(RichPanel(CONTENT, title="T", expand=False)))
    assert [ch for ch, _ in ours] == list("Helloworld")
    assert [(ch, style or Style()) for ch, style in ours] == [(ch, style or Style()) for ch, style in rich]


@pytest.mark.parametrize("name", FACTORIES)
def test_without_border_only_content_takes_the_gradient(name: str) -> None:
    """The default still paints the content with the gradient."""
    cells = _content_cells(_segments(FACTORIES[name]("Hello world", title="T", colors=COLORS)))
    assert all(style is not None and style.color is not None for _, style in cells)


@pytest.mark.parametrize("name", FACTORIES)
def test_title_takes_the_gradient(name: str) -> None:
    """The title is drawn in the border style, so it takes the gradient too."""
    segs = _segments(FACTORIES[name]("x", title="T", colors=COLORS, border_only=True))
    title = [seg for seg in segs if seg.text == "T"]
    assert title and title[0].style is not None and title[0].style.color is not None
    assert title[0].style.color.get_truecolor().hex not in ("#ff0000", "#0000ff")  # mid-gradient


@pytest.mark.parametrize("name", FACTORIES)
def test_content_style_background_is_kept(name: str) -> None:
    """A panel ``style`` background stays on the content, even with ``bg_colors``."""
    segs = _segments(
        FACTORIES[name]("hi", style="on #333333", colors=COLORS, bg_colors=COLORS, border_only=True)
    )
    content = [seg for seg in segs if seg.text == "h" or seg.text.startswith("hi")]
    assert content and all(seg.style and seg.style.bgcolor and seg.style.bgcolor.get_truecolor().hex == "#333333" for seg in content)


@pytest.mark.parametrize("name", FACTORIES)
def test_border_marker_does_not_leak(name: str) -> None:
    """The internal border marker never reaches the rendered output."""
    segs = _segments(FACTORIES[name](CONTENT, title="T", subtitle="S", colors=COLORS, border_only=True))
    assert not any(seg.style and seg.style._meta for seg in segs)


@pytest.mark.parametrize("name", FACTORIES)
def test_border_only_can_be_toggled(name: str) -> None:
    """Setting ``border_only`` after construction takes effect on the next render."""
    panel = FACTORIES[name]("Hello world", title="T", colors=COLORS)
    assert panel.border_only is False
    panel.border_only = True
    cells = _content_cells(_segments(panel))
    assert all(style is None or style.color is None for _, style in cells)


def test_border_style_theme_name_still_works() -> None:
    """A theme style name as ``border_style`` resolves normally with ``border_only``."""
    # "repr.number" is a Rich theme style (bold cyan); the gradient replaces the color.
    segs = _segments(Panel("x", border_style="repr.number", colors=COLORS, border_only=True, expand=False))
    border = [seg for seg in segs if seg.text and set(seg.text) <= BORDER_CHARS]
    assert border and all(seg.style and seg.style.bold for seg in border)
    assert len(_border_colors(segs)) > 1
