"""
Test suite for Gradient class and color interpolation logic.
Covers color computation, style merging, rendering, and quit panel logic.
"""

import pytest
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style

from rich_gradient.gradient import Gradient


@pytest.mark.parametrize("rainbow", [True, False])
def test_gradient_color_computation(rainbow):
    """
    Test that Gradient._color_at returns a valid hex color string for both rainbow and non-rainbow modes.
    """
    gradient = Gradient("Hello", rainbow=rainbow)
    color = gradient._color_at(5, 1, 10)
    assert color.startswith("#") and len(color) == 7


def test_gradient_styled_foreground():
    """
    Test that _styled correctly merges foreground color and preserves style attributes.
    """
    original = Style(bold=True)
    gradient = Gradient("Test", colors=["#f00", "#0f0"])
    color = "#00ff00"
    styled = gradient._styled(original, color)
    assert styled.bold
    assert styled.color is not None
    assert styled.color.get_truecolor().hex.lower() == color.lower()


def test_gradient_styled_background():
    """
    Test that _styled correctly merges background color and preserves style attributes.
    """
    original = Style(dim=True)
    gradient = Gradient("Test", colors=["#f00", "#0f0"], background=True)
    color = "#00ff00"
    styled = gradient._styled(original, color)
    assert styled.dim
    assert styled.bgcolor is not None
    assert styled.bgcolor.get_truecolor().hex.lower() == color.lower()


def test_gradient_render_static():
    """
    Test that static gradient rendering produces only Segment objects.
    """
    console = Console()
    gradient = Gradient(
        Panel("Static Gradient Test", title="Test"), colors=["#f00", "#0f0"]
    )
    segments = list(gradient.__rich_console__(console, console.options))
    assert all(isinstance(seg, Segment) for seg in segments)


def test_gradient_with_single_color():
    """
    Test that a single color input produces two identical stops for smooth gradient.
    """
    gradient = Gradient("Single Color", colors=["#f00"])
    assert len(gradient._active_stops) == 2
    assert all(isinstance(c, tuple) and len(c) == 3 for c in gradient._active_stops)


def test_gradient_color_interpolation_boundaries():
    """
    Test that color interpolation at boundaries returns correct RGB values.
    """
    gradient = Gradient("Interp", colors=["#000000", "#ffffff"])
    assert gradient._interpolated_color(
        0.0, gradient._active_stops, len(gradient._active_stops)
    ) == (
        0,
        0,
        0,
    )
    assert gradient._interpolated_color(
        1.0, gradient._active_stops, len(gradient._active_stops)
    ) == (
        255,
        255,
        255,
    )


def test_gradient_rich_console_without_quit_panel():
    """
    Test that the quit panel text is not present when show_quit_panel is False.
    """
    console = Console()
    gradient = Gradient(
        Panel("No Quit Panel"), colors=["#f00", "#0f0"], show_quit_panel=False
    )
    segments = list(gradient.__rich_console__(console, console.options))
    rendered_text = "".join(seg.text for seg in segments if isinstance(seg, Segment))
    assert "Press [bold]Ctrl+C[/bold] to stop." not in rendered_text


def test_gradient_rich_console_with_quit_panel():
    """
    Test that the quit panel text is present when show_quit_panel is True.
    """
    console = Console()
    gradient = Gradient(
        Panel("With Quit Panel"), colors=["#f00", "#0f0"], show_quit_panel=True
    )
    segments = list(gradient.__rich_console__(console, console.options))
    rendered_text = "".join(seg.text for seg in segments if isinstance(seg, Segment))
    assert "Press [bold]Ctrl+C[/bold] to stop." in rendered_text


# In __init__ at the end:
# self._stops = self.colors if not self.background else self.bg_colors

# In __rich_console__ method, change quit panel text:
# if self.show_quit_panel:
#     panel = Panel("Press Ctrl+C to stop.", expand=False)
#     content = Group(content, Align(panel, align="right"))

# _interpolated_color method (already present) is fine.
# _interpolated_color method (already present) is fine.
