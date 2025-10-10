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


def test_parse_renderable_with_string():
    """Test parse_renderable with string input."""
    result = parse_renderable("Hello, [bold]World[/bold]!")
    assert isinstance(result, RichText)
    assert result.plain == "Hello, World!"


def test_parse_renderable_with_console_renderable():
    """Test parse_renderable with ConsoleRenderable (Panel) input."""
    panel = Panel("Test content", title="Test")
    result = parse_renderable(panel)
    assert result is panel  # Should return the same object
    assert isinstance(result, Panel)


def test_parse_renderable_with_richcast():
    """Test parse_renderable with RichCast (object with __rich__ method)."""
    class CustomRenderable:
        def __rich__(self):
            return RichText("Custom content")
    
    custom = CustomRenderable()
    result = parse_renderable(custom)
    assert isinstance(result, RichText)
    assert result.plain == "Custom content"


def test_parse_renderable_with_richcast_returning_string():
    """Test parse_renderable with RichCast that returns a string."""
    class StringRichCast:
        def __rich__(self):
            return "[green]Green text[/green]"
    
    string_cast = StringRichCast()
    result = parse_renderable(string_cast)
    assert isinstance(result, RichText)
    assert result.plain == "Green text"


def test_parse_renderable_with_richtext():
    """Test parse_renderable with RichText input."""
    text = RichText("Direct text", style="bold")
    result = parse_renderable(text)
    assert result is text  # Should return the same object
    assert isinstance(result, RichText)


def test_cli_gradient_command():
    """Gradient command should render gradient showcase text."""

    result = runner.invoke(app, ["gradient"])
    assert result.exit_code == 0
    assert "Gradient Showcase" in result.stdout


def test_cli_rule_command():
    """Rule command should print explanatory text alongside the gradient rule."""

    result = runner.invoke(app, ["rule"])
    assert result.exit_code == 0
    assert "Gradient rules are perfect for separating sections." in result.stdout


def test_cli_panel_command():
    """Panel command should wrap gradient text in a panel output."""

    result = runner.invoke(app, ["panel"])
    assert result.exit_code == 0
    assert "Panels can frame gradient text for call-outs and highlights." in result.stdout


def test_cli_table_command():
    """Table command should render gradient table content."""

    result = runner.invoke(app, ["table"])
    assert result.exit_code == 0
    assert "Color stops" in result.stdout


def test_cli_progress_command():
    """Progress command should complete successfully with summary text."""

    result = runner.invoke(app, ["progress"])
    assert result.exit_code == 0
    assert "Gradient progress complete!" in result.stdout


def test_cli_syntax_command():
    """Syntax command should include its gradient heading."""

    result = runner.invoke(app, ["syntax"])
    assert result.exit_code == 0
    assert "Gradient Syntax" in result.stdout


def test_cli_markdown_command():
    """Markdown command should emit the markdown heading text."""

    result = runner.invoke(app, ["markdown"])
    assert result.exit_code == 0
    assert "Gradient Markdown" in result.stdout


def test_cli_markup_command():
    """Markup command should parse markup and print the resulting text."""

    result = runner.invoke(app, ["markup"])
    assert result.exit_code == 0
    assert "Rich markup meets gradients!" in result.stdout


def test_cli_box_command():
    """Box command should render descriptive gradient text."""

    result = runner.invoke(app, ["box"])
    assert result.exit_code == 0
    assert "borders pair nicely with gradients" in result.stdout


def test_cli_prompts_command():
    """Prompts command should simulate a prompt and echo the response."""

    result = runner.invoke(app, ["prompts"])
    assert result.exit_code == 0
    assert "Simulated response" in result.stdout


def test_cli_live_command():
    """Live command should finish and print its closing message."""

    result = runner.invoke(app, ["live"])
    assert result.exit_code == 0
    assert "Exited live rendering session." in result.stdout
