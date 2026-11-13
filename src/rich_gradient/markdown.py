"""Gradient-enabled Markdown renderables built on top of Rich."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console
from rich.markdown import Markdown as RichMarkdown

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import (ColorType, Gradient, HighlightRegexType,
                                    HighlightWordsType)
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

MarkdownSource: TypeAlias = str | RichMarkdown

__all__ = ["Markdown", "create_markdown_renderable"]


class GradientRichMarkdown(RichMarkdown):
    """Rich Markdown variant that compares equal to its original source string.

    Args:
        source (str): The Markdown source text.
        **kwargs (Any): Keyword arguments forwarded to ``rich.markdown.Markdown``, e.g.
            ``code_theme="dracula"``.
    """

    def __init__(self, source: str, **kwargs: Any) -> None:
        """Initialize the Markdown and remember its source (see the class docstring)."""
        self._rg_source = source
        super().__init__(source, **kwargs)

    def __eq__(self, other: object) -> bool:  # pragma: no cover - trivial comparison
        """Compare equal to another instance or a string with the same source.

        Args:
            other: The object to compare with.

        Returns:
            ``True`` if ``other`` has (or is) the same Markdown source.
        """
        if isinstance(other, GradientRichMarkdown):
            return self._rg_source == other._rg_source
        if isinstance(other, str):
            return self._rg_source == other
        return super().__eq__(other)


def create_markdown_renderable(
    markdown: MarkdownSource,
    markdown_kwargs: Mapping[str, Any] | None = None,
) -> RichMarkdown:
    """Normalize Markdown input into a Rich Markdown renderable.

    Args:
        markdown: Markdown source text, e.g. ``"# Title"``, or an existing Rich
            ``Markdown`` renderable.
        markdown_kwargs: Keyword arguments for ``rich.markdown.Markdown`` when
            ``markdown`` is a string, e.g. ``{"code_theme": "dracula"}``.
            Defaults to None.

    Returns:
        The Rich ``Markdown`` unchanged, or a new ``GradientRichMarkdown`` built
        from the source text.

    Raises:
        ValueError: If ``markdown_kwargs`` is given with a Rich ``Markdown``.
        TypeError: If ``markdown`` is neither a string nor a Rich ``Markdown``.
    """
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
    return GradientRichMarkdown(markdown, **kwargs)


class Markdown(Gradient):
    """Apply rich-gradient coloring to Markdown content.

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
        justify (AlignMethod): Horizontal alignment of the Markdown: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the Markdown:
            ``"top"``, ``"middle"``, or ``"bottom"``. Defaults to ``"top"``.
        repeat_scale (Optional[float]): Width of one full color cycle as a multiple of
            the rendered width; larger values give a more gradual gradient, e.g.
            ``1.5``. ``None`` derives it from the stops so one pass runs from the first
            color to the last (1.0 for two colors, 2.0 for three or more). Defaults to
            None.
        console (Optional[Console]): Console used for rendering and measurement.
            Defaults to ``rich.get_console()``.
        highlight_words (Optional[HighlightWordsType]): Words to restyle on top of the
            gradient. Accepts a mapping of a word (or a tuple of words) to a style, e.g.
            ``{"error": "bold red", ("warn", "caution"): "yellow"}``; a sequence of
            ``(words, style[, case_sensitive])`` tuples, e.g.
            ``[("error", "bold red"), (("warn", "caution"), "yellow", False)]``; or
            ``HighlightWords`` instances, e.g.
            ``[HighlightWords(words=("error",), style=Style.parse("bold red"))]``.
            Matching is case-sensitive unless ``case_sensitive`` is False. Colors in
            these styles are shown: they replace the gradient on the matched text.
            Defaults to None.
        highlight_regex (Optional[HighlightRegexType]): Regular expressions whose
            matches are restyled on top of the gradient. Accepts a mapping of a pattern
            to a style, e.g. ``{r"[0-9]+": "bold cyan"}``; a sequence of
            ``(pattern, style[, flags])`` tuples, e.g.
            ``[(r"error|fail", "red", re.IGNORECASE)]``; or ``HighlightRegex``
            instances, e.g.
            ``[HighlightRegex(pattern=re.compile(r"[0-9]+"), style=Style.parse("cyan"))]``.
            Colors in these styles are shown: they replace the gradient on the matched
            text. Defaults to None.
        markdown_kwargs (Optional[Mapping[str, Any]]): Keyword arguments for
            ``rich.markdown.Markdown`` when ``markdown`` is a string, e.g.
            ``{"code_theme": "dracula", "hyperlinks": False}``. Must be omitted for a
            Rich ``Markdown`` instance. Defaults to None.
        animate (bool): Mark the content as changing between renders, so highlight
            matches are recomputed every frame instead of cached. Static renderables
            never animate on their own; use the ``Animated*`` classes for live
            animation. Defaults to False.
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
        repeat_scale: float | None = None,
        console: Console | None = None,
        highlight_words: HighlightWordsType | None = None,
        highlight_regex: HighlightRegexType | None = None,
        markdown_kwargs: Mapping[str, Any] | None = None,
        animate: bool = False,
    ) -> None:
        """Initialize the gradient Markdown; see the class docstring for arguments.

        Raises:
            ValueError: If ``markdown_kwargs`` is given with a Rich ``Markdown`` instance.
            TypeError: If ``markdown`` is neither a string nor a Rich ``Markdown``.
        """
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
            animate=animate,
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
        """Replace the Markdown content while reusing gradient configuration.

        Args:
            markdown: New Markdown source text, e.g. ``"# Updated"``, or a Rich
                ``Markdown`` renderable.
            markdown_kwargs: Keyword arguments for ``rich.markdown.Markdown``, e.g.
                ``{"code_theme": "dracula"}``. Defaults to None, which reuses the
                previous kwargs for string input.

        Raises:
            ValueError: If ``markdown_kwargs`` is given with a Rich ``Markdown``.
            TypeError: If ``markdown`` is neither a string nor a Rich ``Markdown``.
        """
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


MD_TEXT: str = """# **Rich Gradient Markdown**

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


def markdown_example(markdown: str = MD_TEXT) -> None:
    """Render a Markdown example and save it to ``docs/img/markdown_example.svg``.

    Args:
        markdown: Markdown content to render. Defaults to ``MD_TEXT``, a short
            sample document.
    """
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
