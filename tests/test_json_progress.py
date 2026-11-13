"""Tests for the gradient JSON and ProgressBar wrappers."""

from __future__ import annotations

from rich.console import Console
from rich.progress_bar import ProgressBar as RichProgressBar
from rich.segment import Segment

from rich_gradient import Rule
from rich_gradient.json import JSON
from rich_gradient.progress_bar import ProgressBar

COLORS = ["#ff0000", "#0000ff"]


def _console(width: int = 40) -> Console:
    return Console(width=width, force_terminal=True, color_system="truecolor")


def _chars(renderable: object, width: int = 40) -> list[tuple[str, object]]:
    console = _console(width)
    return [
        (ch, seg.style)
        for seg in console.render(renderable)
        if isinstance(seg, Segment) and seg.text != "\n"
        for ch in seg.text
    ]


def test_json_applies_gradient_colors() -> None:
    chars = [(c, s) for c, s in _chars(JSON('{"a": [1, 2]}', highlight=False, indent=None, colors=COLORS), 14) if c.strip()]
    first, last = chars[0][1].color.triplet, chars[-1][1].color.triplet
    assert first.red > first.blue
    assert last.blue > first.blue and last.red < first.red


def test_json_from_data_matches_string() -> None:
    console = _console(30)
    with console.capture() as ca:
        console.print(JSON.from_data({"k": 1}, colors=COLORS))
    with console.capture() as cb:
        console.print(JSON('{\n  "k": 1\n}', colors=COLORS))
    assert ca.get() == cb.get()


def test_json_from_data_accepts_rich_option_names() -> None:
    renderable = JSON.from_data({"b": 1, "a": 2}, skip_keys=True, sort_keys=True, colors=COLORS)
    console = Console(width=30, record=True)
    console.print(renderable)
    text = console.export_text()
    assert text.index('"a"') < text.index('"b"')


def test_progress_bar_gradient_only_on_filled() -> None:
    chars = _chars(ProgressBar(total=100, completed=50, width=20, colors=COLORS))
    ref = _chars(RichProgressBar(total=100, completed=50, width=20))
    assert len(chars) == 20
    assert len({s.color for _, s in chars[:10]}) > 1  # gradient varies
    assert [s for _, s in chars[10:]] == [s for _, s in ref[10:]]  # track untouched


def test_progress_bar_complete_and_empty() -> None:
    full = _chars(ProgressBar(total=10, completed=10, width=10, colors=COLORS))
    assert len({s.color for _, s in full}) > 1
    empty = _chars(ProgressBar(total=10, completed=0, width=10, colors=COLORS))
    assert empty == _chars(RichProgressBar(total=10, completed=0, width=10))


def test_progress_bar_same_fill_and_track_color_still_gets_gradient() -> None:
    bar = ProgressBar(
        total=10, completed=5, width=10, colors=COLORS,
        style="white", complete_style="white",
    )
    chars = _chars(bar)
    assert len({s.color for _, s in chars[:5]}) > 1
    assert len({s for _, s in chars[6:]}) == 1


def test_progress_bar_keeps_fill_attributes() -> None:
    bar = ProgressBar(
        total=10, completed=10, width=10, colors=COLORS,
        finished_style="bold on blue",
    )
    for _, style in _chars(bar):
        assert style.bold and style.bgcolor is not None


def test_progress_bar_indeterminate_pulses_with_gradient() -> None:
    """Indeterminate bars keep Rich's pulse characters but color the wave from the gradient."""
    ours = _chars(ProgressBar(total=None, width=10, colors=COLORS, animation_time=0.0))
    rich = _chars(RichProgressBar(total=None, width=10, animation_time=0.0))
    assert [c for c, _ in ours] == [c for c, _ in rich]
    assert [s for _, s in ours] != [s for _, s in rich]


def test_progress_bar_exposes_rich_state() -> None:
    bar = ProgressBar(total=80, completed=20, width=12, colors=COLORS)
    assert (bar.total, bar.completed, bar.width) == (80, 20, 12)
    assert bar.complete_style == "bar.complete"
    bar.completed = 40
    assert bar.bar.completed == 40 and bar.percentage_completed == 50


def test_rule_honors_trailing_newline_flag() -> None:
    rule = Rule()
    rule.trailing_newline = False
    console = Console(width=10)
    with console.capture() as cap:
        console.print(rule)
    assert not cap.get().endswith("\n")
