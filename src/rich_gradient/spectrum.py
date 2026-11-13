"""A small, seedable color palette helper built on Rich.

This module exposes:

- ``COLOR_STOPS``: a mapping of human-friendly color names to hex strings.
- ``Spectrum``: a convenience class that builds lists of Rich ``Color``,
    ``Style``, and ``ColorTriplet`` objects drawn from the palette. It is
    iterable and implements ``__rich__`` to render a preview table suitable
    for ``rich.console.Console.print``.
- ``validate_hues``: the shared ``hues >= 2`` check used across the package.

Notes on determinism and `seed`:
- The `Spectrum` constructor accepts an optional `seed` argument. When
    provided, a dedicated `random.Random(seed)` instance is used to pick the
    initial palette offset, so the same `seed` + same parameters yield the
    same palette order without touching global random state.

Usage example:

    from rich.console import Console
    from rich_gradient.spectrum import Spectrum

    console = Console()
    spectrum = Spectrum(hues=8, seed=42)
    console.print(spectrum)

"""

__all__ = ["COLOR_STOPS", "GradientTheme", "Spectrum"]

from itertools import cycle
from random import Random
from collections.abc import Iterator
from typing import Dict, List, Optional

from rich.color import Color
from rich.color_triplet import ColorTriplet
from rich.console import Console
from rich.style import Style, StyleType
from rich.table import Table as RichTable
from rich.text import Text

from rich_gradient._color_ext import ensure_installed, get_css_map, parse_color
from rich_gradient._logger import logger
from rich_gradient.config import config
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

ensure_installed()

COLOR_STOPS = {}
try:
    COLOR_STOPS = dict(getattr(config, "colors", {}) or {})
except (AttributeError, TypeError, ValueError):
    COLOR_STOPS = {
        "red": "#FF0000", #  1
        "tomato": "#FF5500", #  2
        "orange": "#FF9900", #  3
        "gold": "#FFCC00", #  4
        "yellow": "#FFFF00", #  5
        "green": "#AAFF00", #  6
        "lime": "#00FF00", #  7
        "mint": "#00FF99", #  8
        "cyan": "#00FFFF", #  9
        "lightblue": "#00CCFF", #  10
        "skyblue": "#0099FF", #  11
        "blue": "#5066FF", #  12
        "purple": "#8055FF", #  13
        "violet": "#B033FF", #  14
        "magenta": "#FF00FF", #  15
        "pink": "#FF00AA", #  16
        "rose": "#FF0055", #  17
    }


MIN_HUES = 2


def validate_hues(hues: int) -> int:
    """Return ``hues`` if it meets the minimum, otherwise raise.

    Args:
        hues: Requested number of hues.

    Returns:
        int: ``hues`` unchanged.

    Raises:
        ValueError: If ``hues`` is less than ``MIN_HUES`` (2).
    """
    if hues < MIN_HUES:
        raise ValueError(f"hues must be at least {MIN_HUES}; got {hues}")
    return hues


class Spectrum:
    """A run of consecutive colors from the 17-color spectrum palette.

    The palette is treated as a color wheel: ``Spectrum`` picks a starting hue
    (random, or fixed by ``seed``) and takes ``hues`` neighboring colors from
    there, exposing them as ``Color``, ``ColorTriplet``, ``Style``, hex, and
    name lists.

    Examples:
        >>> Spectrum(hues=4, seed=42).hex  # same four colors every run
        >>> from rich.console import Console
        >>> Console().print(Spectrum())  # preview table of the palette

    Args:
        hues (int): Number of colors to take from the 17-color palette, as a run of
            consecutive hues. Valid values are 2 to 17. Defaults to 17.
        invert (bool): Reverse the order of the generated colors. Defaults to False.
        seed (Optional[int]): Seed that fixes the starting hue, e.g. ``42``, so the same
            colors come back every run. ``None`` picks a random start. Defaults to None.

    Raises:
        ValueError: If ``hues`` is outside 2-17 or ``seed`` is not an integer.

    Attributes:
        colors (list[Color]): The generated colors.
        triplets (list[ColorTriplet]): The colors as truecolor triplets.
        styles (list[Style]): One foreground ``Style`` per color.
        hex (list[str]): The colors as uppercase ``#RRGGBB`` strings.
        names (list[str]): Palette names of the colors (hex for unnamed ones).
    """

    def __init__(
        self, hues: int = 17, invert: bool = False, seed: int | None = None
    ) -> None:
        """Initialize the spectrum; see the class docstring for arguments.

        Raises:
            ValueError: If ``hues`` is outside 2-17 or ``seed`` is not an integer.
        """
        validate_hues(hues)
        if hues > len(COLOR_STOPS):
            raise ValueError(
                f"hues must be at most {len(COLOR_STOPS)} (the size of the "
                f"spectrum palette); got {hues}"
            )
        if seed is not None and not isinstance(seed, int):
            raise ValueError("seed must be an integer or None")

        # Use a dedicated RNG to avoid mutating global random state
        rng = Random(seed)

        # Generate a random cycle of colors from the spectrum
        colors: list[Color] = [parse_color(color) for color in COLOR_STOPS.values()]
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
            parse_color(value).get_truecolor().hex.upper(): name
            for name, value in COLOR_STOPS.items()
        }
        self.names = [
            hex_to_name.get(
                color.get_truecolor().hex.upper(), color.get_truecolor().hex.upper()
            )
            for color in self.colors
        ]

        self._styles = [
            Style(color=color, bold=False, italic=False, underline=False)
            for color in self.colors
        ]
        self.hex = [color.get_truecolor().hex.upper() for color in self.colors]

    @property
    def colors(self) -> list[Color]:
        """The generated ``Color`` instances."""
        return self._colors

    @colors.setter
    def colors(self, value: list[Color]) -> None:
        """Set the colors.

        Args:
            value: At least two ``rich.color.Color`` instances.

        Raises:
            ValueError: If ``value`` is not a list of ``Color`` or has fewer
                than two entries.
        """
        if not isinstance(value, list) or not all(isinstance(c, Color) for c in value):
            raise ValueError("colors must be a list of Color instances")
        if len(value) < 2:
            raise ValueError("colors must contain at least two Color instances")
        self._colors = value

    @property
    def triplets(self) -> list[ColorTriplet]:
        """The colors as truecolor ``ColorTriplet`` instances."""
        return [color.get_truecolor() for color in self._colors]

    @property
    def styles(self) -> list[Style]:
        """One foreground ``Style`` per color."""
        return self._styles

    @styles.setter
    def styles(self, styles: list[StyleType]) -> None:
        """Set the styles from strings or ``Style`` instances.

        Args:
            styles: One style per color, e.g. ``["bold", Style(italic=True)]``.

        Raises:
            TypeError: If ``styles`` is not a list or holds a non-style value.
            ValueError: If the number of styles differs from the number of colors.
        """
        if not isinstance(styles, list):
            raise TypeError("styles must be a list")
        if len(styles) != len(self.colors):
            raise ValueError("styles length must match colors length")
        parsed_styles: list[Style] = []
        for style in styles:
            if isinstance(style, str):
                parsed_styles.append(Style.parse(style))
            elif isinstance(style, Style):
                parsed_styles.append(style)
            else:
                raise TypeError("styles must contain strings or Style instances")
        self._styles = parsed_styles

    @property
    def names(self) -> list[str]:
        """Palette names of the colors (hex for colors without a name)."""
        return self._names

    @names.setter
    def names(self, value: list[str]) -> None:
        """Set the color names.

        Args:
            value: One name per color, e.g. ``["red", "orange"]``.

        Raises:
            ValueError: If ``value`` is not a list of strings or its length
                differs from the number of colors.
        """
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
        """Return the color at an index, e.g. ``spectrum[0]``.

        Args:
            index: Position in the spectrum, from 0 to ``len(colors) - 1``.

        Returns:
            The ``Color`` at that position.

        Raises:
            TypeError: If ``index`` is not an integer.
            IndexError: If ``index`` is negative or out of range.
        """
        if not isinstance(index, int):
            raise TypeError("Index must be an integer")
        if index < 0 or index >= len(self.colors):
            raise IndexError("Index out of range")
        return self.colors[index]

    def __iter__(self) -> Iterator[Color]:
        """Iterate over the colors in the spectrum.

        Returns:
            An iterator of ``Color`` instances.
        """
        return iter(self.colors)

    def __rich__(self) -> RichTable:
        """Render the spectrum as a preview table.

        Returns:
            A table with a sample swatch, name, hex, and RGB value per color.
        """

        def rainbow_title(text: str) -> Text:
            """Color ``text`` two characters at a time with the spectrum colors.

            Args:
                text: The heading text.

            Returns:
                Bold, underlined ``Text`` cycling through the colors.
            """
            chunks = [text[i : i + 2] for i in range(0, len(text), 2)]
            pieces: list[Text] = []
            for idx, chunk in enumerate(chunks):
                color = self.colors[idx % len(self.colors)]
                hex_code = color.get_truecolor().hex
                pieces.append(Text(chunk, style=f"b u {hex_code}"))
            return Text.assemble(*pieces)

        table = RichTable(title=rainbow_title("Spectrum Colors"))
        table.add_column(rainbow_title("Sample"), justify="center")
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
            rgb_text = Text.assemble(
                *[
                    Text("rgb", style=f"bold {hex_code}"),
                    Text("(", style="i white"),
                    Text(f"{red:>3}", style="#FF0000"),
                    Text(",", style="i #555"),
                    Text(f"{green:>3}", style="#00FF00"),
                    Text(",", style="i #555"),
                    Text(f"{blue:>3}", style="#00AAFF"),
                    Text(")", style="i white"),
                ]
            )
            sample = Text("█" * 10, style=Style(color=hex_code, bold=True))
            table.add_row(sample, name_text, hex_text, rgb_text)
        return table

    @property
    def rich(self) -> RichTable:
        """The spectrum's preview table (same as ``__rich__()``)."""
        return self.__rich__()


def example(save: bool = False) -> None:
    """Print a preview table of a seeded spectrum.

    Args:
        save: Record the output and save it to ``docs/img/v0.3.4/spectrum_example.svg``.
            Defaults to False.
    """
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
