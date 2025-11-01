"""Gradient-enabled Markdown renderables built on top of Rich."""

from __future__ import annotations

import time
from typing import Any, Mapping, Optional, Sequence, TypeAlias, cast

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown as RichMarkdown

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import (
    ColorType,
    Gradient,
    HighlightRegexType,
    HighlightWordsType,
)
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

MarkdownSource: TypeAlias = str | RichMarkdown

__all__ = ["Markdown", "create_markdown_renderable"]


def create_markdown_renderable(
    markdown: MarkdownSource,
    markdown_kwargs: Optional[Mapping[str, Any]] = None,
) -> RichMarkdown:
    """Normalize Markdown input into a Rich Markdown renderable."""
    if isinstance(markdown, RichMarkdown):
        if markdown_kwargs:
            raise ValueError(
                "markdown_kwargs cannot be provided when supplying a Rich Markdown instance."
            )
        return markdown
    if not isinstance(markdown, str):
        raise TypeError(
            "markdown must be either a string of Markdown content or a Rich Markdown instance."
        )
    kwargs = dict(markdown_kwargs or {})
    return RichMarkdown(markdown, **kwargs)


class Markdown(Gradient):
    """Apply rich-gradient coloring to Markdown content."""

    def __init__(
        self,
        markdown: MarkdownSource,
        *,
        colors: Optional[Sequence[ColorType]] = None,
        bg_colors: Optional[Sequence[ColorType]] = None,
        rainbow: bool = False,
        hues: int = 5,
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "top",
        repeat_scale: float = 4.0,
        console: Optional[Console] = None,
        highlight_words: Optional[HighlightWordsType] = None,
        highlight_regex: Optional[HighlightRegexType] = None,
        markdown_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> None:
        renderable = create_markdown_renderable(markdown, markdown_kwargs)
        super().__init__(
            renderables=renderable,
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
        self._markdown_kwargs: dict[str, Any] = (
            dict(markdown_kwargs or {}) if isinstance(markdown, str) else {}
        )

    @property
    def rich_markdown(self) -> RichMarkdown:
        """Return the underlying Rich Markdown renderable."""
        if not self.renderables:
            raise RuntimeError("Markdown renderables have not been initialised.")
        renderable = self.renderables[0]
        if not isinstance(renderable, RichMarkdown):
            raise TypeError("Stored renderable is not a Rich Markdown instance.")
        return cast(RichMarkdown, renderable)

    def update_markdown(
        self,
        markdown: MarkdownSource,
        *,
        markdown_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> None:
        """Replace the Markdown content while reusing gradient configuration."""
        if isinstance(markdown, str):
            effective_kwargs = (
                markdown_kwargs
                if markdown_kwargs is not None
                else self._markdown_kwargs
            )
            renderable = create_markdown_renderable(markdown, effective_kwargs)
            self.renderables = [renderable]
            if markdown_kwargs is not None:
                self._markdown_kwargs = dict(markdown_kwargs)
            else:
                self._markdown_kwargs = dict(effective_kwargs or {})
        else:
            renderable = create_markdown_renderable(markdown, markdown_kwargs)
            self.renderables = [renderable]
            self._markdown_kwargs = {}


MD_TEXT: str = """# **Rich Gradient Markdown**

This is an example of **Markdown** content rendered with `rich-gradient`.

## Features

- Gradient text coloring
- Support for all standard Markdown elements
- Customizable colors and styles

```python
from rich_gradient.markdown import Markdown
md = Markdown("# Hello, World!", colors=["red", "blue"])
"""


def markdown_example(markdown: str = MD_TEXT) -> None:
    _console = Console(record=True, width=64)
    _console.line(2)
    _console.print(Markdown(markdown))
    _console.line(2)
    _console.save_svg(
        "docs/img/markdown_example.svg",
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME,
    )


if __name__ == "__main__":
    markdown_example()
