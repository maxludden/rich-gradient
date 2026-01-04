"""Animated gradient text rendered with Rich Live."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence, TypeAlias

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console
from rich.text import Text as RichText
from rich.text import TextType

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import ColorType, HighlightRegexType, HighlightWordsType
from rich_gradient.text import Text as GradientText

TextSource: TypeAlias = TextType

__all__ = ["AnimatedText"]

_console = Console()

def create_text_renderable(
    text: TextSource,
    *,
    markup: bool = True,
    text_kwargs: Optional[Mapping[str, Any]] = None,
) -> RichText:
    """Create a Rich Text renderable from a string or Text instance."""
    if isinstance(text, GradientText):
        return text.as_rich()
    if isinstance(text, RichText):
        return text

    kwargs = dict(text_kwargs or {})
    if markup:
        return RichText.from_markup(text, **kwargs)
    return RichText(text, **kwargs)


class AnimatedText(AnimatedGradient):
    """Animated gradient variant for text content."""

    def __init__(
        self,
        text: TextSource,
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
        text_kwargs: Optional[Mapping[str, Any]] = None,
        markup: bool = True,
        auto_refresh: bool = True,
        refresh_per_second: float = 30.0,
        console: Console = _console,
        transient: bool = False,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        animate: Optional[bool] = None,
        duration: Optional[float] = None,
    ) -> None:
        renderable = create_text_renderable(
            text,
            markup=markup,
            text_kwargs=text_kwargs,
        )
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
        self._text_kwargs: dict[str, Any] = dict(text_kwargs or {})
        self._markup = bool(markup)

    @property
    def rich_text(self) -> RichText:
        """Return the underlying Rich Text renderable."""
        if not self.renderables:
            raise RuntimeError("Text renderables have not been initialised.")
        renderable = self.renderables[0]
        if not isinstance(renderable, RichText):
            raise TypeError("Stored renderable is not a Rich Text instance.")
        return renderable

    def update_text(
        self,
        text: TextSource,
        *,
        text_kwargs: Optional[Mapping[str, Any]] = None,
        markup: Optional[bool] = None,
    ) -> None:
        """Replace the Text content safely during animation."""
        with self._lock:
            if isinstance(text, GradientText):
                self.renderables = [text.as_rich()]
                return
            if isinstance(text, RichText):
                self.renderables = [text]
                return

            effective_markup = self._markup if markup is None else bool(markup)
            effective_kwargs = (
                self._text_kwargs if text_kwargs is None else dict(text_kwargs)
            )
            renderable = create_text_renderable(
                text,
                markup=effective_markup,
                text_kwargs=effective_kwargs,
            )
            self.renderables = [renderable]

            if text_kwargs is not None:
                self._text_kwargs = dict(text_kwargs)
            if markup is not None:
                self._markup = bool(markup)


if __name__ == "__main__":
    from time import sleep

    from rich.live import Live


    animated_text = AnimatedText(
        "Hello, World! This is animated gradient text with Rich!",
        rainbow=True,
        justify="center",
        expand=True,
        animate=True,
        duration=4.0
    )
    with Live(
        animated_text,
        console=_console,
        refresh_per_second=30.0
    ) as live:
        animated_text.start()
        try:
            dur = animated_text.duration or 4.0
            sleep(dur)
        finally:
            animated_text.stop()
    _console.line()

