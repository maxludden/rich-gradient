# rich_gradient/_base_gradient.py

"""
BaseGradient module for rich-gradient.

This module defines the BaseGradient class, which provides the core logic for
rendering color gradients in the terminal using the Rich library. It supports
foreground and background gradients, color interpolation with gamma
correction, and flexible alignment options. The BaseGradient class is
intended to be subclassed or used as a foundation for more specialized
gradient renderables.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import List, Optional, TypeAlias, Union

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
from rich.measure import Measurement
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style
from rich.text import Text as RichText

from rich_gradient.spectrum import Spectrum

# Type alias for accepted color inputs
ColorType: TypeAlias = Union[str, Color, ColorTriplet]

# Gamma correction exponent for linear interpolation
_GAMMA_CORRECTION: float = 2.2


class BaseGradient(JupyterMixin):
    """
    Base class for rendering color gradients in the terminal using Rich.

    This class applies a smoothly interpolated gradient of foreground and/or
    background colors across supplied renderable content.

    Attributes:
        console: Console instance used for rendering.
    """

    def __init__(
        self,
        renderables: ConsoleRenderable | List[ConsoleRenderable],
        colors: Optional[List[ColorType]] = None,
        bg_colors: Optional[List[ColorType]] = None,
        console: Optional[Console] = None,
        hues: int = 5,
        rainbow: bool = False,
        expand: bool = False,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "top",
        show_quit_panel: bool = False,
        repeat_scale: float = 2.0,
        background: bool = False,
    ) -> None:
        """
        Initialize a BaseGradient instance.

        Args:
            renderables: A single renderable or list of renderable objects to
                which the gradient will be applied.
            colors: Optional list of colors (strings, Color, or
                ColorTriplet) for the gradient foreground. If omitted and
                rainbow is False, a spectrum of `hues` colors is used.
            bg_colors: Optional list of colors for the gradient
                background. If omitted, no background gradient is applied.
            console: Optional Rich Console to render to. Defaults to
                `rich.get_console()`.
            hues: Number of hues to generate if no explicit colors are given.
            rainbow: If True, ignore `colors` and use a full rainbow.
            expand: Whether to expand renderables to the full console width.
            justify: Horizontal alignment: 'left', 'center', or 'right'.
            vertical_justify: Vertical alignment: 'top', 'center', or 'bottom'.
            show_quit_panel: If True, displays a quit instruction panel.
            repeat_scale: Scale factor controlling gradient repeat span.
        """
        self.console: Console = console or get_console()
        self.hues: int = max(hues, 2)
        self.rainbow: bool = rainbow
        self.repeat_scale: float = repeat_scale
        self.phase: float = 0.0
        self.expand: bool = expand
        self.justify = justify  # setter will validate
        self.vertical_justify = vertical_justify  # setter will validate
        self.show_quit_panel = show_quit_panel  # setter via property
        self.background: bool = bool(background)
        if renderables is None:
            renderables = []
        self.renderables = renderables
        self.colors = colors or []
        self.bg_colors = bg_colors or []
        self._active_stops = self._initialize_color_stops()

    @property
    def renderables(self) -> List[ConsoleRenderable]:
        """List of renderable objects to which the gradient is applied."""
        return self._renderables

    @renderables.setter
    def renderables(self, value: ConsoleRenderable | List[ConsoleRenderable]) -> None:
        """Set and normalize the list of renderables."""
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
        """
        Parse and set the foreground color stops.

        Args:
            colors: List of color strings, Color, or ColorTriplet.
        """
        if self.rainbow:
            triplets = Spectrum().triplets
        elif not colors:
            triplets = Spectrum(self.hues).triplets
        else:
            triplets = self._to_color_triplets(colors)

        # Loop smoothly by appending reversed middle stops
        if len(triplets) > 2:
            # Append reversed stops excluding final stop so gradient wraps smoothly
            triplets += list(reversed(triplets[:-1]))
        self._foreground_colors = triplets

    @property
    def bg_colors(self) -> List[ColorTriplet]:
        """List of parsed ColorTriplet objects for gradient background."""
        return self._background_colors

    @bg_colors.setter
    def bg_colors(self, colors: Optional[List[ColorType]]) -> None:
        """
        Parse and set the background color stops.

        Args:
            colors: Optional list of color strings, Color, or ColorTriplet.
        """
        if not colors:
            self._background_colors = []
            return

        if len(colors) == 1:
            triplet = Color.parse(colors[0]).get_truecolor()
            # repeat single color across hues
            self._background_colors = [triplet] * self.hues
        else:
            triplets = self._to_color_triplets(colors)
            self._background_colors = triplets

    @property
    def justify(self) -> AlignMethod:
        """Horizontal alignment method."""
        return self._justify  # type: ignore

    @justify.setter
    def justify(self, method: AlignMethod) -> None:
        """
        Validate and set horizontal alignment.

        Args:
            method: 'left', 'center', or 'right'.

        Raises:
            ValueError: If method is invalid.
        """
        if isinstance(method, str) and method.lower() in {"left", "center", "right"}:
            self._justify = method.lower()  # type: ignore
        else:
            raise ValueError(f"Invalid justify method: {method}")

    @property
    def vertical_justify(self) -> VerticalAlignMethod:
        """Vertical alignment method."""
        return self._vertical_justify  # type: ignore

    @vertical_justify.setter
    def vertical_justify(self, method: VerticalAlignMethod) -> None:
        """
        Validate and set vertical alignment.

        Args:
            method: 'top', 'center', or 'bottom'.

        Raises:
            ValueError: If method is invalid.
        """
        if isinstance(method, str) and method.lower() in {"top", "center", "bottom"}:
            self._vertical_justify = method.lower()  # type: ignore
        else:
            raise ValueError(f"Invalid vertical justify method: {method}")

    @property
    def show_quit_panel(self) -> bool:
        """Whether to display the quit instructions panel."""
        return self._show_quit_panel  # type: ignore

    @show_quit_panel.setter
    def show_quit_panel(self, value: bool) -> None:
        """
        Set whether to display the quit instructions panel.

        Args:
            show: True to display, False to hide.
        """
        self._show_quit_panel = bool(value)

    @staticmethod
    def _to_color_triplets(colors: List[ColorType]) -> List[ColorTriplet]:
        """
        Convert a list of color specifications to ColorTriplet instances.

        Args:
            colors: List of color strings, Color, or ColorTriplet.

        Returns:
            List of ColorTriplet.

        Raises:
            TypeError: If unsupported color type encountered.
            ColorParseError: If a color string fails to parse.
        """
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
        """
        Measure the minimum and maximum width for the gradient content.

        Args:
            console: Console for measurement.
            options: Rendering options.

        Returns:
            Measurement: Combined width constraints.
        """
        measurements = [Measurement.get(console, options, r) for r in self.renderables]
        if not measurements:
            # No renderables — return a reasonable default measurement.
            # Min width is 0; max width is the available maximum from options.
            return Measurement(0, options.max_width or 0)

        min_width = min(m.minimum for m in measurements)
        max_width = max(m.maximum for m in measurements)
        return Measurement(min_width, max_width)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """
        Render the gradient by applying interpolated colors to each segment.

        Args:
            console: Console to render to.
            options: Rendering options.

        Yields:
            Segment: Colored text segments for gradient effect.
        """
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
        """
        Compute the Rich Style for a character cluster at a given position.

        Args:
            position: Starting cell index of the cluster.
            width: Cell width of the cluster.
            span: Total available width for gradient calculation.

        Returns:
            Style with appropriate foreground and/or background colors.
        """
        frac = self._compute_fraction(position, width, span)
        # If background mode is enabled, apply gradient to background only.
        if self.background:
            active = self.bg_colors if self.bg_colors else self.colors
            if not active:
                return Style()
            r, g, b = self._interpolate_color(frac, active)
            bg_style = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
            return Style(bgcolor=bg_style)

        # Default: apply gradient to foreground; background uses bg_colors if provided.
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
        """
        Compute fractional position for gradient interpolation, including phase.

        Args:
            position: Starting cell index.
            width: Cell width.
            span: Total span for gradient.

        Returns:
            Fraction between 0.0 and 1.0.
        """
        total_width = (span or 0) * (self.repeat_scale or 1.0)
        if total_width <= 0:
            # Avoid division by zero; return phase-only fraction.
            return self.phase % 1.0

        base = (position + width / 2) / total_width
        return (base + self.phase) % 1.0

    def _interpolate_color(
        self, frac: float, color_stops: list[ColorTriplet]
    ) -> tuple[float, float, float]:
        """
        Interpolate color in linear light space with gamma correction.

        Args:
            frac: Fractional position between 0.0 and 1.0.
            color_stops: List of ColorTriplet stops.

        Returns:
            Tuple of (r, g, b) in sRGB space.
        """
        if frac <= 0:
            return color_stops[0]
        if frac >= 1:
            return color_stops[-1]

        # Determine segment and local position
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
        """
        Merge original Style with gradient Style, preserving original attributes.

        Args:
            original: The existing Rich Style.
            gradient_style: Style with gradient colors.

        Returns:
            Combined Style.
        """
        return original + gradient_style if original else gradient_style

    # -----------------
    # Test helper parity
    # -----------------
    def _initialize_color_stops(self) -> List[ColorTriplet]:
        """Initialize the active color stops based on mode and provided stops.

        If only one stop is provided, duplicate it to create a smooth segment pair.
        """
        source = self.bg_colors if self.background else self.colors
        if not source:
            return []
        return [source[0], source[0]] if len(source) == 1 else source

    def _color_at(self, pos: int, width: int, span: int) -> str:
        """Return the hex color at a given position (for tests)."""
        stops = self._active_stops
        if not stops:
            return "#000000"
        frac = self._compute_fraction(pos, width, span)
        r, g, b = self._interpolate_color(frac, stops)
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    def _styled(self, original: Style, color: str) -> Style:
        """Return a Style with the given color or bgcolor, preserving original (for tests)."""
        return (
            original + Style(bgcolor=color)
            if self.background
            else original + Style(color=color)
        )

    def _interpolated_color(self, frac: float, stops: list, n: int):
        """Return the interpolated color at a fraction (for tests)."""
        return self._interpolate_color(frac, stops)


if __name__ == "__main__":
    # Example BaseGradient Usage
    gradient = BaseGradient(
        renderables=[
            RichText.from_markup(
                "BaseGradient can print any [reverse bold]rich.console.ConsoleRenderable[/reverse bold] \
in [i]smooth[/i], [b]gradient[/b] color. If no explicit colors are given, a spectrum of \
colors is generated based on the BaseGradient.[b][i]hue[/i][/b]."
            ),
            NewLine(),
            Panel(
                "BaseGradient can parse and render gradients from:\n\t- CSS3 named colors,\n\t- 3 \
and 6 digit hex codes,\n\t- RGB triplets [i](rich.color.ColorTriplet)[/i]",
                title="BaseGradient Color Parsing",
            ),
        ],
        justify="center",
        vertical_justify="top",
        bg_colors=["#000000"],
    )
    console = get_console()
    console.print(gradient)
