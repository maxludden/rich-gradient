"""Animated gradient Rule rendered with Rich Live.

This module provides an AnimatedRule class that mirrors the behavior of
``rich_gradient.rule.Rule`` but animates the gradient over time using the
same Live/animation machinery as ``AnimatedGradient`` and ``AnimatedPanel``.
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from threading import Event, Thread
from time import sleep
from typing import Optional

from rich.align import AlignMethod
from rich.color import ColorParseError
from rich.console import Console, ConsoleOptions, RenderResult
from rich.rule import Rule as RichRule
from rich.style import Style, StyleType
from rich.text import Text as RichText
from rich.text import TextType

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import ColorType
from rich_gradient.text import Text

__all__ = ["AnimatedRule"]


# Thickness-to-character mapping (kept in sync with rule.Rule)
CHARACTER_MAP = {0: "─", 1: "━", 2: "═", 3: "█"}


class AnimatedRule(AnimatedGradient):
    """A Rich Rule that animates a gradient across the line.

    Args:
            title: Optional title text placed within the rule.
            title_style: Style applied to the title text after gradients.
            colors: Foreground gradient color stops.
            bg_colors: Background gradient color stops.
            rainbow: If True, generate a rainbow regardless of colors.
            hues: Number of hues when generating default spectrum.
            thickness: 0..3 selects line character style.
            style: Base style for the rule line (merged with gradients).
            end: Trailing characters after the rule (default newline).
            align: Alignment for the rule within the available width.
            auto_refresh: Whether the Live context refreshes on its own.
            refresh_per_second: Target frames per second.
            console: Console to render to.
            transient: Keep Live transient (don’t clear on stop).
            redirect_stdout: Redirect stdout to Live.
            redirect_stderr: Redirect stderr to Live.
            repeat_scale: Stretch factor for gradient color stops.
            animate (bool | None): Toggle animation on or off. ``None`` defers to
                the global configuration.
            duration: Optional duration in seconds for automatic stop.
    """

    def __init__(
        self,
        title: str | None = None,
        title_style: StyleType = "bold",
        colors: Sequence[ColorType] | None = None,
        bg_colors: Sequence[ColorType] | None = None,
        *,
        rainbow: bool = False,
        hues: int = 7,
        thickness: int = 2,
        style: StyleType = "",
        end: str = "\n",
        align: AlignMethod = "center",
        # Live / animation parameters (mirroring AnimatedGradient)
        auto_refresh: bool = True,
        refresh_per_second: float = 20.0,
        console: Console | None = None,
        transient: bool = False,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        repeat_scale: float = 4.0,
        animate: bool | None = None,
        duration: float | None = None,
    ) -> None:
        rule_title = title or ""
        self.title = rule_title
        self.title_style = title_style
        self.thickness = thickness

        base_rule = RichRule(
            title=rule_title,
            characters=self.characters,
            style=style,
            end=end,
            align=align,
        )

        try:
            highlight_words = {self.title: self.title_style} if self.title else None

            super().__init__(
                renderables=base_rule,
                colors=list(colors) if colors is not None else None,
                bg_colors=list(bg_colors) if bg_colors is not None else None,
                auto_refresh=auto_refresh,
                refresh_per_second=refresh_per_second,
                console=console,
                transient=transient,
                redirect_stdout=redirect_stdout,
                redirect_stderr=redirect_stderr,
                expand=True,
                justify=align,
                vertical_justify="middle",
                hues=hues,
                rainbow=rainbow,
                repeat_scale=repeat_scale,
                highlight_words=highlight_words,
                animate=animate,
                duration=duration,
            )
            if self.animate:
                # Rules look better with a slightly faster cycle than the base default.
                self._phase_per_second = 0.25
        except ColorParseError as err:
            raise ValueError(f"Invalid color provided: {err}") from err

    @contextmanager
    def for_duration(self, duration: float) -> Iterator[AnimatedRule]:
        """Run the rule animation for ``duration`` seconds within a context.

        The animation starts when entering the context and will stop
        automatically once the requested duration elapses. Leaving the context
        early stops the animation immediately.
        """
        if duration <= 0:
            raise ValueError("duration must be greater than 0")
        cancel = Event()

        def _auto_stop() -> None:
            if not cancel.wait(duration):
                self.stop()

        timer = Thread(target=_auto_stop, daemon=True)
        self.start()
        timer.start()
        try:
            yield self
        finally:
            cancel.set()
            self.stop()
            timer.join(timeout=max(duration, 0.1))

    # underlying RichRule expands correctly across the console width,
    # while still applying animated gradient styles per character.
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        content = self.renderables[0] if self.renderables else RichText("")
        yield from self._render_styled_lines(
            console, options, content, trailing_newline=True
        )

    # For Rules, let the underlying RichRule handle width/align. Avoid the
    # outer Align wrapper from AnimatedGradient to prevent the line from
    # collapsing under nested alignment contexts.
    def get_renderable(self):  # type: ignore[override]
        return self

    # -----------------
    # Properties (parity with Rule)
    # -----------------
    @property
    def title(self) -> TextType | None:
        """The title text of the Rule."""
        return self._title or None

    @title.setter
    def title(self, value: TextType | None) -> None:
        """Set the title text of the Rule."""
        if value is not None and not isinstance(value, (str, RichText, Text)):
            raise TypeError(
                f"title must be str, RichText, or Text, got {type(value).__name__}"
            )
        self._title = value

    @property
    def title_style(self) -> StyleType | None:
        """The style applied to the title text of the Rule."""
        return self._title_style or None

    @title_style.setter
    def title_style(self, value: StyleType | None) -> None:
        """Set the style applied to the title text of the Rule."""
        if value is not None and not isinstance(value, (str, Style)):
            raise TypeError(
                f"title_style must be str or Style, got {type(value).__name__}"
            )
        self._title_style = Style.parse(str(value)) if value is not None else None

    @property
    def thickness(self) -> int:
        """The thickness of the Rule line (0..3)."""
        for key, char in CHARACTER_MAP.items():
            if char == self.characters:
                return key
        return 1  # Default if character is custom

    @thickness.setter
    def thickness(self, value: int):
        """Set the thickness of the Rule line (0..3)."""
        if value not in CHARACTER_MAP:
            raise ValueError(f"thickness must be one of {list(CHARACTER_MAP.keys())}")
        self.characters = CHARACTER_MAP[value]

    @property
    def characters(self) -> str:
        """The character used to draw the Rule line."""
        if not self._rule_char:
            if self.thickness:
                return CHARACTER_MAP.get(self.thickness, "━")
            return "─"
        return self._rule_char

    @characters.setter
    def characters(self, value: str) -> None:
        """Set the character used to draw the Rule line."""
        if not isinstance(value, str) or len(value) == 0:
            raise ValueError("characters must be a non-empty string")
        if value not in ["─", "━", "═", "█"]:
            raise ValueError(
                f"characters must be one of {list(CHARACTER_MAP.values())}"
            )
        self._rule_char = value


if __name__ == "__main__":  # pragma: no cover
    _console = Console(width=64)
    _console.line(2)
    animated_rule = AnimatedRule(
        title="Animated Gradient Rule",
        rainbow=True
    )
    animated_rule.start()
    sleep(5)
    animated_rule.stop()
