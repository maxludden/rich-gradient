"""Gradient-enabled convenience wrapper for Rich tables."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Optional

from rich.align import AlignMethod, VerticalAlignMethod
from rich.box import HEAVY_HEAD, Box
from rich.console import Console, RenderableType
from rich.padding import PaddingDimensions
from rich.style import StyleType
from rich.table import Column
from rich.table import Table as RichTable
from rich.text import TextType

from rich_gradient.gradient import (ColorType, Gradient, HighlightRegexType,
                                    HighlightWordsType)


class Table(Gradient):
    """A Rich table convenience constructor with gradient rendering.

    Args:
        *headers (str | Column): Column headers, as strings or ``rich.table.Column``
            instances, e.g. ``"Name", Column("Size", justify="right")``.
        title (Optional[TextType]): Title rendered above the table: a string (parsed as
            console markup) or a ``Text``. Defaults to None.
        caption (Optional[TextType]): Caption rendered below the table. Defaults to
            None.
        width (Optional[int]): Fixed table width in cells, or ``None`` to fit the
            content. Defaults to None.
        min_width (Optional[int]): Minimum table width in cells. Defaults to None.
        box (Optional[Box]): Box characters for the borders, any ``rich.box`` constant
            (e.g. ``rich.box.ROUNDED``), or ``None`` for no borders. Defaults to
            ``rich.box.HEAVY_HEAD``.
        safe_box (Optional[bool]): Use box characters that render on legacy Windows
            terminals. ``None`` lets the console decide. Defaults to None.
        padding (PaddingDimensions): Cell padding, CSS-style: ``1``,
            ``(top_bottom, left_right)``, or ``(top, right, bottom, left)``. Defaults to
            ``(0, 1)``.
        collapse_padding (bool): Merge the padding of neighboring cells. Defaults to
            False.
        pad_edge (bool): Pad the outer edge cells. Defaults to True.
        expand (bool): Stretch the table to the full available width. Defaults to False.
        show_header (bool): Show the header row. Defaults to True.
        show_footer (bool): Show the footer row. Defaults to False.
        show_edge (bool): Draw the outer border. Defaults to True.
        show_lines (bool): Draw lines between rows. Defaults to False.
        leading (int): Blank lines between rows. Defaults to 0.
        style (StyleType): Base style of the table. A style string or
            ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to ``"none"``.
        row_styles (Optional[Sequence[StyleType]]): Styles cycled across rows, e.g.
            ``["", "dim"]`` for zebra striping. Defaults to None.
        header_style (StyleType): Style of the header row. A style string or
            ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to
            ``"table.header"``.
        footer_style (StyleType): Style of the footer row. A style string or
            ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to
            ``"table.footer"``.
        border_style (Optional[StyleType]): Style of the borders. A style string or
            ``rich.style.Style``, e.g. ``"italic cyan"``. Defaults to None.
        title_style (Optional[StyleType]): Style of the title. A style string or
            ``rich.style.Style``, e.g. ``"italic cyan"``. Defaults to None.
        caption_style (Optional[StyleType]): Style of the caption. A style string or
            ``rich.style.Style``, e.g. ``"italic cyan"``. Defaults to None.
        title_justify (AlignMethod): Alignment of the title: ``"left"``, ``"center"``,
            or ``"right"``. Defaults to ``"center"``.
        caption_justify (AlignMethod): Alignment of the caption: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"center"``.
        highlight (bool): Apply Rich's repr highlighting to cell contents. Defaults to
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
        justify (AlignMethod): Horizontal alignment of the table: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the table:
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
        animate (bool): Mark the content as changing between renders, so highlight
            matches are recomputed every frame instead of cached. Static renderables
            never animate on their own; use the ``Animated*`` classes for live
            animation. Defaults to False.
    """

    def __init__(
        self,
        *headers: str | Column,
        title: TextType | None = None,
        caption: TextType | None = None,
        width: int | None = None,
        min_width: int | None = None,
        box: Box | None = HEAVY_HEAD,
        safe_box: bool | None = None,
        padding: PaddingDimensions = (0, 1),
        collapse_padding: bool = False,
        pad_edge: bool = True,
        expand: bool = False,
        show_header: bool = True,
        show_footer: bool = False,
        show_edge: bool = True,
        show_lines: bool = False,
        leading: int = 0,
        style: StyleType = "none",
        row_styles: Sequence[StyleType] | None = None,
        header_style: StyleType = "table.header",
        footer_style: StyleType = "table.footer",
        border_style: StyleType | None = None,
        title_style: StyleType | None = None,
        caption_style: StyleType | None = None,
        title_justify: AlignMethod = "center",
        caption_justify: AlignMethod = "center",
        highlight: bool = False,
        colors: Sequence[ColorType] | None = None,
        bg_colors: Sequence[ColorType] | None = None,
        rainbow: bool = False,
        hues: int = 5,
        repeat_scale: float | None = None,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        console: Console | None = None,
        highlight_words: HighlightWordsType | None = None,
        highlight_regex: HighlightRegexType | None = None,
        animate: bool = False,
    ) -> None:
        """Initialize a gradient-enabled Rich table; see the class docstring for arguments."""
        table = RichTable(
            *headers,
            title=title,
            caption=caption,
            width=width,
            min_width=min_width,
            box=box,
            safe_box=safe_box,
            padding=padding,
            collapse_padding=collapse_padding,
            pad_edge=pad_edge,
            expand=expand,
            show_header=show_header,
            show_footer=show_footer,
            show_edge=show_edge,
            show_lines=show_lines,
            leading=leading,
            style=style,
            row_styles=list(row_styles) if row_styles is not None else None,
            header_style=header_style,
            footer_style=footer_style,
            border_style=border_style,
            title_style=title_style,
            caption_style=caption_style,
            title_justify=title_justify,
            caption_justify=caption_justify,
            highlight=highlight,
        )
        self._table = table
        super().__init__(
            table,
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
    def table(self) -> RichTable:
        """The underlying Rich table."""
        return self._table

    def add_column(self, *args: Any, **kwargs: Any) -> None:
        """Forward ``add_column`` to the underlying Rich table.

        Args:
            *args: Positional arguments for ``rich.table.Table.add_column``,
                e.g. the header ``"Name"``.
            **kwargs: Keyword arguments for ``rich.table.Table.add_column``,
                e.g. ``justify="right", style="cyan"``.
        """
        self._table.add_column(*args, **kwargs)

    def add_row(self, *args: RenderableType, **kwargs: Any) -> None:
        """Forward ``add_row`` to the underlying Rich table.

        Args:
            *args: One renderable per column, e.g. ``"README.md", "4 KB"``.
            **kwargs: Keyword arguments for ``rich.table.Table.add_row``, e.g.
                ``style="dim", end_section=True``.
        """
        self._table.add_row(*args, **kwargs)


def demo() -> None:
    """Render a small gradient table demo to the terminal."""
    console = Console(width=80)
    table = Table(
        "Service",
        "Status",
        "Latency",
        title="Gradient Table",
        colors=["#38bdf8", "#a855f7", "#f97316"],
        border_style="white",
        show_lines=True,
        highlight_words={"ok": "bold #0f0", "degraded": "bold yellow"},
        highlight_regex={r"\d+ ms": "bold #0ff"},
    )
    table.add_row("api", "ok", "42 ms")
    table.add_row("worker", "degraded", "180 ms")
    table.add_row("database", "ok", "19 ms")
    console.print(table)


if __name__ == "__main__":
    demo()
