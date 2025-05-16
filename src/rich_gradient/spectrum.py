from __future__ import annotations

from itertools import cycle
from random import randint
from typing import Generator

from rich.console import Console
from rich.table import Table
from rich.text import Text

from rich_gradient._colors import COLORS_BY_NAME, COLORS_BY_HEX
from rich_gradient.color import Color
from rich_gradient.style import Style


class Spectrum(list):
    """Create a list of Color instances by:
    1. Cycling through the first 18 keys of COLORS_BY_NAME.
    2. Skipping a random offset.
    3. Collecting the next `length` colors.
    4. Optionally reversing the sequence.

    Args:
        length (int): Number of colors to generate. Defaults to 18.
        invert (bool, optional): If True, reverse the generated list. Defaults to False.

    Returns:
        List[Color]: A list of Color instances.

    Example:
        >>> spectrum = Spectrum(5)
        >>> print(spectrum)
        [Color(name='purple'), Color(name='violet'), Color(name='blue'), Color(name='deepblue'), Color(name='skyblue')]
    """

    def __new__(cls, length: int = 18, invert: bool = False):
        """
        Create a list of `length` Color instances by:
            1. Cycling through the first 18 keys of COLORS_BY_NAME.
            2. Skipping a random offset.
            3. Collecting the next `length` colors.
            4. Optionally reversing the sequence.

        Args:
            length (int): Number of colors to generate.
            invert (bool, optional): If True, reverse the generated list. Defaults to False.

        Returns:
            List[Color]: A list of Color instances.

        Example:
            >>> spectrum = Spectrum(5)
            >>> print(spectrum)
            [Color(name='purple'), Color(name='violet'), Color(name='blue'), Color(name='deepblue'), Color(name='skyblue')]
        """
        base_names = list(COLORS_BY_NAME.keys())[:18]
        base_colors = [Color(name) for name in base_names]
        color_cycle = cycle(base_colors)
        offset = randint(1, len(base_colors))
        for _ in range(offset):
            next(color_cycle)
        colors = [next(color_cycle) for _ in range(length)]
        if invert:
            colors = list(reversed(colors))
        return colors

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

        colors = Spectrum()
        for index, color in enumerate(colors):
            style = str(Style(color=color.hex, bold=True))
            name_str = COLORS_BY_HEX.get(color.hex.upper(), {}).get("name", color.name)
            name = Text(f"{str(name_str).capitalize(): <13}", style=style)
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
