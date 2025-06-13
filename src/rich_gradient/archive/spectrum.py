from __future__ import annotations

from itertools import cycle
from random import randint
from typing import Generator, List, Union

import rich_color_ext
from rich.console import Console
from rich.table import Table
from rich.text import Text

# from rich_gradient._colors import COLORS_BY_HEX, COLORS_BY_NAME
from rich_gradient.color import Color
from rich_gradient.style import Style

SPECTRUM_COLORS = [
    "#FF00FF", # 1 magenta
    "#CC55FF", # 2 purple
    "#9955FF", # 3 violet
    "#6666FF", # 4 purple-blue
    "#0099FF", # 5 blue
    "#00CCFF", # 6 lightblue
    "#00FFFF", # 7 cyan
    "#00FFC3", # 8 aquamarine
    "#00FF00", # 9 lime
    "#7CFF00",  # 10 green
    "#FFFF00",  # 11 yellow
    "#FFAF00",  # 12 orange
    "#FF7700",  # 13 orange-red
    "#FF0000",  # 14 red
    "#FF00AA",  # 16 pink
]
SPECTRUM_NAMES = {
    "#FF00FF": "magenta",
    "#CC55FF": "purple",
    "#9955FF": "violet",
    "#6666FF": "purple-blue",
    "#0099FF": "blue",
    "#00CCFF": "lightblue",
    "#00FFFF": "cyan",
    "#00FFC3": "aquamarine",
    "#00FF00": "lime",
    "#7CFF00": "green",
    "#FFFF00": "yellow",
    "#FFAF00": "orange",
    "#FF7700": "orange-red",
    "#FF0000": "red",
    "#FF00AA": "pink"
}


class Spectrum:
    """Create a list of concurrent Color and/or Style instances.

    Args:
        length (int): Number of colors to generate. Defaults to 18.
        invert (bool, optional): If True, reverse the generated list. Defaults to False.
        bold (bool, optional): If True, apply bold style. Defaults to False.
        italic (bool, optional): If True, apply italic style. Defaults to False.
        underline (bool, optional): If True, apply underline style. Defaults to False.
        strike (bool, optional): If True, apply strikethrough style. Defaults to False.
        reverse (bool, optional): If True, apply reverse style. Defaults to False.
        dim (bool, optional): If True, apply dim style. Defaults to False.

    Attributes:
        colors (List[Color]): A list of Color instances.
        styles (List[Style]): A list of Style instances.

    Example:
        >>> spectrum = Spectrum(5).colors
        >>> print(spectrum)
        [Color(name='purple'), Color(name='violet'), Color(name='blue'), Color(name='deepblue'), Color(name='skyblue')]
    """

    def __init__(
        self,
        length: int = 18,
        invert: bool = False,
        *,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strike: bool = False,
        reverse: bool = False,
        dim: bool = False,
    ) -> None:
        """
        Args:
            length (int): Number of colors to generate. Defaults to 18.
            invert (bool, optional): If True, reverse the generated list. Defaults to False.
            bold (bool, optional): If True, apply bold style. Defaults to False.
            italic (bool, optional): If True, apply italic style. Defaults to False.
            underline (bool, optional): If True, apply underline style. Defaults to False.
            strike (bool, optional): If True, apply strikethrough style. Defaults to False.
            reverse (bool, optional): If True, apply reverse style. Defaults to False.
            dim (bool, optional): If True, apply dim style. Defaults to False.

        Returns:
            List[Color]: A list of Color instances.

        Example:
            >>> spectrum = Spectrum(5).colors
            >>> print(spectrum)
            [Color(name='purple'), Color(name='violet'), Color(name='blue'), Color(name='deepblue'), Color(name='skyblue')]
        """
        base_colors = [Color(name) for name in SPECTRUM_COLORS]
        color_cycle = cycle(base_colors)
        offset = randint(1, len(base_colors))
        for _ in range(offset):
            next(color_cycle)
        self.colors: List[Color] = [next(color_cycle) for _ in range(length)]
        if invert:
            self.colors = list(reversed(self.colors))

        self.styles: List[Style] = [
            Style(
                color=color.hex,
                bold=bold,
                italic=italic,
                underline=underline,
                strike=strike,
                reverse=reverse,
                dim=dim,
            )
            for color in self.colors
        ]
        self.hex: List[str] = [color.hex for color in self.colors]

    def __getitem__(self, index: int) -> Style:
        return self.styles[index]

        self.hex: List[str] = [color.hex for color in self.colors]
        self.hex: List[str] = [color.hex for color in self.colors]

    def __rich__(self) -> Table:
        """Returns a rich Table object representing the Spectrum colors.

        Returns:
            Table: A rich Table object representing the Spectrum colors.

        """
        return self.table()

    @staticmethod
    def table() -> Table:
        """Returns a rich Table object representing the Spectrum colors.

        Returns:
            Table: A rich Table object representing the Spectrum colors.
        """
        table = Table(
            "[b i #ffffff]Sample[/]",
            "[b i #ffffff]Name[/]",
            "[b i #ffffff]Hex[/]",
            "[b i #ffffff]RGB[/]",
            title="[b #ffffff]Spectrum[/]",
            show_footer=False,
            show_header=True,
            row_styles=(["on #1f1f1f", "on #000000"]),
        )

        spectrum = Spectrum()
        for color in spectrum.colors:
            style = str(Style(color=color.hex, bold=True))
            name = Text(f"{SPECTRUM_NAMES[color.hex.upper()].capitalize():>16}", style=style)
            sample = Text(f"{'█' * 10}", style=style)
            hex_str = f" {color.as_hex('long').upper()} "
            hex_text = Text(f"{hex_str: ^7}", style=f"bold on {color.hex}")
            rgb = color._rgba

            table.add_row(sample, name, hex_text, rgb)

        return table


if __name__ == "__main__":
    from rich.console import Console

    console = Console(width=64)
    console.line(2)
    # spectrum = Spectrum()
    console.print(Spectrum.table())
    console.line(2)
    console.save_svg("docs/img/spectrum.svg")
