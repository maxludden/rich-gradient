"""Common utilities for the rich-gradient CLI."""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple, cast

import click
import typer
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.table import Table
from rich.text import Text as RichText
from rich.theme import Theme
from rich.traceback import install as tr_install
from rich_color_ext import install as rc_install
from typer import Typer
from typer.core import TyperGroup

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.panel import Panel
from rich_gradient.text import Text
from rich_gradient.theme import GradientTheme

rc_install()
tr_install()
_console = Console(theme=GradientTheme())

__all__ = ["DefaultCommandGroup", "main"]


class DefaultCommandGroup(TyperGroup):
    """A Typer/Click group that defaults to a command when none is provided.

    This makes these work equivalently:
    - rich-gradient "hello"            -> rich-gradient print "hello"
    - echo "hello" | rich-gradient     -> rich-gradient print (reads stdin)
    - rich-gradient -R "hello"         -> rich-gradient print -R "hello"
    """

    # Name of the default command to invoke
    _default_cmd_name = "print"

    def parse_args(self, ctx: click.Context, args: list[str]) -> None:  # type: ignore[override]
        # Respect root-level flags and completion env
        root_flags = {
            "--help",
            "-h",
            "--version",
            "-V",
            "--install-completion",
            "--show-completion",
            "--help-all",
        }

        if not args:
            # No args: default to the print command (stdin supported within command)
            args.insert(0, self._default_cmd_name)
        else:
            first = args[0]
            # Known subcommand? leave as-is
            if first not in self.commands:
                # Root flags/completion? leave as-is for Typer to handle
                if not (first in root_flags or first.startswith("_TYPER_COMPLETE")):
                    # Either an option (starts with '-') or free text: route to default
                    if first.startswith("-") or True:
                        args.insert(0, self._default_cmd_name)

        super().parse_args(ctx, args)


class RichGradientCommand(click.Command):
    """Override Clicks help with a Rich Gradient version."""

    def format_help(self, ctx, formatter) -> None:
        class OptionHighlighter(RegexHighlighter):
            highlights = [
                r"(?P<switch>\-\w)",
                r"(?P<option>\-\-[\w\-]+)",
            ]

        highlighter = OptionHighlighter()

        console = Console(
            theme=Theme({
                "option": "bold #99ff00",
                "switch": "bold cyan",
            }),
            highlighter=highlighter,
        )

        console.print(
            Text(
                "[b]rich-gradient CLI[/b] [magenta]v{VERSION}[/] 🤑\n\n[dim]Rich text, formatting, and gradients in the terminal\n",
            ),
            justify="center",
        )

        usage: Text = Text(
            "Usage: [b]rich-gradient[/b] [b][OPTIONS][/] \
[b cyan]<PATH,TEXT,URL, or '-'>\n"
        )
        usage.highlight_words(["Usage"], "bold yellow")
        usage.highlight_words(["[", "]", ",", "<", ">"], "bold white")
        console.print(usage)

        options_table = Table(highlight=True, box=None, show_header=False)

        for param in self.get_params(ctx)[1:]:
            if len(param.opts) == 2:
                opt1 = highlighter(param.opts[1])
                opt2 = highlighter(param.opts[0])
            else:
                opt2 = highlighter(param.opts[0])
                opt1 = Text("")

            if param.metavar:
                opt2 += Text(f" {param.metavar}", style="bold yellow")

            options = Text(" ".join(reversed(param.opts)))
            help_record = param.get_help_record(ctx)
            if help_record is None:
                _help = RichText("")
            else:
                # help_record is a tuple (opts, help_text)
                _, help_text = help_record
                _help = RichText.from_markup(help_text, emoji=False)

            if param.metavar:
                options.append_text(Text(f" {param.metavar}"))

            options_table.add_row(opt1, opt2, highlighter(_help))

        console.print(
            Panel(
                options_table, border_style="dim", title="Options", title_align="left"
            )
        )

        console.print(
            Text(
                "♥ https://maxludden.github.io/rich-gradient/",
                rainbow=True,
                style="italic",
            ),
            justify="left",
            style="bold",
        )


# Version
def version_callback(value: bool) -> bool:
    """Display package version when requested."""

    if value:
        from rich_gradient import __version__  # pylint: disable=import-outside-toplevel

        _console.print(Text(__version__))
        raise typer.Exit()
    return value


# Animation helpers
def validate_duration(value: float) -> float:
    """Validate animation duration input."""

    if value <= 0:
        raise typer.BadParameter("duration must be greater than zero")
    return value


def run_animation(animation: AnimatedGradient, duration: float) -> None:
    """Start an animation for the requested duration."""

    animation.start()
    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        # Allow graceful exit with Ctrl+C without stack trace noise.
        pass
    finally:
        animation.stop()


# Rule helpers
def validate_thickness(value: int) -> int:
    """Ensure thickness option stays within the supported range."""

    if not 0 <= value <= 3:
        raise typer.BadParameter("thickness must be between 0 and 3")
    return value


# Panel Helpers
def normalize_arguments(app: Typer, arguments: Sequence[str]) -> List[str]:
    """Ensure a default command is inserted when none is provided."""

    root_flags = {
        "--help",
        "-h",
        "--version",
        "-V",
        "--install-completion",
        "--show-completion",
        "--help-all",
    }
    if not arguments:
        return ["print"]

    first = arguments[0]
    registered_commands = set(app.registered_commands)

    if first in registered_commands:
        return list(arguments)

    if first in root_flags or first.startswith("_TYPER_COMPLETE"):
        return list(arguments)

    if first.startswith("-"):
        return ["print", *arguments]

    return ["print", *arguments]


def read_text_source(source: Optional[str]) -> str:
    """Resolve CLI text input from an argument or stdin."""

    if source is not None and "=" in source:
        key, value = source.split("=", 1)
        if key.strip().lower() == "text":
            source = value.strip()

    if source == "-":
        data = sys.stdin.read()
        if not data:
            raise typer.BadParameter("stdin did not provide any data")
        return data

    if source is None:
        if sys.stdin.isatty():
            raise typer.BadParameter("provide text or pipe content to stdin")
        data = sys.stdin.read()
        if not data:
            raise typer.BadParameter("stdin did not provide any data")
        return data

    return source


def colors_callback(value: Optional[str]) -> Optional[list[str]]:
    """Callback to parse comma-separated colors into a list.
    Args:
        value: Comma-separated string of colors.
    Returns:
        A list of color strings or None if no colors provided.
    """
    value = value[0] if isinstance(value, list) else value
    if not value:
        return None
    if "," in value:
        _colors = value.split(",")
        return [str(color).strip() for color in _colors]
    return [value.strip()]


def justify_callback(value: str) -> str:
    """Callback to validate justification option."""

    valid_justifications = {"left", "center", "right"}
    if value not in valid_justifications:
        raise ValueError(f"Justification must be one of {valid_justifications}")
    return value


def parse_padding(
    value: str | Tuple[int] | Tuple[int, int] | Tuple[int, int, int, int],
) -> Tuple[int, int, int, int]:
    """Parse CLI padding values into a 4-tuple of integers (top, right, bottom, left).

    Accepts either:
    - A string with 1,2 or 4 comma-separated integers (e.g. "1", "1,2", "1,2,3,4").
    - A tuple of 1,2 or 4 integers (e.g. (1,), (1,2), (1,2,3,4)).

    Raises ValueError for invalid input.
    """
    # If string provided, split and convert
    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",") if p.strip()]
        if not parts:
            raise ValueError("Padding must contain at least one integer.")
        try:
            nums = [int(p) for p in parts]
        except ValueError as error:
            raise ValueError("Padding values must be integers.") from error
        value_tuple = tuple(nums)
    else:
        value_tuple = tuple(value)

    if len(value_tuple) == 1:
        val = value_tuple[0]
        return (val, val, val, val)
    if len(value_tuple) == 2:
        return (value_tuple[0], value_tuple[1], value_tuple[0], value_tuple[1])
    if len(value_tuple) == 4:
        return cast(Tuple[int, int, int, int], value_tuple)
    raise ValueError("Padding must be 1, 2, or 4 comma-separated integers.")


def main(app: Typer, argv: Optional[Iterable[str]] = None) -> None:
    """CLI entry point that supports implicit default commands.

    Behaviors:
    - No subcommand provided: defaults to `print`.
    - Leading options (e.g., `-c`, `--rainbow`) without a command: treated as `print` options.
    - Root flags like `--help` and `--version` are respected.
    """

    if argv is None:
        args = sys.argv[1:]
    else:
        args = list(argv)

    normalized = normalize_arguments(app, args)

    # Invoke the Typer app with normalized arguments (Click-compatible invocation)
    app(prog_name="rich-gradient", args=normalized)
