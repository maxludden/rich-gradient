from pathlib import Path

from typer.testing import CliRunner
from rich.panel import Panel
from rich.text import Text as RichText

from rich_gradient.cli import app, parse_renderable


runner = CliRunner()


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
