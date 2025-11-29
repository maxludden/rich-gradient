"""Text/print command wiring for the CLI."""

from __future__ import annotations

from typing import Optional, Tuple, cast

import rich_click as click
from rich.align import AlignMethod
from rich.console import JustifyMethod, OverflowMethod

from rich_gradient.text import Text

from .common import console, parse_colors, parse_style


@click.command("print", help="Print text in gradient color.")
@click.argument("text", nargs=-1, required=True)
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
[#ff00ce]e[/][#ff00a4]n[/][#ff0084]t[/][#ff0054].[/]",
)
@click.option(
    "-h",
    "--hues",
    metavar="HUES",
    type=int,
    default=7,
    help="The number of hues to use for a random gradient.",
    show_default=True,
)
@click.option(
    "--style",
    metavar="STYLE",
    type=str,
    default=None,
    help="The style to apply to the text. [dim italic]*Only non-color \
styles will be applied as the gradient's colors override color styles.[/]",
)
@click.option(
    "-j",
    "--justify",
    metavar="JUSTIFY",
    type=click.Choice(["left", "center", "right"], case_sensitive=False),
    default="left",
    help="Justification of the text. [lime](left, center, right)[/]",
    show_default=True,
)
@click.option(
    "--overflow",
    metavar="OVERFLOW",
    type=click.Choice(["crop", "fold", "ellipsis"], case_sensitive=False),
    default="fold",
    help="How to handle overflow of text. [lime](crop, fold, ellipsis)[/]",
    show_default=True,
)
@click.option(
    "--no-wrap",
    is_flag=True,
    default=False,
    help="Disable wrapping of text.",
    show_default=True,
)
@click.option(
    "--end",
    metavar="END",
    type=str,
    default="\n",
    help="String appended after the text is printed. [dim]\\[default: '\\n'][/dim]",
)
@click.option(
    "--bgcolors",
    metavar="BGCOLORS",
    type=str,
    default=None,
    help="Optional comma separated string of background colors. [dim]If not provided, \
background is transparent.[/]",
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
    bgcolors: Optional[str],
) -> None:
    """Print text in gradient color to the console."""
    content = " ".join(text)
    fg_list = parse_colors(colors)
    bg_list = parse_colors(bgcolors)
    style_obj = parse_style(style)
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
        bg_colors=bg_list,
    )
    console.print(gradient)


__all__ = ["print_command"]
