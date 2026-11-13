"""Tests for the gradient ``inspect`` module."""

from __future__ import annotations

import io
from dataclasses import dataclass

import pytest
from rich import inspect as rich_inspect
from rich.console import Console
from rich.segment import Segment

import rich_gradient
from rich_gradient import Inspect, inspect
from rich_gradient.inspect import Inspect as ModuleInspect

FRAME = set("╭╮╰╯─│")


@dataclass
class Point:
    """A 2D point."""

    x: int = 1
    y: float = 2.5
    label: str = "origin"


def _console(width: int = 70) -> Console:
    """Build a quiet, recording truecolor console.

    Args:
        width: Console width in cells. Defaults to 70.

    Returns:
        The console.
    """
    return Console(width=width, color_system="truecolor", record=True, file=io.StringIO())


def _segments(renderable: object) -> list[Segment]:
    """Render to segments with visible text.

    Args:
        renderable: What to render.

    Returns:
        The rendered segments, excluding blank ones.
    """
    return [s for s in _console().render(renderable) if s.text.strip()]


def test_package_exports() -> None:
    """``Inspect`` and ``inspect`` are importable from the package and the module."""
    assert Inspect is ModuleInspect
    assert rich_gradient.inspect is inspect


def test_content_matches_rich_inspect() -> None:
    """The text is the same as ``rich.inspect``; only the colors differ."""
    ours, theirs = _console(), _console()
    ours.print(Inspect(Point(), colors=["#ff0000", "#0000ff"]))
    rich_inspect(Point(), console=theirs)
    ours_text, theirs_text = ours.export_text(), theirs.export_text()
    assert ours_text.strip()
    assert [line.rstrip() for line in ours_text.splitlines()] == [
        line.rstrip() for line in theirs_text.splitlines()
    ]


def test_frame_takes_the_gradient() -> None:
    """The outer frame varies in color along its length."""
    frame_colors = {
        s.style.color.get_truecolor().hex
        for s in _segments(Inspect(Point(), colors=["#ff0000", "#0000ff"]))
        if s.text in FRAME and s.style and s.style.color
    }
    assert len(frame_colors) > 5


def test_title_is_plain_and_gradient_colored() -> None:
    """The title has no repr highlighting; it takes the gradient in bold."""
    segs = _segments(Inspect(Point(), colors=["#ff0000", "#0000ff"]))
    title = [s for s in segs if s.style and s.style.bold and s.text in "<class'__main__.Point>tests_inspect"]
    assert title
    assert len({s.style.color.get_truecolor().hex for s in title if s.style.color}) > 3


def test_value_colors_are_kept_by_default() -> None:
    """Attribute names keep Rich's yellow, so the output stays readable."""
    yellow = [s.text for s in _segments(Inspect(Point())) if s.style and s.style.color and s.style.color.name == "yellow"]
    assert {"x", "y"} <= set("".join(yellow))


def test_keep_value_colors_false_recolors_everything() -> None:
    """With ``keep_value_colors=False`` no Rich colors remain."""
    segs = _segments(Inspect(Point(), colors=["#ff0000", "#0000ff"], keep_value_colors=False))
    assert not [s for s in segs if s.style and s.style.color and s.style.color.name == "yellow"]


def test_options_are_forwarded() -> None:
    """``methods``, ``private``, ``title`` and friends reach Rich's inspector."""
    console = _console()
    console.print(Inspect(Point(), title="Custom title", value=False, docs=False))
    text = console.export_text()
    assert "Custom title" in text
    assert "A 2D point." not in text
    assert "Point(x=1" not in text


def test_inspect_function_prints_to_console() -> None:
    """``inspect()`` prints to the given console."""
    console = _console()
    inspect([1, 2, 3], console=console, rainbow=True)
    assert "[1, 2, 3]" in console.export_text()


def test_inspecting_inspect_shows_full_help() -> None:
    """Like ``rich.inspect(rich.inspect)``, inspecting this function shows its help."""
    console = _console(width=100)
    inspect(inspect, console=console)
    assert "keep_value_colors" in console.export_text()


def test_invalid_hues_raises() -> None:
    """``hues`` below 2 is rejected."""
    with pytest.raises(ValueError):
        Inspect(Point(), hues=1)
