import pytest
from rich_gradient import Gradient, Text
from rich.console import Console
from rich.color import ColorParseError
from rich_color_ext import install

install()  # Ensure rich_color_ext is installed for color support


console = Console()

def render_to_text(renderable):
    """Render to plain text for assertion."""
    console.begin_capture()
    console.print(renderable)
    return console.end_capture()

@pytest.mark.parametrize("length", [1_000, 10_000])
def test_gradient_long_text(length):
    txt = "X" * length
    grad = Gradient(txt, ["#9f0", "#0f0", "#0f9", "#0ff"])
    out = render_to_text(grad)
    assert len(out) >= length  # ensure all characters output

def test_unicode_input():
    s = "こんにちは世界"  # Japanese + emoji
    grad = Gradient(Text(s + "🌟"), ["#9f0", "#0f0", "#0f9", "#0ff"])
    out = render_to_text(grad)
    assert "こんにちは世界" in out and "🌟" in out


@pytest.mark.parametrize(
    "colors",
    [
        # Invalid hex codes
        ["#GGGGGG", "blue"],
        ["#12345", "red"],  # too short
        ["#1234567", "green"],  # too long
        ["#12G45F", "yellow"],  # invalid character
        # Named colors that don't exist
        ["notacolor", "blue"],
        ["bluish", "red"],
        ["reddish", "green"],
        # Invalid rgb/rgba strings
        ["rgb(300,0,0)", "blue"],  # out of range
        ["rgb(-1,0,0)", "blue"],   # negative value
        ["rgb(0,0)", "blue"],      # too few components
        ["rgb(0,0,0,0,0)", "blue"],  # too many components
        ["rgba(0,0,0,2)", "blue"],  # alpha out of range
        ["rgba(0,0,0,-1)", "blue"], # negative alpha
        ["rgba(0,0,0)", "blue"],    # missing alpha
        # Completely invalid strings
        ["", "blue"],
        [None, "blue"],
        [123, "blue"],
        ["#FFF", None],
        ["#FFF", ""],
        ["#FFF", 123],
    ]
)
def test_invalid_color_raises_all_cases(colors):
    text = "Testing invalid color input"
    with pytest.raises((ColorParseError, TypeError, ValueError)):
        console.begin_capture()
        console.print(Text(text, colors=colors))
        console.end_capture()
