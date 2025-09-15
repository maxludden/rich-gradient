import time
from threading import Event, RLock, Thread
from typing import Any, Callable, List, Optional, TypeAlias, Union, cast

from rich import get_console
from rich.align import Align, AlignMethod, VerticalAlignMethod
from rich.cells import get_character_cell_size
from rich.color import Color, ColorParseError
from rich.color_triplet import ColorTriplet
from rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    Group,
    NewLine,
    RenderResult,
)
from rich.jupyter import JupyterMixin
from rich.live import Live
from rich.measure import Measurement
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style
from rich.table import Column, Table
from rich.text import Text as RichText
# rich-color-ext is installed in package __init__

from rich_gradient._base_gradient import BaseGradient
from rich_gradient.spectrum import Spectrum

__all__ = [
    "AnimatedGradient",
    "ColorType",
]


GAMMA_CORRECTION = 2.2
ColorType: TypeAlias = Union[str, Color, ColorTriplet]

# rich_color_ext is installed at package import time


class AnimatedGradient(BaseGradient):
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
        speed (int): Animation speed in milliseconds. Defaults to 4.
        show_quit_panel (bool): Show a quit instructions panel. Defaults to True.
        repeat_scale (float): Stretch color stops across a wider span. Defaults to 2.0.
        background (bool): Apply gradient to background instead of foreground. Defaults to False.

    Examples:
        >>> ag = AnimatedGradient(renderables=["Hello"], rainbow=True)
        >>> ag.run()  # blocks until Ctrl+C

        Or as a context manager:
        >>> with AnimatedGradient(renderables=["Hi"], rainbow=True) as ag:
        ...     time.sleep(2)
    """

    def __init__(
        self,
        renderables: Optional[List[ConsoleRenderable]] = None,
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
        expand: bool = False,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "top",
        hues: int = 5,
        rainbow: bool = False,
        speed: int = 4,
        show_quit_panel: bool = True,
        repeat_scale: float = 2.0,  # Scale factor to stretch the color stops across a wider span
        background: bool = False,
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
        self._speed = speed / 1000.0

        # Thread / control flags
        self._running: bool = False
        self._thread: Optional[Thread] = None
        self._stop_event: Event = Event()

        # Initialise BaseGradient (this sets _renderables, colors, etc.)
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
            show_quit_panel=show_quit_panel,
            repeat_scale=repeat_scale,
            background=background,
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
        return self.live.console

    @live_console.setter
    def live_console(self, value: Console) -> None:
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
            self._thread.join(timeout=1.0)
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

            # BaseGradient.__rich_console__ applies the gradient to *everything* it renders, including

            return Align(
                self,
                align=self.justify,
                vertical=cast(VerticalAlignMethod, self.vertical_justify),
                width=self.console.width if self.expand else None,
                height=self.console.height if self.expand else None,
                pad=self.expand,
            )

    def _gen_quit_panel(self) -> Panel:
        """Generate a panel with instructions to quit the animation."""
        return Panel(
            "[dim]Press [bold]Ctrl+C[/bold] to quit the animation.[/dim]",
        )

    def _generate_quit_subtitle(self) -> RichText:
        """Generate a subtitle for the quit panel."""
        return RichText(
            "[i]Press[/i] [b u]Ctrl+C[/b u] [i]to stop the animation.[/i]",
        )

    def _animate(self) -> None:
        """Run the animation loop, updating at the requested FPS until stopped."""
        try:
            frame_time = 1.0 / self.refresh_per_second
            while not self._stop_event.is_set():
                # Advance the gradient phase
                self._cycle += self._speed
                self.phase = self._cycle
                # Push an update to Live
                self.live.update(self.get_renderable(), refresh=not self.auto_refresh)
                if not self.auto_refresh:
                    self.live.refresh()
                # Sleep but remain responsive to stop_event
                self._stop_event.wait(frame_time)
        except KeyboardInterrupt:
            # Allow graceful exit on Ctrl+C
            pass
        finally:
            self._running = False


## Note: The public Gradient factory now lives in `rich_gradient/gradient.py`.
## Keeping a duplicate here risks confusion, so it has been removed.


if __name__ == "__main__":
    console = get_console()

    animated_gradient = AnimatedGradient(
        repeat_scale=1.0,
        renderables=[
            RichText("This is an animated gradient example."),
            NewLine(),
            Panel(
                "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
                title="Animated Gradient Example",
            ),
        ],
        rainbow=True,
        auto_refresh=True,
        refresh_per_second=20,
        console=console,
        transient=False,
    )
    animated_gradient.run()
