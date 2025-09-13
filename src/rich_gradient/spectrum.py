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

__all__ = ["SPECTRUM_COLORS", "Spectrum"]

from itertools import cycle
from random import Random
from typing import Dict, List, Optional

from rich.color import Color
from rich.color_triplet import ColorTriplet
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

SPECTRUM_COLORS: Dict[str, str] = {
    "#FF0000": "red",  # 1
    "#FF5500": "tomato",  # 2
    "#FF9900": "orange",  # 3
    "#FFCC00": "light-orange",  # 4
    "#FFFF00": "yellow",  # 5
    "#AAFF00": "green",  # 6
    "#00FF00": "lime",  # 7
    "#00FF99": "sea-green",  # 8
    "#00FFFF": "cyan",  # 9
    "#00CCFF": "powderblue",  # 10
    "#0088FF": "sky-blue",  # 11
    "#5066FF": "blue",  # 12
    "#A066FF": "purple",  # 13
    "#C030FF": "violet",  # 14
    "#FF00FF": "magenta",  # 15
    "#FF00AA": "pink",  # 16
    "#FF0055": "hot-pink",  # 17
}
# Ensure no color is paired with a white foreground when style is
# reversed. This is handled by always using the color itself as the
# foreground, and never setting foreground to white in style creation.


class Spectrum:
    """Create a list of concurrent Color and/or Style instances.
    Args:
        hues (int): Number of colors to generate. Defaults to 17.
        invert (bool, optional): If True, reverse the generated list. Defaults to False.
        seed (Optional[int], optional): If provided, sets the random seed for deterministic color order.
    """

    def __init__(
        self, hues: int = 17, invert: bool = False, seed: Optional[int] = None
    ) -> None:
        """Initialize the Spectrum with a specified number of hues and optional inversion and seed.
        Args:
            hues (int): Number of colors to generate. Defaults to 17.
            invert (bool, optional): If True, reverse the generated list. Defaults to False.
            seed (Optional[int], optional): If provided, sets the random seed for deterministic color order.
        Raises:
            ValueError: If hues < 2.
            ValueError: If seed is not None and not an integer.
        Returns:
            None
        """
        if hues < 2:
            raise ValueError("hues must be at least 2")
        # Use a dedicated RNG to avoid mutating global random state
        rng = Random(seed)
        # Generate a random cycle of colors from the spectrum
        colors: List[Color] = [Color.parse(color) for color in SPECTRUM_COLORS.keys()]
        color_cycle = cycle(colors)
        # Skip a pseudo-random number of colors to add variability, deterministically per seed
        for _ in range(rng.randint(1, 18)):
            next(color_cycle)
        # Create a list of colors based on the specified number of hues
        colors = [next(color_cycle) for _ in range(hues)]
        self._colors: List[Color] = colors
        if invert:
            self._colors.reverse()
        self._names = [
            SPECTRUM_COLORS[color.get_truecolor().hex.upper()] for color in self._colors
        ]
        self._styles = [
            Style(color=color, bold=False, italic=False, underline=False)
            for color in self._colors
        ]
        self.hex = [color.get_truecolor().hex.upper() for color in self._colors]
        # Do not maintain a stateful iterator; Spectrum is an iterable, not a stateful iterator.
        # If consumers need an iterator, they should call iter(spectrum).
        # self._iterator = iter(self._colors)

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

    @property
    def names(self) -> List[str]:
        """Return the list of color names."""
        return self._names

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
        table = Table(title="Spectrum Colors")
        table.add_column("[b white]Sample[/]", justify="center")
        table.add_column("[b white]Color[/]", style="bold")
        table.add_column("[b white]Hex[/]", style="bold")
        table.add_column("[b white]Name[/]", style="bold")

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


def example(save: bool = False) -> None:
    """Generate a rich table with all of the colors in the Spectrum."""
    from rich.console import Console

    console = Console(width=80)

    console.clear()
    console.line(2)
    console.print(
        f"Number of colors in the spectrum: [bold #FF00FF]{len(SPECTRUM_COLORS)}[/]"
    )
    console.line(2)
    console = Console(record=True, width=64) if save else Console(width=80)
    spectrum = Spectrum(seed=1)
    console.print(spectrum, justify="center")
    console.line(2)

    if save:
        console.save_svg(
            "docs/img/v0.3.4/spectrum_example.svg",
            title="rich-gradient",
            unique_id="spectrum_example",
            theme=GRADIENT_TERMINAL_THEME
        )


if __name__ == "__main__":
    example(True)
