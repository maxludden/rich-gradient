""""Tests for animated gradient functionality."""
# pylint: disable=protected-access
import math

from rich.console import Console

from rich_gradient import AnimatedGradient, Gradient  # type: ignore[reportMissingTypeStubs]


def test_phase_progression_changes_color():
    """Test that advancing the phase changes the sampled color at a position."""
    console = Console(record=True, width=40)
    ag = AnimatedGradient(
        renderables="Test",
        colors=["#ff0000", "#0000ff"],
        refresh_per_second=20.0,
        phase_per_second=0.5,
        auto_refresh=False,
        console=console,
        disable=True,
    )
    # Use Gradient helpers to sample color at a fixed position
    span = 80
    pos = 10
    before = ag._color_at(pos, 1, span)
    # Advance one frame equivalent
    ag.phase += ag._phase_per_second / ag.refresh_per_second
    after = ag._color_at(pos, 1, span)
    assert before != after


def test_speed_back_compat_mapping_equivalence():
    """Test that speed parameter maps correctly to phase_per_second."""
    # Old behavior: per-frame delta = speed/1000.0
    # New behavior: per-frame delta = (phase_per_second / refresh_per_second)
    refresh = 25.0
    speed_ms = 10  # 10ms per frame -> 0.01 phase per frame
    ag = AnimatedGradient(
        renderables="X",
        colors=["#f00", "#0f0"],
        refresh_per_second=refresh,
        speed=speed_ms,
        auto_refresh=False,
        disable=True,
    )
    expected_per_frame = speed_ms / 1000.0
    computed_per_frame = ag._phase_per_second / ag.refresh_per_second
    assert math.isclose(
        computed_per_frame, expected_per_frame, rel_tol=1e-9, abs_tol=1e-9
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
