"""Gradient-enabled convenience wrapper for Rich Syntax."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from pygments.lexer import Lexer
from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console
from rich.padding import PaddingDimensions
from rich.syntax import Syntax as RichSyntax

from rich_gradient.gradient import (ColorType, Gradient, HighlightRegexType,
                                    HighlightWordsType)


class Syntax(Gradient):
    """A Rich syntax-highlighting convenience constructor with gradient rendering.

    Args:
        code: Source code to highlight.
        lexer: Lexer name or Pygments lexer instance.
        theme: Pygments style theme.
        dedent: Whether to strip initial indentation.
        line_numbers: Whether to render line numbers.
        start_line: Starting line number.
        line_range: Optional start/end line range.
        highlight_lines: Optional line numbers to highlight.
        code_width: Optional code width.
        tab_size: Spaces per tab.
        word_wrap: Whether to wrap long lines.
        background_color: Optional background color.
        indent_guides: Whether to show indentation guides.
        padding: Padding around syntax output.
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
        repeat_scale: float = 2.0,
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        console: Console | None = None,
        highlight_words: HighlightWordsType | None = None,
        highlight_regex: HighlightRegexType | None = None,
    ) -> None:
        """Initialize gradient-enabled Rich syntax highlighting."""
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
        )

    @property
    def syntax(self) -> RichSyntax:
        """Return the underlying Rich Syntax renderable."""
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
