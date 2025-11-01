"""CLI module for the rich-gradient package."""

from __future__ import annotations

import sys
import time
from typing import Annotated, Any, Iterable, List, Optional, Sequence, cast

import click
import typer
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.panel import Panel as RichPanel
from rich.table import Table
from rich.text import Text as RichText
from rich.theme import Theme
from rich.traceback import install as tr_install
from rich_color_ext import install as rc_install
from typer import Argument, Option, Typer
from typer.core import TyperGroup

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.animated_rule import AnimatedRule
from rich_gradient.panel import Panel
from rich_gradient.rule import Rule
from rich_gradient.text import Text
from rich_gradient.theme import GradientTheme

rc_install()
tr_install()
_console = Console(theme=GradientTheme())


class _DefaultCommandGroup(TyperGroup):
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
                "[b]rich-gradient CLI[/b] [magenta]v{VERSION}[/] 🤑\n\n\
[dim]Rich text, formatting, and gradients in the terminal\n",
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


app = Typer(
    name="rich-gradient",
    short_help="rich-gradient CLI tool",
    rich_markup_mode="rich",
    cls=_DefaultCommandGroup,
    epilog="rich-gradient",
)


def _version_callback(value: bool) -> bool:
    """Display package version when requested."""

    if value:
        from rich_gradient import __version__  # pylint: disable=import-outside-toplevel

        console.print(Text(__version__))
        raise typer.Exit()
    return value


def _validate_duration(value: float) -> float:
    """Validate animation duration input."""

    if value <= 0:
        raise typer.BadParameter("duration must be greater than zero")
    return value


def _run_animation(animation: AnimatedGradient, duration: float) -> None:
    """Start an animation for the requested duration."""

    animation.start()
    try:
        time.sleep(duration)
    except KeyboardInterrupt:
        # Allow graceful exit with Ctrl+C without stack trace noise.
        pass
    finally:
        animation.stop()


def _validate_thickness(value: int) -> int:
    """Ensure thickness option stays within the supported range."""

    if not 0 <= value <= 3:
        raise typer.BadParameter("thickness must be between 0 and 3")
    return value


def _normalize_arguments(arguments: Sequence[str]) -> List[str]:
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


def main(argv: Optional[Iterable[str]] = None) -> None:
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

    normalized = _normalize_arguments(args)
    # Invoke the Typer app with normalized arguments (Click-compatible invocation)
    app(prog_name="rich-gradient", args=normalized)


def _read_text_source(source: Optional[str]) -> str:
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
        value: The raw CLI input value.
    Returns:
        A list of color strings or None.
    """
    value = value[0] if isinstance(value, list) else value
    if not value:
        return None
    if "," in value:
        _colors = value.split(",")
        return [color.strip() for color in _colors]
    return [value.strip()]


def justify_callback(value: str) -> str:
    """Callback to validate justification option.
    Args:
        value: The raw CLI input value.
    Returns:
        The validated justification string.
    """
    valid_justifications = {"left", "center", "right"}
    if value not in valid_justifications:
        raise ValueError(f"Justification must be one of {valid_justifications}")
    return value


def _parse_padding(value: str) -> List[int]:
    """Parse CLI padding values into a list of integers.
    Args:
        value: The raw CLI input value.
    Returns:
        A list of four integers representing padding.
    Raises:
        ValueError: If the input is invalid.
    """
    parts = [element.strip() for element in value.split(",") if element.strip()]
    if not parts:
        raise ValueError("Padding must contain at least one integer.")
    try:
        numbers = [int(part) for part in parts]
    except ValueError as error:
        raise ValueError("Padding values must be integers.") from error
    if len(numbers) == 1:
        pad = numbers[0]
        return [pad, pad, pad, pad]
    if len(numbers) == 2:
        vertical, horizontal = numbers
        return [vertical, horizontal, vertical, horizontal]
    if len(numbers) == 4:
        return numbers
    raise ValueError("Padding must be 1, 2, or 4 comma-separated integers.")


@click.command(cls=RichGradientCommand)
@app.command(name="print", help="Print gradient text to the terminal")
def print_command(
    text: Annotated[
        Optional[str],
        Argument(help="The text to display with gradient or '-' for stdin"),
    ] = None,
    colors: Annotated[
        Optional[list[str]],
        Option(
            "-c",
            "--colors",
            callback=colors_callback,
            help="Comma-separated list of colors for the gradient \
(e.g., '#ff0000,#f90,yellow')",
        ),
    ] = None,
    rainbow: Annotated[
        bool,
        Option(
            "-r/-R",
            "--rainbow/--no-rainbow",
            help="Use rainbow colors for the gradient",
        ),
    ] = False,
    hues: Annotated[
        int,
        Option(
            "-u",
            "--hues",
            help="Number of hues for rainbow gradient",
        ),
    ] = 7,
    justify: Annotated[
        str,
        Option(
            "-j",
            "--justify",
            callback=justify_callback,
            help="Justification of the text",
        ),
    ] = "left",
    animated: Annotated[
        bool,
        Option(
            "-a",
            "--animated",
            help="Animate the gradient text.",
            is_flag=True,
        ),
    ] = False,
    duration: Annotated[
        float,
        Option(
            "-d",
            "--duration",
            callback=_validate_duration,
            help="Length of the animation in seconds (requires --animated).",
        ),
    ] = 10.0,
):
    """Print gradient text to the terminal."""
    content = _read_text_source(text)
    _colors = colors if colors else None

    if animated:
        try:
            renderable = RichText.from_markup(content)
        except Exception as error:
            raise typer.BadParameter(f"invalid markup: {error}") from error

        animation = AnimatedGradient(
            renderable,
            colors=cast(Any, _colors),  # use parsed colors if provided
            rainbow=rainbow,
            hues=hues,
            console=console,
            justify=cast(Any, justify),
            expand=True,
        )
        _run_animation(animation, duration)
        return

    try:
        gradient_text = Text(
            content,
            colors=_colors,
            rainbow=rainbow,
            hues=hues,
            justify=cast(Any, justify),
        )
    except Exception as error:
        raise typer.BadParameter(f"invalid markup: {error}") from error

    console.print(gradient_text, justify=cast(Any, justify))


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool,
        Option(
            "-V",
            "--version",
            help="Show the installed rich-gradient version and exit.",
            is_flag=True,
            callback=_version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Provide global CLI options."""

    # The version flag is handled eagerly by the callback.
    _ = version

    if ctx.invoked_subcommand is not None:
        return


@app.command(name="rule", short_help="Display a gradient rule")
def rule_command(
    title: Annotated[
        Optional[str], Option("-t", "--title", help="Optional title for the rule")
    ] = None,
    title_style: Annotated[
        str,
        Option(
            "-s",
            "--title-style",
            help="Style to apply to the title text",
        ),
    ] = "bold",
    justify: Annotated[
        str,
        Option(
            "-j",
            "--justify",
            help="Justification of the title text",
            callback=justify_callback,
        ),
    ] = "center",
    colors: Annotated[
        Optional[list[str]],
        Option(
            "-c",
            "--colors",
            callback=colors_callback,
            help="Comma-separated list of colors for the gradient \
(e.g., '#ff0,#00ff00,cyan')",
        ),
    ] = None,
    rainbow: Annotated[
        bool,
        Option(
            "-R/-n",
            "--rainbow/--no-rainbow",
            help="Use rainbow colors for the gradient",
            is_flag=True,
        ),
    ] = False,
    hues: Annotated[
        int,
        Option(
            "-u",
            "--hues",
            help="Number of hues for rainbow gradient",
        ),
    ] = 7,
    thickness: Annotated[
        int,
        Option(
            "-T",
            "--thickness",
            callback=_validate_thickness,
            help="Thickness of the rule (0-3)",
        ),
    ] = 1,
    animated: Annotated[
        bool,
        Option(
            "-a",
            "--animated",
            help="Animate the gradient rule.",
            is_flag=True,
        ),
    ] = False,
    duration: Annotated[
        float,
        Option(
            "-d",
            "--duration",
            callback=_validate_duration,
            help="Length of the animation in seconds (requires --animated).",
        ),
    ] = 10.0,
):
    """Display a gradient rule."""
    _colors = colors if colors else None

    if animated:
        try:
            animation = AnimatedRule(
                title=title,
                title_style=title_style,
                colors=_colors,
                rainbow=rainbow,
                hues=hues,
                thickness=thickness,
                align=cast(Any, justify),
                console=console,
            )
        except ValueError as error:
            raise typer.BadParameter(str(error)) from error
        _run_animation(animation, duration)
        return

    try:
        gradient_rule = Rule(
            title=title,
            title_style=title_style,
            colors=_colors,
            rainbow=rainbow,
            hues=hues,
            thickness=thickness,
            align=cast(Any, justify),
            console=console,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(gradient_rule)


if __name__ == "__main__":
    main()
