"""Gradient-enabled convenience wrapper for Rich trees."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console, RenderableType
from rich.style import StyleType
from rich.tree import Tree as RichTree

from rich_gradient.gradient import (ColorType, Gradient, HighlightRegexType,
                                    HighlightWordsType)


class Tree(Gradient):
    """A Rich tree convenience constructor with gradient rendering.

    Args:
        label: Root label for the tree.
        style: Base tree style.
        guide_style: Style for guide lines.
        expanded: Whether child nodes are expanded.
        highlight: Whether Rich should highlight labels.
        hide_root: Whether to hide the root label.
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
        label: RenderableType,
        *,
        style: StyleType = "tree",
        guide_style: StyleType = "tree.line",
        expanded: bool = True,
        highlight: bool = False,
        hide_root: bool = False,
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
        """Initialize a gradient-enabled Rich tree."""
        tree = RichTree(
            label,
            style=style,
            guide_style=guide_style,
            expanded=expanded,
            highlight=highlight,
            hide_root=hide_root,
        )
        self._tree = tree
        super().__init__(
            tree,
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
    def tree(self) -> RichTree:
        """Return the underlying Rich tree."""
        return self._tree

    def add(
        self,
        label: RenderableType,
        *,
        style: StyleType | None = None,
        guide_style: StyleType | None = None,
        expanded: bool = True,
        highlight: Optional[bool] = False,
    ) -> RichTree:
        """Forward `add` to the underlying Rich tree.

        Args:
            label: Label for the child tree node.
            style: Optional style for the child label.
            guide_style: Optional style for the child guide lines.
            expanded: Whether the child node is expanded.
            highlight: Whether Rich should highlight the child label.

        Returns:
            The newly-created Rich tree node.
        """
        return self._tree.add(
            label,
            style=style,
            guide_style=guide_style,
            expanded=expanded,
            highlight=highlight,
        )


def demo() -> None:
    """Render a small gradient tree demo to the terminal."""
    console = Console(width=80)
    tree = Tree(
        "rich-gradient",
        colors=["#22d3ee", "#a78bfa", "#f472b6"],
        guide_style="dim",
        highlight_words={
            "docs": "bold cyan",
            "tests": "bold magenta",
            "src": "bold yellow",
        },
    )
    src = tree.add("src")
    src.add("rich_gradient")
    docs = tree.add("docs")
    docs.add("gradient.md")
    tests = tree.add("tests")
    tests.add("test_custom_renderables.py")
    console.print(tree)


if __name__ == "__main__":
    demo()
