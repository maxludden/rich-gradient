"""
Test suite for Rule and AnimatedRule covering rendering, style, color validation, and context helpers.
"""

import time
import os
from pathlib import Path

os.environ.setdefault(
    "RICH_GRADIENT_CONFIG_HOME",
    str((Path(__file__).parent / ".rg_config_test").resolve()),
)

import pytest
from rich.color import ColorParseError
from rich.console import Console
from rich.style import Style
from rich.text import Text as RichText

from rich_gradient.animated_rule import AnimatedRule
from rich_gradient.rule import Rule


@pytest.mark.parametrize("thickness", [0, 1, 2, 3])
def test_gradient_rule_renders_thickness(thickness) -> None:
    """Rule should render with the requested thickness without crashing."""
    console = Console()
    rule = Rule(title="Test", colors=["#f00", "#0f0"], thickness=thickness)
    rendered = console.render_str(str(rule))
    assert isinstance(rendered, RichText)


def test_gradient_rule_title_and_style() -> None:
    """Title and style attributes should roundtrip when provided."""
    rule = Rule(
        title="Hello",
        title_style="bold white",
        colors=["red", "green"],
        thickness=1,
        style="italic",
    )
    assert rule.title == "Hello"
    assert isinstance(rule.title_style, Style)


def test_gradient_rule_rainbow_colors() -> None:
    """Rainbow rules should auto-populate multiple colour stops."""
    rule = Rule(title="Rainbow", rainbow=True, thickness=1)
    assert len(rule.colors) > 1


@pytest.mark.parametrize("bad", [["not-a-color"], ["#f00", "bad"]])
def test_gradient_rule_color_validation(bad) -> None:
    """Invalid colour inputs should raise ValueError."""
    with pytest.raises(ValueError):
        Rule(title="BadColor", colors=bad)


@pytest.mark.parametrize("thickness", [-1, 5])
def test_gradient_rule_invalid_thickness(thickness) -> None:
    """Out-of-range thickness values should be rejected."""
    with pytest.raises(ValueError):
        Rule(title="Fail", colors=["#f00", "#0f0"], thickness=thickness)


@pytest.mark.parametrize("title", [None, ""]) 
def test_gradient_rule_no_title(title) -> None:
    """Rules should instantiate even when title is omitted."""
    rule = Rule(title=title, colors=["#f00", "#0f0"])
    assert isinstance(rule, Rule)


def test_gradient_rule_render_output() -> None:
    """Rich console rendering should yield segments with text content."""
    console = Console()
    rule = Rule(title="Centered", colors=["#f00", "#0f0"])
    segments = list(rule.__rich_console__(console, console.options))
    assert segments
    assert all(hasattr(seg, "text") for seg in segments)


def test_animated_rule_for_duration_auto_stop(monkeypatch) -> None:
    """for_duration should trigger stop automatically once the timer expires."""
    rule = AnimatedRule(
        title="Timed",
        colors=["#ff0000", "#00ff00"],
        auto_refresh=False,
        refresh_per_second=30.0,
        console=Console(record=True, width=40),
        animate=False,
    )

    start_calls: list[None] = []
    stop_calls: list[None] = []
    original_start = rule.start
    original_stop = rule.stop

    def start_wrapper() -> None:
        start_calls.append(None)
        return original_start()

    def stop_wrapper() -> None:
        stop_calls.append(None)
        return original_stop()

    monkeypatch.setattr(rule, "start", start_wrapper, raising=False)
    monkeypatch.setattr(rule, "stop", stop_wrapper, raising=False)

    with rule.for_duration(0.02):
        time.sleep(0.05)

    # entering the context should call start exactly once
    assert len(start_calls) == 1
    # timer thread plus teardown may both invoke stop, but at least one call should occur
    assert len(stop_calls) >= 1


def test_animated_rule_for_duration_early_exit(monkeypatch) -> None:
    """Leaving the context before the deadline should stop exactly once."""
    rule = AnimatedRule(
        title="Early",
        colors=["#112233", "#334455"],
        auto_refresh=False,
        refresh_per_second=30.0,
        console=Console(record=True, width=40),
        animate=False,
    )

    start_calls: list[None] = []
    stop_calls: list[None] = []
    original_start = rule.start
    original_stop = rule.stop

    def start_wrapper() -> None:
        start_calls.append(None)
        return original_start()

    def stop_wrapper() -> None:
        stop_calls.append(None)
        return original_stop()

    monkeypatch.setattr(rule, "start", start_wrapper, raising=False)
    monkeypatch.setattr(rule, "stop", stop_wrapper, raising=False)

    with rule.for_duration(10.0):
        # exit immediately without waiting for timer expiration
        pass

    # give the watcher thread a moment to notice the cancellation
    time.sleep(0.05)

    assert len(start_calls) == 1
    # only the teardown path should call stop since we exited early
    assert len(stop_calls) == 1
