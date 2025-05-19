"""Gradient rendering utilities using Rich.

This module defines a `Gradient` ConsoleRenderable that can wrap any Rich renderable
and apply a left-to-right color gradient to it using either a provided color palette
or a default rainbow spectrum.
"""

from colorsys import hls_to_rgb
from typing import List, Optional, Union

from rich.console import Console, ConsoleOptions, ConsoleRenderable, RenderResult
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from rich_gradient.color import Color
from rich_gradient.spectrum import Spectrum


def hsl_to_rgb_hex(h: float, s: float, l: float) -> str:
    """Convert an HSL color to a hex RGB string.

    Args:
        h: Hue component (0–1).
        s: Saturation component (0–1).
        l: Lightness component (0–1).

    Returns:
        Hex RGB color string.
    """
    r, g, b = hls_to_rgb(h, l, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


class Gradient(ConsoleRenderable):
    """
    A Rich ConsoleRenderable that applies a horizontal color gradient to any renderable.

    The gradient can be configured using a list of hex colors, a rainbow flag,
    or a number of generated hues.
    """
    def __init__(
        self,
        renderable: ConsoleRenderable,
        colors: Optional[List[str]] = None,
        hues: int = 5,
        *,
        rainbow: bool = False,
        spread: Optional[float] = None,
        saturation: float = 1.0,
        lightness: float = 0.5,
        offset: float = 0.0,
        animate: bool = False,
    ) -> None:
        """
        Initialize a Gradient renderable.

        Args:
            renderable: The Rich renderable to wrap.
            colors: Optional list of color stops (hex strings).
            hues: Number of hues to generate if colors is None and rainbow is False.
            rainbow: Whether to use a rainbow spectrum for the gradient.
            spread: Fixed width to spread the gradient over. Defaults to visual line width.
            saturation: Saturation value for rainbow generation (0–1).
            lightness: Lightness value for rainbow generation (0–1).
            offset: Hue offset for animation or scrolling effects.
            animate: Whether to animate the gradient with continuous updates.
        """
        self.renderable: ConsoleRenderable = renderable
        self.colors: List[str] = self.parse_colors(rainbow, hues, colors)
        self.spread: Optional[float] = spread
        self.saturation: float = saturation
        self.lightness: float = lightness
        self.offset: float = offset
        self.animate = animate

    def parse_colors(
        self, rainbow: bool, hues: int, colors: Optional[List[str]]
    ) -> List[str]:
        """
        Parse or generate a list of hex color strings to use for the gradient.

        Args:
            rainbow: Whether to use a rainbow color spectrum.
            hues: Number of hues to generate if not using a rainbow.
            colors: Optional list of hex color strings.

        Returns:
            A list of hex colors suitable for the gradient.
        """
        if rainbow:
            return Spectrum().hex
        if colors is None:
            return Spectrum(hues).hex
        parsed_colors: List[str] = []
        for color in colors:
            parsed_colors.append(Color(str(color)).hex)
        return parsed_colors

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """
        Render the gradient-wrapped content.

        Args:
            console: The console to render with.
            options: Rendering options, including width and styles.

        Yields:
            Rich Text lines with gradient applied character-by-character.
        """
        if self.animate:
            from time import sleep
            try:
                while True:
                    yield from Gradient(
                        self.renderable,
                        colors=self.colors,
                        hues=len(self.colors),
                        rainbow=False,
                        spread=self.spread,
                        saturation=self.saturation,
                        lightness=self.lightness,
                        offset=self.offset,
                        animate=False,
                    ).__rich_console__(console, options)
                    self.offset += 0.01
                    sleep(1 / 30)
            except KeyboardInterrupt:
                return

        lines = list(console.render_lines(self.renderable, options, style=None))

        for line in lines:
            width = (
                int(self.spread)
                if self.spread is not None
                else sum(len(seg.text) for seg in line)
            )
            gradient_line = Text()
            char_index = 0
            for segment in line:
                style = segment.style or Style()
                for char in segment.text:
                    color = self.get_color_at(char_index, width)
                    gradient_line.append(char, style=style + Style(color=color))
                    char_index += 1
            yield gradient_line

    def get_color_at(self, index: int, width: int) -> str:
        """
        Get the interpolated color for the character at the given index.

        Args:
            index: Position of the character in the line.
            width: Total width of the line.

        Returns:
            A hex color string.
        """
        if self.colors and len(self.colors) > 1:
            # Calculate position in gradient [0, 1]
            t = index / max(width - 1, 1)
            num_segments = len(self.colors) - 1
            scaled_t = t * num_segments
            seg_index = int(scaled_t)
            local_t = scaled_t - seg_index

            if seg_index >= num_segments:
                return self.colors[-1]

            def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
                """Convert a hex color string to an RGB tuple."""
                if hex_color.startswith("#"):
                    hex_color = hex_color.lstrip("#")
                if len(hex_color) == 3:
                    hex_color = "".join([c * 2 for c in hex_color])
                if len(hex_color) != 6:
                    raise ValueError(f"Invalid hex color: {hex_color}")
                if not all(c in "0123456789abcdefABCDEF" for c in hex_color):
                    raise ValueError(f"Invalid hex color: {hex_color}")
                return (
                    int(hex_color[0:2], 16),
                    int(hex_color[2:4], 16),
                    int(hex_color[4:6], 16),
                )

            def rgb_to_hex(rgb: tuple[int, ...]) -> str:
                return "#{:02x}{:02x}{:02x}".format(*rgb)

            start_rgb = hex_to_rgb(self.colors[seg_index])
            end_rgb = hex_to_rgb(self.colors[seg_index + 1])

            blended = tuple(
                int(start + (end - start) * local_t)
                for start, end in zip(start_rgb, end_rgb)
            )
            return rgb_to_hex(blended)

        # fallback to hue wheel
        hue = (self.offset + index / width) % 1.0
        return hsl_to_rgb_hex(hue, self.saturation, self.lightness)


if __name__ == "__main__":
    console = Console()
    text: Text = Text("""
Ipsum ullamco sint veniam id sunt commodo ipsum veniam aliquip labore sint pariatur dolore proident cillum. Eiusmod nulla veniam dolore consequat ea irure. Labore cupidatat nulla laboris reprehenderit esse aliquip velit sunt do adipisicing aliqua ex dolore ad. Nulla sit amet nostrud. Tempor ipsum Lorem aliquip et eiusmod aliquip ullamco cupidatat. Consequat occaecat tempor cillum aliqua reprehenderit in consectetur quis veniam nostrud tempor occaecat qui est duis.

Sunt quis esse occaecat eu commodo sint anim pariatur aute non laboris ad. Magna elit culpa consequat nulla. Aliqua culpa magna aliqua aliqua sint deserunt occaecat duis ex adipisicing ut non. Duis esse proident irure cupidatat do commodo esse proident Lorem. Quis adipisicing nostrud eiusmod amet incididunt dolor excepteur commodo ea sit tempor anim.

Veniam qui excepteur pariatur voluptate fugiat. Eu amet incididunt est aute fugiat sunt. Adipisicing qui aliqua duis elit nulla. Irure aute nostrud reprehenderit id aliquip. Adipisicing laboris pariatur veniam fugiat et dolor eiusmod excepteur voluptate. Pariatur ea excepteur ipsum. Non in excepteur ea ut aliquip officia excepteur esse esse deserunt sunt ipsum incididunt.""",
        justify="right", style="bold"
    )
    console.print(Gradient(Panel(text),))
