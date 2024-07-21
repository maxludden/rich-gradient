# ruff: noqa: F401
import pytest

from rich.console import Console

from rich_gradient._simple_gradient import SimpleGradient
from rich_gradient.color import Color
from rich_gradient.gradient import Gradient

@pytest.fixture
def simple_gradient():
    return Gradient(
        "This is a test.",
        colors=[
            Color("red"),
            Color("orange")
        ]
    )

@pytest.fixture
def gradient():
    return Gradient(
        "This a test of complex gradients.",
        colors=[
            Color("red"),
            Color("green"),
            Color("blue")
        ]
    )

def test_simple_gradient_initialization(simple_gradient):
    # Test default initialization
    assert len(simple_gradient) == 15