"""Integration tests for the Typer-based ``rich-gradient`` CLI."""

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
    assert result.stdout.strip()  # Version string is non-empty


@pytest.mark.parametrize(
    "args, expected",
    [
        (["print", "Hello world"], "Hello world"),
        (["print", "text=From assignment"], "From assignment"),
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


def test_print_command_handles_colours() -> None:
    """Explicit colour stops should render without errors."""

    result = runner.invoke(app, ["print", "Colourful", "-c", "#f00,#0f0"])
    assert result.exit_code == 0
    assert "Colourful" in result.stdout


def test_print_command_rejects_invalid_colour() -> None:
    """An invalid colour stop should produce an error message."""

    result = runner.invoke(app, ["print", "Bad", "-c", "not-a-colour"])
    assert result.exit_code != 0
    assert "Error" in result.stdout


def test_print_command_supports_animation() -> None:
    """Animations with zero duration should complete immediately."""

    result = runner.invoke(app, ["print", "Animated", "-a", "-d", "0"])
    assert result.exit_code == 0


def test_rule_command_outputs_title() -> None:
    """The ``rule`` command should include the provided title."""

    result = runner.invoke(app, ["rule", "-t", "Section", "-c", "red,blue", "-T", "2"])
    assert result.exit_code == 0
    assert "Section" in result.stdout


def test_rule_command_invalid_colour() -> None:
    """Invalid colours should cause the rule command to fail."""

    result = runner.invoke(app, ["rule", "-c", "#GGGGGG"])
    assert result.exit_code != 0


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
            "--align",
            "center",
            "--padding",
            "1,2",
            "--no-expand",
        ],
    )
    assert result.exit_code == 0
    assert "Panel body" in result.stdout
    assert "Info" in result.stdout


def test_panel_command_supports_animation() -> None:
    """Animated panels should honour the duration flag."""

    result = runner.invoke(app, ["panel", "Animated panel", "-a", "-d", "0"])
    assert result.exit_code == 0


def test_panel_command_rejects_bad_padding() -> None:
    """Invalid padding strings should surface an error."""

    result = runner.invoke(app, ["panel", "Pad me", "-p", "1,2,3"])
    assert result.exit_code != 0


def test_panel_command_rejects_bad_colour() -> None:
    """Invalid colours should cause the panel command to fail."""

    result = runner.invoke(app, ["panel", "Oops", "-c", "#XYZ"])
    assert result.exit_code != 0
