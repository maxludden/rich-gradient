"""CLI module for rich-gradient."""

from __future__ import annotations

import io
from typing import Any, List, Optional, Tuple, cast

import click
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.style import Style, StyleType
from rich.text import Text as RichText
from rich.align import AlignMethod, VerticalAlignMethod

from rich_gradient.markdown import Markdown, AnimatedMarkdown
from rich_gradient.panel import Panel
from rich_gradient.rule import Rule
from rich_gradient.text import Text

console = Console()
VERSION = "1.0.0"


def _parse_colors(colors: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated color strings into a list of color specifiers."""
    if colors is None:
        return None
    return [c.strip() for c in colors.split(",") if c.strip()]


def _parse_style(style: Optional[str]) -> Style:
    """Parse a style string into a Rich Style or return null style."""
    if style is None:
        return Style.null()
    return Style.parse(style)


class GradientHelpCommand(click.Command):
    """Click Command that displays help via a GradientPanel."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        sio = io.StringIO()
        temp_console = Console(file=sio, force_terminal=True, width=formatter.width)
        temp_console.print(ctx.get_help())
        captured = sio.getvalue()
        panel = Panel(
            RichText.from_markup(captured), title=ctx.command_path, expand=False
        )
        console.print(panel)


class GradientHelpGroup(click.Group):
    """Click Group that displays help via a rich-gradient Panel."""

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        sio = io.StringIO()
        temp_console = Console(file=sio, force_terminal=True, width=formatter.width)
        temp_console.print(ctx.get_help())
        captured = sio.getvalue()
        panel = Panel(
            RichText.from_markup(captured), title=ctx.command_path, expand=False
        )
        console.print(panel)


@click.group(
    cls=GradientHelpGroup,
    command_class=GradientHelpCommand,
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"]),
    help="A CLI for rich-gradient: create beautiful gradient-rich output with Rich.",
)
@click.version_option(version=VERSION, message="%(prog)s version %(version)s")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """rich-gradient CLI tool. Use subcommands to print gradients, panels, rules, or markdown."""
    if ctx.invoked_subcommand is None:
        panel = Panel(RichText.from_markup(ctx.get_help()))
        console.print(panel)


# ── Print command ───────────────────────────────────────────────────────────
@cli.command("print", cls=GradientHelpCommand, help="Print text in gradient color.")
@click.argument("text", nargs=-1, required=True)
@click.option(
    "-c",
    "--colors",
    metavar="COLORS",
    type=str,
    default=None,
    help="parse a comma separated string of colors (e.g., 'red,#ff9900,yellow').",
)
@click.option(
    "-r",
    "--rainbow",
    is_flag=True,
    default=False,
    help="print text in rainbow colors (overrides --colors if set).",
)
@click.option(
    "-h",
    "--hues",
    metavar="HUES",
    type=int,
    default=7,
    help="The number of hues to use for a random gradient.",
)
@click.option(
    "--style",
    metavar="STYLE",
    type=str,
    default=None,
    help="The style to apply to the text.",
)
@click.option(
    "-j",
    "--justify",
    metavar="JUSTIFY",
    type=click.Choice(["left", "center", "right"], case_sensitive=False),
    default="left",
    help="Justification of the text.",
)
@click.option(
    "--overflow",
    metavar="OVERFLOW",
    type=click.Choice(["crop", "fold", "ellipsis"], case_sensitive=False),
    default="fold",
    help="How to handle overflow of text.",
)
@click.option(
    "--no-wrap", is_flag=True, default=False, help="Disable wrapping of text."
)
@click.option(
    "--end",
    metavar="END",
    type=str,
    default="\n",
    help="String appended after the text is printed.",
)
@click.option(
    "--bgcolors",
    metavar="BGCOLORS",
    type=str,
    default=None,
    help="parse a comma separated string of background colors.",
)
def print_command(
    text: Tuple[str, ...],
    colors: Optional[str],
    rainbow: bool,
    hues: int,
    style: Optional[str],
    justify: str,
    overflow: str,
    no_wrap: bool,
    end: str,
    bgcolors: Optional[str]
) -> None:
    """Print text in gradient color to the console."""
    content = " ".join(text)
    fg_list = _parse_colors(colors)
    bg_list = _parse_colors(bgcolors)
    style_obj = _parse_style(style)
    gradient = Text(
        content,
        colors=fg_list,
        rainbow=rainbow,
        hues=hues,
        style=style_obj,
        justify=cast(JustifyMethod, justify),
        overflow=cast(OverflowMethod, overflow),
        end=end,
        no_wrap=no_wrap,
        bgcolors=bg_list
    )
    console.print(gradient)


# ── Panel command ───────────────────────────────────────────────────────────
@cli.command(
    "panel", cls=GradientHelpCommand, help="Display text inside a gradient panel."
)
@click.argument("renderable", metavar="RENDERABLE", nargs=1, required=True)
@click.option(
    "-c",
    "--colors",
    metavar="COLORS",
    type=str,
    default=None,
    help="Comma-separated list of colors for the gradient (e.g., `red,#ff9900,yellow`).",
)
@click.option(
    "--bgcolors",
    metavar="BGCOLORS",
    type=str,
    default=None,
    help="Comma-separated list of background colors for the gradient (e.g., `red,#ff9900,yellow`).",
)
@click.option(
    "-r",
    "--rainbow",
    is_flag=True,
    default=False,
    help="Use rainbow colors for the gradient. Overrides -c/--colors if set.",
)
@click.option(
    "--hues",
    metavar="HUES",
    type=int,
    default=5,
    help="Number of hues for rainbow gradient.",
)
@click.option(
    "-t", "--title", metavar="TITLE", type=str, default=None, help="Title of the panel."
)
@click.option(
    "--title-style",
    metavar="TITLE_STYLE",
    type=str,
    default="bold",
    help="Style of the panel title text (requires -t/--title).",
)
@click.option(
    "--title-align",
    metavar="TITLE_ALIGN",
    type=click.Choice(["left", "center", "right"], case_sensitive=False),
    default="center",
    help="Alignment of the panel title (requires -t/--title).",
)
@click.option(
    "--subtitle",
    metavar="SUBTITLE",
    type=str,
    default=None,
    help="Subtitle of the panel.",
)
@click.option(
    "--subtitle-style",
    metavar="SUBTITLE_STYLE",
    type=str,
    default=None,
    help="Style of the panel subtitle text (requires --subtitle).",
)
@click.option(
    "--subtitle-align",
    metavar="SUBTITLE_ALIGN",
    type=click.Choice(["left", "center", "right"], case_sensitive=False),
    default="right",
    help="Alignment of the panel subtitle (requires --subtitle).",
)
@click.option(
    "--style",
    metavar="STYLE",
    type=str,
    default=None,
    help="The style to apply to the panel.",
)
@click.option(
    "--border-style",
    metavar="BORDER_STYLE",
    type=str,
    default=None,
    help="The style to apply to the panel border.",
)
@click.option(
    "-p",
    "--padding",
    metavar="PADDING",
    type=str,
    default="0,1",
    help="Padding inside the panel (1, 2, or 4 comma-separated integers).",
)
@click.option(
    "-V",
    "--vertical-justify",
    metavar="VERTICAL_JUSTIFY",
    type=click.Choice(["top", "middle", "bottom"], case_sensitive=False),
    default="top",
    help="Vertical justification of the panel inner text.",
)
@click.option(
    "-J",
    "--text-justify",
    metavar="TEXT_JUSTIFY",
    type=click.Choice(["left", "center", "right"], case_sensitive=False),
    default="left",
    help="Justification of the text inside the panel.",
)
@click.option(
    "-j",
    "--justify",
    metavar="JUSTIFY",
    type=click.Choice(["left", "center", "right"], case_sensitive=False),
    default="left",
    help="Justification of the panel itself.",
)
@click.option(
    "-e/--no-expand",
    "--expand/--no-expand",
    is_flag=True,
    default=True,
    help="Whether to expand the panel to fill the width.",
)
@click.option(
    "--width",
    metavar="WIDTH",
    type=int,
    default=None,
    help="Width of the panel (requires --no-expand if set).",
)
@click.option(
    "--height",
    metavar="HEIGHT",
    type=int,
    default=None,
    help="Height of the panel; content determines by default.",
)
@click.option(
    "--end",
    metavar="END",
    type=str,
    default="\n",
    help="String appended after the panel is printed.",
)
@click.option(
    "--box",
    metavar="BOX",
    type=click.Choice(
        ["SQUARE", "ROUNDED", "HEAVY", "DOUBLE", "ASCII"], case_sensitive=False
    ),
    default="ROUNDED",
    help="Box style for the panel border.",
)
@click.option(
    "--animate", is_flag=True, default=False, help="Animate the panel gradient."
)
@click.option(
    "-d",
    "--duration",
    metavar="DURATION",
    type=float,
    default=5.0,
    help="Duration of the panel animation in seconds (only used if --animate).",
)
def panel_command(
    renderable: str,
    colors: Optional[str],
    bgcolors: Optional[str],
    rainbow: bool,
    hues: int,
    title: Optional[str],
    title_style: str,
    title_align: str,
    subtitle: Optional[str],
    subtitle_style: Optional[str],
    subtitle_align: str,
    style: Optional[str],
    border_style: Optional[str],
    padding: Optional[str],
    vertical_justify: str,
    text_justify: str,
    justify: str,
    expand: bool,
    width: Optional[int],
    height: Optional[int],
    end: str,
    box: str,
    animate: bool,
    duration: float,
) -> None:
    """Display a renderable inside a gradient panel."""
    fg_list = _parse_colors(colors)
    bg_list = _parse_colors(bgcolors)
    style_obj = _parse_style(style)
    _text_justify = cast(JustifyMethod, text_justify)
    padding_tuple: Optional[Tuple[int, ...]] = None
    if padding:
        padding_tuple = tuple(int(x) for x in padding.split(",") if x.strip())

    from rich import box as rich_box

    box_map: dict[str, Any] = {
        "SQUARE": rich_box.SQUARE,
        "ROUNDED": rich_box.ROUNDED,
        "HEAVY": rich_box.HEAVY,
        "DOUBLE": rich_box.DOUBLE,
        "ASCII": rich_box.ASCII,
    }
    box_style = box_map.get(box.upper(), rich_box.ROUNDED)

    panel = Panel(
        renderable,
        colors=cast(Any, fg_list),
        rainbow=rainbow,
        hues=hues,
        bg_colors=cast(Any, bg_list),
        title=title,
        title_style=_parse_style(title_style),
        title_align=cast(AlignMethod, title_align),
        subtitle=subtitle,
        subtitle_style=_parse_style(subtitle_style),
        subtitle_align=cast(AlignMethod, subtitle_align),
        style=style_obj,
        border_style=_parse_style(border_style),
        padding=cast(Any, padding_tuple),
        vertical_justify=cast(Any, vertical_justify),
        justify=cast(AlignMethod, justify),
        text_justify=cast(AlignMethod, text_justify),
        expand=expand,
        width=width,
        height=height,
        box=box_style,
    )
    console.print(panel, end=end)


# ── Rule command ───────────────────────────────────────────────────────────
@cli.command(
    "rule", cls=GradientHelpCommand, help="Display a gradient rule in the console."
)
@click.option(
    "-t", "--title", metavar="TITLE", type=str, default=None, help="Title of the rule."
)
@click.option(
    "-s",
    "--title-style",
    metavar="TITLE_STYLE",
    type=str,
    default=None,
    help="The style of the rule’s title text.",
)
@click.option(
    "-c",
    "--colors",
    metavar="COLORS",
    type=str,
    default=None,
    help="Comma-separated list of colors for the gradient (e.g., `red,#ff9900,yellow`).",
)
@click.option(
    "--bgcolors",
    metavar="BGCOLORS",
    type=str,
    default=None,
    help="Comma-separated list of background colors for the gradient.",
)
@click.option(
    "-r",
    "--rainbow",
    is_flag=True,
    default=False,
    help="Use rainbow colors for the gradient (overrides --colors).",
)
@click.option(
    "--hues",
    metavar="HUES",
    type=int,
    default=10,
    help="Number of hues for rainbow gradient.",
)
@click.option(
    "--end",
    metavar="END",
    type=str,
    default="\n",
    help="String appended after the rule is printed.",
)
@click.option(
    "-T",
    "--thickness",
    metavar="THICKNESS",
    type=int,
    default=2,
    help="Thickness of the rule line (choices 0-3).",
)
@click.option(
    "-a",
    "--align",
    metavar="ALIGN",
    type=click.Choice(["left", "center", "right"], case_sensitive=False),
    default="center",
    help="Alignment of the rule in the console.",
)
def rule_command(
    title: Optional[str],
    title_style: Optional[str],
    colors: Optional[str],
    bgcolors: Optional[str],
    rainbow: bool,
    hues: int,
    end: str,
    thickness: int,
    style: Optional[str],
    align: str,
) -> None:
    """Display a gradient rule in the console."""
    _colors = _parse_colors(colors)
    _bgcolors = _parse_colors(bgcolors)
    _title_style = _parse_style(title_style)
    _style = _parse_style(style)

    rule = Rule(
        title=title or "",
        title_style=_title_style,
        colors=_colors,
        rainbow=rainbow,
        hues=hues,
        bg_colors=_bgcolors,
        thickness=thickness,
        end=end,
        style=_style,
        align=cast(AlignMethod, align)
    )
    console.print(rule)


# ── Markdown command ─────────────────────────────────────────────────────────
@cli.command(
    "markdown",
    cls=GradientHelpCommand,
    help="Render markdown text with gradient colors.",
)
@click.argument("markdown", nargs=1, type=str, required=True, metavar="MARKDOWN")
@click.option(
    "-c",
    "--colors",
    metavar="COLORS",
    type=str,
    default=None,
    help="Comma-separated list of colors for the gradient (e.g., `red,#ff9900,yellow`).",
)
@click.option(
    "--bgcolors",
    metavar="BGCOLORS",
    type=str,
    default=None,
    help="Comma-separated list of background colors for the gradient.",
)
@click.option(
    "-r",
    "--rainbow",
    is_flag=True,
    default=False,
    help="Use rainbow colors for the gradient (overrides --colors).",
)
@click.option(
    "--hues",
    metavar="HUES",
    type=int,
    default=7,
    help="Number of hues for rainbow gradient.",
)
@click.option(
    "--style",
    metavar="STYLE",
    type=str,
    default=None,
    help="The style to apply to the markdown text.",
)
@click.option(
    "-j",
    "--justify",
    metavar="JUSTIFY",
    type=click.Choice(["left", "center", "right"], case_sensitive=False),
    default="left",
    help="Justification of the markdown text.",
)
@click.option(
    "--vertical-justify",
    metavar="VERTICAL_JUSTIFY",
    type=click.Choice(["top", "middle", "bottom"], case_sensitive=False),
    default="top",
    help="Vertical justification of the markdown text.",
)
@click.option(
    "--overflow",
    metavar="OVERFLOW",
    type=click.Choice(["crop", "fold", "ellipsis"], case_sensitive=False),
    default="fold",
    help="How to handle overflow of markdown text.",
)
@click.option(
    "--no-wrap", is_flag=True, default=False, help="Disable wrapping of markdown text."
)
@click.option(
    "--end",
    metavar="END",
    type=str,
    default="\n",
    help="String appended after the markdown text is printed.",
)
@click.option(
    "--animate", is_flag=True, default=False, help="Animate the gradient markdown text."
)
@click.option(
    "-d",
    "--duration",
    metavar="DURATION",
    type=float,
    default=5.0,
    help="Duration of the animation in seconds (only used if --animate).",
)
def markdown_command(
    markdown: str,
    colors: Optional[str],
    bgcolors: Optional[str],
    rainbow: bool,
    hues: int,
    justify: str,
    vertical_justify: str,
    end: str,
    animate: bool,
    duration: float,
) -> None:
    """Render markdown text with gradient colors in a rich console."""
    _colors = _parse_colors(colors)
    _bgcolors = _parse_colors(bgcolors)

    if animate and console.is_terminal is True:
        console.clear()
        md = AnimatedMarkdown(
            markdown,
            colors=_colors,
            rainbow=rainbow,
            hues=hues,
            justify=cast(AlignMethod, justify),
            vertical_justify=cast(VerticalAlignMethod, vertical_justify),
            bg_colors=_bgcolors,
        )
    md = Markdown(
        markdown,
        colors=_colors,
        rainbow=rainbow,
        hues=hues,
        justify=cast(AlignMethod, justify),
        bg_colors=_bgcolors,
        animate=animate,
        duration=duration,
    )
    console.print(md, end=end)


if __name__ == "__main__":
    cli()
