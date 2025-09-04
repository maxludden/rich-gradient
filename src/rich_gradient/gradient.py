import threading
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
from rich.text import Text as RichText
from rich_color_ext import install as color_ext_install

from rich_gradient.spectrum import Spectrum

# rich_color_ext is installed at package import time

# Type alias for accepted color inputs
ColorType: TypeAlias = Union[str, Color, ColorTriplet]

_GAMMA_CORRECTION: float = 2.2


class Gradient(JupyterMixin):
    """
    Gradient class that can act as a static or animated gradient.
    If animated=True, it animates the gradient using Live.
    """

    def __init__(
        self,
        # --- Rendering-related ---
        renderables: Optional[
            Union[str, ConsoleRenderable, List[ConsoleRenderable]]
        ] = None,
        expand: bool = False,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "top",
        show_quit_panel: bool = False,
        repeat_scale: float = 2.0,
        *,
        console: Optional[Console] = None,
        # --- Color-related ---
        colors: Optional[List[ColorType]] = None,
        bg_colors: Optional[List[ColorType]] = None,
        hues: int = 3,
        rainbow: bool = False,
        background: bool = False,
        # --- Animation-related ---
        animated: bool = False,
        auto_start: bool = True,
        auto_refresh: bool = True,
        refresh_per_second: float = 20.0,
        speed: int = 2,
        # --- Console/Debug options ---
        transient: bool = False,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        disable: bool = False,
    ) -> None:
        self.console: Console = console or get_console()
        self.hues: int = max(hues, 2)
        self.rainbow: bool = rainbow
        self.repeat_scale: float = repeat_scale
        self.phase: float = 0.0
        self.expand: bool = expand
        self.justify = justify
        self.vertical_justify = vertical_justify
        # Ensure quit panel is shown by default for animated gradients unless explicitly disabled
        self.show_quit_panel = bool(show_quit_panel or animated)
        self.background = background

        self.renderables = self._normalize_renderables(renderables, colors)
        self.colors = colors or []
        self.bg_colors = bg_colors or []
        # Animation related
        self.animated = animated
        self.auto_refresh = auto_refresh
        self.refresh_per_second = refresh_per_second
        self.transient = transient
        self.redirect_stdout = redirect_stdout
        self.redirect_stderr = redirect_stderr
        self.disable = disable
        self._speed = speed / 1000.0
        self._cycle = 0.0
        self._running: bool = False
        self._thread: Optional[Thread] = None
        self._stop_event: Event = Event()
        self._lock = RLock()
        self.live: Optional[Live] = None
        if self.animated:
            # Live must exist before we set / forward console
            self.live = Live(
                console=self.console,
                auto_refresh=self.auto_refresh,
                refresh_per_second=self.refresh_per_second,
                transient=self.transient,
                redirect_stdout=self.redirect_stdout,
                redirect_stderr=self.redirect_stderr,
            )
            self.console = self.live.console
        if self.animated and auto_start:
            self.start()
        self._active_stops = self._initialize_color_stops()

    def _normalize_renderables(
        self,
        renderables: Optional[Union[str, ConsoleRenderable, List[ConsoleRenderable]]],
        colors: Optional[List[ColorType]],
    ) -> List[ConsoleRenderable]:
        from rich_gradient.text import Text

        if renderables is None:
            return []
        if isinstance(renderables, str):
            return [Text(renderables, colors=colors)]
        if isinstance(renderables, list):
            return [
                (Text(r, colors=colors) if isinstance(r, str) else r)
                for r in renderables
            ]
        return [renderables]

    def _initialize_color_stops(self) -> List[ColorTriplet]:
        source = self.bg_colors if self.background else self.colors
        # Safely handle empty color sources
        if not source:
            return []
        return [source[0], source[0]] if len(source) == 1 else source

    @property
    def renderables(self) -> List[ConsoleRenderable]:
        """List of renderable objects to which the gradient is applied."""
        return self._renderables

    @renderables.setter
    def renderables(self, value: ConsoleRenderable | List[ConsoleRenderable]) -> None:
        render_list = value if isinstance(value, list) else [value]
        normalized: List[ConsoleRenderable] = []
        for item in render_list:
            if isinstance(item, str):
                normalized.append(RichText.from_markup(item))
            else:
                normalized.append(item)
        self._renderables = normalized

    @property
    def colors(self) -> List[ColorTriplet]:
        """List of parsed ColorTriplet objects for gradient foreground."""
        return self._foreground_colors

    @colors.setter
    def colors(self, colors: List[ColorType]) -> None:
        # User-provided colors take priority, even if rainbow is True
        if colors:
            triplets = self._to_color_triplets(colors)
        elif self.rainbow:
            triplets = Spectrum().triplets
        else:
            triplets = Spectrum(self.hues).triplets
        if len(triplets) > 2:
            # Repeat the gradient by reversing all but the last color stop, to smoothly wrap to the first color
            triplets += list(reversed(triplets[:-1]))
        self._foreground_colors = triplets

    @property
    def bg_colors(self) -> List[ColorTriplet]:
        """List of parsed ColorTriplet objects for gradient background."""
        return self._background_colors

    @bg_colors.setter
    def bg_colors(self, colors: Optional[List[ColorType]]) -> None:
        if not colors:
            self._background_colors = []
            return
        if len(colors) == 1:
            triplet = Color.parse(colors[0]).get_truecolor()
            self._background_colors = [triplet] * self.hues
        else:
            triplets = self._to_color_triplets(colors)
            self._background_colors = triplets

    @property
    def justify(self) -> AlignMethod:
        return self._justify  # type: ignore

    @justify.setter
    def justify(self, method: AlignMethod) -> None:
        if isinstance(method, str) and method.lower() in {"left", "center", "right"}:
            self._justify = method.lower()  # type: ignore
        else:
            raise ValueError(f"Invalid justify method: {method}")

    @property
    def vertical_justify(self) -> VerticalAlignMethod:
        return self._vertical_justify  # type: ignore

    @vertical_justify.setter
    def vertical_justify(self, method: VerticalAlignMethod) -> None:
        if isinstance(method, str) and method.lower() in {"top", "center", "bottom"}:
            self._vertical_justify = method.lower()  # type: ignore
        else:
            raise ValueError(f"Invalid vertical justify method: {method}")

    @property
    def show_quit_panel(self) -> bool:
        return self._show_quit_panel  # type: ignore

    @show_quit_panel.setter
    def show_quit_panel(self, value: bool) -> None:
        self._show_quit_panel = bool(value)

    @staticmethod
    def _to_color_triplets(colors: List[ColorType]) -> List[ColorTriplet]:
        triplets: List[ColorTriplet] = []
        for c in colors:
            if isinstance(c, ColorTriplet):
                triplets.append(c)
            elif isinstance(c, Color):
                triplets.append(c.get_truecolor())
            elif isinstance(c, str):
                triplets.append(Color.parse(c).get_truecolor())
            else:
                raise ColorParseError(
                    f"Unsupported color type: {type(c)}\n\tCould not parse color: {c}"
                )
        return triplets

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        measurements = [Measurement.get(console, options, r) for r in self.renderables]
        min_width = min(m.minimum for m in measurements)
        max_width = max(m.maximum for m in measurements)
        return Measurement(min_width, max_width)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        width = options.max_width
        content = Group(*self.renderables)
        if self.show_quit_panel:
            # Use a Rich Text renderable so the bracketed markup tags remain literal in the output
            panel = Panel(RichText("Press [bold]Ctrl+C[/bold] to stop."), expand=False)
            content = Group(content, Align(panel, align="right"))
        lines = console.render_lines(content, options, pad=True, new_lines=False)
        for line_idx, segments in enumerate(lines):
            col = 0
            for seg in segments:
                text = seg.text
                base_style = seg.style or Style()
                cluster = ""
                cluster_width = 0
                for ch in text:
                    w = get_character_cell_size(ch)
                    if w <= 0:
                        cluster += ch
                        continue
                    if cluster:
                        style = self._get_style_at_position(
                            col - cluster_width, cluster_width, width
                        )
                        yield Segment(cluster, self._merge_styles(base_style, style))
                        cluster = ""
                        cluster_width = 0
                    cluster = ch
                    cluster_width = w
                    col += w
                if cluster:
                    style = self._get_style_at_position(
                        col - cluster_width, cluster_width, width
                    )
                    yield Segment(cluster, self._merge_styles(base_style, style))
            if line_idx < len(lines) - 1:
                yield Segment.line()

    def _get_style_at_position(self, position: int, width: int, span: int) -> Style:
        frac = self._compute_fraction(position, width, span)
        fg_style = ""
        bg_style = ""
        if self.colors:
            r, g, b = self._interpolate_color(frac, self.colors)
            fg_style = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        if self.bg_colors:
            r, g, b = self._interpolate_color(frac, self.bg_colors)
            bg_style = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        return Style(color=fg_style or None, bgcolor=bg_style or None)

    def _compute_fraction(self, position: int, width: int, span: float) -> float:
        total_width = span * self.repeat_scale
        base = (position + width / 2) / total_width
        return (base + self.phase) % 1.0

    def _interpolate_color(
        self, frac: float, color_stops: list[ColorTriplet]
    ) -> tuple[float, float, float]:
        if frac <= 0:
            return color_stops[0]
        if frac >= 1:
            return color_stops[-1]
        segment_count = len(color_stops) - 1
        pos = frac * segment_count
        idx = int(pos)
        t = pos - idx
        r0, g0, b0 = color_stops[idx]
        r1, g1, b1 = color_stops[min(idx + 1, segment_count)]

        def to_linear(c: float) -> float:
            return (c / 255.0) ** _GAMMA_CORRECTION

        def to_srgb(x: float) -> float:
            return (x ** (1.0 / _GAMMA_CORRECTION)) * 255.0

        lr0, lg0, lb0 = to_linear(r0), to_linear(g0), to_linear(b0)
        lr1, lg1, lb1 = to_linear(r1), to_linear(g1), to_linear(b1)
        lr = lr0 + (lr1 - lr0) * t
        lg = lg0 + (lg1 - lg0) * t
        lb = lb0 + (lb1 - lb0) * t
        return to_srgb(lr), to_srgb(lg), to_srgb(lb)

    @staticmethod
    def _merge_styles(original: Style, gradient_style: Style) -> Style:
        return original + gradient_style if original else gradient_style

    # ------------- Animation methods --------------
    @property
    def live_console(self) -> Optional[Console]:
        return self.live.console if self.live is not None else None

    @live_console.setter
    def live_console(self, value: Console) -> None:
        if self.live is not None:
            self.live.console = value

    def start(self) -> None:
        """Start the Live context and the animation loop in a background thread."""
        if not self.animated:
            return
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        if self.live is not None:
            self.live.start()
        self._thread = Thread(target=self._animate, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signal the animation to stop, wait for the thread, and close Live."""
        if not self.animated:
            return
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None
        if self.live is not None:
            self.live.stop()

    def run(self) -> None:
        """Blocking helper: start, then wait for Ctrl+C, then stop."""
        if not self.animated:
            raise RuntimeError("run() is only available if animated=True")
        try:
            self.start()
            while self._running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def __enter__(self):
        if self.animated:
            self.start()
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.animated:
            self.stop()
        return False

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
        try:
            frame_time = 1.0 / self.refresh_per_second
            while not self._stop_event.is_set():
                self._cycle += self._speed
                self.phase = self._cycle
                if self.live is not None:
                    self.live.update(
                        self.get_renderable(), refresh=not self.auto_refresh
                    )
                    if not self.auto_refresh:
                        self.live.refresh()
                self._stop_event.wait(frame_time)
        except KeyboardInterrupt:
            pass
        finally:
            self._running = False

    # Add this method for test compatibility
    def _color_at(self, pos: int, width: int, span: int) -> str:
        """Return the hex color at a given position."""
        stops = self._active_stops
        frac = self._compute_fraction(pos, width, span)
        r, g, b = self._interpolate_color(frac, stops)
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    # Add this method for test compatibility
    def _styled(self, original: Style, color: str) -> Style:
        """Return a Style with the given color or bgcolor, preserving original."""
        if self.background:
            return original + Style(bgcolor=color)
        else:
            return original + Style(color=color)

    # Add this method for test compatibility
    def _interpolated_color(self, frac: float, stops: list, n: int):
        """Return the interpolated color at a fraction (for test)."""
        return self._interpolate_color(frac, stops)


if __name__ == "__main__":
    # Example usage
    console = Console()
    gradient = Gradient(
        [Panel("This is an animated gradient")],
        colors=["#f00", "#f90", "#ff0"],
        animated=True,
        speed=50,
        show_quit_panel=False,
    )
    if isinstance(gradient, Gradient):
        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            gradient.stop()
    else:
        console.print(gradient)
