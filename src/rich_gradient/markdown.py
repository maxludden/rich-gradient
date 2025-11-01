"""Gradient-enabled Markdown renderables built on top of Rich."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence, TypeAlias, cast

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console
from rich.markdown import Markdown as RichMarkdown

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import (
    ColorType,
    Gradient,
    HighlightRegexType,
    HighlightWordsType,
)

MarkdownSource: TypeAlias = str | RichMarkdown

__all__ = ["Markdown", "AnimatedMarkdown"]


def _create_markdown_renderable(
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
        repeat_scale: float = 2.0,
        console: Optional[Console] = None,
        highlight_words: Optional[HighlightWordsType] = None,
        highlight_regex: Optional[HighlightRegexType] = None,
        markdown_kwargs: Optional[Mapping[str, Any]] = None,
    ) -> None:
        renderable = _create_markdown_renderable(markdown, markdown_kwargs)
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
            effective_kwargs = markdown_kwargs if markdown_kwargs is not None else self._markdown_kwargs
            renderable = _create_markdown_renderable(markdown, effective_kwargs)
            self.renderables = renderable
            if markdown_kwargs is not None:
                self._markdown_kwargs = dict(markdown_kwargs)
            else:
                self._markdown_kwargs = dict(effective_kwargs or {})
        else:
            renderable = _create_markdown_renderable(markdown, markdown_kwargs)
            self.renderables = renderable
            self._markdown_kwargs = {}


class AnimatedMarkdown(AnimatedGradient):
    """Animated gradient variant for Markdown content."""

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
        repeat_scale: float = 2.0,
        highlight_words: Optional[HighlightWordsType] = None,
        highlight_regex: Optional[HighlightRegexType] = None,
        markdown_kwargs: Optional[Mapping[str, Any]] = None,
        auto_refresh: bool = True,
        refresh_per_second: float = 30.0,
        console: Optional[Console] = None,
        transient: bool = False,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        disable: bool = False,
        phase_per_second: Optional[float] = None,
        speed: Optional[int] = None,
    ) -> None:
        renderable = _create_markdown_renderable(markdown, markdown_kwargs)
        super().__init__(
            renderables=renderable,
            colors=list(colors) if colors is not None else None,
            bg_colors=list(bg_colors) if bg_colors is not None else None,
            auto_refresh=auto_refresh,
            refresh_per_second=refresh_per_second,
            console=console,
            transient=transient,
            redirect_stdout=redirect_stdout,
            redirect_stderr=redirect_stderr,
            disable=disable,
            expand=expand,
            justify=justify,
            vertical_justify=vertical_justify,
            hues=hues,
            rainbow=rainbow,
            phase_per_second=phase_per_second,
            speed=speed,
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
        """Replace the Markdown content safely during animation."""
        with self._lock:
            if isinstance(markdown, str):
                effective_kwargs = (
                    markdown_kwargs
                    if markdown_kwargs is not None
                    else self._markdown_kwargs
                )
                renderable = _create_markdown_renderable(markdown, effective_kwargs)
                self.renderables = renderable
                if markdown_kwargs is not None:
                    self._markdown_kwargs = dict(markdown_kwargs)
                else:
                    self._markdown_kwargs = dict(effective_kwargs or {})
            else:
                renderable = _create_markdown_renderable(markdown, markdown_kwargs)
                self.renderables = renderable
                self._markdown_kwargs = {}

if __name__ == "__main__":
    console = Console(record=True, width=64)
    console.line()
    md_content = """# Rich Gradient Markdown
This is an example of **rich-gradient** applied to Markdown content. You can
use *all* of Rich's [link](https://rich.readthedocs.io/en/stable/markdown.html)
features, including:
- Lists
- Code blocks
- Tables
- And more!

```python
from rich_gradient.markdown import Markdown

md = Markdown("# Hello, World!", colors=["#ff0000", "#0000ff"])
console.print(md)
```
    console.print(
