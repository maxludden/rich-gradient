"""Typer-based command line interface for ``rich-gradient``.

This CLI mirrors the functionality exposed by the underlying ``rich-gradient``
renderables (text, panels, rules, and markdown) and provides a high-fidelity
front end similar to the ``rich`` project's ``rich`` command.  In addition to
exposing gradient-aware subcommands, the CLI renders contextual help inside
``rich_gradient.panel.Panel`` instances so that ``--help`` output showcases the
package's styling capabilities.

Every command honours the palette-handling options common across the project:
explicit colour stops, rainbow gradients, background colours, hue selection,
and optional animation with controllable duration.  Input text can be provided
inline, loaded from files, or streamed from standard input when ``-`` is
specified as the argument.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Literal, Optional, Sequence

import typer
from rich.align import Align
from rich.box import ASCII, DOUBLE, HEAVY, ROUNDED, SQUARE, Box
from rich.color import ColorParseError
from rich.console import Console, RenderableType
from rich.markdown import Markdown as RichMarkdown
from rich.text import Text as RichText

from click.core import ParameterSource

from rich_gradient import __version__
from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.animated_rule import AnimatedRule
from rich_gradient.gradient import Gradient
from rich_gradient.panel import Panel as GradientPanel
from rich_gradient.rule import Rule as GradientRule
from rich_gradient.text import Text as GradientText

JustifyOption = Literal["left", "center", "right"]
VerticalJustifyOption = Literal["top", "middle", "bottom"]
OverflowOption = Literal["crop", "fold", "ellipsis"]
RuleThickness = Literal[0, 1, 2, 3]
BoxChoice = Literal["SQUARE", "ROUNDED", "HEAVY", "DOUBLE", "ASCII"]

HELP_COLORS = ["#b877ff", "#ff6b9e", "#ffd56b"]


def _create_console() -> Console:
    """Return a console configured for terminal output."""

    return Console(color_system="auto")


class _GradientHelpMixin:
    """Mixin that renders Click/Typer help inside a gradient panel."""

    help_panel_colors: Sequence[str] = HELP_COLORS

    def _render_help_panel(self, ctx: typer.Context, help_text: str) -> str:
        """Return help text wrapped in a ``GradientPanel``.

        Args:
            ctx: The Typer context requesting help output.
            help_text: The standard Click help string.
        Returns:
            A string representation of the help content rendered through a
            gradient panel.
        """

        width = ctx.terminal_width or 100
        constrained_width = max(60, min(width, 120))
        console = Console(
            record=True,
            width=constrained_width,
            color_system="truecolor",
        )
        title = ctx.command_path or "rich-gradient"
        content = RichText(help_text.rstrip("\n"), no_wrap=False, overflow="fold")
        panel = GradientPanel(
            content,
            colors=list(self.help_panel_colors),
            rainbow=False,
            hues=max(len(self.help_panel_colors), 2),
            title=title,
            title_align="left",
            title_style="bold",  # Highlight the command path
            padding=(1, 2),
            expand=True,
            justify="left",
        )
        panel.console = console
        console.print(panel)
        return console.export_text(clear=False)


class GradientCommand(_GradientHelpMixin, typer.core.TyperCommand):
    """Command subclass that emits help using gradient panels."""

    def get_help(self, ctx: typer.Context) -> str:  # type: ignore[override]
        """Render Click help text within a gradient panel."""

        help_text = super().get_help(ctx)
        return self._render_help_panel(ctx, help_text)


class GradientGroup(_GradientHelpMixin, typer.core.TyperGroup):
    """Group subclass that emits help using gradient panels."""

    def get_help(self, ctx: typer.Context) -> str:  # type: ignore[override]
        """Render Click help text within a gradient panel."""

        help_text = super().get_help(ctx)
        return self._render_help_panel(ctx, help_text)


BOX_MAP: dict[BoxChoice, Box] = {
    "SQUARE": SQUARE,
    "ROUNDED": ROUNDED,
    "HEAVY": HEAVY,
    "DOUBLE": DOUBLE,
    "ASCII": ASCII,
}

DEFAULT_SOURCES = {ParameterSource.DEFAULT, ParameterSource.DEFAULT_MAP}

app = typer.Typer(
    cls=GradientGroup,
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _version_callback(value: bool) -> None:
    """Print the installed package version when ``--version`` is supplied."""

    if value:
        typer.echo(__version__)
        raise typer.Exit()


@app.callback()
def root_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show the rich-gradient version and exit.",
    ),
) -> None:
    """Root callback registering shared global options."""

    # ``ctx`` is required so Typer retains the context for subcommands.
    _ = ctx


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


def _parse_color_stops(spec: Optional[str]) -> Optional[list[str]]:
    """Split a comma-separated colour specification into individual stops."""

    if spec is None:
        return None
    stops = [part.strip() for part in spec.split(",") if part.strip()]
    if not stops:
        raise typer.BadParameter("provide at least one colour stop")
    return stops


def _parse_padding(value: Optional[str]) -> tuple[int, int, int, int]:
    """Parse padding strings (``"1"``, ``"2,4"``, ``"1,2,3,4"``) into a 4-tuple."""

    if not value:
        return (0, 0, 0, 0)
    parts = [element.strip() for element in value.split(",") if element.strip()]
    try:
        numbers = [int(part) for part in parts]
    except ValueError as error:  # pragma: no cover - validated via Typer
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


def _parse_box_choice(choice: BoxChoice) -> Box:
    """Return the ``rich.box`` instance matching the requested style."""

    return BOX_MAP[choice]


def _run_animation(animation: AnimatedGradient, duration: float) -> None:
    """Run an animated gradient for the requested duration."""

    if duration <= 0:
        animation.start()
        animation.stop()
        return

    try:
        with animation:
            time.sleep(duration)
    except KeyboardInterrupt:  # pragma: no cover - manual interruption
        animation.stop()


def _handle_color_error(error: ColorParseError | ValueError) -> None:
    """Convert colour parsing errors into user-facing CLI errors."""

    raise typer.BadParameter(str(error)) from error


@app.command("print", cls=GradientCommand)
def print_command(
    text: Optional[str] = typer.Argument(
        None,
        help="Text to render, '-' for stdin, or text=...",
    ),
    colors: Optional[str] = typer.Option(
        None,
        "--colors",
        "-c",
        metavar="COLORS",
        help="Comma-separated colour stops (e.g., 'red,#ff9900,yellow').",
    ),
    rainbow: bool = typer.Option(
        False,
        "--rainbow",
        "-r",
        help="Print text in rainbow colours (overrides --colors).",
    ),
    hues: int = typer.Option(
        7,
        "--hues",
        "-h",
        min=2,
        metavar="HUES",
        help="The number of hues to use for a random gradient.",
    ),
    style: Optional[str] = typer.Option(
        None,
        "--style",
        metavar="STYLE",
        help="Rich style string applied to the text.",
    ),
    justify: JustifyOption = typer.Option(
        "left",
        "--justify",
        "-j",
        case_sensitive=False,
        metavar="JUSTIFY",
        help="Justification of the text.",
    ),
    overflow: OverflowOption = typer.Option(
        "fold",
        "--overflow",
        metavar="OVERFLOW",
        help="How to handle text overflow.",
    ),
    no_wrap: bool = typer.Option(
        False,
        "--no-wrap",
        help="Disable text wrapping.",
    ),
    end: str = typer.Option(
        "\n",
        "--end",
        metavar="END",
        help="String appended after the text is printed.",
    ),
    bgcolors: Optional[str] = typer.Option(
        None,
        "--bgcolors",
        metavar="BGCOLORS",
        help=(
            "Comma-separated list of background colours for the gradient "
            "(e.g., 'red,#ff9900,yellow')."
        ),
    ),
    animate: bool = typer.Option(
        False,
        "--animate",
        help="Animate the gradient text.",
    ),
    duration: float = typer.Option(
        5.0,
        "--duration",
        "-d",
        min=0.0,
        metavar="DURATION",
        help="Duration of the animation in seconds.",
    ),
) -> None:
    """Print gradient-coloured text to the console."""

    console = _create_console()
    text_value = _read_text_source(text)
    color_stops = _parse_color_stops(colors)
    bg_color_stops = _parse_color_stops(bgcolors)

    base_text = RichText.from_markup(
        text_value,
        style=style or "",
        justify=justify,
        overflow=overflow,
    )
    base_text.no_wrap = no_wrap
    base_text.end = end

    try:
        if animate:
            animation = AnimatedGradient(
                renderables=base_text,
                colors=color_stops,
                bg_colors=bg_color_stops,
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
                style=style or "",
                justify=justify,
                overflow=overflow,
                no_wrap=no_wrap,
                end=end,
                bgcolors=bg_color_stops,
            )
            console.print(gradient_text)
    except (ColorParseError, ValueError) as error:
        _handle_color_error(error)


@app.command("panel", cls=GradientCommand)
def panel_command(
    ctx: typer.Context,
    renderable: Optional[str] = typer.Argument(
        None,
        help="Panel content, '-' for stdin, or text=...",
    ),
    colors: Optional[str] = typer.Option(
        None,
        "--colors",
        "-c",
        metavar="COLORS",
        help="Comma-separated list of colours for the gradient.",
    ),
    bgcolors: Optional[str] = typer.Option(
        None,
        "--bgcolors",
        metavar="BGCOLORS",
        help=(
            "Comma-separated list of background colours for the gradient "
            "(e.g., 'red,#ff9900,yellow')."
        ),
    ),
    rainbow: bool = typer.Option(
        False,
        "--rainbow",
        "-r",
        help="Use rainbow colours for the gradient.",
    ),
    hues: int = typer.Option(
        5,
        "--hues",
        metavar="HUES",
        min=2,
        help="Number of hues for rainbow gradient.",
    ),
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        metavar="TITLE",
        help="Title of the panel.",
    ),
    title_style: Optional[str] = typer.Option(
        None,
        "--title-style",
        metavar="TITLE_STYLE",
        show_default="bold",
        help="Style applied to the panel title (requires --title).",
    ),
    title_align: JustifyOption = typer.Option(
        "center",
        "--title-align",
        metavar="TITLE_ALIGN",
        case_sensitive=False,
        help="Alignment of the panel title (requires --title).",
    ),
    subtitle: Optional[str] = typer.Option(
        None,
        "--subtitle",
        metavar="SUBTITLE",
        help="Subtitle of the panel.",
    ),
    subtitle_style: Optional[str] = typer.Option(
        None,
        "--subtitle-style",
        metavar="SUBTITLE_STYLE",
        help="Style applied to the panel subtitle (requires --subtitle).",
    ),
    subtitle_align: JustifyOption = typer.Option(
        "right",
        "--subtitle-align",
        metavar="SUBTITLE_ALIGN",
        case_sensitive=False,
        help="Alignment of the panel subtitle (requires --subtitle).",
    ),
    style: Optional[str] = typer.Option(
        None,
        "--style",
        metavar="STYLE",
        help="Style applied to the panel content.",
    ),
    border_style: Optional[str] = typer.Option(
        None,
        "--border-style",
        metavar="BORDER_STYLE",
        help="Style applied to the panel border.",
    ),
    padding: Optional[str] = typer.Option(
        None,
        "--padding",
        "-p",
        metavar="PADDING",
        help="Padding inside the panel (1, 2, or 4 comma-separated integers).",
    ),
    vertical_justify: VerticalJustifyOption = typer.Option(
        "top",
        "--vertical-justify",
        "-V",
        metavar="VERTICAL_JUSTIFY",
        case_sensitive=False,
        help="Vertical justification of the panel content.",
    ),
    text_justify: JustifyOption = typer.Option(
        "left",
        "--text-justify",
        "-J",
        metavar="TEXT_JUSTIFY",
        case_sensitive=False,
        help="Justification of the text inside the panel.",
    ),
    justify: JustifyOption = typer.Option(
        "left",
        "--justify",
        "-j",
        metavar="JUSTIFY",
        case_sensitive=False,
        help="Justification of the panel itself.",
    ),
    expand: bool = typer.Option(
        True,
        "--expand/--no-expand",
        "-e/-E",
        help="Expand the panel to fill the width of the console.",
    ),
    width: Optional[int] = typer.Option(
        None,
        "--width",
        metavar="WIDTH",
        help="Width of the panel (requires --no-expand).",
    ),
    height: Optional[int] = typer.Option(
        None,
        "--height",
        metavar="HEIGHT",
        help="Height of the panel.",
    ),
    end: str = typer.Option(
        "\n",
        "--end",
        metavar="END",
        help="String appended after the panel is printed.",
    ),
    box: BoxChoice = typer.Option(
        "ROUNDED",
        "--box",
        metavar="BOX",
        help="Box style for the panel border.",
    ),
    animate: bool = typer.Option(
        False,
        "--animate",
        help="Animate the panel gradient.",
    ),
    duration: float = typer.Option(
        5.0,
        "--duration",
        "-d",
        min=0.0,
        metavar="DURATION",
        help="Duration of the panel animation in seconds.",
    ),
) -> None:
    """Display text inside a gradient panel."""

    console = _create_console()
    text_value = _read_text_source(renderable)
    color_stops = _parse_color_stops(colors)
    bg_color_stops = _parse_color_stops(bgcolors)
    padding_values = _parse_padding(padding)

    if width is not None and expand:
        raise typer.BadParameter("--width requires --no-expand")

    title_style_source = ctx.get_parameter_source("title_style")
    title_align_source = ctx.get_parameter_source("title_align")
    subtitle_style_source = ctx.get_parameter_source("subtitle_style")
    subtitle_align_source = ctx.get_parameter_source("subtitle_align")

    if title is None and title_style_source not in DEFAULT_SOURCES and title_style:
        raise typer.BadParameter("--title-style requires --title to be set")
    if title is None and title_align_source not in DEFAULT_SOURCES:
        raise typer.BadParameter("--title-align requires --title to be set")
    if subtitle is None and subtitle_style_source not in DEFAULT_SOURCES and subtitle_style:
        raise typer.BadParameter("--subtitle-style requires --subtitle to be set")
    if subtitle is None and subtitle_align_source not in DEFAULT_SOURCES:
        raise typer.BadParameter("--subtitle-align requires --subtitle to be set")

    resolved_title_style = title_style or ("bold" if title else "")
    resolved_subtitle_style = subtitle_style or ""

    content = Align(
        RichText.from_markup(text_value, style=style or ""),
        align=text_justify,
    )

    try:
        panel_kwargs = dict(
            colors=color_stops,
            bg_colors=bg_color_stops,
            rainbow=rainbow,
            hues=hues,
            title=title,
            title_style=resolved_title_style,
            title_align=title_align,
            subtitle=subtitle,
            subtitle_style=resolved_subtitle_style,
            subtitle_align=subtitle_align,
            border_style=border_style or "",
            padding=padding_values,
            expand=expand,
            justify=justify,
            vertical_justify=vertical_justify,
            box=_parse_box_choice(box),
            style=style or "",
            width=width,
            height=height,
        )
        if animate:
            animation = AnimatedPanel(
                content,
                console=console,
                **panel_kwargs,
            )
            _run_animation(animation, duration)
        else:
            panel_renderable = GradientPanel(
                content,
                **panel_kwargs,
            )
            panel_renderable.console = console
            console.print(panel_renderable, end=end)
    except (ColorParseError, ValueError) as error:
        _handle_color_error(error)


@app.command("rule", cls=GradientCommand)
def rule_command(
    title: Optional[str] = typer.Option(
        None,
        "--title",
        "-t",
        metavar="TITLE",
        help="Title of the rule.",
    ),
    title_style: Optional[str] = typer.Option(
        None,
        "--title-style",
        "-s",
        metavar="TITLE_STYLE",
        help="Style applied to the rule title.",
    ),
    colors: Optional[str] = typer.Option(
        None,
        "--colors",
        "-c",
        metavar="COLORS",
        help="Comma-separated list of colours for the gradient.",
    ),
    bgcolors: Optional[str] = typer.Option(
        None,
        "--bgcolors",
        metavar="BGCOLORS",
        help="Comma-separated list of background colours for the gradient.",
    ),
    rainbow: bool = typer.Option(
        False,
        "--rainbow",
        "-r",
        help="Use rainbow colours for the gradient.",
    ),
    hues: int = typer.Option(
        10,
        "--hues",
        metavar="HUES",
        min=2,
        help="Number of hues for rainbow gradient.",
    ),
    end: str = typer.Option(
        "\n",
        "--end",
        metavar="END",
        help="String appended after the rule is printed.",
    ),
    thickness: RuleThickness = typer.Option(
        2,
        "--thickness",
        "-T",
        metavar="THICKNESS",
        help="Thickness of the rule line.",
    ),
    align: JustifyOption = typer.Option(
        "center",
        "--align",
        "-a",
        metavar="ALIGN",
        case_sensitive=False,
        help="Alignment of the rule in the console.",
    ),
    animate: bool = typer.Option(
        False,
        "--animate",
        help="Animate the rule gradient.",
    ),
    duration: float = typer.Option(
        5.0,
        "--duration",
        "-d",
        min=0.0,
        metavar="DURATION",
        help="Duration of the rule animation in seconds.",
    ),
) -> None:
    """Display a gradient rule in the console."""

    console = _create_console()
    color_stops = _parse_color_stops(colors)
    bg_color_stops = _parse_color_stops(bgcolors)

    try:
        if animate:
            animation = AnimatedRule(
                title=title,
                title_style=title_style or "bold",
                colors=color_stops,
                bg_colors=bg_color_stops,
                rainbow=rainbow,
                hues=hues,
                thickness=thickness,
                align=align,
                console=console,
                end=end,
            )
            _run_animation(animation, duration)
        else:
            rule_renderable = GradientRule(
                title=title,
                title_style=title_style or "bold",
                colors=color_stops,
                bg_colors=bg_color_stops,
                rainbow=rainbow,
                hues=hues,
                thickness=thickness,
                align=align,
                console=console,
                end=end,
            )
            console.print(rule_renderable)
    except (ColorParseError, ValueError) as error:
        _handle_color_error(error)


@app.command("markdown", cls=GradientCommand)
def markdown_command(
    markdown: Optional[str] = typer.Argument(
        None,
        metavar="MARKDOWN",
        help="Markdown text, file path, or '-' for stdin.",
    ),
    colors: Optional[str] = typer.Option(
        None,
        "--colors",
        "-c",
        metavar="COLORS",
        help="Comma-separated list of colours for the gradient.",
    ),
    bgcolors: Optional[str] = typer.Option(
        None,
        "--bgcolors",
        metavar="BGCOLORS",
        help="Comma-separated list of background colours for the gradient.",
    ),
    rainbow: bool = typer.Option(
        False,
        "--rainbow",
        "-r",
        help="Use rainbow colours for the gradient (overrides --colors).",
    ),
    hues: int = typer.Option(
        7,
        "--hues",
        metavar="HUES",
        min=2,
        help="The number of hues to use for a random gradient.",
    ),
    style: Optional[str] = typer.Option(
        None,
        "--style",
        metavar="STYLE",
        help="Base style applied to the markdown content.",
    ),
    justify: JustifyOption = typer.Option(
        "left",
        "--justify",
        "-j",
        metavar="JUSTIFY",
        case_sensitive=False,
        help="Justification of the markdown output.",
    ),
    overflow: OverflowOption = typer.Option(
        "fold",
        "--overflow",
        metavar="OVERFLOW",
        help="How to handle overflow of markdown text.",
    ),
    no_wrap: bool = typer.Option(
        False,
        "--no-wrap",
        help="Disable wrapping of markdown text.",
    ),
    end: str = typer.Option(
        "\n",
        "--end",
        metavar="END",
        help="String appended after the markdown text is printed.",
    ),
    animate: bool = typer.Option(
        False,
        "--animate",
        help="Animate the gradient markdown text.",
    ),
    duration: float = typer.Option(
        5.0,
        "--duration",
        "-d",
        min=0.0,
        metavar="DURATION",
        help="Duration of the animation in seconds.",
    ),
) -> None:
    """Render markdown text with gradient colours in the console."""

    console = _create_console()
    markdown_value = _read_text_source(markdown)
    color_stops = _parse_color_stops(colors)
    bg_color_stops = _parse_color_stops(bgcolors)

    rich_markdown = RichMarkdown(markdown_value, style=style or "")
    aligned_renderable: RenderableType = Align(
        rich_markdown,
        align=justify,
    )

    try:
        if animate:
            animation = AnimatedGradient(
                renderables=aligned_renderable,
                colors=color_stops,
                bg_colors=bg_color_stops,
                rainbow=rainbow,
                hues=hues,
                console=console,
                justify=justify,
                expand=True,
            )
            _run_animation(animation, duration)
        else:
            gradient_renderable = Gradient(
                aligned_renderable,
                colors=color_stops,
                bg_colors=bg_color_stops,
                console=console,
                rainbow=rainbow,
                hues=hues,
                justify=justify,
                expand=True,
            )
            console.print(
                gradient_renderable,
                end=end,
                overflow=overflow,
                no_wrap=True if no_wrap else None,
            )
    except (ColorParseError, ValueError) as error:
        _handle_color_error(error)


def main() -> None:
    """Execute the Typer application."""

    app()


if __name__ == "__main__":
    main()
