"""Tests for the gradient JSON and ProgressBar wrappers."""

from __future__ import annotations

from rich.console import Console
from rich.segment import Segment

from rich_gradient.json import JSON
from rich_gradient.progress_bar import ProgressBar

COLORS = ["#ff0000", "#0000ff"]


def _console(width: int = 40) -> Console:
    return Console(width=width, force_terminal=True, color_system="truecolor")


def _segments(renderable: object, width: int = 40) -> list[Segment]:
    console = _console(width)
    return [s for s in console.render(renderable) if s.text != "\n"]


def test_json_renders_text_and_colors() -> None:
    console = _console(60)
    with console.capture() as cap:
        console.print(JSON('{"a": [1, 2]}', colors=COLORS))
    out = cap.get()
    assert "\x1b[38;2;" in out
    plain = Console(width=60, file=None, record=True, force_terminal=True)
    plain.print(JSON('{"a": [1, 2]}', colors=COLORS))
    assert '"a"' in plain.export_text()


def test_json_from_data_matches_string() -> None:
    a = JSON.from_data({"k": 1}, colors=COLORS)
    b = JSON('{"k": 1}', colors=COLORS)
    console = _console(30)
    with console.capture() as ca:
        console.print(a)
    with console.capture() as cb:
        console.print(b)
    assert ca.get() == cb.get()


def test_progress_bar_width_and_gradient_only_on_filled() -> None:
    segs = _segments(ProgressBar(total=100, completed=50, width=20, colors=COLORS))
    chars = [(c, s.style) for s in segs for c in s.text]
    assert len(chars) == 20
    filled = [st for _, st in chars[:9]]
    track = [st for _, st in chars[11:]]
    assert len({st.color for st in filled if st}) > 1  # gradient varies
    assert all(st == track[0] for st in track)  # untouched track


def test_progress_bar_complete_and_empty() -> None:
    full = _segments(ProgressBar(total=10, completed=10, width=10, colors=COLORS))
    assert len({s.style.color for s in full if s.style}) > 1
    empty = _segments(ProgressBar(total=10, completed=0, width=10, colors=COLORS))
    assert len({s.style for s in empty}) == 1


def test_progress_bar_indeterminate_falls_back() -> None:
    assert _segments(ProgressBar(total=None, width=10, colors=COLORS))
