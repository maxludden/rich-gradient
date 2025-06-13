from contextlib import suppress
from typing import List, Optional, Union

from rich.color import Color
from rich.console import Console, ConsoleOptions, RenderResult
from rich.measure import Measurement
from rich.segment import Segment
from rich.style import Style
from rich.cells import get_character_cell_size

from rich_gradient.spectrum import Spectrum

from rich.live import Live
import time

from rich.console import Group
from rich.align import Align
from rich.panel import Panel as RichPanel


class Gradient:
    """
    Render any Rich renderable with a smooth horizontal gradient.

    Parameters
    ----------
    renderable : RenderableType
        The content to render (Text, Panel, Table, etc.).
    colors : List[ColorType], optional
        A list of Rich color identifiers (hex, names, Color).  If provided, these
        are used as gradient stops.  If omitted and rainbow=False, Spectrum is used.
    rainbow : bool
        If True, uses the full rainbow spectrum instead of custom stops.
    background : bool
        If True, applies gradient to the background color; otherwise to foreground.
    """

    def __init__(
        self,
        renderable,
        colors=None,
        rainbow=False,
        background=False,
        phase: int = 0,
    ):
        self.renderable = renderable
        self.rainbow = rainbow
        self.background = background
        # Determine color stops
        if rainbow or not colors:
            spec = Spectrum()
            self._stops = []
            for color in spec.colors:
                r, g, b = color.get_truecolor()
                self._stops.append((r, g, b))
        else:
            self._stops = []
            for c in colors:
                col = c if isinstance(c, Color) else Color.parse(c)
                r, g, b = col.get_truecolor()
                self._stops.append((r, g, b))
            if len(self._stops) == 1:
                self._stops *= 2

        # animation phase offset
        self.phase = phase

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        # Delegate layout measurement to the inner renderable
        return Measurement.get(console, options, self.renderable)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        # Use the renderable's width constraint for gradient span
        target_width = console.width or 80

        # Include padding (borders, margins) in the rendered lines
        lines = console.render_lines(
            self.renderable, options, pad=True, new_lines=False
        )

        for line_no, segments in enumerate(lines):
            # Compute total visible width of this line
            total = sum(seg.cell_length for seg in segments)
            col = 0
            for seg in segments:
                text = seg.text
                base_style = seg.style or Style()
                cluster = ""
                cluster_width = 0
                for ch in text:
                    w = get_character_cell_size(ch)  # Use rich.text.cells instead of wcwidth
                    if w <= 0:
                        cluster += ch
                        continue
                    # flush any accumulated cluster
                    if cluster:
                        color = self._color_at(
                            col - cluster_width, cluster_width, target_width
                        )
                        yield Segment(cluster, self._styled(base_style, color))
                        cluster = ""
                        cluster_width = 0
                    cluster = ch
                    cluster_width = w
                    col += w
                if cluster:
                    color = self._color_at(
                        col - cluster_width, cluster_width, target_width
                    )
                    yield Segment(cluster, self._styled(base_style, color))
            # end-of-line: newline if not last
            if line_no < len(lines) - 1:
                yield Segment.line()

    def _color_at(self, position: int, width: int, span: int) -> str:
        # incorporate phase shift and wrap around for animation
        frac = (position + width / 2 + self.phase) / max(span - 1, 1)
        frac = frac % 1.0
        stops = self._stops
        count = len(stops)
        if count == 0:
            return ""
        if frac <= 0:
            r, g, b = stops[0]
        elif frac >= 1:
            r, g, b = stops[-1]
        else:
            seg = frac * (count - 1)
            idx = int(seg)
            t = seg - idx
            r1, g1, b1 = stops[idx]
            r2, g2, b2 = stops[min(idx + 1, count - 1)]
            r = r1 + (r2 - r1) * t
            g = g1 + (g2 - g1) * t
            b = b1 + (b2 - b1) * t
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    def _styled(self, original: Style, color: str) -> Style:
        if self.background:
            grad = Style(bgcolor=color)
        else:
            grad = Style(color=color)
        return Style.combine([original, grad])

def example():
    from rich.panel import Panel
    from rich.console import Console

    console = Console()

    console.print(
        Gradient(
            Panel("[i b]Aute eu voluptate velit dolor est Lorem nulla mollit.[/] Enim ad sint duis. Culpa excepteur amet esse voluptate cillum dolor exercitation mollit sit eu excepteur id ad eu. Quis quis tempor proident labore consequat voluptate nostrud non in est ea laborum officia Lorem. Ea sunt incididunt nulla aliqua anim ipsum labore qui eiusmod qui voluptate Lorem pariatur. Eu tempor commodo occaecat commodo exercitation ex do amet occaecat occaecat commodo. Ea Lorem minim cupidatat occaecat elit deserunt eiusmod sint labore velit et et voluptate labore irure. Veniam commodo ea est sit et quis nulla commodo sit laborum dolor eu est officia.",
                  title="Gradient Example",
                  padding=(1,2)
                  ),
            rainbow=True
        )
    )


# Animated example using Live
def animated_example():
    """Demonstrate an animated gradient using rich.live.Live."""
    from rich.panel import Panel
    from rich.console import Console

    console = Console()
    panel = Panel(
        "Animating gradient...\nPress Ctrl+C to stop.",
        title="Animated Gradient",
        padding=(1, 2),
    )
    gradient = Gradient(panel, rainbow=True)
    footer = Align.right(RichPanel(" Press Ctrl+C to stop.", expand=False))
    live_renderable = Group(gradient, footer)
    # animate at ~30 FPS
    with Live(live_renderable, console=console, refresh_per_second=30):
        try:
            while True:
                time.sleep(0.03)
                gradient.phase += 1
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    animated_example()
