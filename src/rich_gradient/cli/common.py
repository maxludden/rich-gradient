"""Shared helpers and configuration for the rich-gradient CLI."""

from __future__ import annotations

from typing import List, Optional

from rich.console import Console
from rich.style import Style

from rich_click import rich_click as rich_click_config

console = Console()
VERSION = "1.0.0"

# Configure global rich-click styling so every command gets consistent output.
rich_click_config.USE_RICH_MARKUP = True
rich_click_config.SHOW_ARGUMENTS = True
rich_click_config.SHOW_METAVARS_COLUMN = True
rich_click_config.HEADER_TEXT = "[#ff5500]r[/][#ff6f00]i[/][#ff8300]c[/]\
[#ff9500]h[/][#ffa600]-[/][#ffb600]g[/][#ffc500]r[/][#ffd400]a[/]\
[#ffe500]d[/][#fff400]i[/][#f9ff00]e[/][#e2ff00]n[/][#c8ff00]t[/]\
[#a9ff00] [/][bold #fff]CLI[/]"
rich_click_config.FOOTER_TEXT = "[#ff5500]🌈[/][#ff7400] [/][#ff8c00]h[/]\
[#ffa100]t[/][#ffb500]t[/][#ffc700]p[/][#ffdc00]s[/][#ffef00]:[/]\
[#fbff00]/[/][#dfff00]/[/][#bdff00]m[/][#9aff00]a[/][#73ff00]x[/]\
[#2aff00]l[/][#00ff5c]u[/][#00ff83]d[/][#00ffa6]d[/][#00ffd1]e[/]\
[#00fff3]n[/][#00f4ff].[/][#00e1ff]g[/][#00ccff]i[/][#00baff]t[/]\
[#00a6ff]h[/][#2192ff]u[/][#3b81ff]b[/][#4c6cff].[/][#6061ff]i[/]\
[#725bff]o[/][#8253ff]/[/][#9648ff]r[/][#a83bff]i[/][#c22eff]c[/]\
[#e122ff]h[/][#fb0cff]-[/][#ff00e6]g[/][#ff00c6]r[/][#ff00a4]a[/]\
[#ff0089]d[/][#ff0066]i[/][#ff004b]e[/][#ff0036]n[/][#ff0000]t[/]"
rich_click_config.STYLE_USAGE_COMMAND = "bold magenta"
rich_click_config.STYLE_OPTION = "bold cyan"
rich_click_config.STYLE_SWITCH = "bold magenta"
rich_click_config.STYLE_HEADER_TEXT = "bold cyan"
rich_click_config.STYLE_FOOTER_TEXT = "not dim bold"
rich_click_config.COMMANDS_BEFORE_OPTIONS = True


def parse_colors(colors: Optional[str]) -> Optional[List[str]]:
    """Parse comma-separated color tokens into a list."""
    if colors is None:
        return None
    return [c.strip() for c in colors.split(",") if c.strip()]


def parse_style(style: Optional[str]) -> Style:
    """Parse a Rich style string or return a null style."""
    if style is None:
        return Style.null()
    return Style.parse(style)


__all__ = [
    "VERSION",
    "console",
    "parse_colors",
    "parse_style",
]
