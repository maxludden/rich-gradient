"""CLI module for the rich-gradient package."""

# pylint: disable=W0611
from __future__ import annotations

import sys
import time
from typing import Annotated, Any, Iterable, List, Optional, Sequence, cast

import typer
from rich.console import Console
from rich.text import Text as RichText
from rich_color_ext import install as rc_install
from typer import Argument, Option, Typer

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.animated_rule import AnimatedRule
from rich_gradient.panel import Panel
from rich_gradient.rule import Rule
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

rc_install()

app = Typer(
    name="rich-gradient",
    short_help="rich-gradient CLI tool",
    rich_markup_mode="rich",
)


def _make_console() -> Console:
    """Create a console with the gradient theme applied."""

    return Console(theme=GradientTheme())


def _version_callback(value: bool) -> bool:
    """Display package version when requested."""

    if value:
        from rich_gradient import __version__

        typer.echo(__version__)
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
    """Callback to parse comma-separated colors into a list."""
    if not value:
        return None
    if "," in value:
        _colors = value.split(",")
        return [color.strip() for color in _colors]
    return [value.strip()]


def justify_callback(value: str) -> str:
    """Callback to validate justification option."""
    valid_justifications = {"left", "center", "right"}
    if value not in valid_justifications:
        raise ValueError(f"Justification must be one of {valid_justifications}")
    return value


def _parse_padding(value: str) -> List[int]:
    """Parse CLI padding values into a list of integers."""
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
            "-R/-n",
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
    ] = 5.0,
):
    """Print gradient text to the terminal."""
    content = _read_text_source(text)
    console = _make_console()
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
            expand=False,
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
        Optional[str],
        Option("-t", "--title", help="Optional title for the rule"),
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
(e.g., '#ff0000,#00ff00,#0000ff')",
        ),
    ] = None,
    rainbow: Annotated[
        bool,
        Option(
            "-R/-n",
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
    ] = 5.0,
):
    """Display a gradient rule."""
    console = _make_console()
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


@app.command(
    name="panel",
    help="Display text inside a gradient panel",
    short_help="Display a gradient panel",
)
def panel_command(
    text: Annotated[
        Optional[str],
        Argument(help="The text to display inside the panel or '-' for stdin"),
    ] = None,
    text_option: Annotated[
        Optional[str],
        Option(
            "--text",
            "-T",
            help="Alternative way to supply panel text (supports '-' for stdin).",
        ),
    ] = None,
    title: Annotated[
        Optional[str], Option("-t", "--title", help="Title of the panel")
    ] = None,
    title_style: Annotated[
        str,
        Option(
            "-s",
            "--title-style",
            help="Style of the panel title text",
        ),
    ] = "bold",
    colors: Annotated[
        Optional[list[str]],
        Option(
            "-c",
            "--colors",
            callback=colors_callback,
            help="Comma-separated list of colors for the gradient \
(e.g., '#f00,#ff9900,yellow')",
        ),
    ] = None,
    rainbow: Annotated[
        bool,
        Option(
            "-R/-n",
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
    padding: Annotated[
        Optional[str],
        Option(
            "-p",
            "--padding",
            help="Padding inside the panel (1, 2, or 4 comma-separated integers).",
        ),
    ] = None,
    justify: Annotated[
        str,
        Option(
            "-j",
            "--justify",
            callback=justify_callback,
            help="Justification of the panel title",
        ),
    ] = "center",
    expand: Annotated[
        bool,
        Option(
            "--expand/--no-expand",
            help="Whether to expand the panel to fill the width of the console",
            is_flag=True,
        ),
    ] = True,
    animated: Annotated[
        bool,
        Option(
            "-a",
            "--animated",
            help="Animate the gradient panel.",
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
    ] = 5.0,
):
    """Display input in a gradient panel.

    Options:
    - `--title`: Title of the panel.
    - `--title-style`: Style of the title text.
    - `--colors`: Comma-separated list of colors for the gradient.
    - `--rainbow`: Use rainbow colors for the gradient.
    - `--hues`: Number of hues for rainbow gradient.
    - `--padding`: Padding inside the panel (1, 2, or 4 comma-separated integers).
    - `--justify`: Justification of the panel title.
    - `--expand/--no-expand`: Whether to expand the panel to fill the width of the console.
    """
    console = _make_console()

    source_value = text_option if text_option is not None else text
    if source_value is None:
        # Provide a friendly default demo when no input is supplied
        content = "Panels can frame gradient text for call-outs and highlights."
        if title is None:
            title = "Gradient Panel"
    else:
        content = _read_text_source(source_value)

    _colors = colors if colors else None

    parsed_padding: Optional[List[int]] = None
    if padding is not None:
        try:
            parsed_padding = _parse_padding(padding)
        except ValueError as error:
            raise typer.BadParameter(str(error)) from error

    panel_kwargs: dict[str, Any] = {}
    if parsed_padding is not None:
        panel_kwargs["padding"] = tuple(parsed_padding)

    try:
        inner_renderable = RichText.from_markup(content)
    except Exception as error:
        raise typer.BadParameter(f"invalid markup: {error}") from error

    panel_align = cast(Any, justify)
    panel_kwargs["title_align"] = panel_align

    if animated:
        try:
            animation = AnimatedPanel(
                inner_renderable,
                title=title,
                title_style=title_style,
                colors=cast(Any, _colors),
                rainbow=rainbow,
                hues=hues,
                justify=panel_align,
                expand=expand,
                console=console,
                **panel_kwargs,
            )
        except ValueError as error:
            raise typer.BadParameter(str(error)) from error
        _run_animation(animation, duration)
        return

    try:
        gradient_panel = Panel(
            inner_renderable,
            title=title,
            title_style=title_style,
            colors=cast(Any, _colors),
            rainbow=rainbow,
            hues=hues,
            justify=panel_align,
            expand=expand,
            **panel_kwargs,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(gradient_panel, justify=panel_align)


if __name__ == "__main__":
    main()
