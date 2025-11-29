"""rich_gradient.spectrum

Module providing a small color palette helper built on Rich.

This module exposes:

- SPECTRUM_COLORS: a mapping of hex color strings to human-friendly names.
- Spectrum: a convenience class that builds lists of Rich Color, Style,
    and ColorTriplet objects drawn from the spectrum. It is iterable and
    implements __rich__ to render a preview table suitable for
    `rich.console.Console.print`.py

Notes on determinism and `seed`:
- The `Spectrum` constructor accepts an optional `seed` argument. When
    provided it calls the global `random.seed(seed)` to make the initial
    random offset deterministic. That means the same `seed` + same
    parameters will yield the same palette order, but it also affects the
    global random state.
- If you need determinism without altering global random state, use a
    dedicated `random.Random` instance and adapt the implementation.

Usage example:

    from rich.console import Console
    from rich_gradient.spectrum import Spectrum

    console = Console()
    spectrum = Spectrum(hues=8, seed=42)
    console.print(spectrum)

"""

__all__ = ["COLOR_STOPS", "Spectrum", "GradientTheme"]

from itertools import cycle
from random import Random

from typing import Dict, List, Optional

from rich.color import Color
from rich.color_triplet import ColorTriplet
from rich.console import Console
from rich.style import Style, StyleType
from rich.table import Table
from rich.text import Text
from rich_gradient._color_ext import get_css_map, install, is_installed

from rich_gradient.config import config
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme
from rich_gradient._logger import logger

if not is_installed():
    install()

COLOR_STOPS = {}
try:
    COLOR_STOPS = dict(getattr(config, "colors", {}) or {})
except (AttributeError, TypeError, ValueError):
    COLOR_STOPS = {
        "red": "#FF0000",
        "tomato": "#FF5500",
        "orange": "#FF9900",
        "gold": "#FFCC00",
        "yellow": "#FFFF00",
        "green": "#AAFF00",
        "lime": "#00FF00",
        "mint": "#00FF99",
        "cyan": "#00FFFF",
        "lightblue": "#00CCFF",
        "skyblue": "#0099FF",
        "blue": "#5066FF",
        "purple": "#8055FF",
        "violet": "#B033FF",
        "magenta": "#FF00FF",
        "pink": "#FF00AA",
        "rose": "#FF0055"
    }


class Spectrum:
    """Create a list of concurrent Color and/or Style instances.
    Args:
        hues (int): Number of colors to generate. Defaults to 17.
        invert (bool, optional): If True, reverse the generated list.
            Defaults to False.
        seed (Optional[int], optional): If provided, sets the random \
seed for deterministic color order.
    Raises:
        ValueError: If hues < 2.
        ValueError: If seed is not None and not an integer.
    Properties:
        colors (List[Color]): List of Color instances.
        names (List[str]): List of color names.

    """

    def __init__(
        self, hues: int = 17, invert: bool = False, seed: Optional[int] = None
    ) -> None:
        """Initialize the Spectrum with a specified number of hues and optional \
inversion and seed.
        Args:
            hues (int): Number of colors to generate. Defaults to 17.
            invert (bool, optional): If True, reverse the generated list.
                Defaults to False.
            seed (Optional[int], optional): If provided, sets the random seed for \
deterministic color order.
        Raises:
            ValueError: If hues < 2.
            ValueError: If seed is not None and not an integer.
        """
        if hues < 2:
            raise ValueError("hues must be at least 2")
        if hues > len(COLOR_STOPS):
            raise ValueError(f"hues must be at most {len(COLOR_STOPS)}")
        if seed is not None and not isinstance(seed, int):
            raise ValueError("seed must be an integer or None")

        # Use a dedicated RNG to avoid mutating global random state
        rng = Random(seed)

        # Generate a random cycle of colors from the spectrum
        colors: List[Color] = [Color.parse(color) for color in COLOR_STOPS.values()]
        color_cycle = cycle(colors)

        # Skip a pseudo-random number of colors to add variability, deterministically per seed
        for _ in range(rng.randint(1, 18)):
            next(color_cycle)

        # Create a list of colors based on the specified number of hues
        colors = [next(color_cycle) for _ in range(hues)]
        self.colors = colors
        if invert:
            self.colors.reverse()

        # Set names based on COLOR_STOPS mapping
        # Build a reverse map from normalized hex -> name and assign names for the selected colors

        hex_to_name = {
            Color.parse(value).get_truecolor().hex.upper(): name
            for name, value in COLOR_STOPS.items()
        }
        self.names = [
            hex_to_name.get(color.get_truecolor().hex.upper(), color.get_truecolor().hex.upper())
            for color in self.colors
        ]


        self.styles = [
            Style(color=color, bold=False, italic=False, underline=False)
            for color in self.colors
        ]
        self.hex = [color.get_truecolor().hex.upper() for color in self.colors]

    @property
    def colors(self) -> List[Color]:
        """Return the list of Color instances."""
        return self._colors

    @colors.setter
    def colors(self, value: List[Color]) -> None:
        """Set the list of Color instances."""
        if not isinstance(value, list) or not all(isinstance(c, Color) for c in value):
            raise ValueError("colors must be a list of Color instances")
        if len(value) < 2:
            raise ValueError("colors must contain at least two Color instances")
        self._colors = value

    @property
    def triplets(self) -> List[ColorTriplet]:
        """Return the list of ColorTriplet instances."""
        return [color.get_truecolor() for color in self._colors]

    @property
    def styles(self) -> List[Style]:
        """Return the list of Style instances."""
        return self._styles

    @styles.setter
    def styles(self, styles: List[StyleType]) -> None:
        """Set the list of Style instances."""
        if not isinstance(styles, list) or not all(
            isinstance(s, Style) for s in styles
        ):
            raise ValueError("styles must be a list of Style instances")
        if len(styles) != len(self.colors):
            raise ValueError("styles length must match colors length")
        parsed_styles: List[Style] = []
        for style in styles:
            if isinstance(style, (str)):
                parsed_styles.append(Style.parse(style))
            if isinstance(style, Style):
                parsed_styles.append(style)
        self._styles = parsed_styles

    @property
    def names(self) -> List[str]:
        """Return the list of color names."""
        return self._names

    @names.setter
    def names(self, value: List[str]) -> None:
        """Set the list of color names."""
        if not isinstance(value, list) or not all(isinstance(n, str) for n in value):
            raise ValueError("names must be a list of strings")
        if len(value) != len(self._colors):
            raise ValueError("names length must match colors length")
        self._names = value

    def __repr__(self) -> str:
        """Return a string representation of the Spectrum."""
        colors = [f"{name}" for name in self.names]
        colors_str = ", ".join(colors)
        return f"Spectrum({colors_str})"

    def __len__(self) -> int:
        """Return the number of colors in the Spectrum."""
        return len(self.colors)

    def __getitem__(self, index: int) -> Color:
        """Return the Color at the specified index."""
        if not isinstance(index, int):
            raise TypeError("Index must be an integer")
        if index < 0 or index >= len(self.colors):
            raise IndexError("Index out of range")
        return self.colors[index]

    def __iter__(self):
        """Return an iterator over the colors in the Spectrum."""
        return iter(self.colors)

    def __rich__(self) -> Table:
        """Return a rich Table representation of the Spectrum."""

        def rainbow_title(text: str) -> Text:
            chunks = [text[i : i + 2] for i in range(0, len(text), 2)]
            pieces: List[Text] = []
            for idx, chunk in enumerate(chunks):
                color = self.colors[idx % len(self.colors)]
                hex_code = color.get_truecolor().hex
                pieces.append(Text(chunk, style=f"b u {hex_code}"))
            return Text.assemble(*pieces)

        table = Table(title=rainbow_title("Spectrum Colors"))
        table.add_column(
            rainbow_title("Sample"), justify="center")
        table.add_column(rainbow_title("Color"), style="bold")
        table.add_column(rainbow_title("Hex"), style="bold")
        table.add_column(rainbow_title("Name"), style="bold")

        for color, name in zip(self.colors, self.names):
            hex_code = color.get_truecolor().hex
            red = color.get_truecolor().red
            green = color.get_truecolor().green
            blue = color.get_truecolor().blue

            name_text = Text(
                name.capitalize(),
                Style(color=hex_code, bold=True),
                no_wrap=True,
                justify="left",
            )
            hex_text = Text(
                f" {hex_code.upper()} ",
                Style(bgcolor=hex_code, color="#000000", bold=True),
                no_wrap=True,
                justify="center",
            )
            rgb_text = Text.assemble(*[
                Text("rgb", style=f"bold {hex_code}"),
                Text("(", style="i white"),
                Text(f"{red:>3}", style="#FF0000"),
                Text(",", style="i #555"),
                Text(f"{green:>3}", style="#00FF00"),
                Text(",", style="i #555"),
                Text(f"{blue:>3}", style="#00AAFF"),
                Text(")", style="i white"),
            ])
            sample = Text("█" * 10, style=Style(color=hex_code, bold=True))
            table.add_row(sample, name_text, hex_text, rgb_text)
        return table

    @property
    def rich(self) -> Table:
        """Return the rich Table representation of the Spectrum."""
        return self.__rich__()


def example(save: bool = False) -> None:
    """Generate a rich table with all of the colors in the Spectrum."""
    console = Console(record=True, width=64) if save else Console(width=80)
    console.line(2)
    spectrum = Spectrum(seed=5)
    console.print(spectrum, justify="center")
    console.line(2)

    if save:
        console.save_svg(
            "docs/img/v0.3.4/spectrum_example.svg",
            title="rich-gradient",
            unique_id="spectrum_example",
            theme=GRADIENT_TERMINAL_THEME,
        )


if __name__ == "__main__":
    example(True)
