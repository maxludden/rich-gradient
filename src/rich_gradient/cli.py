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

from click.core import ParameterSource

from rich_gradient import __version__
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

JustifyOption = Literal["left", "center", "right"]
VerticalJustifyOption = Literal["top", "middle", "bottom"]
OverflowOption = Literal["crop", "fold", "ellipsis"]
RuleThickness = Literal[0, 1, 2, 3]
BoxChoice = Literal["SQUARE", "ROUNDED", "HEAVY", "DOUBLE", "ASCII"]

def _version_callback(value: bool) -> bool:
    """Display package version when requested."""

    if value:
        from rich_gradient import __version__  # pylint: disable=import-outside-toplevel

        console.print(Text(__version__))
        raise typer.Exit()
    return value

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

def _parse_color_stops(spec: Optional[str]) -> Optional[list[str]]:
    """Split a comma-separated colour specification into individual stops."""

    if spec is None:
        return None
    stops = [part.strip() for part in spec.split(",") if part.strip()]
    if not stops:
        raise typer.BadParameter("provide at least one colour stop")
    return stops

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

def _parse_padding(value: Optional[str]) -> tuple[int, int, int, int]:
    """Parse padding strings (``"1"``, ``"2,4"``, ``"1,2,3,4"``) into a 4-tuple."""

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
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(gradient_rule)


if __name__ == "__main__":
    main()
