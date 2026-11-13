"""Gradient-enabled Markdown renderables built on top of Rich."""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console
from rich.markdown import Markdown as RichMarkdown

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import (ColorType, HighlightRegexType,
                                    HighlightWordsType)
from rich_gradient.markdown import Markdown, create_markdown_renderable
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

MarkdownSource: TypeAlias = str | RichMarkdown

__all__ = ["AnimatedMarkdown", "Markdown"]


class AnimatedMarkdown(AnimatedGradient):
    """Animated gradient variant for Markdown content.

    Args:
        markdown (str | rich.markdown.Markdown): Markdown source text, e.g.
            ``"# Title"``, or an existing Rich ``Markdown`` renderable.
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
        expand (bool): Expand the output to the full console width. Defaults to True.
        justify (AlignMethod): Horizontal alignment of the content: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the content:
            ``"top"``, ``"middle"``, or ``"bottom"``. Defaults to ``"top"``.
        repeat_scale (float): Width of one full color cycle as a multiple of the
            rendered width; larger values give a more gradual gradient. Defaults to 4.0.
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
        markdown_kwargs (Optional[Mapping[str, Any]]): Keyword arguments for
            ``rich.markdown.Markdown`` when ``markdown`` is a string, e.g.
            ``{"code_theme": "dracula"}``. Must be omitted for a Rich ``Markdown``
            instance. Defaults to None.
        auto_refresh (bool): Let ``Live`` refresh the display on its own timer. Defaults
            to True.
        refresh_per_second (float): Live refresh and animation frame rate, in frames per
            second. Must be positive. Defaults to 30.0.
        console (Optional[Console]): Console used for rendering and measurement.
            Defaults to a new ``Console()``.
        transient (bool): Clear the output from the terminal when the animation stops.
            Defaults to False.
        redirect_stdout (bool): Redirect ``sys.stdout`` into the Live display so prints
            appear above it. Defaults to False.
        redirect_stderr (bool): Redirect ``sys.stderr`` into the Live display so prints
            appear above it. Defaults to False.
        animate (Optional[bool]): Whether to animate. ``None`` defers to
            ``config.animation_enabled`` (the ``RICH_GRADIENT_ANIMATE`` setting);
            ``False`` renders a single static frame. Defaults to None.
        duration (Optional[float]): Seconds after which a running animation stops on its
            own, e.g. ``5.0``. Must be positive. ``None`` runs until stopped. Defaults
            to None.

    Raises:
        ValueError: If ``markdown_kwargs`` is given with a Rich ``Markdown`` instance,
            or ``refresh_per_second``/``duration`` is not positive.
        TypeError: If ``markdown`` is neither a string nor a Rich ``Markdown``.
    """

    def __init__(
        self,
        markdown: MarkdownSource,
        *,
        colors: Sequence[ColorType] | None = None,
        bg_colors: Sequence[ColorType] | None = None,
        rainbow: bool = False,
        hues: int = 5,
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "top",
        repeat_scale: float = 4.0,
        highlight_words: HighlightWordsType | None = None,
        highlight_regex: HighlightRegexType | None = None,
        markdown_kwargs: Mapping[str, Any] | None = None,
        auto_refresh: bool = True,
        refresh_per_second: float = 30.0,
        console: Console | None = None,
        transient: bool = False,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        animate: bool | None = None,
        duration: float | None = None,
    ) -> None:
        """Initialize the animated Markdown; see the class docstring for arguments.

        Raises:
            ValueError: If ``markdown_kwargs`` is given with a Rich ``Markdown``
                instance, or ``refresh_per_second``/``duration`` is not positive.
            TypeError: If ``markdown`` is neither a string nor a Rich ``Markdown``.
        """
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
        """The underlying Rich Markdown renderable.

        Raises:
            RuntimeError: If no renderable has been stored yet.
            TypeError: If the stored renderable is not a Rich ``Markdown``.
        """
        if not self.renderables:
            raise RuntimeError("Markdown renderables have not been initialised.")
        renderable = self.renderables[0]
        if not isinstance(renderable, RichMarkdown):
            raise TypeError("Stored renderable is not a Rich Markdown instance.")
        return renderable

    def update_markdown(
        self,
        markdown: MarkdownSource,
        *,
        markdown_kwargs: Mapping[str, Any] | None = None,
    ) -> None:
        """Replace the Markdown content safely during animation.

        Args:
            markdown: New Markdown source text or a Rich ``Markdown`` renderable.
            markdown_kwargs: Keyword arguments for ``rich.markdown.Markdown``, e.g.
                ``{"code_theme": "dracula"}``. Defaults to None, which reuses the
                previous kwargs for string input.

        Raises:
            ValueError: If ``markdown_kwargs`` is given with a Rich ``Markdown``.
            TypeError: If ``markdown`` is neither a string nor a Rich ``Markdown``.
        """
        with self._lock:
            if isinstance(markdown, str):
                effective_kwargs = (
                    markdown_kwargs
                    if markdown_kwargs is not None
                    else self._markdown_kwargs
                )
                renderable = create_markdown_renderable(markdown, effective_kwargs)
                self._set_renderables([renderable])
                if markdown_kwargs is not None:
                    self._markdown_kwargs = dict(markdown_kwargs)
                else:
                    self._markdown_kwargs = dict(effective_kwargs or {})
            else:
                renderable = create_markdown_renderable(markdown, markdown_kwargs)
                self._set_renderables([renderable])
                self._markdown_kwargs = {}


MD_TEXT: str = """# **Animated Markdown Gradient**

This is an example of **Markdown** content rendered with `rich-gradient`.

## Features

- Gradient text coloring
- Support for all standard Markdown elements
- Customizable colors and styles

```python
from rich_gradient.markdown import Markdown
md = Markdown("# Hello, World!", colors=["#f00", "blue"])
```
"""


def animated_markdown_example(md: str = MD_TEXT) -> None:
    """Demonstrate AnimatedMarkdown with example content.

    Args:
        md (str): Markdown content to render. Defaults to ``MD_TEXT``, a short
            sample document.
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
