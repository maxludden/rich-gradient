"""Panel command wiring for the CLI."""

from __future__ import annotations

import sys
from typing import Any, Optional, Tuple, cast

import rich_click as click
from rich.align import Align, AlignMethod, VerticalAlignMethod
from rich.text import Text as RichText

from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.panel import Panel
from rich_gradient.text import Text

from .common import console, parse_colors, parse_style


@click.command("panel", help="Display text inside a gradient panel.")
@click.argument("renderable", metavar="RENDERABLE", nargs=1, required=True)
@click.option(
    "-c",
    "--colors",
    metavar="COLORS",
    type=str,
    default=None,
    help="Comma-separated list of colors for the gradient. [dim](e.g., \
`[/][red]red[/][dim], [/][#ff9900]#ff9900[/][dim], [/][yellow]yellow[/][dim]`). \
If no colors are provided, the color stops are automatically generated.",
)
@click.option(
    "--bgcolors",
    metavar="BGCOLORS",
    type=str,
    default=None,
    help="Comma-separated list of background colors for the gradient. [dim](e.g., \
`[/][red]red[/][dim],[/][#ff9900]#ff9900[/][dim],[/][#ff0]#ff0[/][dim]`). \
Defaults to [/][bold #fff]transparent[/][dim].[/dim]",
)
@click.option(
    "-r",
    "--rainbow",
    is_flag=True,
    default=False,
    help="[#ff0000]U[/][#ff3b00]s[/][#ff5100]e[/][#ff7400] [/]\
[#ff9000]r[/][#ffa900]a[/][#ffc000]i[/][#ffd700]n[/]\
[#ffee00]b[/][#f7ff00]o[/][#d3ff00]w[/][#a7ff00] [/] \
[#7dff00]c[/][#2eff00]o[/][#00ff64]l[/][#00ff8e]o[/][#00ffc0]r[/]\
[#00ffec]s[/][#00f4ff] [/][#00ddff]f[/][#00c5ff]o[/][#00afff]r[/]\
[#1596ff] [/][#3b81ff]t[/][#4e67ff]h[/][#675fff]e[/][#7b57ff] [/]\
[#924bff]g[/][#a73bff]r[/][#c72cff]a[/][#eb1cff]d[/][#ff00f2]i[/]\
[#ff00ce]e[/][#ff00a4]n[/][#ff0084]t[/][#ff0054].[/]"
)
@click.option(
    "--hues",
    metavar="HUES",
    type=int,
    default=5,
    help="The number of hues to use for a random gradient.",
    show_default=True,
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
    help="Alignment of the panel title. [lime](left, center, right)[/]",
    show_default=True,
)
@click.option(
    "-s",
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
    help="Alignment of the panel subtitle. [lime](left, center, right)[/]",
    show_default=True,
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
    help="The style to apply to the panel border. [dim italic]*Only non-color \
styles will be applied as the gradient's colors override color styles.[/]",
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
    help="Vertical justification of the panel inner text. [lime](top, middle, bottom)[/]",
    show_default=True,
)
@click.option(
    "-J",
    "--text-justify",
    metavar="TEXT_JUSTIFY",
    type=click.Choice(["left", "center", "right"], case_sensitive=False),
    default="left",
    help="Justification of the text inside the panel. [lime](left, center, right)[/]",
    show_default=True,
)
@click.option(
    "-j",
    "--justify",
    metavar="JUSTIFY",
    type=click.Choice(
        ["left", "center", "right"],
        case_sensitive=False,
    ),
    default="left",
    help="Justification of the panel itself. [lime](left, center, right)[/]",
    show_default=True,
)
@click.option(
    "-e/-E",
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
    help="String appended after the text is printed. [dim]\\[default: '\\n'][/dim]",
)
@click.option(
    "--box",
    metavar="BOX",
    type=click.Choice(
        ["SQUARE", "ROUNDED", "HEAVY", "DOUBLE", "ASCII"],
        case_sensitive=False
    ),
    default="ROUNDED",
    help="Box style for the panel border. [dim](e.g., SQUARE, ROUNDED, \
HEAVY, DOUBLE, ASCII).[/dim]",
)
@click.option(
    "-a", "--animate", is_flag=True, default=False, help="Animate the panel gradient."
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
    fg_list = parse_colors(colors)
    bg_list = parse_colors(bgcolors)
    style_obj = parse_style(style)
    _text_justify = cast(AlignMethod, text_justify)
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

    if animate and console.is_terminal is True:
        # console.clear()
        animated_panel: AnimatedPanel = AnimatedPanel(
            Align(renderable, align=_text_justify),
            colors=cast(Any, fg_list),
            rainbow=rainbow,
            hues=hues,
            bg_colors=cast(Any, bg_list),
            title=title,
            title_style=parse_style(title_style),
            title_align=cast(AlignMethod, title_align),
            subtitle=subtitle,
            subtitle_style=parse_style(subtitle_style),
            subtitle_align=cast(AlignMethod, subtitle_align),
            style=style_obj,
            border_style=parse_style(border_style),
            padding=cast(Any, padding_tuple),
            vertical_justify=cast(Any, vertical_justify),
            justify=cast(AlignMethod, justify),
            expand=expand,
            width=width,
            height=height,
            box=box_style,
            animate=True,
            duration=duration,
        )
        animated_panel.run()
        sys.exit(0)

    panel = Panel(
        Align(renderable, align=_text_justify),
        colors=cast(Any, fg_list),
        rainbow=rainbow,
        hues=hues,
        bg_colors=cast(Any, bg_list),
        title=title,
        title_style=parse_style(title_style),
        title_align=cast(AlignMethod, title_align),
        subtitle=subtitle,
        subtitle_style=parse_style(subtitle_style),
        subtitle_align=cast(AlignMethod, subtitle_align),
        style=style_obj,
        border_style=parse_style(border_style),
        padding=cast(Any, padding_tuple),
        vertical_justify=cast(Any, vertical_justify),
        justify=cast(AlignMethod, justify),
        expand=expand,
        width=width,
        height=height,
        box=box_style,
    )
    console.print(panel, end=end)


__all__ = ["panel_command"]
