"""Cached style ramps for gradient rendering."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil

from rich.color_triplet import ColorTriplet
from rich.style import Style


@dataclass(frozen=True)
class GradientRamp:
    """Precomputed Rich styles for a terminal-width gradient span.

    Args:
        foreground_stops: Foreground color stops used for interpolation.
        background_stops: Background color stops used for interpolation.
        span: Render span in terminal cells.
        repeat_scale: Scale factor controlling the gradient repeat width.
        gamma: Gamma correction exponent for interpolation.
    """

    foreground_stops: tuple[ColorTriplet, ...]
    background_stops: tuple[ColorTriplet, ...]
    span: int
    repeat_scale: float
    gamma: float = 2.2
    _total_width: float = field(init=False, repr=False)
    _styles: tuple[Style, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Build the style ramp after dataclass initialization."""
        object.__setattr__(self, "_total_width", self._compute_total_width())
        object.__setattr__(self, "_styles", self._build_styles())

    @property
    def styles(self) -> tuple[Style, ...]:
        """Return precomputed styles for this ramp."""
        return self._styles

    def style_at(self, position: int, width: int, phase: float = 0.0) -> Style:
        """Return the style for a rendered cluster.

        Args:
            position: Starting terminal-cell position of the cluster.
            width: Terminal-cell width of the cluster.
            phase: Animation phase as a fractional ramp offset.

        Returns:
            A Rich style for the requested cluster position.
        """
        if not self.styles:
            return Style.null()

        total_width: float = self._total_width
        if total_width <= 0:
            ramp_position: float = phase % 1.0
        else:
            ramp_position = ((position + width / 2) / total_width + phase) % 1.0
        index: int = int(ramp_position * len(self.styles)) % len(self.styles)
        return self.styles[index]

    def _compute_total_width(self) -> float:
        """Return the scaled width used for gradient positioning."""
        return max(0.0, float(self.span or 0) * float(self.repeat_scale or 1.0))

    def _build_styles(self) -> tuple[Style, ...]:
        """Precompute styles for all cells in the ramp."""
        total_width: float = self._total_width
        ramp_size: int = max(1, ceil(total_width))
        return tuple(
            self._style_for_fraction(((index + 0.5) / total_width) % 1.0)
            if total_width > 0
            else self._style_for_fraction(0.0)
            for index in range(ramp_size)
        )

    def _style_for_fraction(self, fraction: float) -> Style:
        """Build a Rich style for a fractional position in the ramp."""
        color: str | None = self._hex_for_stops(fraction, self.foreground_stops)
        bgcolor: str | None = self._hex_for_stops(fraction, self.background_stops)
        return Style(color=color, bgcolor=bgcolor)

    def _hex_for_stops(
        self, fraction: float, color_stops: tuple[ColorTriplet, ...]
    ) -> str | None:
        """Return a hex color for color stops at a fractional position."""
        if not color_stops:
            return None
        red, green, blue = self._interpolate_color(fraction, color_stops)
        return f"#{int(red):02x}{int(green):02x}{int(blue):02x}"

    def _interpolate_color(
        self, fraction: float, color_stops: tuple[ColorTriplet, ...]
    ) -> tuple[float, float, float]:
        """Interpolate color stops in linear light space.

        Args:
            fraction: Fractional position between 0.0 and 1.0.
            color_stops: Color stops to interpolate.

        Returns:
            Red, green, and blue sRGB channel values.
        """
        if fraction <= 0:
            return color_stops[0]
        if fraction >= 1:
            return color_stops[-1]

        segment_count: int = len(color_stops) - 1
        position: float = fraction * segment_count
        index = int(position)
        ratio: float = position - index

        red0, green0, blue0 = color_stops[index]
        red1, green1, blue1 = color_stops[min(index + 1, segment_count)]

        def to_linear(channel: float) -> float:
            return (channel / 255.0) ** self.gamma

        def to_srgb(channel: float) -> float:
            return (channel ** (1.0 / self.gamma)) * 255.0

        linear_red: float = to_linear(red0) + (to_linear(red1) - to_linear(red0)) * ratio
        linear_green: float = (
            to_linear(green0) + (to_linear(green1) - to_linear(green0)) * ratio
        )
        linear_blue: float = to_linear(blue0) + (to_linear(blue1) - to_linear(blue0)) * ratio

        return to_srgb(linear_red), to_srgb(linear_green), to_srgb(linear_blue)
