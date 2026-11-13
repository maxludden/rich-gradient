"""Gradient-enabled convenience wrapper for Rich Pretty."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Optional

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.highlighter import Highlighter
from rich.pretty import Pretty as RichPretty

from rich_gradient.gradient import (ColorType, Gradient, HighlightRegexType,
                                    HighlightWordsType)


class Pretty(Gradient):
    """A Rich pretty-printer convenience constructor with gradient rendering.

    Args:
        object_ (Any): The object to pretty-print, e.g. ``{"a": [1, 2, 3]}``.
        highlighter (Optional[Highlighter]): Rich highlighter applied before the
            gradient, e.g. ``ReprHighlighter()``. ``None`` uses Rich's default. Defaults
            to None.
        indent_size (int): Spaces per indentation level. Defaults to 4.
        pretty_justify (Optional[JustifyMethod]): Justification of the pretty-printed
            text: ``"default"``, ``"left"``, ``"center"``, ``"right"``, or ``"full"``.
            Defaults to None.
        overflow (Optional[OverflowMethod]): How to handle lines that are too long:
            ``"fold"``, ``"crop"``, ``"ellipsis"``, or ``"ignore"``. Defaults to None.
        no_wrap (Optional[bool]): Disable wrapping of long lines. Defaults to False.
        indent_guides (bool): Draw indentation guide lines. Defaults to False.
        max_length (Optional[int]): Abbreviate containers longer than this, e.g. ``10``.
            ``None`` disables it. Defaults to None.
        max_string (Optional[int]): Truncate strings longer than this, e.g. ``80``.
            ``None`` disables it. Defaults to None.
        max_depth (Optional[int]): Abbreviate containers nested deeper than this, e.g.
            ``3``. ``None`` disables it. Defaults to None.
        expand_all (bool): Expand every container, even ones that fit on one line.
            Defaults to False.
        margin (int): Width to subtract from the available width when deciding whether
            to expand. Defaults to 0.
        insert_line (bool): Insert a blank line before multi-line output. Defaults to
            False.
        colors (Optional[Sequence[ColorType]]): Foreground color stops. Each stop may be
            a color name (Rich/ANSI names such as ``"red"`` keep Rich's meaning; CSS
            names such as ``"tomato"`` also work), a hex string (``"#f00"``,
            ``"#ff0000"``), an ``"rgb(255, 0, 0)"`` string, an ``(r, g, b)`` tuple, or a
            ``rich.color.Color``, e.g. ``["#f00", "orange", (0, 128, 255)]``. If omitted
            and ``rainbow`` is False, ``hues`` colors are taken from the spectrum
            palette. Defaults to None.
        bg_colors (Optional[Sequence[ColorType]]): Background color stops, in the same
            formats as ``colors``, e.g. ``["#000033", "#330033"]``. If omitted, no
            background gradient is applied. Defaults to None.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues``. Defaults to False.
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted (a run of consecutive hues with a random starting point). Valid
            values are 2 to 17. Defaults to 5.
        repeat_scale (Optional[float]): Width of one full color cycle as a multiple of
            the rendered width; larger values give a more gradual gradient, e.g.
            ``1.5``. ``None`` derives it from the stops so one pass runs from the first
            color to the last (1.0 for two colors, 2.0 for three or more). Defaults to
            None.
        expand (bool): Expand the output to the full console width. Defaults to True.
        justify (AlignMethod): Horizontal alignment of the output: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the output:
            ``"top"``, ``"middle"``, or ``"bottom"``. Defaults to ``"middle"``.
        console (Optional[Console]): Console used for rendering and measurement.
            Defaults to ``rich.get_console()``.
        highlight_words (Optional[HighlightWordsType]): Words to restyle on top of the
            gradient. Accepts a mapping of a word (or a tuple of words) to a style, e.g.
            ``{"error": "bold red", ("warn", "caution"): "yellow"}``; a sequence of
            ``(words, style[, case_sensitive])`` tuples, e.g.
            ``[("error", "bold red"), (("warn", "caution"), "yellow", False)]``; or
            ``HighlightWords`` instances, e.g.
            ``[HighlightWords(words=("error",), style=Style.parse("bold red"))]``.
            Matching is case-sensitive unless ``case_sensitive`` is False. Colors in
            these styles are shown: they replace the gradient on the matched text.
            Defaults to None.
        highlight_regex (Optional[HighlightRegexType]): Regular expressions whose
            matches are restyled on top of the gradient. Accepts a mapping of a pattern
            to a style, e.g. ``{r"[0-9]+": "bold cyan"}``; a sequence of
            ``(pattern, style[, flags])`` tuples, e.g.
            ``[(r"error|fail", "red", re.IGNORECASE)]``; or ``HighlightRegex``
            instances, e.g.
            ``[HighlightRegex(pattern=re.compile(r"[0-9]+"), style=Style.parse("cyan"))]``.
            Colors in these styles are shown: they replace the gradient on the matched
            text. Defaults to None.
        animate (bool): Mark the content as changing between renders, so highlight
            matches are recomputed every frame instead of cached. Static renderables
            never animate on their own; use the ``Animated*`` classes for live
            animation. Defaults to False.
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
        colors: Sequence[ColorType] | None = None,
        bg_colors: Sequence[ColorType] | None = None,
        rainbow: bool = False,
        hues: int = 5,
        repeat_scale: float | None = None,
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        console: Console | None = None,
        highlight_words: HighlightWordsType | None = None,
        highlight_regex: HighlightRegexType | None = None,
        animate: bool = False,
    ) -> None:
        """Initialize a gradient-enabled Rich pretty-printer; see the class docstring for arguments."""
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
            animate=animate,
        )

    @property
    def pretty(self) -> RichPretty:
        """The underlying Rich Pretty renderable."""
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
