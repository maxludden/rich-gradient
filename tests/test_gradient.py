# No changes needed in this file (tests/test_gradient.py) as the instructions apply to a different file (tests/test_spectrum.py).
# Outputting the original file content unchanged.

import pytest
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.segment import Segment
from rich_gradient.gradient import Gradient


@pytest.mark.parametrize("rainbow", [True, False])
def test_gradient_color_computation(rainbow):
    gradient = Gradient("Hello", rainbow=rainbow)
    color = gradient._color_at(5, 1, 10)
    assert color.startswith("#") and len(color) == 7


def test_gradient_styled_foreground():
    original = Style(bold=True)
    gradient = Gradient("Test", colors=["#f00", "#0f0"])
    color = "#00ff00"
    styled = gradient._styled(original, color)
    assert styled.bold
    assert styled.color is not None
    assert styled.color.get_truecolor().hex.lower() == color.lower()


def test_gradient_styled_background():
    original = Style(dim=True)
    gradient = Gradient("Test", colors=["#f00", "#0f0"], background=True)
    color = "#00ff00"
    styled = gradient._styled(original, color)
    assert styled.dim
    assert styled.bgcolor is not None
    assert styled.bgcolor.get_truecolor().hex.lower() == color.lower()


def test_gradient_render_static():
    console = Console()
    gradient = Gradient(Panel("Static Gradient Test", title="Test"), colors=["#f00", "#0f0"])
    segments = list(gradient.__rich_console__(console, console.options))
    assert all(isinstance(seg, Segment) for seg in segments)


def test_gradient_render_animated_footer():
    console = Console()
    gradient = Gradient(Panel("Animated", title="Test"), colors=["#f00", "#0f0"], animated=True)
    segments = list(gradient.__rich_console__(console, console.options))
    rendered_text = "".join(seg.text for seg in segments if isinstance(seg, Segment))
    assert "Press Ctrl+C to stop." in rendered_text


def test_gradient_with_single_color():
    gradient = Gradient("Single Color", colors=["#f00"])
    assert len(gradient._stops) == 2
    assert all(isinstance(c, tuple) and len(c) == 3 for c in gradient._stops)


def test_gradient_color_interpolation_boundaries():
    gradient = Gradient("Interp", colors=["#000000", "#ffffff"])
    assert gradient._interpolated_color(0.0, gradient._stops, len(gradient._stops)) == (0, 0, 0)
    assert gradient._interpolated_color(1.0, gradient._stops, len(gradient._stops)) == (255, 255, 255)
