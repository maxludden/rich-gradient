"""Animated gradient text rendered with Rich Live."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypeAlias

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console
from rich.live import Live
from rich.text import Text as RichText
from rich.text import TextType

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import (ColorType, HighlightRegexType,
                                    HighlightWordsType)
from rich_gradient.text import Text as GradientText

TextSource: TypeAlias = TextType

__all__ = ["AnimatedText"]

_console = Console()


def create_text_renderable(
    text: TextSource,
    *,
    markup: bool = True,
    text_kwargs: Mapping[str, Any] | None = None,
) -> RichText:
    """Create a Rich Text renderable from a string or Text instance.

    Args:
        text: A string, Rich ``Text``, or rich-gradient ``Text``.
        markup: Parse Rich console markup in string input. Defaults to True.
        text_kwargs: Keyword arguments forwarded to ``rich.text.Text`` (or
            ``Text.from_markup``) for string input, e.g. ``{"justify": "center"}``.
            Ignored for ``Text`` input. Defaults to None.

    Returns:
        A plain Rich ``Text``. Rich ``Text`` input is returned unchanged and
        rich-gradient ``Text`` is converted with ``as_rich()``.
    """
    if isinstance(text, GradientText):
        return text.as_rich()
    if isinstance(text, RichText):
        return text

    kwargs = dict(text_kwargs or {})
    if markup:
        return RichText.from_markup(text, **kwargs)
    return RichText(text, **kwargs)


class AnimatedText(AnimatedGradient):
    """Animated gradient variant for text content.

    Args:
        text (TextType): The text: a string, Rich ``Text``, or rich-gradient ``Text``,
            e.g. ``"[bold]Loading[/bold]..."``.
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
        text_kwargs (Optional[Mapping[str, Any]]): Keyword arguments for
            ``rich.text.Text`` when ``text`` is a string, e.g.
            ``{"justify": "center"}``. Defaults to None.
        markup (bool): Parse Rich console markup in string input. Defaults to True.
        auto_refresh (bool): Let ``Live`` refresh the display on its own timer. Defaults
            to True.
        refresh_per_second (float): Live refresh and animation frame rate, in frames per
            second. Must be positive. Defaults to 30.0.
        console (Console): Console to render to. Defaults to a module-level
            ``Console()`` shared by all ``AnimatedText`` instances.
        transient (bool): Clear the output from the terminal when the animation stops.
            Defaults to False.
        redirect_stdout (bool): Redirect ``sys.stdout`` into the Live display so prints
            appear above it. Defaults to False.
        redirect_stderr (bool): Redirect ``sys.stderr`` into the Live display so prints
            appear above it. Defaults to False.
        animate (Optional[bool]): Whether to animate. The global config is a kill
            switch: when ``config.animation_enabled`` is False (``"animate": false`` in
            the config file, or ``RICH_GRADIENT_ANIMATE=0``), nothing animates, even if
            this is True. ``False`` renders a single static frame. ``None`` is treated
            as True. Defaults to True.
        duration (Optional[float]): Seconds after which a running animation stops on its
            own, e.g. ``5.0``. Must be positive. ``None`` runs until stopped. Defaults
            to None.

    Raises:
        ValueError: If ``hues`` < 2, or ``refresh_per_second``/``duration`` is not
            positive.
    """

    def __init__(
        self,
        text: TextSource,
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
        text_kwargs: Mapping[str, Any] | None = None,
        markup: bool = True,
        auto_refresh: bool = True,
        refresh_per_second: float = 30.0,
        console: Console = _console,
        transient: bool = False,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        animate: bool | None = True,
        duration: float | None = None,
    ) -> None:
        """Initialize the animated text; see the class docstring for arguments.

        Raises:
            ValueError: If ``hues`` < 2, or ``refresh_per_second``/``duration`` is
                not positive.
        """
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
        """The underlying Rich Text renderable.

        Raises:
            RuntimeError: If no renderable has been stored yet.
            TypeError: If the stored renderable is not a Rich ``Text``.
        """
        if not self.renderables:
            raise RuntimeError("Text renderables have not been initialized.")
        renderable = self.renderables[0]
        if not isinstance(renderable, RichText):
            raise TypeError("Stored renderable is not a Rich Text instance.")
        return renderable

    def update_text(
        self,
        text: TextSource,
        *,
        text_kwargs: Mapping[str, Any] | None = None,
        markup: bool | None = None,
    ) -> None:
        """Replace the Text content safely during animation.

        Args:
            text: New content: a string, Rich ``Text``, or rich-gradient ``Text``.
            text_kwargs: Keyword arguments for ``rich.text.Text`` for string input,
                e.g. ``{"justify": "center"}``. Defaults to None, which reuses the
                previous kwargs.
            markup: Parse console markup in string input. Defaults to None,
                which reuses the previous setting.
        """
        with self._lock:
            if isinstance(text, GradientText):
                self._set_renderables([text.as_rich()])
                return
            if isinstance(text, RichText):
                self._set_renderables([text])
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
            self._set_renderables([renderable])

            if text_kwargs is not None:
                self._text_kwargs = dict(text_kwargs)
            if markup is not None:
                self._markup = bool(markup)


if __name__ == "__main__":
    from time import sleep

    animated_text = AnimatedText(
        "Hello, World! This is animated gradient text with Rich!",
        rainbow=True,
        justify="center",
        expand=True,
        animate=True,
        duration=4.0,
    )
    with Live(animated_text, console=_console, refresh_per_second=30.0) as live:
        animated_text.start()
        try:
            dur = animated_text.duration or 4.0
            sleep(dur)
        finally:
            animated_text.stop()
    _console.line()
