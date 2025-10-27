"""Typer-based command line interface for ``rich-gradient``.

This module exposes three subcommands—``print``, ``rule``, and ``panel``—that
mirror the usage documented in ``docs/cli.md``.  Each command accepts the same
colour handling options (explicit stops, rainbow gradients, hue selection) and
implements the ergonomic text sourcing described in the guide: inline text
arguments, ``text=...`` syntax, or streamed standard input via ``-``.

The CLI is intentionally compact so that the options showcased in the
documentation remain the single source of truth for expected behaviour.  Helper
functions centralise repeated tasks such as parsing colour stops, padding
strings, and resolving text sources.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Literal, Optional, Sequence, Tuple

import typer
from rich.align import Align
from rich.color import ColorParseError
from rich.console import Console, RenderableType
from rich.text import Text as RichText

from rich_gradient import __version__
from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.animated_rule import AnimatedRule
from rich_gradient.panel import Panel as GradientPanel
from rich_gradient.rule import Rule as GradientRule
from rich_gradient.text import Text as GradientText

JustifyOption = Literal["left", "center", "right"]

app = typer.Typer(help="Render colourful text, rules, and panels using gradients.")


def _create_console() -> Console:
    """Return a console used for rendering CLI output."""

    return Console()


def _version_callback(value: bool) -> None:
    """Print the installed package version when ``--version`` is supplied."""

    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(  # noqa: D401 - Typer uses the callback docstring.
        False,
        "--version",
        "-V",
        help="Show the rich-gradient version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    """Root callback for shared global options."""


def _read_text_source(argument: Optional[str]) -> str:
    """Resolve command input from inline arguments, files, or standard input."""

    if argument is None:
        if sys.stdin.isatty():
            raise typer.BadParameter("provide text or pipe content to stdin")
        data = sys.stdin.read()
        if not data:
            raise typer.BadParameter("stdin did not provide any data")
        return data

    if argument == "-":
        data = sys.stdin.read()
        if not data:
            raise typer.BadParameter("stdin did not provide any data")
        return data

    if argument.startswith("text="):
        argument = argument.split("=", 1)[1]

    candidate = Path(argument)
    if candidate.exists() and candidate.is_file():
        try:
            return candidate.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:  # pragma: no cover - defensive
            raise typer.BadParameter("file is not valid UTF-8 text") from error

    return argument


def _parse_color_stops(spec: Optional[str]) -> Optional[Sequence[str]]:
    """Split a comma-separated colour specification into individual stops."""

    if spec is None:
        return None
    stops = [part.strip() for part in spec.split(",") if part.strip()]
    if not stops:
        raise typer.BadParameter("provide at least one colour stop")
    return stops


def _parse_padding(value: Optional[str]) -> Tuple[int, int, int, int]:
    """Parse padding strings (``"1"``, ``"2,4"``, ``"1,2,3,4"``) into a 4-tuple."""

    if not value:
        return (0, 0, 0, 0)
    parts = [element.strip() for element in value.split(",") if element.strip()]
    try:
        numbers = [int(part) for part in parts]
    except ValueError as error:  # pragma: no cover - validated via typer
        raise typer.BadParameter("padding must contain integers") from error

    if len(numbers) == 1:
        top = right = bottom = left = numbers[0]
    elif len(numbers) == 2:
        top, right = numbers
        bottom, left = top, right
    elif len(numbers) == 4:
        top, right, bottom, left = numbers
    else:
        raise typer.BadParameter("padding requires 1, 2 or 4 integers")
    return (top, right, bottom, left)


def _as_list(values: Optional[Sequence[str]]) -> Optional[list[str]]:
    """Convert an optional sequence of strings into a mutable list."""

    return list(values) if values is not None else None


def _run_animation(animation: AnimatedGradient, duration: float) -> None:
    """Run an animated gradient for the requested duration."""

    if duration <= 0:
        animation.start()
        animation.stop()
        return

    try:
        with animation:
            time.sleep(duration)
    except KeyboardInterrupt:
        animation.stop()


def _handle_color_error(error: ColorParseError | ValueError) -> None:
    """Convert colour parsing errors into user-facing CLI errors."""

    raise typer.BadParameter(str(error)) from error


@app.command("print")
def print_command(  # noqa: D401 - Command help is provided via Typer metadata.
    text: Optional[str] = typer.Argument(
        None,
        help="Text to render, '-' for stdin, or text=...",
    ),
    colors: Optional[str] = typer.Option(
        None,
        "--colors",
        "-c",
        help="Comma-separated colour stops (e.g. '#f00,#ff0,#0f0').",
    ),
    rainbow: bool = typer.Option(
        False,
        "--rainbow/--no-rainbow",
        "-R/-n",
        help="Generate a rainbow gradient automatically.",
    ),
    hues: int = typer.Option(
        7,
        "--hues",
        "-h",
        min=2,
        help="Number of hues when auto-generating colours.",
    ),
    justify: JustifyOption = typer.Option(
        "left",
        "--justify",
        "-j",
        case_sensitive=False,
        help="Align the rendered text.",
    ),
    animated: bool = typer.Option(
        False,
        "--animated",
        "-a",
        help="Animate the gradient instead of rendering once.",
    ),
    duration: float = typer.Option(
        5.0,
        "--duration",
        "-d",
        min=0.0,
        help="Animation length in seconds.",
    ),
) -> None:
    """Render gradient text or an animated gradient in place."""

    console = _create_console()
    text_value = _read_text_source(text)
    color_stops = _as_list(_parse_color_stops(colors))

    try:
        if animated:
            animation = AnimatedGradient(
                renderables=text_value,
                colors=color_stops,
                rainbow=rainbow,
                hues=hues,
                console=console,
                justify=justify,
                expand=False,
            )
            _run_animation(animation, duration)
        else:
            gradient_text = GradientText(
                text_value,
                colors=color_stops,
                rainbow=rainbow,
                hues=hues,
                justify=justify,
            )
            console.print(gradient_text)
    except ColorParseError as error:
        _handle_color_error(error)


@app.command("rule")
def rule_command(  # noqa: D401 - Command help is provided via Typer metadata.
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        help="Optional title displayed within the rule.",
    ),
    title_style: str = typer.Option(
        "bold",
        "--title-style",
        "-s",
        help="Rich style applied to the rule title.",
    ),
    justify: JustifyOption = typer.Option(
        "center",
        "--justify",
        "-j",
        case_sensitive=False,
        help="Alignment for the rule title.",
    ),
    colors: Optional[str] = typer.Option(
        None,
        "--colors",
        "-c",
        help="Comma-separated colour stops for the rule.",
    ),
    rainbow: bool = typer.Option(
        False,
        "--rainbow/--no-rainbow",
        "-R/-n",
        help="Generate a rainbow gradient across the rule.",
    ),
    hues: int = typer.Option(
        7,
        "--hues",
        "-h",
        min=2,
        help="Number of hues when auto-generating colours.",
    ),
    thickness: int = typer.Option(
        1,
        "--thickness",
        "-T",
        min=0,
        max=3,
        help="Line thickness between 0 and 3.",
    ),
    animated: bool = typer.Option(
        False,
        "--animated",
        "-a",
        help="Animate the rule using Rich Live.",
    ),
    duration: float = typer.Option(
        5.0,
        "--duration",
        "-d",
        min=0.0,
        help="Animation length in seconds.",
    ),
) -> None:
    """Draw a gradient rule line, optionally with animation."""

    console = _create_console()
    color_stops = _as_list(_parse_color_stops(colors))

    try:
        if animated:
            animation = AnimatedRule(
                title=title,
                title_style=title_style,
                colors=color_stops,
                rainbow=rainbow,
                hues=hues,
                thickness=thickness,
                align=justify,
                console=console,
            )
            _run_animation(animation, duration)
        else:
            rule_renderable = GradientRule(
                title=title,
                title_style=title_style,
                colors=color_stops,
                rainbow=rainbow,
                hues=hues,
                thickness=thickness,
                align=justify,
                console=console,
            )
            console.print(rule_renderable)
    except (ColorParseError, ValueError) as error:
        _handle_color_error(error)


def _panel_content(text: str, align: JustifyOption) -> RenderableType:
    """Return an aligned renderable for panel content."""

    return Align(RichText.from_markup(text), align=align)


@app.command("panel")
def panel_command(  # noqa: D401 - Command help is provided via Typer metadata.
    text: Optional[str] = typer.Argument(
        None,
        help="Panel content, '-' for stdin, or text=...",
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        help="Optional panel title.",
    ),
    title_style: str = typer.Option(
        "bold",
        "--title-style",
        "-s",
        help="Rich style applied to the panel title.",
    ),
    justify: JustifyOption = typer.Option(
        "center",
        "--justify",
        "-j",
        case_sensitive=False,
        help="Title alignment inside the panel.",
    ),
    align: JustifyOption = typer.Option(
        "left",
        "--align",
        case_sensitive=False,
        help="Content alignment inside the panel.",
    ),
    colors: Optional[str] = typer.Option(
        None,
        "--colors",
        "-c",
        help="Comma-separated colour stops for the panel background.",
    ),
    rainbow: bool = typer.Option(
        False,
        "--rainbow/--no-rainbow",
        "-R/-n",
        help="Generate a rainbow panel background.",
    ),
    hues: int = typer.Option(
        7,
        "--hues",
        "-h",
        min=2,
        help="Number of hues when auto-generating colours.",
    ),
    padding: Optional[str] = typer.Option(
        None,
        "--padding",
        "-p",
        help="Panel padding (N, V,H or T,R,B,L).",
    ),
    expand: bool = typer.Option(
        True,
        "--expand/--no-expand",
        help="Expand the panel to available width.",
    ),
    animated: bool = typer.Option(
        False,
        "--animated",
        "-a",
        help="Animate the panel background.",
    ),
    duration: float = typer.Option(
        5.0,
        "--duration",
        "-d",
        min=0.0,
        help="Animation length in seconds.",
    ),
) -> None:
    """Produce a gradient-backed panel around text or streamed content."""

    console = _create_console()
    text_value = _read_text_source(text)
    color_stops = _as_list(_parse_color_stops(colors))
    padding_values = _parse_padding(padding)
    content = _panel_content(text_value, align)

    try:
        if animated:
            animation = AnimatedPanel(
                content,
                colors=color_stops,
                rainbow=rainbow,
                hues=hues,
                title=title,
                title_align=justify,
                title_style=title_style,
                padding=padding_values,
                expand=expand,
                console=console,
                justify="center",
            )
            _run_animation(animation, duration)
        else:
            panel_renderable = GradientPanel(
                content,
                colors=color_stops,
                rainbow=rainbow,
                hues=hues,
                title=title,
                title_align=justify,
                title_style=title_style,
                padding=padding_values,
                expand=expand,
                justify="center",
            )
            console.print(panel_renderable)
    except ColorParseError as error:
        _handle_color_error(error)
