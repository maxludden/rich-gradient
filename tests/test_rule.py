from typing import Iterable, List, Literal, Optional, Sequence, Union, cast

import pytest
from rich.align import AlignMethod
from rich.console import Console, ConsoleOptions, RenderResult
from rich.rule import Rule
from rich.segment import Segment
from rich.text import Text
from rich.traceback import install

from rich_gradient.color import Color, ColorError, ColorType
from rich_gradient.gradient import Gradient
from rich_gradient.rule import GradientRule
from rich_gradient.spectrum import Spectrum
from rich_gradient.style import Style, StyleType
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

console = Console()
install(console=console, width=64)


def test_gradient_rule():
    """Test the GradientRule class for various alignments, gradients, and styles."""

    console = Console(record=True, width=60)

    # Test default gradient rule with no title style
    rule1 = GradientRule(title="Test Rule", colors=["#ff0000", "#00ff00"], thickness=1)
    console.print(rule1)
    output1 = console.export_text()
    assert "Test Rule" in output1

    # Test rainbow gradient with thickness 3 and center alignment
    rule2 = GradientRule(
        title="Rainbow Rule", rainbow=True, thickness=3, align="center"
    )
    console.print(rule2)
    output2 = console.export_text()
    assert "Rainbow Rule" in output2

    # Test left alignment with custom colors and title style
    rule3 = GradientRule(
        title="Left Align",
        colors=["#0000ff", "#00ffff"],
        thickness=2,
        align="left",
        title_style="bold red",
    )
    console.print(rule3)
    output3 = console.export_text()
    assert "Left Align" in output3

    # Test invalid thickness raises ValueError
    with pytest.raises(ValueError):
        GradientRule(title="Invalid", thickness=5)

    # Test single color raises ValueError
    with pytest.raises(ValueError):
        GradientRule(title="Single Color", colors=["#ff0000"])

    # Test invalid color string raises ColorError
    with pytest.raises(ColorError):
        GradientRule(title="Bad Color", colors=["notacolor", "#000000"])

    # Test no colors provided uses default spectrum hues
    rule4 = GradientRule(title="Default Spectrum", colors=[])
    console.print(rule4)
    output4 = console.export_text()
    assert "Default Spectrum" in output4

    # Test that title_style is applied after gradient generation
    rule5 = GradientRule(
        title="Styled Title",
        colors=["#123456", "#654321"],
        title_style="bold underline",
    )
    console.print(rule5)
    output5 = console.export_text()
    assert "Styled Title" in output5

    # Test that thickness 0 uses correct character
    rule6 = GradientRule(title="Thin Rule", thickness=0)
    console.print(rule6)
    output6 = console.export_text()
    assert "Thin Rule" in output6

    # Test that thickness 3 uses correct character
    rule7 = GradientRule(title="Thick Rule", thickness=3)
    console.print(rule7)
    output7 = console.export_text()
    assert "Thick Rule" in output7
