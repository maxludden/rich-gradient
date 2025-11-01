"""A module providing an AnimatedGradient class for creating animated
gradients in the terminal using Rich."""

import time
import warnings
from threading import Event, RLock, Thread
from typing import (
    Any,
    Callable,
    List,
    Mapping,
    Optional,
    Sequence,
    cast,
)

from rich import get_console
from rich.align import Align, AlignMethod, VerticalAlignMethod
from rich.console import Console, ConsoleRenderable, Group, NewLine
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text as RichText

from rich_gradient.gradient import Gradient, ColorType

__all__ = [
    "AnimatedGradient",
    "ColorType",
]

class AnimatedGradient(Gradient):
    """A gradient that animates over time using `rich.live.Live`.

    Args:
        renderables (Optional[List[ConsoleRenderable]]): Renderables to apply the gradient to.
        colors (Optional[List[ColorType]]): Foreground color stops for the gradient.
        bg_colors (Optional[List[ColorType]]): Background color stops for the gradient.
        auto_refresh (bool): Automatically refresh the Live context. Defaults to True.
        refresh_per_second (float): Refresh rate for the Live context. Defaults to 30.0.
        console (Optional[Console]): Console to use for rendering. Defaults to the global console.
        transient (bool): Keep Live transient (don’t clear on stop). Defaults to False.
        redirect_stdout (bool): Redirect stdout to Live. Defaults to False.
        redirect_stderr (bool): Redirect stderr to Live. Defaults to False.
        disable (bool): Disable rendering. Defaults to False.
        expand (bool): Expand to fill console width/height. Defaults to False.
        justify (AlignMethod): Horizontal justification. Defaults to "left".
        vertical_justify (VerticalAlignMethod): Vertical justification. Defaults to "top".
        hues (int): Number of hues when auto-generating colors. Defaults to 5.
        rainbow (bool): Use a rainbow gradient. Defaults to False.
        phase_per_second (float | None): Phase advance per second (cycles per second).
            Defaults to 0.12.
        speed (int | None): DEPRECATED. Old per-frame ms step. If provided,
            it will be mapped to an equivalent `phase_per_second` using
            `phase_per_second = refresh_per_second * (speed/1000.0)`.
        repeat_scale (float): Stretch color stops across a wider span. Defaults to 2.0.
        highlight_words: Optional configurations for word highlighting.
        highlight_regex: Optional configurations for regex highlighting.

    Examples:
        >>> ag = AnimatedGradient(renderables=["Hello"], rainbow=True)
        >>> ag.run()  # blocks until Ctrl+C

        Or as a context manager:
        >>> with AnimatedGradient(renderables=["Hi"], rainbow=True) as ag:
        ...     time.sleep(2)
    """

    def __init__(
        self,
        renderables: Optional[List[ConsoleRenderable] | ConsoleRenderable | str] = None,
        colors: Optional[List[ColorType]] = None,
        bg_colors: Optional[List[ColorType]] = None,
        *,
        auto_refresh: bool = True,
        refresh_per_second: float = 30.0,
        console: Optional[Console] = None,
        transient: bool = False,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        disable: bool = False,
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "top",
        hues: int = 5,
        rainbow: bool = False,
        phase_per_second: Optional[float] = None,
        speed: Optional[int] = None,
        repeat_scale: float = 2.0,  # Scale factor to stretch the color stops across a wider span
        highlight_words: Mapping[Any, Any] | Sequence[Any] | None = None,
        highlight_regex: Mapping[Any, Any] | Sequence[Any] | None = None,
    ) -> None:
        assert refresh_per_second > 0, "refresh_per_second must be greater than 0"
        self._lock = RLock()

        # Live must exist before we set / forward console
        self.live: Live = Live(
            console=console or get_console(),
            auto_refresh=auto_refresh,
            refresh_per_second=refresh_per_second,
            transient=transient,
            redirect_stdout=redirect_stdout,
            redirect_stderr=redirect_stderr,
        )
        self.auto_refresh = auto_refresh
        self.transient = transient
        self.disable = disable
        self.refresh_per_second = refresh_per_second
        self.expand = expand

        # Determine phase advance per second. Default mirrors older behavior
        # where speed=4ms at 30 FPS ≈ 0.12 cycles/second.
        if phase_per_second is not None:
            self._phase_per_second = float(phase_per_second)
        elif speed is not None:
            # Back-compat with deprecated 'speed' argument.
            warnings.warn(
                "AnimatedGradient 'speed' is deprecated; use 'phase_per_second' \
(cycles per second) instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self._phase_per_second = refresh_per_second * (speed / 1000.0)
        else:
            self._phase_per_second = 0.12

        # Thread / control flags
        self._running: bool = False
        self._thread: Optional[Thread] = None
        self._stop_event: Event = Event()

        # Initialise Gradient (this sets _renderables, colors, etc.)
        super().__init__(
            renderables=renderables or [],
            colors=colors,
            bg_colors=bg_colors,
            console=self.live.console,
            hues=hues,
            rainbow=rainbow,
            expand=expand,
            justify=justify,
            vertical_justify=vertical_justify,
            repeat_scale=repeat_scale,
            highlight_words=highlight_words,
            highlight_regex=highlight_regex,
        )
        self._cycle = 0.0

        # Convenience bound methods
        self.print: Callable[..., None] = self.console.print
        self.log: Callable[..., None] = self.console.log

    # -----------------
    # Console forwarding
    # -----------------
    @property
    def live_console(self) -> Console:
        """Get the console used by the Live instance."""
        return self.live.console

    @live_console.setter
    def live_console(self, value: Console) -> None:
        """Set the console used by the Live instance."""
        self.live.console = value

    # -----------------
    # Animation control
    # -----------------
    def start(self) -> None:
        """Start the Live context and the animation loop in a background thread."""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self.live.start()
        self._thread = Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the animation to stop, wait for the thread, and close Live."""
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread is not None:
            # Give the animation thread a short time to exit cleanly.
            # Use a slightly larger timeout to reduce risk of background
            # thread still touching Live while we stop it.
            self._thread.join(timeout=2.0)
            self._thread = None
        # Ensure Live stops and clears if transient
        self.live.stop()

    def run(self) -> None:
        """Blocking helper: start, then wait for Ctrl+C, then stop."""
        try:
            self.start()
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.stop()
        return False

    # -----------------
    # Live renderable
    # -----------------
    def get_renderable(self) -> ConsoleRenderable:
        """Return the renderable the Live instance should display each frame."""
        with self._lock:
            if not self.renderables:
                raise AssertionError("No renderables set for the gradient")

            return Align(
                self,
                align=self.justify,
                vertical=cast(VerticalAlignMethod, self.vertical_justify),
                width=self.console.width if self.expand else None,
                height=self.console.height if self.expand else None,
                pad=self.expand,
            )

    def _animate(self) -> None:
        """Run the animation loop, updating at the requested FPS until stopped."""
        try:
            frame_time = 1.0 / self.refresh_per_second
            while not self._stop_event.is_set():
                # Advance the gradient phase (guarded by lock to avoid
                # race conditions with the render path).
                with self._lock:
                    self._cycle += self._phase_per_second * frame_time
                    self.phase = self._cycle
                    _renderable = self.get_renderable()

                # Push an update to Live. If auto_refresh is True, rely on
                # Live's own auto refresh; otherwise request an explicit
                # refresh via update(refresh=True).
                if self.auto_refresh:
                    self.live.update(_renderable, refresh=False)
                else:
                    self.live.update(_renderable, refresh=True)
                # Sleep but remain responsive to stop_event
                self._stop_event.wait(frame_time)
        except KeyboardInterrupt:
            # Allow graceful exit on Ctrl+C
            pass
        finally:
            self._running = False


def animated_gradient_example() -> None:
    """Run an example of AnimatedGradient with multiple rich renderables."""
    _console = Console(width=64)

    def _generate_table()-> Table:
        """Generate a sample table to include in the animated gradient."""
        table = Table(collapse_padding=False, expand=True, width=40)
        table.add_column("Renderable", justify="right", ratio=4)
        table.add_column("Works", justify="center", ratio=1)

        renderable_list: List[str] = [
            "rich.text.Text",
            "rich.panel.Panel",
            "rich.console.Group",
            "rich.rule.Rule",
            "rich.emoji.Emoji",
            "rich.markdown.Markdown",
            "rich.table.Table",
            "rich.columns.Columns",
        ]
        for renderable in renderable_list:
            table.add_row(renderable, ":heavy_check_mark:")
        return table

    def _generate_group(table: Table) -> Group:
        """Generate a group containing a panel and the provided table."""
        return Group(
            Panel(
                Group(
                    RichText(
                        "This is an animated gradient that contains: \n\
panel and table in a group inside a panel!\n\n",
                        style="bold",
                        justify="center",
                    ),
                    Align(table, align="center"),
                ),
                title="Animated Gradient Example",
                padding=(1, 2),
            ),
            NewLine(),
        )

    _console.line()
    table = _generate_table()
    renderable = _generate_group(table)

    # Create the AnimatedGradient
    animated_gradient = AnimatedGradient(
        renderable,
        rainbow=True,
        highlight_words={
            "Animated Gradient Example": "bold white",
            "Renderable": "bold white",
            "Works": "bold white",
            ".": "#ccc",
            "✔": "#0f0",
        },
        repeat_scale=4.0,
        justify="center",
        console=_console,
    )
    _console.line(2)

    # Run the animation
    animated_gradient.run()

if __name__ == "__main__":
    animated_gradient_example()
