"""Tests for ProgressBar's per-state gradients and the GradientBarColumn."""

from __future__ import annotations

import io

import pytest
from rich.color import Color
from rich.console import Console
from rich.progress import Progress, TextColumn
from rich.progress_bar import ProgressBar as RichProgressBar
from rich.segment import Segment
from rich.style import Style

from rich_gradient import GradientBarColumn, ProgressBar

RED = ["#ff0000", "#ff0000"]
GREEN = ["#00ff00", "#00ff00"]
BLUE_TO_YELLOW = ["#0000ff", "#ffff00"]


def _console(width: int = 40, color_system: str | None = "truecolor") -> Console:
    """Build a quiet console with a fixed width and color system.

    Args:
        width: Console width in cells. Defaults to 40.
        color_system: Rich color system name, or ``None`` for no color.
            Defaults to ``"truecolor"``.

    Returns:
        The console.
    """
    return Console(
        width=width, color_system=color_system, file=io.StringIO(), force_terminal=True  # type: ignore[arg-type]
    )


def _cells(renderable: object, console: Console | None = None) -> list[tuple[str, Style]]:
    """Render to one ``(char, style)`` pair per cell, dropping newlines.

    Args:
        renderable: What to render.
        console: Console to render with. Defaults to ``_console()``.

    Returns:
        The rendered cells.
    """
    console = console or _console()
    return [
        (ch, seg.style or Style())
        for seg in console.render(renderable)
        if isinstance(seg, Segment) and seg.text != "\n"
        for ch in seg.text
    ]


def _hexes(cells: list[tuple[str, Style]]) -> set[str]:
    """Collect the distinct foreground colors of the cells as hex strings.

    Args:
        cells: Rendered ``(char, style)`` pairs.

    Returns:
        The hex colors present.
    """
    return {s.color.get_truecolor().hex for _, s in cells if s.color is not None}


def test_in_progress_uses_colors() -> None:
    """A running bar paints its filled cells with ``colors``."""
    cells = _cells(ProgressBar(total=10, completed=5, width=10, colors=RED, finished_colors=GREEN))
    assert _hexes(cells[:5]) == {"#ff0000"}


def test_finished_uses_finished_colors() -> None:
    """A complete bar switches to ``finished_colors``."""
    cells = _cells(ProgressBar(total=10, completed=10, width=10, colors=RED, finished_colors=GREEN))
    assert _hexes(cells) == {"#00ff00"}


def test_finished_falls_back_to_colors() -> None:
    """Without ``finished_colors`` a complete bar keeps ``colors``."""
    cells = _cells(ProgressBar(total=10, completed=10, width=10, colors=RED))
    assert _hexes(cells) == {"#ff0000"}


def test_pulse_uses_pulse_colors_and_keeps_rich_characters() -> None:
    """The pulse keeps Rich's wave characters but takes its color from ``pulse_colors``."""
    ours = _cells(
        ProgressBar(total=None, width=20, animation_time=0.0, colors=RED, pulse_colors=BLUE_TO_YELLOW)
    )
    rich = _cells(RichProgressBar(total=None, width=20, animation_time=0.0))
    assert [c for c, _ in ours] == [c for c, _ in rich]
    assert len(_hexes(ours)) > 10
    assert "#ff0000" not in _hexes(ours)  # ``colors`` is not used for the pulse


def test_pulse_brightest_cell_is_the_gradient_color() -> None:
    """Where the wave peaks, the cell is exactly the gradient color at that position."""
    # With animation_time=0 the wave peaks halfway through each pulse period.
    from rich.progress_bar import PULSE_SIZE

    cells = _cells(ProgressBar(total=None, width=PULSE_SIZE, animation_time=0.0, pulse_colors=RED))
    assert cells[PULSE_SIZE // 2][1].color == Color.from_rgb(255, 0, 0)


def test_pulse_flag_pulses_even_with_total() -> None:
    """``pulse=True`` draws the gradient pulse even when a total is set."""
    cells = _cells(ProgressBar(total=10, completed=5, width=20, pulse=True, animation_time=0.0, pulse_colors=GREEN))
    assert len(_hexes(cells)) > 5  # a fading wave, not a two-tone bar


def test_pulse_moves_with_animation_time() -> None:
    """Advancing ``animation_time`` shifts the wave."""
    first = _cells(ProgressBar(total=None, width=20, animation_time=0.0, pulse_colors=BLUE_TO_YELLOW))
    later = _cells(ProgressBar(total=None, width=20, animation_time=0.5, pulse_colors=BLUE_TO_YELLOW))
    assert first != later


def test_pulse_without_color_blending_matches_rich() -> None:
    """On terminals that can't blend colors, the pulse is Rich's own."""
    console = _console(color_system=None)
    ours = _cells(ProgressBar(total=None, width=10, animation_time=0.0, pulse_colors=RED), console)
    rich = _cells(RichProgressBar(total=None, width=10, animation_time=0.0), console)
    assert ours == rich


def test_auto_palette_is_stable_across_renders() -> None:
    """Without ``colors`` the palette is picked once, so frames don't flicker."""
    bar = ProgressBar(total=10, completed=6, width=20)
    assert _cells(bar) == _cells(bar)


def test_colors_set_after_construction_are_used() -> None:
    """Assigning ``colors`` later takes effect on the next render."""
    bar = ProgressBar(total=10, completed=10, width=10)
    bar.colors = GREEN
    assert _hexes(_cells(bar)) == {"#00ff00"}


def test_rainbow_ignores_colors_but_not_finished_colors() -> None:
    """``rainbow`` overrides ``colors``; per-state colors still apply."""
    running = _cells(ProgressBar(total=10, completed=9, width=20, rainbow=True, colors=RED))
    assert len(_hexes(running)) > 3
    done = _cells(ProgressBar(total=10, completed=10, width=10, rainbow=True, finished_colors=GREEN))
    assert _hexes(done) == {"#00ff00"}


def test_invalid_hues_raises() -> None:
    """``hues`` below 2 is rejected at construction."""
    with pytest.raises(ValueError):
        ProgressBar(hues=1)


def test_gradient_bar_column_renders_each_state() -> None:
    """The column draws running, finished, and not-started tasks with their gradients."""
    console = _console(width=60)
    column = GradientBarColumn(bar_width=20, colors=RED, finished_colors=GREEN, pulse_colors=BLUE_TO_YELLOW)
    progress = Progress(TextColumn("{task.description}"), column, console=console, auto_refresh=False)
    running = progress.add_task("run", total=10, completed=5)
    done = progress.add_task("done", total=10, completed=10)
    waiting = progress.add_task("wait", total=None, start=False)
    tasks = {task.id: task for task in progress.tasks}

    assert _hexes(_cells(column.render(tasks[running]), console)[:10]) == {"#ff0000"}
    assert _hexes(_cells(column.render(tasks[done]), console)) == {"#00ff00"}
    pulse_bar = column.render(tasks[waiting])
    assert pulse_bar.pulse is True
    assert len(_hexes(_cells(pulse_bar, console))) > 5


def test_gradient_bar_column_palette_is_stable() -> None:
    """Auto colors are resolved once per column, so every refresh matches."""
    console = _console(width=60)
    column = GradientBarColumn(bar_width=20)
    progress = Progress(column, console=console, auto_refresh=False)
    task_id = progress.add_task("x", total=10, completed=4)
    task = next(t for t in progress.tasks if t.id == task_id)
    assert _cells(column.render(task), console) == _cells(column.render(task), console)


def test_gradient_bar_column_in_live_progress_output() -> None:
    """A Progress display with the column renders without errors."""
    console = Console(width=60, file=io.StringIO(), record=True, color_system="truecolor")
    with Progress(GradientBarColumn(bar_width=10), console=console, auto_refresh=False) as progress:
        task = progress.add_task("x", total=4)
        progress.update(task, advance=2)
        progress.refresh()
    assert "━" in console.export_text()
