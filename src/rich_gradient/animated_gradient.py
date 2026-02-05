"""Animated gradient support built on top of Rich Live."""

import signal
import time
from contextlib import suppress
from threading import Event, RLock, Thread
from typing import Any, Callable, List, Mapping, Optional, Sequence, cast

from rich import get_console
from rich.align import Align, AlignMethod, VerticalAlignMethod
from rich.console import Console, ConsoleRenderable, Group, NewLine
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text as RichText

from rich_gradient.config import config
from rich_gradient.gradient import ColorType, Gradient

__all__ = [
    "AnimatedGradient",
    "ColorType",
    "FPS",
]

FPS = 0.12


class AnimatedGradient(Gradient):
    """A gradient that animates over time using `rich.live.Live`.

    Args:
        renderables (Optional[List[ConsoleRenderable]]): Renderables to apply the gradient to.
        colors (Optional[List[ColorType]]): Foreground color stops for the gradient.
        bg_colors (Optional[List[ColorType]]): Background color stops for the gradient.
        hues (int): Number of hues when auto-generating colors. Defaults to 5.
        rainbow (bool): Generate a rainbow gradient instead of using ``colors``. Defaults to False.
        repeat_scale (float): Stretch color stops across a wider span. Defaults to 4.0.
        expand (bool): Expand to fill console width/height. Defaults to False.
        justify (AlignMethod): Horizontal justification. Defaults to "left".
        vertical_justify (VerticalAlignMethod): Vertical justification. Defaults to "top".
        console (Optional[Console]): Console to use for rendering. Defaults to the global console.
        highlight_words: Optional configurations for word highlighting.
        highlight_regex: Optional configurations for regex highlighting.
        redirect_stdout (bool): Redirect stdout to Live. Defaults to False.
        redirect_stderr (bool): Redirect stderr to Live. Defaults to False.
        auto_refresh (bool): Automatically refresh the Live context. Defaults to True.
        refresh_per_second (float): Refresh rate for the Live context. Defaults to 20.0.
        animate (bool | None): Whether to animate. When ``None`` (default), the global
            configuration is used. Set to ``False`` to disable live updates explicitly.
        duration (Optional[float]): Optional duration for automatic stop when running animations.

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
        # color args
        colors: Optional[List[ColorType]] = None,
        bg_colors: Optional[List[ColorType]] = None,
        hues: int = 5,
        rainbow: bool = False,
        repeat_scale: float = 4.0,
        # layout args
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "top",
        highlight_words: Mapping[Any, Any] | Sequence[Any] | None = None,
        highlight_regex: Mapping[Any, Any] | Sequence[Any] | None = None,
        # live args
        console: Optional[Console] = None,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        auto_refresh: bool = True,
        refresh_per_second: float = 30.0,
        transient: bool = False,
        animate: Optional[bool] = None,
        duration: Optional[float] = None,
    ) -> None:
        self.animate = self.get_animated(animate)
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
        self.refresh_per_second = refresh_per_second
        self.expand = expand
        if duration is not None:
            if duration <= 0:
                raise ValueError("duration must be greater than 0")
            self.duration: Optional[float] = float(duration)
        else:
            self.duration = None

        # Fixed phase advance per second mirrors the legacy default of ≈0.12 cycles/sec.
        self._phase_per_second = FPS

        # Thread / control flags
        self._running: bool = False
        self._thread: Optional[Thread] = None
        self._stop_event: Event = Event()
        self._live_active: bool = False
        self._deadline: Optional[float] = None

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
            animated=self.animate,
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
        if self._running or self._live_active:
            return
        if not self.animate:
            # Static render: render one frame via Live so transient behaviour matches Rich.
            self.live.start()
            self._live_active = True
            with self._lock:
                renderable = self.get_renderable()
            self.live.update(renderable, refresh=True)
            self.live.stop()
            self._live_active = False
            return
        self._running = True
        self.live.start()
        self._live_active = True
        if self.duration is not None:
            self._deadline = time.monotonic() + self.duration
        else:
            self._deadline = None
        self._thread = Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the animation to stop, wait for the thread, and close Live."""
        if not self._live_active and not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._live_active:
            self.live.stop()
            self._live_active = False
        self._deadline = None

    def run(self) -> None:
        """Blocking helper: start, then wait for Ctrl+C, then stop."""
        # Install a temporary SIGINT handler so Ctrl+C will immediately
        # attempt to stop the animation and close the Live console cleanly.
        previous_handler = signal.getsignal(signal.SIGINT)

        def _sigint_handler(_signum, _frame):
            # Stop animation and ensure Live is closed. Keep handler small
            # and defensive to avoid raising from signal context.
            try:
                self.stop()
            except (RuntimeError, OSError):
                pass

        signal.signal(signal.SIGINT, _sigint_handler)

        try:
            self.start()
            if not self.animate:
                if self.duration:
                    time.sleep(self.duration)
                return
            while self._running and not self._stop_event.is_set():
                time.sleep(0.1)
        except KeyboardInterrupt:
            # If KeyboardInterrupt is raised, ensure we stop cleanly.
            self.stop()
        finally:
            # Restore the previous SIGINT handler and ensure Live is stopped.
            try:
                signal.signal(signal.SIGINT, previous_handler)
            except (ValueError, OSError):
                pass
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
            with suppress(KeyboardInterrupt):
                frame_time = 1.0 / self.refresh_per_second
                while not self._stop_event.is_set():
                    # Advance the gradient phase (guarded by lock to avoid
                    # race conditions with the render path).
                    deadline = self._deadline
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
                    if deadline is not None and time.monotonic() >= deadline:
                        self._stop_event.set()
                        break
                    # Sleep but remain responsive to stop_event
                    self._stop_event.wait(frame_time)
            self.live.stop()
        except KeyboardInterrupt:
            self.live.stop()

    def get_animated(self, animate: Optional[bool] = None) -> bool:
        """Return whether animation is enabled."""
        if animate is None:
            return config.animation_enabled
        return bool(animate)


def animated_gradient_example() -> None:
    """Run an example of AnimatedGradient with multiple rich renderables."""
    _console = Console(width=64)

    def _generate_table() -> Table:
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
        justify="center",
        console=_console,
        duration=3.0,
    )

    # Run the animation
    animated_gradient.run()


if __name__ == "__main__":
    animated_gradient_example()
