"""Animated gradient support built on top of Rich Live."""

import signal
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import suppress
from importlib import import_module
from threading import Event, RLock, Thread
from typing import Any, Literal

from rich import get_console
from rich.align import Align, AlignMethod, VerticalAlignMethod
from rich.console import (Console, ConsoleRenderable, Group, NewLine,
                          RenderableType)
from rich.live import Live
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text as RichText

from rich_gradient.gradient import ColorType, Gradient

# Look the config module up by name so the config is read at call time and
# honors reload_config(). (``import rich_gradient.config as ...`` would bind the
# package attribute, which ``rich_gradient/__init__.py`` rebinds to the config
# instance.)
_config_module = import_module("rich_gradient.config")

__all__ = [
    "FPS",
    "AnimatedGradient",
    "ColorType",
]

FPS = 0.12


# MARK: AnimatedGradient
class AnimatedGradient(Gradient):
    """A gradient that animates over time using `rich.live.Live`.

    Args:
        renderables (RenderableType | Iterable[RenderableType] | None): A renderable or
            an iterable of renderables to animate. Strings are parsed as console markup,
            e.g. ``"Loading..."``. Defaults to None (nothing until renderables are set).
        colors (Optional[list[ColorType]]): Foreground color stops. Each stop may be a
            color name (Rich/ANSI names such as ``"red"`` keep Rich's meaning; CSS names
            such as ``"tomato"`` also work), a hex string (``"#f00"``, ``"#ff0000"``),
            an ``"rgb(255, 0, 0)"`` string, an ``(r, g, b)`` tuple, or a
            ``rich.color.Color``, e.g. ``["#f00", "orange", (0, 128, 255)]``. If omitted
            and ``rainbow`` is False, ``hues`` colors are taken from the spectrum
            palette. Defaults to None.
        bg_colors (Optional[list[ColorType]]): Background color stops, in the same
            formats as ``colors``, e.g. ``["#000033", "#330033"]``. If omitted, no
            background gradient is applied. Defaults to None.
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted (a run of consecutive hues with a random starting point). Valid
            values are 2 to 17. Defaults to 5.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues``. Defaults to False.
        repeat_scale (float): Width of one full color cycle as a multiple of the
            rendered width; larger values give a more gradual gradient. Defaults to 4.0.
        expand (bool): Expand the output to the full console width. Defaults to True.
        justify (AlignMethod): Horizontal alignment of the content: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the content:
            ``"top"``, ``"middle"``, or ``"bottom"``. Defaults to ``"top"``.
        highlight_words (Optional[Mapping | Sequence]): Words to restyle on top of the
            gradient. Accepts a mapping of a word (or a tuple of words) to a style, e.g.
            ``{"error": "bold red", ("warn", "caution"): "yellow"}``; a sequence of
            ``(words, style[, case_sensitive])`` tuples, e.g.
            ``[("error", "bold red"), (("warn", "caution"), "yellow", False)]``; or
            ``HighlightWords`` instances, e.g.
            ``[HighlightWords(words=("error",), style=Style.parse("bold red"))]``.
            Matching is case-sensitive unless ``case_sensitive`` is False. Defaults to
            None.
        highlight_regex (Optional[Mapping | Sequence]): Regular expressions whose
            matches are restyled on top of the gradient. Accepts a mapping of a pattern
            to a style, e.g. ``{r"[0-9]+": "bold cyan"}``; a sequence of
            ``(pattern, style[, flags])`` tuples, e.g.
            ``[(r"error|fail", "red", re.IGNORECASE)]``; or ``HighlightRegex``
            instances, e.g.
            ``[HighlightRegex(pattern=re.compile(r"[0-9]+"), style=Style.parse("cyan"))]``.
            Defaults to None.
        console (Optional[Console]): Console used for rendering and measurement.
            Defaults to ``rich.get_console()``.
        redirect_stdout (bool): Redirect ``sys.stdout`` into the Live display so prints
            appear above it. Defaults to False.
        redirect_stderr (bool): Redirect ``sys.stderr`` into the Live display so prints
            appear above it. Defaults to False.
        auto_refresh (bool): Let ``Live`` refresh the display on its own timer. Defaults
            to True.
        refresh_per_second (float): Live refresh and animation frame rate, in frames per
            second. Must be positive. Defaults to 30.0.
        transient (bool): Clear the output from the terminal when the animation stops.
            Defaults to False.
        animate (Optional[bool]): Whether to animate. The global config is a kill
            switch: when ``config.animation_enabled`` is False (``"animate": false`` in
            the config file, or ``RICH_GRADIENT_ANIMATE=0``), nothing animates, even if
            this is True. ``False`` renders a single static frame. ``None`` is treated
            as True. Defaults to True.
        duration (Optional[float]): Seconds after which a running animation stops on its
            own, e.g. ``5.0``. Must be positive. ``None`` runs until stopped. Defaults
            to None.

    Raises:
        ValueError: If ``refresh_per_second`` or ``duration`` is not positive.

    Examples:
        >>> ag = AnimatedGradient(renderables=["Hello"], rainbow=True)
        >>> ag.run()  # blocks until Ctrl+C

        Or as a context manager:
        >>> with AnimatedGradient(renderables=["Hi"], rainbow=True) as ag:
        ...     time.sleep(2)
    """

    def __init__(
        self,
        renderables: RenderableType | Iterable[RenderableType] | None = None,
        # color args
        colors: list[ColorType] | None = None,
        bg_colors: list[ColorType] | None = None,
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
        console: Console | None = None,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        auto_refresh: bool = True,
        refresh_per_second: float = 30.0,
        transient: bool = False,
        animate: bool | None = True,
        duration: float | None = None,
    ) -> None:
        """Initialize the animated gradient; see the class docstring for arguments.

        Raises:
            ValueError: If ``refresh_per_second`` or ``duration`` is not positive.
        """
        self.animate = self.get_animated(animate)
        if refresh_per_second <= 0:
            raise ValueError("refresh_per_second must be greater than 0")
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
            self.duration: float | None = float(duration)
        else:
            self.duration = None

        # Fixed phase advance per second mirrors the legacy default of ≈0.12 cycles/sec.
        self._phase_per_second = FPS

        # Thread / control flags
        self._running: bool = False
        self._thread: Thread | None = None
        self._stop_event: Event = Event()
        self._live_active: bool = False
        self._deadline: float | None = None

        # Initialise Gradient (this sets _renderables, colors, etc.)
        super().__init__(
            renderables=[] if renderables is None else renderables,
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
            animate=self.animate,
        )
        self._cycle = 0.0

        # Convenience bound methods
        self.print: Callable[..., None] = self.console.print
        self.log: Callable[..., None] = self.console.log

    # -----------------
    # MARK: Console Forwarding
    # -----------------
    @property
    def live_console(self) -> Console:
        """The console used by the Live instance."""
        return self.live.console

    @live_console.setter
    def live_console(self, value: Console) -> None:
        """Set the console used by the Live instance.

        Args:
            value: The console Live should render to.
        """
        self.live.console = value

    # -----------------
    # MARK: Animation Control
    # -----------------
    def start(self) -> None:
        """Start the Live context and the animation loop in a background thread."""
        if self._running or self._live_active:
            return
        self._stop_event.clear()
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

    def _mark_stopped(self) -> None:
        """Record that the animation loop has stopped."""
        self._running = False
        self._live_active = False
        self._deadline = None

    def run(self) -> None:
        """Blocking helper: start, then wait for Ctrl+C, then stop."""
        # Install a temporary SIGINT handler so Ctrl+C will immediately
        # attempt to stop the animation and close the Live console cleanly.
        previous_handler = signal.getsignal(signal.SIGINT)

        def _sigint_handler(_signum: int, _frame: object) -> None:
            """Stop the animation when Ctrl+C is pressed.

            Args:
                _signum: The received signal number (unused).
                _frame: The interrupted stack frame (unused).
            """
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

    def __enter__(self) -> "AnimatedGradient":
        """Start the animation when entering a ``with`` block.

        Returns:
            This ``AnimatedGradient`` instance.
        """
        self.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> Literal[False]:
        """Stop the animation when leaving a ``with`` block.

        Args:
            exc_type: The exception type raised in the block, if any.
            exc: The exception instance raised in the block, if any.
            tb: The traceback of the exception, if any.

        Returns:
            ``False``, so exceptions raised in the block propagate.
        """
        self.stop()
        return False

    # -----------------
    # MARK: Live Renderable
    # -----------------
    def get_renderable(self) -> ConsoleRenderable:
        """Build the renderable the Live instance should display each frame.

        Returns:
            This gradient wrapped in an ``Align`` sized to the console when
            ``expand`` is true.

        Raises:
            AssertionError: If no renderables have been set.
        """
        with self._lock:
            if not self.renderables:
                raise AssertionError("No renderables set for the gradient")

            return Align(
                renderable=self,
                align=self.justify,
                vertical=self.vertical_justify,
                width=self.console.width if self.expand else None,
                height=self.console.height if self.expand else None,
                pad=self.expand,
            )

    def _animate(self) -> None:
        """Run the animation loop, updating at the requested FPS until stopped."""
        try:
            with suppress(KeyboardInterrupt):
                frame_time: int | float = 1.0 / self.refresh_per_second
                while not self._stop_event.is_set():
                    # Advance the gradient phase (guarded by lock to avoid
                    # race conditions with the render path).
                    deadline: int | float | None = self._deadline
                    with self._lock:
                        self._cycle += self._phase_per_second * frame_time
                        self.phase: int | float = self._cycle
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
        finally:
            self._mark_stopped()

    def get_animated(self, animate: bool | None = True) -> bool:
        """Resolve whether animation is enabled.

        The global config is a kill switch: when ``config.animation_enabled``
        is False (``"animate": false`` in the config file, or
        ``RICH_GRADIENT_ANIMATE=0``), nothing animates, even if ``animate`` is
        True.

        Args:
            animate: Whether this instance should animate. ``None`` is treated
                as ``True`` for backward compatibility. Defaults to True.

        Returns:
            ``True`` if the gradient should animate.
        """
        requested = True if animate is None else bool(animate)
        return requested and _config_module.config.animation_enabled


# MARK: Example
def animated_gradient_example() -> None:
    """Run an example of AnimatedGradient with multiple rich renderables."""
    _console = Console(width=64)

    def _generate_table() -> RichTable:
        """Generate a sample table to include in the animated gradient."""
        table = RichTable(collapse_padding=False, expand=True, width=40)
        table.add_column("Renderable", justify="right", ratio=4)
        table.add_column("Works", justify="center", ratio=1)

        renderable_list: list[str] = [
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

    def _generate_group(table: RichTable) -> Group:
        """Generate a group containing a panel and the provided table.

        Args:
            table: The table to show inside the panel.

        Returns:
            A group of the panel followed by a blank line.
        """
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
        duration=5.0,
    )

    # Run the animation
    animated_gradient.run()


if __name__ == "__main__":
    animated_gradient_example()
