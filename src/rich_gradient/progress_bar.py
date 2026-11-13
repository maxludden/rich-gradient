"""Gradient-filled variant of Rich's ProgressBar."""

from __future__ import annotations

from collections.abc import Sequence

from typing import Any

from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement
from rich.progress_bar import ProgressBar as RichProgressBar
from rich.segment import Segment
from rich.style import Style, StyleType

from rich_gradient.gradient import ColorType, Gradient


class ProgressBar:
    """A progress bar whose completed portion is painted with a gradient.

    The gradient spans the whole bar width, so colors stay fixed in place and are
    revealed as the bar fills. The unfilled track keeps Rich's ``style``.
    Pulse mode is not gradient-aware and renders as Rich normally would.

    Args:
        total (Optional[float]): Number of steps, or ``None`` for an indeterminate
            (pulsing) bar. Defaults to 100.0.
        completed (float): Number of completed steps. Defaults to 0.
        width (Optional[int]): Fixed width in cells, or ``None`` to fill the available
            width. Defaults to None.
        pulse (bool): Render Rich's pulse animation (no gradient). Defaults to False.
        style (StyleType): Style of the unfilled track. A style string or
            ``rich.style.Style``, e.g. ``"dim italic"``. The track is not part of the
            gradient, so a color here is shown. Defaults to ``"bar.back"``.
        complete_style (StyleType): Style of the filled portion, under the gradient. A
            style string or ``rich.style.Style``, e.g. ``"dim italic"``. A foreground
            color in this style is replaced by the gradient; background and attributes
            are kept. Defaults to ``"bar.complete"``.
        finished_style (StyleType): Style used once the bar is complete. A style string
            or ``rich.style.Style``, e.g. ``"dim italic"``. A foreground color in this
            style is replaced by the gradient; background and attributes are kept.
            Defaults to ``"bar.finished"``.
        pulse_style (StyleType): Style used in pulse mode. A style string or
            ``rich.style.Style``, e.g. ``"dim italic"``. Pulse mode has no gradient, so
            a color here is shown. Defaults to ``"bar.pulse"``.
        colors (Optional[Sequence[ColorType]]): Foreground color stops. Each stop may be
            a color name (Rich/ANSI names such as ``"red"`` keep Rich's meaning; CSS
            names such as ``"tomato"`` also work), a hex string (``"#f00"``,
            ``"#ff0000"``), an ``"rgb(255, 0, 0)"`` string, an ``(r, g, b)`` tuple, or a
            ``rich.color.Color``, e.g. ``["#f00", "orange", (0, 128, 255)]``. If omitted
            and ``rainbow`` is False, ``hues`` colors are taken from the spectrum
            palette. Defaults to None.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues``. Defaults to False.
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted (a run of consecutive hues with a random starting point). Valid
            values are 2 to 17. Defaults to 5.
    """

    def __init__(
        self,
        total: float | None = 100.0,
        completed: float = 0,
        width: int | None = None,
        pulse: bool = False,
        style: StyleType = "bar.back",
        complete_style: StyleType = "bar.complete",
        finished_style: StyleType = "bar.finished",
        pulse_style: StyleType = "bar.pulse",
        *,
        colors: Sequence[ColorType] | None = None,
        rainbow: bool = False,
        hues: int = 5,
    ) -> None:
        """Initialize the gradient progress bar; see the class docstring for arguments."""
        self.bar = RichProgressBar(
            total=total,
            completed=completed,
            width=width,
            pulse=pulse,
            style=style,
            complete_style=complete_style,
            finished_style=finished_style,
            pulse_style=pulse_style,
        )
        self.colors = list(colors) if colors is not None else None
        self.rainbow = rainbow
        self.hues = hues

    _RICH_ATTRS = frozenset(
        {
            "total",
            "completed",
            "width",
            "pulse",
            "style",
            "complete_style",
            "finished_style",
            "pulse_style",
            "animation_time",
        }
    )

    def __getattr__(self, name: str) -> Any:
        """Expose Rich's bar state (``completed``, ``total``, styles, ...).

        Args:
            name: The attribute being looked up.

        Returns:
            The attribute's value on the wrapped ``rich.progress_bar.ProgressBar``.

        Raises:
            AttributeError: If ``name`` is not one of the forwarded attributes.
        """
        if name in ProgressBar._RICH_ATTRS and "bar" in self.__dict__:
            return getattr(self.__dict__["bar"], name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Route Rich's bar state attributes to the wrapped bar."""
        if name in ProgressBar._RICH_ATTRS and "bar" in self.__dict__:
            setattr(self.__dict__["bar"], name, value)
        else:
            super().__setattr__(name, value)

    @property
    def percentage_completed(self) -> float | None:
        """The completion percentage (0-100), or ``None`` if indeterminate."""
        return self.bar.percentage_completed

    def update(self, completed: float, total: float | None = None) -> None:
        """Update progress.

        Args:
            completed: Number of completed steps, e.g. ``42``.
            total: New total number of steps. Defaults to None, which leaves the
                total unchanged.
        """
        self.bar.update(completed, total)

    def __rich_measure__(self, console: Console, options: ConsoleOptions) -> Measurement:
        """Delegate measurement to Rich's bar.

        Args:
            console: The console used for measurement.
            options: The console options for the current render.

        Returns:
            The wrapped Rich bar's measurement.
        """
        return self.bar.__rich_measure__(console, options)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Render the bar, adding gradient colors to the filled cells.

        Filled cells are identified by position (mirroring Rich's own width math),
        not by color, so they are found even when the fill and track share a color.
        The gradient replaces only the foreground; Rich's fill style keeps its
        background and attributes.

        Args:
            console: The console being rendered to.
            options: The console options for the current render.

        Yields:
            The bar's segments, with gradient colors on the filled cells.
        """
        plain = list(console.render(self.bar, options))
        bar = self.bar
        if bar.pulse or bar.total is None:
            yield from plain
            return
        width = min(bar.width or options.max_width, options.max_width)
        completed = min(bar.total, max(0, bar.completed))
        halves = int(width * 2 * completed / bar.total) if bar.total else width * 2
        filled = halves // 2 + halves % 2
        gradient = Gradient(
            RichProgressBar(total=1, completed=1, width=width),
            colors=self.colors,
            rainbow=self.rainbow,
            hues=self.hues,
            console=console,
        )
        grad_colors = [
            seg.style.color if seg.style else None
            for seg in console.render(gradient, options.update(width=width, height=1))
            if isinstance(seg, Segment) and seg.text != "\n"
            for _ in seg.text
        ]
        index = 0
        for seg in plain:
            if seg.control or seg.text == "\n":
                yield seg
                continue
            base = seg.style or Style()
            for ch in seg.text:
                color = grad_colors[index] if index < min(filled, len(grad_colors)) else None
                yield Segment(ch, base + Style(color=color) if color else base)
                index += 1


def demo() -> None:
    """Render gradient progress bars at several completion levels."""
    console = Console(width=50)
    for done in (10, 45, 80, 100):
        console.print(
            ProgressBar(
                total=100, completed=done, colors=["#f43f5e", "#f59e0b", "#22c55e"]
            )
        )


if __name__ == "__main__":
    demo()
