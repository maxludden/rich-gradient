from pathlib import Path

from typer.testing import CliRunner

from rich_gradient.cli import app


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
