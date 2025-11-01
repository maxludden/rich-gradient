"""Integration tests for the ``rich-gradient`` Typer CLI."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from rich_gradient.cli import app

runner = CliRunner()


def test_version_option() -> None:
    """``--version`` should print the installed package version."""

    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip()


def test_help_renders_gradient_panel() -> None:
    """Help output should render inside a gradient panel."""

    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    # Rounded box-drawing characters signal that a panel rendered.
    assert "╭" in result.stdout
    assert "rich-gradient" in result.stdout
    assert "Commands" in result.stdout


@pytest.mark.parametrize(
    "args, expected",
    [
        (["print", "Hello world"], "Hello world"),
        (["print", "text=Inline"], "Inline"),
    ],
)
def test_print_command_renders_text(args: list[str], expected: str) -> None:
    """The ``print`` command should render supplied text immediately."""

    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert expected in result.stdout


def test_print_command_reads_stdin() -> None:
    """Passing ``-`` should read text from standard input."""

    result = runner.invoke(app, ["print", "-"], input="Streamed input")
    assert result.exit_code == 0
    assert "Streamed input" in result.stdout


def test_print_command_handles_colour_options() -> None:
    """Explicit colour stops and background colours should render without errors."""

    result = runner.invoke(
        app,
        [
            "print",
            "Colourful",
            "-c",
            "#f00,#0f0",
            "--bgcolors",
            "#111111,#222222",
            "--style",
            "bold",
        ],
    )
    assert result.exit_code == 0
    assert "Colourful" in result.stdout


def test_print_command_rejects_invalid_colour() -> None:
    """Invalid colour stops should produce an error message."""

    result = runner.invoke(app, ["print", "Bad", "-c", "not-a-colour"])
    assert result.exit_code != 0
    stderr = result.stderr or ""
    assert "Invalid value for" in stderr or "Error" in stderr


def test_print_command_supports_animation() -> None:
    """Animations with zero duration should complete immediately."""

    result = runner.invoke(app, ["print", "Animated", "--animate", "-d", "0"])
    assert result.exit_code == 0


def test_rule_command_outputs_title() -> None:
    """The ``rule`` command should include the provided title."""

    result = runner.invoke(
        app,
        ["rule", "-t", "Section", "-c", "red,blue", "-T", "2", "--align", "left"],
    )
    assert result.exit_code == 0
    assert "Section" in result.stdout


def test_rule_command_invalid_colour() -> None:
    """Invalid colours should cause the rule command to fail."""

    result = runner.invoke(app, ["rule", "-c", "#GGGGGG"])
    assert result.exit_code != 0
    stderr = result.stderr or ""
    assert "Invalid value for" in stderr or "Error" in stderr


def test_panel_command_renders_content(tmp_path: Path) -> None:
    """The ``panel`` command should wrap file content in a gradient panel."""

    file_path = tmp_path / "content.txt"
    file_path.write_text("Panel body", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "panel",
            str(file_path),
            "-t",
            "Info",
            "--subtitle",
            "Details",
            "--padding",
            "1,2",
            "--text-justify",
            "center",
            "--no-expand",
            "--box",
            "ASCII",
        ],
    )
    assert result.exit_code == 0
    assert "Panel body" in result.stdout
    assert "Info" in result.stdout
    assert "Details" in result.stdout


def test_panel_command_requires_title_for_style() -> None:
    """Providing ``--title-style`` without a title should raise an error."""

    result = runner.invoke(app, ["panel", "content", "--title-style", "italic"])
    assert result.exit_code != 0
    assert "requires --title" in (result.stderr or "")


def test_panel_command_requires_no_expand_for_width() -> None:
    """Specifying ``--width`` should demand ``--no-expand``."""

    result = runner.invoke(app, ["panel", "content", "--width", "40"])
    assert result.exit_code != 0
    assert "requires --no-expand" in (result.stderr or "")


def test_panel_command_rejects_bad_padding() -> None:
    """Invalid padding strings should surface an error."""

    result = runner.invoke(app, ["panel", "Pad me", "-p", "1,2,3"])
    assert result.exit_code != 0


def test_panel_command_rejects_bad_colour() -> None:
    """Invalid colours should cause the panel command to fail."""

    result = runner.invoke(app, ["panel", "Oops", "-c", "#XYZ"])
    assert result.exit_code != 0


def test_panel_command_supports_animation() -> None:
    """Animated panels should honour the duration flag."""

    result = runner.invoke(app, ["panel", "Animated panel", "--animate", "-d", "0"])
    assert result.exit_code == 0


def test_markdown_command_renders_text(tmp_path: Path) -> None:
    """Markdown content provided via file should render inside a gradient."""

    markdown_file = tmp_path / "doc.md"
    markdown_file.write_text("# Heading\n\nBody", encoding="utf-8")

    result = runner.invoke(app, ["markdown", str(markdown_file), "--justify", "center"])
    assert result.exit_code == 0
    assert "Heading" in result.stdout
    assert "Body" in result.stdout


def test_markdown_command_accepts_inline_text() -> None:
    """Inline markdown text should render without errors."""

    result = runner.invoke(
        app,
        ["markdown", "# Title", "--colors", "magenta,cyan", "--bgcolors", "black"],
    )
    assert result.exit_code == 0
    assert "Title" in result.stdout


def test_markdown_command_invalid_colour() -> None:
    """Invalid colour specifications should surface an error."""

    result = runner.invoke(app, ["markdown", "# Bad", "--colors", "not-a-colour"])
    assert result.exit_code != 0
    stderr = result.stderr or ""
    assert "Invalid value for" in stderr or "Error" in stderr


def test_markdown_command_animation() -> None:
    """Animated markdown rendering should respect the duration flag."""

    result = runner.invoke(app, ["markdown", "# Animated", "--animate", "-d", "0"])
    assert result.exit_code == 0
