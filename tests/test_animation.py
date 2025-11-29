"""Tests for animated gradient functionality."""

# pylint: disable=protected-access
import math
import os
from pathlib import Path

# Direct configuration writes into a test-local directory to avoid touching the user home.
os.environ.setdefault(
    "RICH_GRADIENT_CONFIG_HOME",
    str((Path(__file__).parent / ".rg_config_test").resolve()),
)

from rich.console import Console

from rich_gradient import (
    CONFIG,  # type: ignore[reportMissingTypeStubs]
    AnimatedGradient,
    Gradient,
)
from rich_gradient.animated_gradient import FPS


def test_phase_progression_changes_color():
    """Test that advancing the phase changes the sampled color at a position."""
    console = Console(record=True, width=40)
    ag = AnimatedGradient(
        renderables="Test",
        colors=["#ff0000", "#0000ff"],
        refresh_per_second=20.0,
        auto_refresh=False,
        console=console,
    )
    # Use Gradient helpers to sample color at a fixed position
    span = 80
    pos = 10
    before = ag._color_at(pos, 1, span)
    # Advance one frame equivalent using the internal phase rate
    ag.phase += ag._phase_per_second / ag.refresh_per_second
    after = ag._color_at(pos, 1, span)
    assert before != after


def test_default_phase_rate_matches_expected_value():
    """Ensure AnimatedGradient uses the legacy default phase rate."""
    ag = AnimatedGradient(
        renderables="X",
        colors=["#f00", "#0f0"],
        refresh_per_second=30.0,
        auto_refresh=False,
    )
    expected_per_frame = ag._phase_per_second / ag.refresh_per_second
    assert math.isclose(
        expected_per_frame,
        FPS / ag.refresh_per_second,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )


def test_highlight_with_emoji_does_not_crash():
    """Ensure highlight pipeline handles multi-codepoint glyphs without error."""
    text = "Hello 🌟 World"
    grad = Gradient(text, colors=["#f00", "#0f0"], highlight_words={"World": "bold"})
    console = Console(record=True, width=40)
    console.begin_capture()
    console.print(grad)
    out = console.end_capture()
    assert "Hello" in out and "World" in out

    console.begin_capture()
    console.print(grad)
    out = console.end_capture()
    assert "Hello" in out and "World" in out
