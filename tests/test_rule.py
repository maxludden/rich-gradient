

import pytest
from rich.style import Style
from rich.color import ColorParseError
from rich.console import Console
from rich.text import Text as RichText
from rich_gradient.rule import GradientRule

@pytest.mark.parametrize("thickness", [0, 1, 2, 3])
def test_gradient_rule_renders_thickness(thickness):
    console = Console()
    rule = GradientRule(title="Test", colors=["#f00", "#0f0"], thickness=thickness)
    # Render to string to check output is str (not crash)
    rendered = console.render_str(str(rule))
    assert isinstance(rendered, RichText)

def test_gradient_rule_title_and_style():
    rule = GradientRule(
        title="Hello",
        title_style="bold white",
        colors=["red", "green"],
        thickness=1,
        style="italic",
    )
    assert rule.title == "Hello"
    assert isinstance(rule.title_style, Style)

def test_gradient_rule_rainbow_colors():
    rule = GradientRule(title="Rainbow", rainbow=True, thickness=1)
    assert len(rule.colors) > 1  # Should be populated by Spectrum

def test_gradient_rule_color_validation():
    with pytest.raises(ValueError):
        GradientRule(title="BadColor", colors=["not-a-color"])

def test_gradient_rule_invalid_thickness():
    with pytest.raises(ValueError):
        GradientRule(title="Fail", colors=["#f00", "#0f0"], thickness=5)

def test_gradient_rule_no_title():
    rule = GradientRule(title=None, colors=["#f00", "#0f0"])
    assert isinstance(rule, GradientRule)

def test_gradient_rule_render_output():
    console = Console()
    rule = GradientRule(title="Centered", colors=["#f00", "#0f0"])
    segments = list(rule.__rich_console__(console, console.options))
    assert segments
    assert all(hasattr(seg, "text") for seg in segments)
