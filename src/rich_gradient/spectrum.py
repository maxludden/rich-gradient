from itertools import cycle
from random import randint
from typing import Dict, List, Tuple

from rich import get_console
from rich.color import Color
from rich.color_triplet import ColorTriplet
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.traceback import install as tr_install
from rich_color_ext import install

console: Console = get_console()
tr_install(console=console)
install()

SPECTRUM_NAMES: Dict[str, str] = {
    "#FF0000": "red",
    "#FF5500": "tomato",
    "#FF9900": "orange",
    "#FFCC00": "light-orange",
    "#FFFF00": "yellow",
    "#AAFF00": "green",
    "#00FF00": "lime",
    "#00FF99": "sea-green",
    "#00FFFF": "cyan",
    "#00CCFF": "powerderblue",
    "#0088FF": "sky-blue",
    "#5066FF": "blue",
    "#A066FF": "purple",
    "#C030FF": "violet",
    "#FF00FF": "magenta",
    "#FF00AA": "pink",
    "#FF0055": "hot-pink"
}
# Ensure no color is paired with a white foreground, even when reversed.
# This is handled by always using the color itself as the foreground,
# and never setting foreground to white in style creation.


class Spectrum:
    """Create a list of concurrent Color and/or Style instances.
    Args:
        hues (int): Number of colors to generate. Defaults to 18.
        invert (bool, optional): If True, reverse the generated list. Defaults to False.

    Raises:
        ValueError: If hues is less than 2.

    Attributes:
        colors (List[Color]): List of Color instances.
        triplets (List[ColorTriplet]): List of ColorTriplet instances.
        styles (List[Style]): List of Style instances.
        names (List[str]): List of color names corresponding to the colors.
    """

    def __init__(self, hues: int = 17, invert: bool = False) -> None:
        """Initialize the Spectrum with a specified number of hues and optional inversion."""
        if hues < 2:
            raise ValueError("hues must be at least 2")

        # Generate a random cycle of colors from the spectrum
        colors: List[Color] = [Color.parse(color) for color in SPECTRUM_NAMES.keys()]
        color_cycle = cycle(colors)

        # Skip a random number of colors to add variability
        for _ in range(randint(1, 18)):
            next(color_cycle)

        # Create a list of colors based on the specified number of hues
        colors = [next(color_cycle) for _ in range(hues)]
        self._colors: List[Color] = colors

        # If invert is True, reverse the order of colors
        if invert:
            self._colors.reverse()

        # Create names and styles based on the colors
        self._names = [
            SPECTRUM_NAMES[color.get_truecolor().hex.upper()] for color in self._colors
        ]

        # Create Style instances for each color
        self._styles = [
            Style(color=color, bold=False, italic=False, underline=False)
            for color in self._colors
        ]

        self.hex = [color.get_truecolor().hex.upper() for color in self._colors]

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

    def __next__(self):
        """Return the next color in the Spectrum."""
        return next(iter(self.colors))

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
                justify="center",
            )
            hex_text = Text(
                f" {hex_code.upper()} ",
                Style(bgcolor=hex_code, bold=True),
                no_wrap=True,
                justify="center",
            )
            rgb_text = Text.assemble(*[
                Text("rgb", style=f"bold {hex_code}"),
                Text("(", style="i white"),
                Text(f"{red:>3}", style="#f00"),
                Text(",", style="i #555"),
                Text(f"{green:>3}", style="#0f0"),
                Text(",", style="i #555"),
                Text(f"{blue:>3}", style="#09f"),
                Text(")", style="i white"),
            ])
            sample = Text("█" * 10, style=Style(color=hex_code, bold=True))
            table.add_row(sample, name_text, hex_text, rgb_text)
        return table


def example():
    """Generate a rich table with all of the colors in the Spectrum."""
    console.clear()
    console.line(2)
    console.print(f'Number of colors in the spectrum: [bold magenta]{len(SPECTRUM_NAMES)}[/]')
    console.line(2)
    spectrum = Spectrum()
    console.print(spectrum)
    console.line(2)


if __name__ == "__main__":
    example()
