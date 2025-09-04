"""
Test suite for Rule class covering rendering, style, color validation, and error handling.
"""

import pytest
from rich.color import ColorParseError
from rich.console import Console
from rich.style import Style
from rich.text import Text as RichText

from rich_gradient.rule import Rule


@pytest.mark.parametrize("thickness", [0, 1, 2, 3])
def test_gradient_rule_renders_thickness(thickness):
    """
    Test that Rule renders with the specified thickness and produces a RichText output.
    """
    console = Console()
    rule = Rule(title="Test", colors=["#f00", "#0f0"], thickness=thickness)
    # Render to string to check output is str (not crash)
    rendered = console.render_str(str(rule))
    assert isinstance(rendered, RichText)


def test_gradient_rule_title_and_style():
    """
    Test that Rule correctly sets title and title_style attributes.
    """
    rule = Rule(
        title="Hello",
        title_style="bold white",
        colors=["red", "green"],
        thickness=1,
        style="italic",
    )
    assert rule.title == "Hello"
    assert isinstance(rule.title_style, Style)


def test_gradient_rule_rainbow_colors():
    """
    Test that Rule with rainbow=True generates multiple colors.
    """
    rule = Rule(title="Rainbow", rainbow=True, thickness=1)
    assert len(rule.colors) > 1  # Should be populated by Spectrum


def test_gradient_rule_color_validation():
    """
    Test that Rule raises ValueError for invalid color input.
    """
    with pytest.raises(ValueError):
        Rule(title="BadColor", colors=["not-a-color"])


def test_gradient_rule_invalid_thickness():
    """
    Test that Rule raises ValueError for invalid thickness values.
    """
    with pytest.raises(ValueError):
        Rule(title="Fail", colors=["#f00", "#0f0"], thickness=5)


def test_gradient_rule_no_title():
    """
    Test that Rule can be instantiated with no title.
    """
    rule = Rule(title=None, colors=["#f00", "#0f0"])
    assert isinstance(rule, Rule)


def test_gradient_rule_render_output():
    """
    Test that Rule.__rich_console__ produces segments with text attribute.
    """
    console = Console()
    rule = Rule(title="Centered", colors=["#f00", "#0f0"])
    segments = list(rule.__rich_console__(console, console.options))
    assert segments
    assert all(hasattr(seg, "text") for seg in segments)
