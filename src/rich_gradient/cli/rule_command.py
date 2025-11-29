"""Rule command wiring for the CLI."""

from __future__ import annotations

from typing import Optional, cast

import rich_click as click
from rich.align import AlignMethod

from rich_gradient.rule import Rule

from .common import console, parse_colors, parse_style


@click.command("rule", help="Display a gradient rule in the console.")
@click.option("-t", "--title", metavar="TITLE", type=str, default=None, help="Title of the rule.")
@click.option(
    "-s",
    "--title-style",
    metavar="TITLE_STYLE",
    type=str,
    default=None,
    help="The style of the rule's title text. [dim italic]*Only non-color \
styles will be applied as the gradient's colors override color styles.[/]",
)
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
`[/][red]red[/][dim], [/][#ff9900]#ff9900[/][dim], [/][#ff0]#ff0[/][dim]`). \
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
[#ff00ce]e[/][#ff00a4]n[/][#ff0084]t[/][#ff0054].[/]",
)
@click.option(
    "--hues",
    metavar="HUES",
    type=int,
    default=10,
    help="The number of hues to use for a random gradient.",
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
    help="Alignment of the rule in the console. [lime](left, center, right)[/]",
    show_default=True,
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
    align: str,
) -> None:
    """Display a gradient rule in the console."""
    _colors = parse_colors(colors)
    _bgcolors = parse_colors(bgcolors)
    _title_style = parse_style(title_style)

    rule = Rule(
        title=title or "",
        title_style=_title_style,
        colors=_colors,
        rainbow=rainbow,
        hues=hues,
        bg_colors=_bgcolors,
        thickness=thickness,
        end=end,
        align=cast(AlignMethod, align),
    )
    console.print(rule)


__all__ = ["rule_command"]
