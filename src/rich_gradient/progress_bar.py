"""Gradient-filled variants of Rich's ProgressBar and Progress bar column."""

from __future__ import annotations

from collections.abc import Sequence
from math import cos, pi
from time import monotonic
from typing import TYPE_CHECKING, Any

from rich.color import Color, blend_rgb
from rich.color_triplet import ColorTriplet
from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement
from rich.progress import BarColumn
from rich.progress_bar import PULSE_SIZE
from rich.progress_bar import ProgressBar as RichProgressBar
from rich.segment import Segment
from rich.style import Style, StyleType
from rich.table import Column

from rich_gradient.gradient import ColorType, Gradient
from rich_gradient.spectrum import Spectrum, validate_hues

if TYPE_CHECKING:
    from rich.progress import Task

__all__ = ["GradientBarColumn", "ProgressBar"]

# Rich only blends pulse colors on these color systems; elsewhere it draws a
# plain two-tone pulse, which this module leaves to Rich.
_BLENDING_COLOR_SYSTEMS = ("standard", "eight_bit", "truecolor")


def _resolve_palette(
    colors: Sequence[ColorType] | None, rainbow: bool, hues: int
) -> list[ColorType]:
    """Pick a fixed list of color stops.

    Resolving the palette once keeps auto-generated colors stable across
    renders; otherwise each frame of a live display would draw a new random
    starting hue.

    Args:
        colors: Explicit color stops, used as given unless ``rainbow`` is set.
        rainbow: Use the full 17-color spectrum palette.
        hues: Number of spectrum colors to use when ``colors`` is omitted.

    Returns:
        The color stops to paint with.

    Raises:
        ValueError: If ``hues`` is out of range.
    """
    if rainbow:
        return list(Spectrum().colors)
    if colors:
        return list(colors)
    return list(Spectrum(validate_hues(hues)).colors)


class ProgressBar:
    """A progress bar painted with a gradient while in progress, pulsing, and complete.

    - **In progress:** the filled portion is painted with ``colors``. The gradient
      spans the whole bar width, so colors stay fixed in place and are revealed as
      the bar fills. The unfilled track keeps Rich's ``style``.
    - **Complete** (``completed >= total``): the full bar is painted with
      ``finished_colors``, or ``colors`` when that is omitted.
    - **Pulsing** (``pulse=True`` or ``total=None``): Rich's sliding pulse wave is
      kept, but the bright part of the wave takes its color from ``pulse_colors``
      (or ``colors``), so the wave changes color as it moves and fades into the
      track's color.

    When no colors are given, a palette is picked once (from the spectrum, or the
    full rainbow) and reused for every render, so a live display does not flicker.

    Examples:
        >>> from rich.console import Console
        >>> console = Console()
        >>> console.print(ProgressBar(total=100, completed=60, colors=["#38bdf8", "#a855f7"]))
        >>> console.print(ProgressBar(total=10, completed=10, finished_colors=["#22c55e", "#a3e635"]))
        >>> console.print(ProgressBar(total=None, pulse_colors=["#f43f5e", "#f59e0b"]))

    Args:
        total (Optional[float]): Number of steps, or ``None`` for an indeterminate
            (pulsing) bar. Defaults to 100.0.
        completed (float): Number of completed steps. Defaults to 0.
        width (Optional[int]): Fixed width in cells, or ``None`` to fill the available
            width. Defaults to None.
        pulse (bool): Show the pulse animation instead of progress, e.g. before a task
            starts. Defaults to False.
        style (StyleType): Style of the unfilled track. A style string or
            ``rich.style.Style``, e.g. ``"dim italic"``. The track is not part of the
            gradient, so a color here is shown; it is also the color the pulse wave
            fades into. Defaults to ``"bar.back"``.
        complete_style (StyleType): Style of the filled portion, under the gradient. A
            style string or ``rich.style.Style``, e.g. ``"dim italic"``. A foreground
            color in this style is replaced by the gradient; background and attributes
            are kept. Defaults to ``"bar.complete"``.
        finished_style (StyleType): Style used once the bar is complete. A style string
            or ``rich.style.Style``, e.g. ``"dim italic"``. A foreground color in this
            style is replaced by the gradient; background and attributes are kept.
            Defaults to ``"bar.finished"``.
        pulse_style (StyleType): Style used for the pulse wave on terminals without
            color blending, where Rich's plain pulse is drawn. A style string or
            ``rich.style.Style``, e.g. ``"dim italic"``. Elsewhere the wave's color
            comes from the gradient. Defaults to ``"bar.pulse"``.
        animation_time (Optional[float]): Time in seconds that drives the pulse
            position, e.g. ``1.5``. ``None`` uses ``time.monotonic()``, so the pulse
            moves on its own. ``rich.progress`` passes each task's elapsed time.
            Defaults to None.
        colors (Optional[Sequence[ColorType]]): Foreground color stops. Each stop may be
            a color name (Rich/ANSI names such as ``"red"`` keep Rich's meaning; CSS
            names such as ``"tomato"`` also work), a hex string (``"#f00"``,
            ``"#ff0000"``), an ``"rgb(255, 0, 0)"`` string, an ``(r, g, b)`` tuple, or a
            ``rich.color.Color``, e.g. ``["#f00", "orange", (0, 128, 255)]``. If omitted
            and ``rainbow`` is False, ``hues`` colors are taken from the spectrum
            palette. Defaults to None.
        pulse_colors (Optional[Sequence[ColorType]]): Color stops for the pulse wave, in
            the same formats as ``colors``, e.g. ``["#f43f5e", "#f59e0b"]``. Defaults to
            None, which uses the same palette as the in-progress bar.
        finished_colors (Optional[Sequence[ColorType]]): Color stops for a complete bar,
            in the same formats as ``colors``, e.g. ``["#22c55e", "#a3e635"]``. Defaults
            to None, which uses the same palette as the in-progress bar.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues`` (``pulse_colors`` and ``finished_colors`` still apply). Defaults to
            False.
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted (a run of consecutive hues with a random starting point). Valid
            values are 2 to 17. Defaults to 5.

    Raises:
        ValueError: If ``hues`` is out of range.
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
        animation_time: float | None = None,
        *,
        colors: Sequence[ColorType] | None = None,
        pulse_colors: Sequence[ColorType] | None = None,
        finished_colors: Sequence[ColorType] | None = None,
        rainbow: bool = False,
        hues: int = 5,
    ) -> None:
        """Initialize the gradient progress bar; see the class docstring for arguments.

        Raises:
            ValueError: If ``hues`` is out of range.
        """
        self.bar = RichProgressBar(
            total=total,
            completed=completed,
            width=width,
            pulse=pulse,
            style=style,
            complete_style=complete_style,
            finished_style=finished_style,
            pulse_style=pulse_style,
            animation_time=animation_time,
        )
        self.colors = list(colors) if colors is not None else None
        self.pulse_colors = list(pulse_colors) if pulse_colors is not None else None
        self.finished_colors = (
            list(finished_colors) if finished_colors is not None else None
        )
        self.rainbow = rainbow
        self.hues = hues
        # Picked once so auto-generated colors stay put between renders.
        self._palette: list[ColorType] = _resolve_palette(self.colors, rainbow, hues)

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
        """Route Rich's bar state attributes to the wrapped bar.

        Args:
            name: The attribute being set.
            value: The new value.
        """
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

    def _stops_for(self, state: str) -> list[ColorType]:
        """Return the color stops for a bar state.

        Args:
            state: ``"progress"``, ``"pulse"``, or ``"finished"``.

        Returns:
            The state's own colors when given; otherwise ``colors`` (unless
            ``rainbow`` is set), or the palette picked at construction.
        """
        own = {"pulse": self.pulse_colors, "finished": self.finished_colors}.get(state)
        if own:
            return list(own)
        if self.colors and not self.rainbow:
            return list(self.colors)
        return self._palette

    def _gradient_colors(
        self,
        console: Console,
        options: ConsoleOptions,
        width: int,
        stops: list[ColorType],
    ) -> list[Color | None]:
        """Sample one gradient color per cell across the bar width.

        Args:
            console: The console being rendered to.
            options: The console options for the current render.
            width: The bar width in cells.
            stops: The color stops to interpolate.

        Returns:
            One foreground color per cell (``None`` where the gradient has none).
        """
        gradient = Gradient(
            RichProgressBar(total=1, completed=1, width=width),
            colors=stops,
            console=console,
        )
        return [
            seg.style.color if seg.style else None
            for seg in console.render(gradient, options.update(width=width, height=1))
            if isinstance(seg, Segment) and seg.text != "\n"
            for _ in seg.text
        ]

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
        """Render the bar with gradient colors for its current state.

        Filled cells are identified by position (mirroring Rich's own width math),
        not by color, so they are found even when the fill and track share a color.
        The gradient replaces only the foreground; Rich's fill style keeps its
        background and attributes.

        Args:
            console: The console being rendered to.
            options: The console options for the current render.

        Yields:
            The bar's segments, with gradient colors on the filled cells (or the
            pulse wave).
        """
        bar = self.bar
        width = min(bar.width or options.max_width, options.max_width)
        if bar.pulse or bar.total is None:
            yield from self._render_pulse(console, options, width)
            return
        plain = list(console.render(bar, options))
        completed = min(bar.total, max(0, bar.completed))
        halves = int(width * 2 * completed / bar.total) if bar.total else width * 2
        filled = halves // 2 + halves % 2
        state = "finished" if bar.completed >= bar.total else "progress"
        grad_colors = self._gradient_colors(
            console, options, width, self._stops_for(state)
        )
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

    def _render_pulse(
        self, console: Console, options: ConsoleOptions, width: int
    ) -> RenderResult:
        """Render Rich's pulse wave with its bright part colored by the gradient.

        Mirrors ``rich.progress_bar.ProgressBar._render_pulse``: the same wave shape,
        speed, and timing, but each cell blends the gradient color at that position
        (instead of a single ``pulse_style`` color) with the track color.

        Args:
            console: The console being rendered to.
            options: The console options for the current render.
            width: The bar width in cells.

        Yields:
            One segment per cell.
        """
        bar = self.bar
        if console.color_system not in _BLENDING_COLOR_SYSTEMS or console.no_color:
            # Rich draws a plain two-tone pulse here; there is nothing to blend.
            yield from console.render(bar, options)
            return
        ascii_only = options.legacy_windows or options.ascii_only
        char = "-" if ascii_only else "━"
        back_style = console.get_style(bar.style, default="black")
        back = (
            back_style.color.get_truecolor() if back_style.color else ColorTriplet(0, 0, 0)
        )
        fallback = console.get_style(bar.pulse_style, default="white").color
        grad_colors = self._gradient_colors(
            console, options, width, self._stops_for("pulse")
        )
        current_time = monotonic() if bar.animation_time is None else bar.animation_time
        offset = int(-current_time * 15) % PULSE_SIZE
        for index in range(width):
            color = grad_colors[index] if index < len(grad_colors) else None
            color = color or fallback
            fore = color.get_truecolor() if color else ColorTriplet(255, 0, 255)
            position = ((index + offset) % PULSE_SIZE) / PULSE_SIZE
            fade = 0.5 + cos(position * pi * 2) / 2.0
            blended = blend_rgb(fore, back, cross_fade=fade)
            yield Segment(char, Style(color=Color.from_triplet(blended)))


class GradientBarColumn(BarColumn):
    """A ``rich.progress`` bar column that draws gradient ``ProgressBar`` bars.

    Use it in place of ``rich.progress.BarColumn``. Running tasks show the
    in-progress gradient, finished tasks the finished gradient, and tasks that
    have not started (or have no total) the gradient pulse. The palette is picked
    once when the column is created, so colors stay steady while the display
    refreshes.

    Examples:
        >>> from rich.progress import Progress, TextColumn
        >>> with Progress(
        ...     TextColumn("{task.description}"),
        ...     GradientBarColumn(colors=["#38bdf8", "#a855f7"], finished_colors=["#22c55e", "#a3e635"]),
        ... ) as progress:
        ...     task = progress.add_task("Downloading", total=100)
        ...     progress.update(task, advance=50)

    Args:
        bar_width (Optional[int]): Width of each bar in cells, or ``None`` to fill the
            column. Defaults to 40.
        style (StyleType): Style of the unfilled track (and the color the pulse fades
            into). A style string or ``rich.style.Style``, e.g. ``"dim italic"``. A
            color here is shown. Defaults to ``"bar.back"``.
        complete_style (StyleType): Style of the filled portion, under the gradient. A
            style string or ``rich.style.Style``, e.g. ``"dim italic"``. A foreground
            color in this style is replaced by the gradient; background and attributes
            are kept. Defaults to ``"bar.complete"``.
        finished_style (StyleType): Style used once a task is complete. A style string
            or ``rich.style.Style``, e.g. ``"dim italic"``. A foreground color in this
            style is replaced by the gradient; background and attributes are kept.
            Defaults to ``"bar.finished"``.
        pulse_style (StyleType): Style of the pulse on terminals without color
            blending. A style string or ``rich.style.Style``, e.g. ``"dim italic"``.
            Defaults to ``"bar.pulse"``.
        table_column (Optional[Column]): Column settings for the progress table, e.g.
            ``Column(ratio=2)``. Defaults to None.
        colors (Optional[Sequence[ColorType]]): Foreground color stops for running
            tasks, in any format ``Gradient`` accepts, e.g.
            ``["#f00", "orange", (0, 128, 255)]``. If omitted and ``rainbow`` is False,
            ``hues`` colors are taken from the spectrum palette. Defaults to None.
        pulse_colors (Optional[Sequence[ColorType]]): Color stops for the pulse wave,
            e.g. ``["#f43f5e", "#f59e0b"]``. Defaults to None, which uses the
            running-task palette.
        finished_colors (Optional[Sequence[ColorType]]): Color stops for finished tasks,
            e.g. ``["#22c55e", "#a3e635"]``. Defaults to None, which uses the
            running-task palette.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues``. Defaults to False.
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted. Valid values are 2 to 17. Defaults to 5.

    Raises:
        ValueError: If ``hues`` is out of range.
    """

    def __init__(
        self,
        bar_width: int | None = 40,
        style: StyleType = "bar.back",
        complete_style: StyleType = "bar.complete",
        finished_style: StyleType = "bar.finished",
        pulse_style: StyleType = "bar.pulse",
        table_column: Column | None = None,
        *,
        colors: Sequence[ColorType] | None = None,
        pulse_colors: Sequence[ColorType] | None = None,
        finished_colors: Sequence[ColorType] | None = None,
        rainbow: bool = False,
        hues: int = 5,
    ) -> None:
        """Initialize the gradient bar column; see the class docstring for arguments.

        Raises:
            ValueError: If ``hues`` is out of range.
        """
        super().__init__(
            bar_width=bar_width,
            style=style,
            complete_style=complete_style,
            finished_style=finished_style,
            pulse_style=pulse_style,
            table_column=table_column,
        )
        # Resolved once: render() builds a new bar on every refresh.
        self.colors: list[ColorType] = _resolve_palette(colors, rainbow, hues)
        self.pulse_colors = list(pulse_colors) if pulse_colors is not None else None
        self.finished_colors = (
            list(finished_colors) if finished_colors is not None else None
        )

    def render(self, task: Task) -> ProgressBar:  # type: ignore[override]
        """Build the gradient bar for a task.

        Args:
            task: The ``rich.progress`` task to draw.

        Returns:
            A gradient ``ProgressBar`` reflecting the task's progress.
        """
        return ProgressBar(
            total=max(0, task.total) if task.total is not None else None,
            completed=max(0, task.completed),
            width=None if self.bar_width is None else max(1, self.bar_width),
            pulse=not task.started,
            animation_time=task.get_time(),
            style=self.style,
            complete_style=self.complete_style,
            finished_style=self.finished_style,
            pulse_style=self.pulse_style,
            colors=self.colors,
            pulse_colors=self.pulse_colors,
            finished_colors=self.finished_colors,
        )


def demo() -> None:
    """Render gradient progress bars in progress, complete, and pulsing."""
    console = Console(width=50)
    for done in (10, 45, 80):
        console.print(
            ProgressBar(
                total=100, completed=done, colors=["#f43f5e", "#f59e0b", "#22c55e"]
            )
        )
    console.print(
        ProgressBar(total=100, completed=100, finished_colors=["#22c55e", "#a3e635"])
    )
    console.print(
        ProgressBar(total=None, animation_time=0.0, pulse_colors=["#38bdf8", "#a855f7"])
    )


if __name__ == "__main__":
    demo()
