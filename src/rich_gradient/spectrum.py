from __future__ import annotations

from itertools import cycle
from random import randint
from typing import List, Tuple

from pydantic_extra_types.color import ColorType
from rich.style import Style
from rich.table import Table
from rich.text import Text

from rich_gradient.color import Color


class Spectrum(List[Color]):
    """The colors from which to create random gradients.

    Attributes:
        NAMES (Tuple[str, ...]): Tuple of color names.
        HEX (Tuple[str, ...]): Tuple of color hex codes.
        RGB (Tuple[str, ...]): Tuple of color RGB values.

    Methods:
        __init__(): Initializes the Spectrum class.
        __rich__(): Returns a rich Table object representing the Spectrum colors.

    """

    NAMES: Tuple[str, ...] = (
        "magenta",  # 1
        "purple",  # 2
        "violet",  # 3
        "blue",  # 4
        "dodgerblue",  # 5
        "deepskyblue",  # 6
        "lightskyblue",  # 7
        "cyan",  # 8
        "springgreen",  # 9
        "lime",  # 10
        "greenyellow",  # 11
        "yellow",  # 12
        "orange",  # 13
        "darkorange",  # 14
        "tomato",  # 15
        "red",  # 16
        "deeppink",  # 17
        "hotpink",  # 18
    )

    HEX: Tuple[ColorType, ...] = (
        "#FF00FF",  # 1
        "#AF00FF",  # 2
        "#5F00FF",  # 3
        "#0000FF",  # 4
        "#0055FF",  # 5
        "#0087FF",  # 6
        "#00C3FF",  # 7
        "#00FFFF",  # 8
        "#00FFAF",  # 9
        "#00FF00",  # 10
        "#AFFF00",  # 11
        "#FFFF00",  # 12
        "#FFAF00",  # 13
        "#FF8700",  # 14
        "#FF4B00",  # 15
        "#FF0000",  # 16
        "#FF005F",  # 17
        "#FF00AF",  # 18
    )

    RGB: Tuple[ColorType, ...] = (
        "rgb(255, 0, 255)",
        "rgb(175, 0, 255)",
        "rgb(95, 0, 255)",
        "rgb(0, 0, 255)",
        "rgb(0, 85, 255)",
        "rgb(0, 135, 255)",
        "rgb(0, 195, 255)",
        "rgb(0, 255, 255)",
        "rgb(0, 255, 175)",
        "rgb(0, 255, 0)",
        "rgb(175, 255, 0)",
        "rgb(255, 255, 0)",
        "rgb(255, 175, 0)",
        "rgb(255, 135, 0)",
        "rgb(255, 75, 0)",
        "rgb(255, 0, 0)",
        "rgb(255, 0, 95)",
        "rgb(255, 0, 175)",
    )

    def __init__(self, length: int = 18,* , invert: bool = False) -> None:
        """Initializes the Spectrum class.

        Initializes the Spectrum class by creating a list of Color objects
        based on the HEX values.

        Args:
            length (int, optional): The number of colors in the Spectrum. Defaults to 18.
            invert (bool, optional): Invert the Spectrum colors. Defaults to False.
        """
        colors: List[Color] = [Color(hex) for hex in self.HEX]
        color_cycle = cycle(colors)
        for _ in range(0, randint(a=0, b=18)):
            color_cycle.__next__()
        if invert:
            self.COLORS = [next(color_cycle) for _ in range(length)][::-1]
        else:
            self.COLORS = [next(color_cycle) for _ in range(length)]
        super().__init__(self.COLORS)

    def __rich__(self) -> Table:
        """Returns a rich Table object representing the Spectrum colors.

        Returns:
            Table: A rich Table object representing the Spectrum colors.

        """
        table = Table(
            "[b i #ffffff]Sample[/]",
            "[b i #ffffff]Name[/]",
            "[b i #ffffff]Hex[/]",
            "[b i #ffffff]RGB[/]",
            title="[b #ffffff]Gradient Colors[/]",
            show_footer=False,
            show_header=True,
            row_styles=(["on #1f1f1f", "on #000000"]),
        )
        for color in self.COLORS:
            assert color.triplet, "ColorTriplet must not be None"
            triplet = color.triplet
            hex_str = triplet.hex.upper()
            if hex_str in [
                "#AF00FF",
                "#5F00FF",
                "#0000FF",
                "#0055FF",
            ]:
                foreground = "#ffffff"
            else:
                foreground = "#000000"
            bg_style = Style(color=foreground, bgcolor=hex_str, bold=True)
            style = Style(color=hex_str, bold=True)
            index = self.HEX.index(hex_str)
            name = self.NAMES[index].capitalize()
            table.add_row(
                Text(" " * 10, style=bg_style),
                Text(name, style=style),
                Text(hex_str, style=style),
                Text(triplet.rgb, style=style),
            )
        return table


if __name__ == "__main__":
    from rich.console import Console

    console = Console(width=64)
    console.line(2)
    console.print(Spectrum(), justify="center")
    console.line(2)
    console.save_svg("docs/img/spectrum.svg")
