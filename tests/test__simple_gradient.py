import pytest
from rich.console import Console
from rich.style import Style
from rich.text import Text

from rich_gradient._simple_gradient import SimpleGradient


@pytest.fixture
def sample_gradient():
    return SimpleGradient(
        text="This is a test", color1="#00FF00", color2="#00FFFF", style="bold"
    )


def test_initialization(sample_gradient):
    assert sample_gradient.text == "This is a test"
    assert sample_gradient.color1.hex.upper() == "#00FF00"  # Hex code for green
    assert sample_gradient.color2.hex.upper() == "#00FFFF"  # Hex code for cyan
    assert sample_gradient.style == Style.parse("bold")


def test_text_property(sample_gradient):
    new_text = "New test text"
    sample_gradient.text = new_text
    assert sample_gradient.text == new_text


def test_style_property(sample_gradient):
    new_style = "italic"
    sample_gradient.style = new_style
    assert sample_gradient.style == Style.parse("italic")


def test_generate_spans(sample_gradient):
    spans = list(sample_gradient.generate_spans())
    assert len(spans) == len(sample_gradient.text)
    assert all(isinstance(span.style, Style) for span in spans)


def test_render(sample_gradient):
    console = Console()
    segments = list(sample_gradient.render(console))
    assert len(segments) == len(sample_gradient.text)
    assert all(segment.text in sample_gradient.text for segment in segments)


def test_rich_console(sample_gradient):
    console = Console()
    options = console.options
    segments = list(sample_gradient.__rich_console__(console, options))
    assert segments


def test_as_text(sample_gradient):
    text = sample_gradient.as_text(style=sample_gradient.style)
    assert isinstance(text, Text)
    assert text.plain == sample_gradient.plain
    assert text.style == sample_gradient.style


if __name__ == "__main__":
    pytest.main()
