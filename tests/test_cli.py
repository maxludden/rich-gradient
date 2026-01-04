"""CLI behavior tests for rich-gradient."""

from __future__ import annotations

import io

import pytest
from click.testing import CliRunner
from rich.console import Console

from rich_gradient.cli import cli
from rich_gradient.cli import common
from rich_gradient.cli import text_command


@pytest.fixture
def cli_console(monkeypatch: pytest.MonkeyPatch) -> Console:
    console = Console(
        file=io.StringIO(),
        record=True,
        force_terminal=False,
        color_system=None,
        width=120,
    )
    monkeypatch.setattr(common, "console", console)
    monkeypatch.setattr(text_command, "console", console)
    return console


def test_cli_defaults_to_print_with_args(cli_console: Console) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["Hello", "World"])
    assert result.exit_code == 0
    assert "Hello World" in cli_console.export_text(styles=False)


def test_cli_defaults_to_print_with_stdin(cli_console: Console) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, input="stdin value")
    assert result.exit_code == 0
    assert "stdin value" in cli_console.export_text(styles=False)


def test_print_command_reads_from_stdin(cli_console: Console) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["print"], input="piped text\n")
    assert result.exit_code == 0
    assert "piped text" in cli_console.export_text(styles=False)


def test_print_command_requires_text_without_stdin() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["print"])
    assert result.exit_code != 0
    stderr = getattr(result, "stderr", "")
    assert "Missing text argument" in f"{result.output}{stderr}"


def test_cli_defaults_to_print_with_options(cli_console: Console) -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--rainbow", "Hi"])
    assert result.exit_code == 0
    assert "Hi" in cli_console.export_text(styles=False)
