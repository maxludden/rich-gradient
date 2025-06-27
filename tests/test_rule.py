import pytest
from rich.color import ColorParseError
from rich.console import Console
from rich.style import Style
from rich.text import Text as RichText

from rich_gradient.rule import Rule


@pytest.mark.parametrize("thickness", [0, 1, 2, 3])
def test_gradient_rule_renders_thickness(thickness):
    console = Console()
    rule = Rule(title="Test", colors=["#f00", "#0f0"], thickness=thickness)
    # Render to string to check output is str (not crash)
    rendered = console.render_str(str(rule))
    assert isinstance(rendered, RichText)


def test_gradient_rule_title_and_style():
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
    rule = Rule(title="Rainbow", rainbow=True, thickness=1)
    assert len(rule.colors) > 1  # Should be populated by Spectrum


def test_gradient_rule_color_validation():
    with pytest.raises(ValueError):
        Rule(title="BadColor", colors=["not-a-color"])


def test_gradient_rule_invalid_thickness():
    with pytest.raises(ValueError):
        Rule(title="Fail", colors=["#f00", "#0f0"], thickness=5)


def test_gradient_rule_no_title():
    rule = Rule(title=None, colors=["#f00", "#0f0"])
    assert isinstance(rule, Rule)


def test_gradient_rule_render_output():
    console = Console()
    rule = Rule(title="Centered", colors=["#f00", "#0f0"])
    segments = list(rule.__rich_console__(console, console.options))
    assert segments
    assert all(hasattr(seg, "text") for seg in segments)
    assert segments
    assert all(hasattr(seg, "text") for seg in segments)
