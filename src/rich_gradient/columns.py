"""Gradient-enabled convenience wrapper for Rich columns."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from rich.align import AlignMethod, VerticalAlignMethod
from rich.columns import Columns as RichColumns
from rich.console import Console, RenderableType
from rich.padding import PaddingDimensions
from rich.text import TextType

from rich_gradient.gradient import (ColorType, Gradient, HighlightRegexType,
                                    HighlightWordsType)


class Columns(Gradient):
    """A Rich columns convenience constructor with gradient rendering.

    Args:
        renderables (Iterable[RenderableType]): Renderables to lay out in columns.
            Strings are parsed as console markup, e.g.
            ``["one", "two", Panel("three")]``.
        width (Optional[int]): Fixed width of each column in cells, or ``None`` to fit
            the content. Defaults to None.
        padding (PaddingDimensions): Padding around each cell, CSS-style: ``1``,
            ``(top_bottom, left_right)``, or ``(top, right, bottom, left)``. Defaults to
            ``(0, 1)``.
        columns_expand (bool): Make the columns themselves fill the available width.
            Defaults to False.
        equal (bool): Give every column the same width. Defaults to False.
        column_first (bool): Fill columns top-to-bottom before moving right, instead of
            row by row. Defaults to False.
        right_to_left (bool): Start laying out from the right. Defaults to False.
        align (Optional[AlignMethod]): Alignment of content within each column:
            ``"left"``, ``"center"``, ``"right"``, or ``None`` for Rich's default.
            Defaults to None.
        title (Optional[TextType]): Title rendered above the columns: a string (parsed
            as console markup) or a ``Text``. Defaults to None.
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
        justify (AlignMethod): Horizontal alignment of the columns: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the columns:
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
            Matching is case-sensitive unless ``case_sensitive`` is False. Defaults to
            None.
        highlight_regex (Optional[HighlightRegexType]): Regular expressions whose
            matches are restyled on top of the gradient. Accepts a mapping of a pattern
            to a style, e.g. ``{r"[0-9]+": "bold cyan"}``; a sequence of
            ``(pattern, style[, flags])`` tuples, e.g.
            ``[(r"error|fail", "red", re.IGNORECASE)]``; or ``HighlightRegex``
            instances, e.g.
            ``[HighlightRegex(pattern=re.compile(r"[0-9]+"), style=Style.parse("cyan"))]``.
            Defaults to None.
    """

    def __init__(
        self,
        renderables: Iterable[RenderableType],
        *,
        width: int | None = None,
        padding: PaddingDimensions = (0, 1),
        columns_expand: bool = False,
        equal: bool = False,
        column_first: bool = False,
        right_to_left: bool = False,
        align: AlignMethod | None = None,
        title: TextType | None = None,
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
    ) -> None:
        """Initialize gradient-enabled Rich columns; see the class docstring for arguments."""
        columns = RichColumns(
            renderables,
            width=width,
            padding=padding,
            expand=columns_expand,
            equal=equal,
            column_first=column_first,
            right_to_left=right_to_left,
            align=align,
            title=title,
        )
        self._columns = columns
        super().__init__(
            columns,
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
    def columns(self) -> RichColumns:
        """The underlying Rich columns renderable."""
        return self._columns


def demo() -> None:
    """Render a small gradient columns demo to the terminal."""
    console = Console(width=80)
    columns = Columns(
        ["Text", "Gradient", "Panel", "Rule", "Table", "Tree", "Syntax", "Pretty"],
        title="Gradient Columns",
        colors=["#00ff55", "#00ffdd", "#0b8cf5"],
        equal=True,
        columns_expand=True,
        highlight_words={"Gradient Columns": "bold white"},
    )
    console.print(columns)


if __name__ == "__main__":
    demo()
