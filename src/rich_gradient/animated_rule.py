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
        title (Optional[str]): Text shown in the middle of the rule, e.g. ``"Loading"``.
            Defaults to None.
        title_style (StyleType): Style layered over the gradient on the title. A style
            string or ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to
            ``"bold"``.
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
            values are 2 to 17. Defaults to 7.
        thickness (int): Line weight: ``0`` (``─``), ``1`` (``━``), ``2`` (``═``), or
            ``3`` (``█``). Defaults to 2.
        style (StyleType): Base style of the line, under the gradient. A style string or
            ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to ``""``.
        end (str): String printed after the rule. Defaults to a newline.
        align (AlignMethod): Alignment of the title within the rule: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"center"``.
        auto_refresh (bool): Let ``Live`` refresh the display on its own timer. Defaults
            to True.
        refresh_per_second (float): Live refresh and animation frame rate, in frames per
            second. Must be positive. Defaults to 20.0.
        console (Optional[Console]): Console used for rendering and measurement.
            Defaults to ``rich.get_console()``.
        transient (bool): Clear the output from the terminal when the animation stops.
            Defaults to False.
        redirect_stdout (bool): Redirect ``sys.stdout`` into the Live display so prints
            appear above it. Defaults to False.
        redirect_stderr (bool): Redirect ``sys.stderr`` into the Live display so prints
            appear above it. Defaults to False.
        repeat_scale (float): Width of one full color cycle as a multiple of the
            rendered width; larger values give a more gradual gradient. Defaults to 4.0.
        animate (Optional[bool]): Whether to animate. The global config is a kill
            switch: when ``config.animation_enabled`` is False (``"animate": false`` in
            the config file, or ``RICH_GRADIENT_ANIMATE=0``), nothing animates, even if
            this is True. ``False`` renders a single static frame. ``None`` is treated
            as True. Defaults to True.
        duration (Optional[float]): Seconds after which a running animation stops on its
            own, e.g. ``5.0``. Must be positive. ``None`` runs until stopped. Defaults
            to None.

    Raises:
        ValueError: If a color cannot be parsed, ``thickness`` is not 0-3, ``hues``
            < 2, or ``refresh_per_second``/``duration`` is not positive.
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
        animate: bool | None = True,
        duration: float | None = None,
    ) -> None:
        """Initialize the animated rule; see the class docstring for arguments.

        Raises:
            ValueError: If a color cannot be parsed, ``thickness`` is not 0-3,
                ``hues`` < 2, or ``refresh_per_second``/``duration`` is not positive.
        """
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

        Args:
            duration: Number of seconds to animate for.

        Yields:
            This ``AnimatedRule``, already started.

        Raises:
            ValueError: If ``duration`` is not positive.
        """
        if duration <= 0:
            raise ValueError("duration must be greater than 0")
        cancel = Event()

        def _auto_stop() -> None:
            """Stop the animation once ``duration`` elapses unless cancelled."""
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
        """Render the rule with the current gradient phase applied.

        Args:
            console: The console being rendered to.
            options: The console options for the current render.

        Yields:
            Styled segments for each rendered line.
        """
        content = self.renderables[0] if self.renderables else RichText("")
        yield from self._render_styled_lines(
            console,
            options,
            content,
            trailing_newline=self.trailing_newline,
        )

    # For Rules, let the underlying RichRule handle width/align. Avoid the
    # outer Align wrapper from AnimatedGradient to prevent the line from
    # collapsing under nested alignment contexts.
    def get_renderable(self) -> AnimatedRule:  # type: ignore[override]
        """Return the rule itself as the Live renderable.

        Returns:
            This ``AnimatedRule``, without the ``Align`` wrapper used by
            ``AnimatedGradient``.
        """
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
        """Set the title text of the Rule.

        Args:
            value: The new title, or ``None`` to clear it.

        Raises:
            TypeError: If ``value`` is not a ``str``, Rich ``Text``, or ``Text``.
        """
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
        """Set the style applied to the title text of the Rule.

        Args:
            value: The new style, or ``None`` to clear it.

        Raises:
            TypeError: If ``value`` is not a ``str`` or ``Style``.
        """
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
    def thickness(self, value: int) -> None:
        """Set the thickness of the Rule line (0..3).

        Args:
            value: The thickness level, 0-3.

        Raises:
            ValueError: If ``value`` is not 0-3.
        """
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
        """Set the character used to draw the Rule line.

        Args:
            value: One of ``─``, ``━``, ``═``, or ``█``.

        Raises:
            ValueError: If ``value`` is empty or not a supported rule character.
        """
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
    animated_rule = AnimatedRule(title="Animated Gradient Rule", rainbow=True)
    animated_rule.start()
    sleep(5)
    animated_rule.stop()
