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
        label (RenderableType): Label for the root node, e.g. ``"[bold]project/"``.
        style (StyleType): Style of the tree. A style string or ``rich.style.Style``,
            e.g. ``"bold #ff8800"``. Defaults to ``"tree"``.
        guide_style (StyleType): Style of the guide lines. A style string or
            ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to ``"tree.line"``.
        expanded (bool): Show the children of the root node. Defaults to True.
        highlight (bool): Apply Rich's repr highlighting to labels. Defaults to False.
        hide_root (bool): Hide the root label and show only its children. Defaults to
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
        justify (AlignMethod): Horizontal alignment of the tree: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the tree:
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
        label: RenderableType,
        *,
        style: StyleType = "tree",
        guide_style: StyleType = "tree.line",
        expanded: bool = True,
        highlight: bool = False,
        hide_root: bool = False,
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
        """Initialize a gradient-enabled Rich tree; see the class docstring for arguments."""
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
        """The underlying Rich tree."""
        return self._tree

    def add(
        self,
        label: RenderableType,
        *,
        style: StyleType | None = None,
        guide_style: StyleType | None = None,
        expanded: bool = True,
        highlight: bool | None = False,
    ) -> RichTree:
        """Forward `add` to the underlying Rich tree.

        Args:
            label: Label for the child tree node, e.g. ``"src/"``.
            style: Style for the child, e.g. ``"bold"``. Defaults to None,
                which inherits the parent's style.
            guide_style: Style for the child's guide lines. Defaults to None,
                which inherits the parent's guide style.
            expanded: Show the child's own children. Defaults to True.
            highlight: Apply Rich's repr highlighting to the label. Defaults
                to False.

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
