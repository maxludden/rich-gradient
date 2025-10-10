from pathlib import Path

from typer.testing import CliRunner
from rich.text import Text as RichText
from rich.panel import Panel
from rich.console import ConsoleRenderable

from rich_gradient.cli import app, parse_renderable


runner = CliRunner()


def test_parse_renderable_string():
    """Test that parse_renderable converts strings to RichText."""
    result = parse_renderable("Hello World")
    assert isinstance(result, ConsoleRenderable)
    assert isinstance(result, RichText)
    assert result.plain == "Hello World"


def test_parse_renderable_with_markup():
    """Test that parse_renderable handles Rich markup in strings."""
    result = parse_renderable("[bold]Hello[/bold]")
    assert isinstance(result, RichText)
    assert result.plain == "Hello"
    # Markup should create spans
    assert len(result._spans) > 0


def test_parse_renderable_console_renderable():
    """Test that parse_renderable passes through ConsoleRenderable objects."""
    panel = Panel("Test")
    result = parse_renderable(panel)
    assert result is panel  # Should be the same object


def test_parse_renderable_rich_cast():
    """Test that parse_renderable handles RichCast objects."""
    
    class MyRichCast:
        def __rich__(self):
            return RichText("From RichCast")
    
    obj = MyRichCast()
    result = parse_renderable(obj)
    assert isinstance(result, ConsoleRenderable)
    assert isinstance(result, RichText)
    assert result.plain == "From RichCast"


def test_parse_renderable_rich_cast_string():
    """Test that parse_renderable handles RichCast objects that return strings."""
    
    class MyRichCast:
        def __rich__(self):
            return "String from RichCast"
    
    obj = MyRichCast()
    result = parse_renderable(obj)
    assert isinstance(result, RichText)
    assert result.plain == "String from RichCast"


def test_parse_renderable_nested_rich_cast():
    """Test that parse_renderable handles nested RichCast objects."""
    
    class InnerRichCast:
        def __rich__(self):
            return RichText("Nested")
    
    class OuterRichCast:
        def __rich__(self):
            return InnerRichCast()
    
    obj = OuterRichCast()
    result = parse_renderable(obj)
    assert isinstance(result, ConsoleRenderable)
    assert isinstance(result, RichText)
    assert result.plain == "Nested"


def test_parse_renderable_invalid_type():
    """Test that parse_renderable raises TypeError for invalid types."""
    try:
        parse_renderable(123)  # type: ignore
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "Cannot parse" in str(e)


def test_parse_renderable_invalid_rich_cast():
    """Test that parse_renderable raises TypeError for RichCast returning invalid types."""
    
    class BadRichCast:
        def __rich__(self):
            return 123  # Invalid return type
    
    obj = BadRichCast()
    try:
        parse_renderable(obj)
        assert False, "Should have raised TypeError"
    except TypeError as e:
        assert "returned" in str(e)


def test_cli_text_basic():
    result = runner.invoke(app, ["text", "Hello", "-c", "magenta", "-c", "cyan"])
    assert result.exit_code == 0
    # Ensure plain text made it to output
    assert "Hello" in result.stdout


def test_cli_save_svg(tmp_path: Path):
    svg_path = tmp_path / "out.svg"
    result = runner.invoke(app, [
        "text",
        "Hello SVG",
        "--save-svg",
        str(svg_path),
        "--width",
        "60",
    ])
    assert result.exit_code == 0
    assert svg_path.exists()
    # Quick sanity check that it's an SVG file
    content = svg_path.read_text(encoding="utf-8", errors="ignore")
    assert "<svg" in content


def test_cli_title_without_panel_warns():
    # Omit mix_stderr for broader Click/Typer compatibility
    result = runner.invoke(app, ["text", "Warn", "--title", "T"]) 
    assert result.exit_code == 0
    warning = "Warning: --title has no effect without --panel"
    # Accept either stdout or stderr depending on environment
    assert (warning in result.stdout) or (warning in result.stderr)


def test_cli_invalid_color_exits_with_error():
    result = runner.invoke(app, ["text", "Bad", "-c", "#GGGGGG"])
    assert result.exit_code != 0
    assert "Error:" in result.stdout or "Error:" in result.stderr
