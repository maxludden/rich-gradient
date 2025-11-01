"""CLI command to display text inside a gradient panel."""

# pylint: disable=W0611
from __future__ import annotations

from time import sleep
from typing import Annotated, Any, List, Literal, Optional, Tuple, cast

import rich
import click
import typer
from rich.align import Align
from rich.console import Console, JustifyMethod
from rich.rule import Rule
from rich.text import Text as RichText
from rich.traceback import install as tr_install
from rich_color_ext import install as rc_install
from typer import Argument, Option, Typer

from rich_gradient._cli.common import (
    RichGradientCommand,
    colors_callback,
    justify_callback,
    parse_padding,
    read_text_source,
    run_animation,
    validate_duration,
)
from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.panel import Panel
from rich_gradient.text import Text
from rich_gradient.theme import GradientTheme

rc_install()
tr_install()
console = Console(theme=GradientTheme())

panel_app = Typer(
    name="panel",
    rich_markup_mode="rich",
)

# def _render_panel_help() -> None:
#     """Render the custom help screen for the panel subcommand."""
#     console.line()
#     console.print(
#         Align.center(
#             Text("rich-gradient panel", style="bold magenta"),
#             vertical="middle",
#         )
#     )
#     console.line()
#     console.print(
#         Align.center(
#             RichText("Display input in a gradient panel.", style="white"),
#             vertical="middle",
#         )
#     )

#     help_args = HelpTable(
#         name="Arguments",
#         rows=[
#             HelpRow(
#                 short="",
#                 long="text",
#                 invert_short="",
#                 invert_long="",
#                 variable="[TEXT]",
#                 description="The text to display inside the panel or '-' for stdin",
#             )
#         ],
#     )
#     console.print(help_args.render)
#     help_options = HelpTable(name="Options", rows=rows)
#     console.print(help_options.render)


# def _panel_help_callback() -> None:
#     """
#     Callback for `--help` in the `panel` subcommand. Prints custom help and exits.
#     """

#     _render_panel_help()
#     raise typer.Exit()


@panel_app.command(
    name="panel",
    no_args_is_help=True,
    context_settings={"help_option_names": ["--help"]},
)
def panel_command(
    text: Annotated[
        str,
        Argument(help="The text to display inside the panel or '-' for stdin"),
    ] = "",
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
            "-r/-R",
            "--rainbow/--no-rainbow",
            help="Use rainbow colors for the gradient. Overrides -c/--colors if set.",
            rich_help_panel="Panel Color Options",
            is_flag=True,
        ),
    ] = False,
    hues: Annotated[
        int,
        Option(
            "-h",
            "--hues",
            help="Number of hues for rainbow gradient",
            rich_help_panel="Panel Color Options",
        ),
    ] = 7,
    padding: Annotated[
        Optional[str],
        Option(
            "-p",
            "--padding",
            help="Padding inside the panel (1, 2, or 4 comma-separated integers).",
            rich_help_panel="Panel Inner Options",
        ),
    ] = "0,1",
    justify: Annotated[
        str,
        Option(
            "-j",
            "--justify",
            callback=justify_callback,
            help="Justification of the panel itself",
        ),
    ] = "left",
    text_justify: Annotated[
        str,
        Option(
            "-J",
            "--text-justify",
            callback=justify_callback,
            help="Justification of the panel inner text",
        ),
    ] = "left",
    expand: Annotated[
        bool,
        Option(
            "-e/-E",
            "--expand/--no-expand",
            help="Whether to expand the panel to fill the width of the console",
            is_flag=True,
        ),
    ] = True,
    width: Annotated[
        Optional[int],
        Option(
            "-w",
            "--width",
            help="Width of the panel. (requires --no-expand)",
        ),
    ] = None,
    subtitle: Annotated[
        Optional[str],
        Option(
            "-s",
            "--subtitle",
            help="Subtitle of the panel",
            rich_help_panel="Panel Subtitle Options",
        ),
    ] = None,
    title: Annotated[
        Optional[str],
        Option(
            "-t",
            "--title",
            help="Title of the panel",
            rich_help_panel="Panel Title Options",
        ),
    ] = None,
    title_style: Annotated[
        str,
        Option(
            "--title-style",
            help="Style of the panel title text (requires -t/--title)",
            rich_help_panel="Panel Title Options",
        ),
    ] = "bold",
    title_align: Annotated[
        Literal["left", "center", "right"],
        Option(
            "--title-align",
            help="Alignment of the panel title (requires -t/--title)",
            rich_help_panel="Panel Title Options",
            callback=justify_callback,
        ),
    ] = "center",
    subtitle_style: Annotated[
        str,
        Option(
            "--subtitle-style",
            help="Style of the panel subtitle text (requires -s/--subtitle)",
            rich_help_panel="Panel Subtitle Options",
        ),
    ] = "",
    subtitle_align: Annotated[
        Literal["left", "center", "right"],
        Option(
            "--subtitle-align",
            help="Alignment of the panel subtitle (requires -s/--subtitle)",
            callback=justify_callback,
            rich_help_panel="Panel Subtitle Options",
        ),
    ] = "right",
    animated: Annotated[
        bool,
        Option(
            "-a",
            "--animated",
            help="Animate the gradient panel.",
            is_flag=True,
            rich_help_panel="Panel Animation Options",
        ),
    ] = False,
    duration: Annotated[
        float,
        Option(
            "-d",
            "--duration",
            callback=validate_duration,
            help="Length of the animation in seconds (requires --animated).",
            rich_help_panel="Panel Animation Options",
        ),
    ] = 10.0,
):
    """Display input in a gradient panel.
    Args:
        text: The text to display inside the panel or '-' for stdin.
    Options:
        - `-c`, `--colors`: Comma-separated list of colors for the gradient.
        - `-t`, `--title`: Title of the panel.
        - `-s`, `--title-style`: Style of the title text.
        - `-a`, `--title-align`: Alignment of the title text.
        - `-R`, `--rainbow`: Use rainbow colors for the gradient.
        - `-u`, `--hues`: Number of hues for rainbow gradient.
        - `-p`, `--padding`: Padding inside the panel (1, 2, or 4 comma-separated integers).
        - `-j`, `--justify`: Justification of the panel title.
        - `-J`, `--text-justify`: Justification of the panel text.
        -       `--expand/--no-expand`: Whether to expand the panel to fill \
the width of the console.
        - `-w`, `--width`: Width of the panel.
        - `-S`, `--subtitle`: Subtitle of the panel.
        - `-B`, `--subtitle-style`: Style of the subtitle text.
        - `-A`, `--subtitle-align`: Alignment of the subtitle text.
        - `-a`, `--animated`: Animate the gradient panel.
        - `-d`, `--duration`: Length of the animation in seconds (requires --animated).
        -       `--help`: Show this message and exit.
    """
    # parse input
    source_value = RichText.from_markup(text).plain
    if source_value is None:
        # Provide a friendly default demo when no input is supplied
        content = "Panels can frame gradient text for call-outs and highlights."
        if title is None:
            title = "Gradient Panel"
    else:
        content = read_text_source(source_value)

    # parse colors
    _colors = colors if colors else None

    # parse padding
    parsed_padding: Optional[Tuple[int, ...]] = None
    if padding is not None:
        try:
            parsed_padding = parse_padding(padding)
        except ValueError as error:
            raise typer.BadParameter(str(error)) from error
    panel_kwargs: dict[str, Any] = {}
    if parsed_padding is not None:
        panel_kwargs["padding"] = tuple(parsed_padding)

    # prepare inner renderable
    try:
        inner_renderable = RichText.from_markup(
            content, justify=cast(JustifyMethod, text_justify)
        )
    except Exception as error:
        raise typer.BadParameter(f"invalid markup: {error}") from error

    _justify = cast(Any, justify)

    if animated:
        try:
            animation = AnimatedPanel(
                inner_renderable,
                title=title,
                title_style=title_style,
                title_align=title_align,
                colors=cast(Any, _colors),
                rainbow=rainbow,
                hues=hues,
                subtitle=subtitle,
                subtitle_style=subtitle_style,
                subtitle_align=subtitle_align,
                justify=_justify,
                expand=expand,
                width=width,
                console=console,
                **panel_kwargs,
            )
        except ValueError as error:
            raise typer.BadParameter(str(error)) from error
        animation.run()
        sleep(duration)
        return

    try:
        gradient_panel = Panel(
            inner_renderable,
            title=title,
            title_style=title_style,
            title_align=title_align,
            colors=cast(Any, _colors),
            rainbow=rainbow,
            hues=hues,
            subtitle=subtitle,
            subtitle_style=subtitle_style,
            subtitle_align=subtitle_align,
            justify=_justify,
            expand=expand,
            width=width,
            **panel_kwargs,
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    console.print(gradient_panel, justify=_justify)
