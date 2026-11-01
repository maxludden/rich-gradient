"""Gradient-filled variant of Rich's ProgressBar."""

from __future__ import annotations

from collections.abc import Sequence

from rich.console import Console, ConsoleOptions, RenderResult
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
        total: Number of steps, or ``None`` for an indeterminate bar.
        completed: Number of completed steps.
        width: Fixed width in cells, or ``None`` to fill the available width.
        pulse: Render Rich's pulse animation (no gradient).
        style: Style of the unfilled track.
        complete_style: Style of the filled portion before the gradient.
        finished_style: Style used once the bar is complete.
        pulse_style: Style used in pulse mode.
        colors: Gradient color stops.
        rainbow: Whether to generate a rainbow palette.
        hues: Number of auto-generated hues.
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
        """Initialize the gradient progress bar."""
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
        self._style = style

    @property
    def percentage_completed(self) -> float | None:
        """Return the completion percentage, or ``None`` if indeterminate."""
        return self.bar.percentage_completed

    def update(self, completed: float, total: float | None = None) -> None:
        """Update progress; ``total`` is left unchanged when omitted."""
        self.bar.update(completed, total)

    def __rich_measure__(self, console: Console, options: ConsoleOptions):  # type: ignore[no-untyped-def]
        """Delegate measurement to Rich's bar."""
        return self.bar.__rich_measure__(console, options)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Render the bar, swapping in gradient styles on filled cells."""
        plain = list(console.render(self.bar, options))
        if self.bar.pulse or self.bar.total is None:
            yield from plain
            return
        width = options.max_width if self.bar.width is None else self.bar.width
        grad_options = options.update(width=width, height=1)
        gradient = Gradient(
            RichProgressBar(total=1, completed=1, width=width, style=self._style),
            colors=self.colors,
            rainbow=self.rainbow,
            hues=self.hues,
            console=console,
        )
        grad_chars = [
            (ch, seg.style)
            for seg in console.render(gradient, grad_options)
            if isinstance(seg, Segment) and seg.text != "\n"
            for ch in seg.text
        ]
        back_color = console.get_style(self._style).color
        index = 0
        for seg in plain:
            if seg.control or seg.text == "\n":
                yield seg
                continue
            base = seg.style or Style()
            for ch in seg.text:
                if index < len(grad_chars) and base.color != back_color:
                    yield Segment(ch, grad_chars[index][1])
                else:
                    yield Segment(ch, base)
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
