"""Markdown command wiring for the CLI."""

from __future__ import annotations

from typing import Any, Optional, cast

import rich_click as click
from rich.align import AlignMethod, VerticalAlignMethod

from rich_gradient.animated_markdown import AnimatedMarkdown
from rich_gradient.markdown import Markdown

from .common import console, parse_colors, parse_style


@click.command("markdown", help="Render markdown text with gradient colors.")
@click.argument("markdown", nargs=1, type=str, required=True, metavar="MARKDOWN")
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
    default=7,
    help="The number of hues to use for a random gradient.",
    show_default=True,
)
@click.option(
    "--style",
    metavar="STYLE",
    type=str,
    default=None,
    help="The style to apply to the markdown text. [dim italic]*Only non-color \
styles will be applied as the gradient's colors override color styles.[/]",
)
@click.option(
    "-j",
    "--justify",
    metavar="JUSTIFY",
    type=click.Choice(["left", "center", "right"], case_sensitive=False),
    default="left",
    help="Justification of the markdown text. [lime](left, center, right)[/]",
    show_default=True,
)
@click.option(
    "--vertical-justify",
    metavar="VERTICAL_JUSTIFY",
    type=click.Choice(["top", "middle", "bottom"], case_sensitive=False),
    default="top",
    help="Vertical justification of the markdown text. [lime](top, middle, bottom)[/]",
    show_default=True,
)
@click.option(
    "--no-wrap",
    is_flag=True,
    default=False,
    help="Disable wrapping of markdown text.",
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
    style: Optional[str],
    justify: str,
    vertical_justify: str,
    no_wrap: bool,
    end: str,
    animate: bool,
    duration: float,
) -> None:
    """Render markdown text with gradient colors in a rich console."""
    _colors = parse_colors(colors)
    _bgcolors = parse_colors(bgcolors)
    markdown_kwargs: dict[str, Any] = {}
    if style:
        markdown_kwargs["style"] = parse_style(style)

    justify_value = cast(AlignMethod, justify)
    vertical_value = cast(VerticalAlignMethod, vertical_justify)

    if animate and console.is_terminal is True:
        console.clear()
        animated = AnimatedMarkdown(
            markdown,
            colors=_colors,
            rainbow=rainbow,
            hues=hues,
            justify=justify_value,
            vertical_justify=vertical_value,
            bg_colors=_bgcolors,
            markdown_kwargs=markdown_kwargs or None,
            animate=True,
            duration=duration,
        )
        animated.run()
        return

    md = Markdown(
        markdown,
        colors=_colors,
        rainbow=rainbow,
        hues=hues,
        justify=justify_value,
        vertical_justify=vertical_value,
        bg_colors=_bgcolors,
        markdown_kwargs=markdown_kwargs or None,
    )
    console.print(md, end=end, no_wrap=no_wrap)


__all__ = ["markdown_command"]
