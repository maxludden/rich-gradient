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
        headers: Optional Rich table headers or `Column` instances.
        title: Optional title rendered above the table.
        caption: Optional caption rendered below the table.
        width: Optional explicit table width.
        min_width: Optional minimum table width.
        box: Rich box style for table borders.
        safe_box: Whether to use safe box drawing characters.
        padding: Padding for table cells.
        collapse_padding: Whether to collapse cell padding.
        pad_edge: Whether to pad edge cells.
        expand: Whether the table expands to fill available width.
        show_header: Whether to show the header row.
        show_footer: Whether to show the footer row.
        show_edge: Whether to draw outer table edges.
        show_lines: Whether to draw lines between rows.
        leading: Blank lines between rows.
        style: Base table style.
        row_styles: Optional alternating row styles.
        header_style: Header style.
        footer_style: Footer style.
        border_style: Optional border style.
        title_style: Optional title style.
        caption_style: Optional caption style.
        title_justify: Title justification.
        caption_justify: Caption justification.
        highlight: Whether Rich should highlight cell contents.
        colors: Foreground gradient color stops.
        bg_colors: Background gradient color stops.
        rainbow: Whether to generate a rainbow palette.
        hues: Number of auto-generated hues.
        repeat_scale: Scale factor controlling gradient repeats.
        justify: Horizontal alignment of the table in the gradient frame.
        vertical_justify: Vertical alignment of the table in the gradient frame.
        console: Optional Rich console.
        highlight_words: Word highlight configuration.
        highlight_regex: Regex highlight configuration.
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
        colors: Optional[Sequence[ColorType]] = None,
        bg_colors: Optional[Sequence[ColorType]] = None,
        rainbow: bool = False,
        hues: int = 5,
        repeat_scale: float = 2.0,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        console: Optional[Console] = None,
        highlight_words: Optional[HighlightWordsType] = None,
        highlight_regex: Optional[HighlightRegexType] = None,
    ) -> None:
        """Initialize a gradient-enabled Rich table."""
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
        )

    @property
    def table(self) -> RichTable:
        """Return the underlying Rich table."""
        return self._table

    def add_column(self, *args: Any, **kwargs: Any) -> None:
        """Forward `add_column` to the underlying Rich table."""
        self._table.add_column(*args, **kwargs)

    def add_row(self, *args: RenderableType, **kwargs: Any) -> None:
        """Forward `add_row` to the underlying Rich table."""
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
