"""Gradient-enabled convenience wrapper for Rich Pretty."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Optional

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.highlighter import Highlighter
from rich.pretty import Pretty as RichPretty

from rich_gradient.gradient import ColorType, Gradient, HighlightRegexType, HighlightWordsType


class Pretty(Gradient):
    """A Rich pretty-printer convenience constructor with gradient rendering.

    Args:
        object_: Object to pretty print.
        highlighter: Optional Rich highlighter.
        indent_size: Number of spaces per indent.
        pretty_justify: Justification used by Rich Pretty.
        overflow: Overflow handling used by Rich Pretty.
        no_wrap: Whether to disable wrapping.
        indent_guides: Whether to show indentation guides.
        max_length: Maximum container length before abbreviation.
        max_string: Maximum string length before truncation.
        max_depth: Maximum nested depth.
        expand_all: Whether to expand all containers.
        margin: Width margin for expansion.
        insert_line: Whether to insert a line before multiline output.
        colors: Foreground gradient color stops.
        bg_colors: Background gradient color stops.
        rainbow: Whether to generate a rainbow palette.
        hues: Number of auto-generated hues.
        repeat_scale: Scale factor controlling gradient repeats.
        expand: Whether the gradient frame expands.
        justify: Horizontal alignment.
        vertical_justify: Vertical alignment.
        console: Optional Rich console.
        highlight_words: Word highlight configuration.
        highlight_regex: Regex highlight configuration.
    """

    def __init__(
        self,
        object_: Any,
        *,
        highlighter: Highlighter | None = None,
        indent_size: int = 4,
        pretty_justify: JustifyMethod | None = None,
        overflow: OverflowMethod | None = None,
        no_wrap: bool | None = False,
        indent_guides: bool = False,
        max_length: int | None = None,
        max_string: int | None = None,
        max_depth: int | None = None,
        expand_all: bool = False,
        margin: int = 0,
        insert_line: bool = False,
        colors: Optional[Sequence[ColorType]] = None,
        bg_colors: Optional[Sequence[ColorType]] = None,
        rainbow: bool = False,
        hues: int = 5,
        repeat_scale: float = 2.0,
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        console: Optional[Console] = None,
        highlight_words: Optional[HighlightWordsType] = None,
        highlight_regex: Optional[HighlightRegexType] = None,
    ) -> None:
        """Initialize a gradient-enabled Rich pretty-printer."""
        pretty = RichPretty(
            object_,
            highlighter=highlighter,
            indent_size=indent_size,
            justify=pretty_justify,
            overflow=overflow,
            no_wrap=no_wrap,
            indent_guides=indent_guides,
            max_length=max_length,
            max_string=max_string,
            max_depth=max_depth,
            expand_all=expand_all,
            margin=margin,
            insert_line=insert_line,
        )
        self._pretty = pretty
        super().__init__(
            pretty,
            colors=list(colors) if colors is not None else None,
            bg_colors=list(bg_colors) if bg_colors is not None else None,
            console=console,
            hues=hues,
            rainbow=rainbow,
            expand=expand,
            justify=justify,
            vertical_justify=vertical_justify,
            repeat_scale=repeat_scale,
            highlight_words=highlight_words,
            highlight_regex=highlight_regex,
        )

    @property
    def pretty(self) -> RichPretty:
        """Return the underlying Rich Pretty renderable."""
        return self._pretty


def demo() -> None:
    """Render a small gradient pretty-printer demo to the terminal."""
    console = Console(width=80)
    payload = {
        "project": "rich-gradient",
        "renderables": ["Table", "Tree", "Columns", "Pretty", "Syntax"],
        "status": {"tests": "passing", "docs": "updated"},
    }
    pretty = Pretty(
        payload,
        colors=["#f43f5e", "#f59e0b", "#22c55e"],
        indent_guides=True,
        expand_all=True,
        highlight_words={"passing": "bold green", "updated": "bold cyan"},
    )
    console.print(pretty)


if __name__ == "__main__":
    demo()
