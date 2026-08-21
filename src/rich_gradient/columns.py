"""Gradient-enabled convenience wrapper for Rich columns."""

from __future__ import annotations

from collections.abc import Iterable, Sequence

from rich.align import AlignMethod, VerticalAlignMethod
from rich.columns import Columns as RichColumns
from rich.console import Console, RenderableType
from rich.padding import PaddingDimensions
from rich.text import TextType

from rich_gradient.gradient import (
    ColorType,
    Gradient,
    HighlightRegexType,
    HighlightWordsType,
)


class Columns(Gradient):
    """A Rich columns convenience constructor with gradient rendering.

    Args:
        renderables: Renderables to arrange in columns.
        width: Optional desired column width.
        padding: Padding around column cells.
        columns_expand: Whether Rich columns expand to full width.
        equal: Whether columns are equal-sized.
        column_first: Whether to lay out top-to-bottom first.
        right_to_left: Whether columns start from the right.
        align: Column content alignment.
        title: Optional title.
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
        repeat_scale: float = 2.0,
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        console: Console | None = None,
        highlight_words: HighlightWordsType | None = None,
        highlight_regex: HighlightRegexType | None = None,
    ) -> None:
        """Initialize gradient-enabled Rich columns."""
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
        """Return the underlying Rich columns renderable."""
        return self._columns


def demo() -> None:
    """Render a small gradient columns demo to the terminal."""
    console = Console(width=80)
    columns = Columns(
        ["Text", "Gradient", "Panel", "Rule", "Table", "Tree", "Syntax", "Pretty"],
        title="Gradient Columns",
        colors=["#34d399", "#60a5fa", "#f59e0b"],
        equal=True,
        columns_expand=True,
        highlight_words={"Gradient": "bold white", "Syntax": "bold cyan"},
    )
    console.print(columns)


if __name__ == "__main__":
    demo()
