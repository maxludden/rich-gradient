"""Gradient-enabled convenience wrapper for Rich Syntax."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from pygments.lexer import Lexer
from rich.align import AlignMethod, VerticalAlignMethod
from rich.color import Color
from rich.console import Console
from rich.padding import PaddingDimensions
from rich.style import Style
from rich.syntax import Syntax as RichSyntax
from pygments.token import Token

from rich_gradient.gradient import (ColorType, Gradient, HighlightRegexType,
                                    HighlightWordsType)


class Syntax(Gradient):
    """A Rich syntax-highlighting convenience constructor with gradient rendering.

    Args:
        code (str): The source code to highlight.
        lexer (str | Lexer): Pygments lexer name or instance, e.g. ``"python"`` or
            ``"json"``.
        theme (str): Pygments style name, e.g. ``"monokai"``, ``"dracula"``, or
            ``"ansi_dark"``. Defaults to ``"monokai"``.
        dedent (bool): Strip common leading indentation from the code. Defaults to
            False.
        line_numbers (bool): Show line numbers. Defaults to False.
        start_line (int): Number shown for the first line. Defaults to 1.
        line_range (Optional[tuple[int | None, int | None]]): Inclusive ``(start, end)``
            range of lines to show, either end may be ``None``, e.g. ``(10, 20)``.
            Defaults to None (all lines).
        highlight_lines (Optional[set[int]]): Line numbers to highlight, e.g.
            ``{3, 4}``. Defaults to None.
        code_width (Optional[int]): Fixed width of the code area, or ``None`` to fit.
            Defaults to None.
        tab_size (int): Spaces per tab. Defaults to 4.
        word_wrap (bool): Wrap long lines. Defaults to False.
        background_color (Optional[str]): Override the theme's background color, e.g.
            ``"#1e1e1e"`` or ``"default"``. Defaults to None.
        indent_guides (bool): Draw indentation guide lines. Defaults to False.
        padding (PaddingDimensions): Padding around the code, CSS-style: ``1``,
            ``(top_bottom, left_right)``, or ``(top, right, bottom, left)``. Defaults to
            0.
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
        justify (AlignMethod): Horizontal alignment of the code: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the code:
            ``"top"``, ``"middle"``, or ``"bottom"``. Defaults to ``"middle"``.
        console (Optional[Console]): Console used for rendering and measurement.
            Defaults to ``rich.get_console()``.
        highlight_words (Optional[HighlightWordsType]): Words to restyle on top of the
            gradient. Accepts a mapping of a word (or a tuple of words) to a style, e.g.
            ``{"error": "bold", ("warn", "caution"): "italic"}``; a sequence of
            ``(words, style[, case_sensitive])`` tuples, e.g.
            ``[("error", "bold"), (("warn", "caution"), "italic", False)]``; or
            ``HighlightWords`` instances, e.g.
            ``[HighlightWords(words=("error",), style=Style.parse("b u"))]``.
            Matching is case-sensitive unless ``case_sensitive`` is False. Defaults to
            None.
        highlight_regex (Optional[HighlightRegexType]): Regular expressions whose
            matches are restyled on top of the gradient. Accepts a mapping of a pattern
            to a style, e.g. ``{r"[0-9]+": "bold"}``; a sequence of
            ``(pattern, style[, flags])`` tuples, e.g.
            ``[(r"error|fail", "reverse", re.IGNORECASE)]``; or ``HighlightRegex``
            instances, e.g.
            ``[HighlightRegex(pattern=re.compile(r"[0-9]+"), style=Style.parse("dim italic"))]``.
            Defaults to None.
        keep_token_colors (bool): Keep the theme's colors for highlighted tokens
            (keywords, strings, comments, ...), so only plain code, line numbers and
            whitespace take the gradient. Set to False to recolor everything with the
            gradient. Defaults to True.
        animate (bool): Mark the content as changing between renders, so highlight
            matches are recomputed every frame instead of cached. Static renderables
            never animate on their own; use the ``Animated*`` classes for live
            animation. Defaults to False.
    """

    def __init__(
        self,
        code: str,
        lexer: str | Lexer,
        *,
        theme: str = "monokai",
        dedent: bool = False,
        line_numbers: bool = False,
        start_line: int = 1,
        line_range: tuple[int | None, int | None] | None = None,
        highlight_lines: set[int] | None = None,
        code_width: int | None = None,
        tab_size: int = 4,
        word_wrap: bool = False,
        background_color: str | None = None,
        indent_guides: bool = False,
        padding: PaddingDimensions = 0,
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
        keep_token_colors: bool = True,
        animate: bool = False,
    ) -> None:
        """Initialize gradient-enabled Rich syntax highlighting; see the class docstring for arguments."""
        self._base_color: Color | None = None
        syntax = RichSyntax(
            code,
            lexer,
            theme=theme,
            dedent=dedent,
            line_numbers=line_numbers,
            start_line=start_line,
            line_range=line_range,
            highlight_lines=highlight_lines,
            code_width=code_width,
            tab_size=tab_size,
            word_wrap=word_wrap,
            background_color=background_color,
            indent_guides=indent_guides,
            padding=padding,
        )
        self._syntax = syntax
        if keep_token_colors:
            self._base_color = syntax._theme.get_style_for_token(Token).color
        super().__init__(
            syntax,
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

    def _merge_styles(self, original: Style, gradient_style: Style) -> Style:
        """Leave highlighted tokens alone; apply the gradient to everything else.

        Args:
            original: The segment's style from the Pygments theme.
            gradient_style: The gradient color for the segment's position.

        Returns:
            ``original`` unchanged for highlighted tokens (when
            ``keep_token_colors`` is on); otherwise the merged style.
        """
        color = original.color
        if self._base_color is not None and color is not None and color != self._base_color:
            return original
        return super()._merge_styles(original, gradient_style)

    @property
    def syntax(self) -> RichSyntax:
        """The underlying Rich Syntax renderable."""
        return self._syntax


def demo() -> None:
    """Render a small gradient syntax demo to the terminal."""
    console = Console(width=88)
    code = """\
from rich.console import Console
from rich_gradient import Syntax

console = Console()
console.print(Syntax("print('hello')", "python"))
"""
    syntax = Syntax(
        code,
        "python",
        colors=["#38bdf8", "#a855f7", "#f97316"],
        line_numbers=True,
        dedent=True,
        padding=(1, 2),
        highlight_words={"Syntax": "bold white"},
    )
    console.print(syntax)


if __name__ == "__main__":
    demo()
