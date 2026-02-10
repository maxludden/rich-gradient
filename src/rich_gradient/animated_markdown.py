"""Gradient-enabled Markdown renderables built on top of Rich."""

from __future__ import annotations

import time
from typing import Any, Mapping, Optional, Sequence, TypeAlias, cast

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console
from rich.markdown import Markdown as RichMarkdown

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import ColorType, HighlightRegexType, HighlightWordsType
from rich_gradient.markdown import Markdown, create_markdown_renderable
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

MarkdownSource: TypeAlias = str | RichMarkdown

__all__ = ["Markdown", "AnimatedMarkdown"]


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
        repeat_scale: float = 4.0,
        highlight_words: Optional[HighlightWordsType] = None,
        highlight_regex: Optional[HighlightRegexType] = None,
        markdown_kwargs: Optional[Mapping[str, Any]] = None,
        auto_refresh: bool = True,
        refresh_per_second: float = 30.0,
        console: Optional[Console] = None,
        transient: bool = False,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        animate: Optional[bool] = None,
        duration: Optional[float] = None,
    ) -> None:
        renderable = create_markdown_renderable(markdown, markdown_kwargs)
        super().__init__(
            renderables=renderable,
            colors=list(colors) if colors is not None else None,
            bg_colors=list(bg_colors) if bg_colors is not None else None,
            auto_refresh=auto_refresh,
            refresh_per_second=refresh_per_second,
            console=console or Console(),
            transient=transient,
            redirect_stdout=redirect_stdout,
            redirect_stderr=redirect_stderr,
            expand=expand,
            justify=justify,
            vertical_justify=vertical_justify,
            hues=hues,
            rainbow=rainbow,
            repeat_scale=repeat_scale,
            highlight_words=highlight_words,
            highlight_regex=highlight_regex,
            animate=animate,
            duration=duration,
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


MD_TEXT: str = """# **Animated Markdown Gradient**

This is an example of **Markdown** content rendered with `rich-gradient`.

## Features

- Gradient text coloring
- Support for all standard Markdown elements
- Customizable colors and styles

```python
from rich_gradient.markdown import Markdown
md = Markdown("# Hello, World!", colors=["red", "blue"])
```
"""


def animated_markdown_example(md: str = MD_TEXT) -> None:
    """Demonstrate AnimatedMarkdown with example content.
    Args:
        md (str): Markdown content to render.
    """
    _console = Console(width=64)
    _console.line(2)

    animated_md = AnimatedMarkdown(
        md,
        bg_colors=["#000"],
        rainbow=True,
        hues=10,
        justify="center",
        vertical_justify="middle",
        repeat_scale=4.0,
        highlight_words={"rich-gradient": "bold white"},
        highlight_regex={"from|import|\\(|\\)": "italic white"},
        auto_refresh=True,
        refresh_per_second=30.0,
        console=_console,
        transient=False,
        redirect_stdout=True,
        redirect_stderr=True,
        animate=True,
        duration=5.0,
    )
    with animated_md as am:
        am.start()
        duration = getattr(am, "duration", None)
        if duration is None:
            duration = 5.0
        time.sleep(duration)

    animated_md.stop()
    _console.save_svg(
        "docs/img/animated_markdown_example.svg",
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME,
    )


if __name__ == "__main__":
    animated_markdown_example()
