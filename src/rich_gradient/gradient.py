import time
from contextlib import suppress
from typing import List, Optional, Union

from rich.align import Align
from rich.cells import get_character_cell_size
from rich.color import Color
from rich.console import Console, ConsoleOptions, RenderResult, RenderableType, Group
from rich.live import Live
from rich.measure import Measurement
from rich.panel import Panel as RichPanel
from rich.segment import Segment
from rich.style import Style

from rich_gradient.spectrum import Spectrum


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
        renderable: RenderableType,
        colors: Optional[List[Union[Color, str]]] = None,
        *,
        rainbow: bool = False,
        background: bool = False,
        animated: bool = False,
        phase: float = 0.0,
    ) -> None:
        """
        Initialize a gradient renderer.

        Parameters:
        -----------
        renderable: RenderableType
            The Rich renderable (Text, Panel, Table, etc.) to which the gradient will be applied.
        colors: Optional[List[Union[Color, str]]]
            List of color stops as Color instances or color identifiers (hex strings or names).
            If omitted and rainbow=False, a default spectrum of hues is used.
        rainbow: bool
            If True, ignore custom colors and use the full rainbow spectrum.
        background: bool
            If True, apply gradient to the background; otherwise to the foreground.
        phase: float
            Initial offset for animation (may be fractional for finer control); increments advance the gradient.
        animated: bool
            If True, wraps renderable with a footer panel indicating Ctrl+C to stop.
        """
        if animated:
            footer = RichPanel(" Press Ctrl+C to stop.", expand=False)
            renderable = Group(renderable, Align.right(footer))
        self.renderable = renderable
        self.rainbow = rainbow
        self.background = background
        self.phase: float = phase
        self.animated = animated
        self._stops = self._compute_stops(colors, rainbow)

    def _compute_stops(
        self, colors: Optional[List[Union[Color, str]]], rainbow: bool
    ) -> list:
        """
        Compute the color stops for the gradient.

        Parameters:
            colors: Optional[List[Union[Color, str]]]
                List of color stops as Color instances or color identifiers.
            rainbow: bool
                If True, use the full rainbow spectrum.

        Returns:
            List[Tuple[int, int, int]]: List of RGB tuples.
        """
        stops = []
        if rainbow or not colors:
            spec = Spectrum()
            color_iter = spec.colors
        else:
            color_iter = [
                c if isinstance(c, Color) else Color.parse(c) for c in colors
            ]
        for color in color_iter:
            r, g, b = color.get_truecolor()
            stops.append((r, g, b))
        if (not rainbow and colors) and len(stops) == 1:
            stops *= 2
        if self.animated and len(stops) > 1 and stops[0] != stops[-1]:
            stops.append(stops[0])
        return stops

    # ---------------------------
    # Layout measurement hook
    # ---------------------------
    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        """
        Measure the size required by the inner renderable under given console constraints.

        Returns:
            Measurement: Width constraints for rendering.
        """
        # Delegate layout measurement to the inner renderable
        return Measurement.get(console, options, self.renderable)

    # ---------------------------
    # Console render hook
    # ---------------------------
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """
        Render each line of the inner renderable, applying the gradient per character.

        Yields:
            Segment: Styled text segments with gradient coloring.
        """
        # Use the renderable's width constraint for gradient span
        target_width = console.width or 80

        # Include padding (borders, margins) in the rendered lines
        lines = console.render_lines(
            self.renderable, options, pad=True, new_lines=False
        )

        for line_no, segments in enumerate(lines):
            # Compute total visible width of this line
            col = 0
            for seg in segments:
                text = seg.text
                base_style = seg.style or Style()
                cluster = ""
                cluster_width = 0
                for ch in text:
                    w = get_character_cell_size(
                        ch
                    )  # Use rich.text.cells instead of wcwidth
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

    # ---------------------------
    # Gradient color calculation
    # ---------------------------
    def _color_at(self, position: int, width: int, span: int) -> str:
        """
        Compute the hex color code at a given character position within the span.

        Parameters:
            position: int
                Starting cell index of the character or cluster.
            width: int
                Cell width of the character or cluster.
            span: int
                Total available width for gradient calculation.

        Returns:
            str: A hex color string (#rrggbb).
        """
        frac = self._compute_frac(position, width, span)
        stops = self._stops
        count = len(stops)
        if count == 0:
            return ""
        r, g, b = self._interpolated_color(frac, stops, count)
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    def _compute_frac(self, position: int, width: int, span: int) -> float:
        """Compute the fractional position for the gradient, including phase shift."""
        frac = (position + width / 2 + self.phase) / max(span - 1, 1)
        return frac % 1.0 if self.animated else min(frac, 1.0)

    def _interpolated_color(self, frac: float, stops: list, count: int):
        """Interpolate the color at the given fractional position."""
        if frac <= 0:
            return stops[0]
        elif frac >= 1:
            return stops[-1]
        else:
            seg = frac * (count - 1)
            idx = int(seg)
            t = seg - idx
            r1, g1, b1 = stops[idx]
            r2, g2, b2 = stops[min(idx + 1, count - 1)]
            r = r1 + (r2 - r1) * t
            g = g1 + (g2 - g1) * t
            b = b1 + (b2 - b1) * t
            return r, g, b

    # ---------------------------
    # Style application helper
    # ---------------------------
    def _styled(self, original: Style, color: str) -> Style:
        """
        Combine the original style with a gradient color applied to foreground or background.

        Parameters:
            original: Style
                The existing Rich style for the segment.
            color: str
                Hex color string to apply.

        Returns:
            Style: A new Style with gradient coloring merged.
        """
        grad = Style(bgcolor=color) if self.background else Style(color=color)
        return Style.combine([original, grad])


def example() -> None:
    """
    Render a static gradient example to the console.

    Demonstrates applying a rainbow gradient to a sample Panel.
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    console.print(
        Gradient(
            Panel(
                "[i b]rich_gradient.gradient.Gradient[/] is a Rich renderable that applies a [u]smooth[/u] horizontal \
gradient to [reverse]ANY[/reverse] Rich renderable. It can be used with Text, Panel, Table, and more. \
It supports both rainbow gradients and custom color stops.",
                title="Gradient Example",
                padding=(1, 2),
            ),
            rainbow=True,
        )
    )

def specific_color_example() -> None:
    """
    Render a gradient example with specific color stops.

    Demonstrates applying a custom gradient to a sample Panel using specific colors.
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console()

    console.print(
        Gradient(
            Panel(
                "This is a [i b]specific color gradient[/] example. \
It uses a custom set of colors to create a smooth gradient effect across the text. \
You can use any valid Rich color identifiers, including hex 3 and 6 digit hex codes \
and CSS color names thanks to rich_color_ext.",
                title="Specific Color Gradient Example",
                subtitle = "red, orange, yellow, green, cyan",
                subtitle_align="right",
                padding=(1, 2),
            ),
            colors=[
                "#f00",  # Red
                "#f90",  # Orange
                "#ff0",  # Yellow
                "#0f0",  # Green
                "#0ff",  # Cyan
            ],
            background=False,  # Apply to foreground
            phase=0,  # No animation phase offset
        )
    )


# Animated example using Live
def animated_example() -> None:
    """
    Run an animated gradient demo in the terminal.

    Uses `rich.live.Live` to continuously animate the gradient effect until interrupted.
    """
    from rich.console import Console
    from rich.panel import Panel

    console = Console(width=80)
    panel = Panel(
        "Animating gradient...\nPress Ctrl+C to stop.",
        title="Animated Gradient",
        padding=(1, 2),
    )
    # Combine main panel and footer, then apply gradient over both
    gradient = Gradient(panel, rainbow=True, animated=True)
    live_renderable = gradient
    # Setup Live to refresh at ~30 FPS
    with Live(live_renderable, console=console, refresh_per_second=30):
        with suppress(KeyboardInterrupt):
            while True:
                time.sleep(0.03)
                # Increment phase to animate gradient shift
                gradient.phase += 0.5


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Gradient demonstration")
    parser.add_argument(
        "--animate",
        action="store_true",
        help="If set, run animated gradient with footer; otherwise run static example.",
    )
    parser.add_argument(
        "--phase",
        type=float,
        default=0.0,
        help="Optional initial phase offset (float) for the gradient.",
    )
    args = parser.parse_args()

    if not args.animate:
        example()
        specific_color_example()
    animated_example()
