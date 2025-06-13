"""
This module defines the RGBA class, an internal representation of colors using red, green,
blue, and alpha (transparency) channels. It provides functionality to create, manipulate,
and convert RGBA values from various color formats including hex, RGB, and HSL.

It also supports conversions to and from Rich library's color classes, string representations,
and provides utility methods for computing contrast and rendering with rich text styles.

Types and constants related to color representation, including alias types for color tuples,
are also defined here.
"""

from __future__ import annotations

import inspect
import re
from colorsys import hls_to_rgb, rgb_to_hls
from functools import cached_property
from typing import Any, Optional, Tuple, TypeAlias, Union

from rich.color import Color as RichColor
from rich.color_triplet import ColorTriplet
from rich.style import Style
from rich.text import Text

from rich_gradient._colors import COLORS_BY_ANSI, COLORS_BY_NAME
from rich_gradient._parsers import (
    r_hex_long,
    r_hex_short,
    r_hsl,
    r_hsl_v4_style,
    r_rgb,
    r_rgb_v4_style,
)

ColorTuple: TypeAlias = Union[Tuple[int, int, int], Tuple[int, int, int, float]]
HslColorTuple: TypeAlias = Union[
    Tuple[float, float, float], Tuple[float, float, float, float]
]
RGBA_ColorType: TypeAlias = Union[
    ColorTuple, str, Tuple[Any, ...], ColorTriplet, RichColor, "RGBA"
]


class RGBAError(Exception):
    """
    An exception that automatically prefixes the module and function
    where it was raised to the message.
    """

    def __init__(self, message: str) -> None:
        # inspect.stack()[1] is the caller’s frame
        frame_info = inspect.stack()[1]
        module_name = frame_info.frame.f_globals.get("__name__", "<unknown module>")
        func_name = frame_info.function
        line_no = frame_info.lineno

        # Build the full message
        full_message = f"{module_name}.{func_name}:{line_no}: {message}"
        super().__init__(full_message)


class RGBA:
    """
    Internal representation of an RGBA color.
    Args:
        r (int): Red value (0-255)
        g (int): Green value (0-255)
        b (int): Blue value (0-255)
        alpha (float): Alpha value (0-1)
    """

    __slots__: Tuple[str, ...] = ("r", "g", "b", "alpha", "_tuple")

    r: int
    g: int
    b: int
    alpha: float
    _tuple: Tuple[int, int, int, float]

    def __init__(self, r: int, g: int, b: int, alpha: float = 1.0) -> None:
        self.r = r
        self.g = g
        self.b = b
        if not (0.0 <= alpha <= 1.0):
            raise RGBAError("Alpha must be between 0.0 and 1.0")
        self.alpha = alpha
        self._tuple = (self.r, self.g, self.b, self.alpha)

    def __getitem__(self, item: Any) -> Any:
        """Get the RGBA color value by index or name.
        Args:
            item (int|str): The index (0-3) or name ('r', 'g', 'b', 'a') of the color value.
        Returns:
            Any: The color value (0-255 for r, g, b; 0.0-1.0 for a).
        Raises:
            IndexError: If the index is out of range.
            KeyError: If the key is not 'r', 'g', 'b', or 'a'.
        """
        return self._tuple[item]

    @property
    def red(self) -> int:
        """Return the red value of the RGBA color.
        Returns:
            int: The red value (0-255).
        """
        return self.r

    @red.setter
    def red(self, value: int | float) -> None:
        """Set the red value of the RGBA color.

        Args:
            value (int|float): The red value (0-255 or 0-1)."""
        self.r = (
            int(round(value * 255))
            if isinstance(value, float) and 0 <= value <= 1
            else int(value)
        )

    @property
    def green(self) -> int:
        """Return the green value of the RGBA color.
        Returns:
            int: The green value (0-255).
        """
        return self.g

    @green.setter
    def green(self, value: int | float) -> None:
        """Set the green value of the RGBA color."""
        self.g = (
            int(round(value * 255))
            if isinstance(value, float) and 0 <= value <= 1
            else int(value)
        )

    @property
    def blue(self) -> int:
        """Return the blue value of the RGBA color.

        Returns:
            int: The blue value (0-255).
        """
        return self.b

    @blue.setter
    def blue(self, value: int | float) -> None:
        self.b = (
            int(round(value * 255))
            if isinstance(value, float) and 0 <= value <= 1
            else int(value)
        )

    def __repr__(self) -> str:
        """Return a string representation of the RGBA color."""
        return f"RGBA({self.r}, {self.g}, {self.b}, {self.alpha})"

    def __str__(self) -> str:
        """Return a string representation of the RGBA color."""
        return self.as_hex()

    def __eq__(self, other: object) -> bool:
        """Check if two RGBA colors are equal."""
        if not isinstance(other, RGBA):
            return NotImplemented
        return (self.r, self.g, self.b, self.alpha) == (
            other.r,
            other.g,
            other.b,
            other.alpha,
        )

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __hash__(self) -> int:
        return hash((self.r, self.g, self.b, self.alpha))

    def __add__(self, other: "RGBA") -> "RGBA":
        """Add two RGBA colors together and return a new RGBA color."""
        if not isinstance(other, RGBA):
            return NotImplemented
        return RGBA(
            round((self.r + other.r) / 2),
            round((self.g + other.g) / 2),
            round((self.b + other.b) / 2),
            (self.alpha + other.alpha) / 2
            if self.alpha != 1.0 and other.alpha != 1.0
            else max(self.alpha, other.alpha),
        )

    def __rich__(self) -> Text:
        """Return a rich text representation of the RGBA color."""
        style: Style = Style(color=self.as_rgb(), bold=True)
        return Text.assemble(
            *[
                Text("rgb", style=style),
                Text("(", style="b #ffffff"),
                Text(f"{self.r:>3}", style="b #ff0000"),
                Text(",", style="b #555"),
                Text(f"{self.g:>3}", style="b #00ff00"),
                Text(",", style="b #555"),
                Text(f"{self.b:>3}", style="b #0099ff"),
                Text(")", style="b #ffffff"),
            ]
        )

    @cached_property
    def hex(self) -> str:
        return self.as_hex()

    def as_hex(self, with_alpha: bool = False) -> str:
        r, g, b = round(self.r), round(self.g), round(self.b)
        if with_alpha and self.alpha < 1.0:
            a = round(self.alpha * 255)
            return f"#{r:02x}{g:02x}{b:02x}{a:02x}"
        return f"#{r:02x}{g:02x}{b:02x}"

    @cached_property
    def rgb(self) -> str:
        return self.as_rgb()

    def as_rgb(self) -> str:
        r, g, b = self.r, self.g, self.b
        if self.alpha == 1.0:
            return f"rgb({r}, {g}, {b})"
        else:
            return f"rgba({r}, {g}, {b}, {round(self.alpha, 2)})"

    def as_hsl(self) -> str:
        hsl = self.as_hsl_tuple(alpha=True)
        h, s, l = hsl[:3]
        if len(hsl) == 4:
            a = hsl[3]
            return f"hsl({h * 360:.0f}, {s:.0%}, {l:.0%}, {round(a, 2)})"
        else:
            return f"hsl({h * 360:.0f}, {s:.0%}, {l:.0%})"

    def as_hsl_tuple(self, *, alpha: bool | None = None) -> HslColorTuple:
        h, l, s = rgb_to_hls(self.r / 255, self.g / 255, self.b / 255)
        if alpha is None:
            if self.alpha == 1.0:
                return h, s, l
            else:
                return h, s, l, self._alpha
        return (h, s, l, self._alpha) if alpha else (h, s, l)

    @property
    def default(self) -> RGBA:
        return self.as_default()

    @staticmethod
    def as_default() -> RGBA:
        default_rich: RichColor = RichColor.default()
        default_triplet: ColorTriplet = default_rich.get_truecolor()
        r, g, b = default_triplet.red, default_triplet.green, default_triplet.blue
        return RGBA(r, g, b)

    @classmethod
    def as_rich_default(seclslf) -> RichColor:
        """Return the default rich color."""
        return RichColor.default()

    @property
    def _alpha(self) -> float:
        return 1.0 if self.alpha == 1.0 else self.alpha

    @cached_property
    def triplet(self) -> ColorTriplet:
        """Return the color as a ColorTriplet."""
        return self.as_triplet()

    def as_triplet(self) -> ColorTriplet:
        """Return the color as a ColorTriplet."""
        return ColorTriplet(self.r, self.g, self.b)

    @cached_property
    def tuple(self) -> Tuple[int, int, int]:
        """Return the color as a tuple of ints (0-255)."""
        return self.as_tuple()

    def as_tuple(self) -> Tuple[int, int, int]:
        """Return the color as a tuple of ints (0-255)."""
        return (self.r, self.g, self.b)

    @cached_property
    def rich(self) -> RichColor:
        """Return the color as a rich.color.Color."""
        return self.as_rich()

    def as_rich(self) -> RichColor:
        """Return the color as a rich.color.Color."""
        return RichColor.from_triplet(self.as_triplet())

    @classmethod
    def from_hex(cls, value: str) -> RGBA:
        """Generate an RGBA instance from a hex color code (str). ie. #ff0000"""
        if not isinstance(value, str):
            raise TypeError(f"Expected string for hex value, got {type(value).__name__}")

        for regex in (r_hex_short, r_hex_long, r_rgb, r_rgb_v4_style):
            match = re.match(regex, value, re.IGNORECASE)
            if match:
                if "x" in regex:
                    r, g, b = (int(match.group(i), 16) for i in range(1, 4))
                else:
                    r, g, b = (int(match.group(i)) for i in range(1, 4))
                return cls(r, g, b)
        raise ValueError(f"Invalid hex value: `{value}`")

    @classmethod
    def from_rgb(cls, value: str) -> RGBA:
        """Parse a RGBA instance from a rgb string.
        Args:
            value (str): A rgb string.
        Returns:
            RGBA: An RGBA instance.
        Raises:
            ValueError: If the value is not a valid rgb string.
        """
        return cls.from_hex(value)

    @classmethod
    def from_rich(cls, value: RichColor) -> RGBA:
        """Parse a RGBA instance from a rich.color.Color.
        Args:
            value (RichColor): A rich.color.Color instance.
        Returns:
            RGBA: An RGBA instance.
        Raises:
            ValueError: If the value is not a valid rich.color.Color instance.
        """
        try:
            triplet = value.triplet if value.triplet else RichColor.parse(value).triplet
            if triplet:
                r, g, b = triplet
                return cls(r, g, b)
            elif value.get_truecolor():
                r, g, b = value.get_truecolor()
                return cls(r, g, b)
            elif value.name in COLORS_BY_NAME:
                color = COLORS_BY_NAME.get(value.name)
                rgb: Tuple[int, int, int] = color["rgb"]  # type: ignore
                r, g, b = rgb
                return cls(r, g, b)
            elif value.number in COLORS_BY_ANSI:
                color = COLORS_BY_ANSI.get(value.number)
                rgb: Tuple[int, int, int] = color["rgb"]  # type: ignore
                r, g, b = rgb
                return cls(r, g, b)
            else:
                color = RichColor.parse(value)
                if color:
                    r, g, b = color.get_truecolor()
                    return cls(r, g, b)
                raise RGBAError(f"Invalid RichColor value: {value}")
        except AttributeError:
            raise RGBAError(f"AttributeError: Invalid RichColor value: {value}")
        except ValueError:
            raise RGBAError(f"ValueError: Invalid RichColor value: {value}")
        except TypeError:
            raise RGBAError(
                f"TypeError: Invalid RichColor value: {value} or type: {type(value)}"
            )
        except RGBAError:
            raise RGBAError(f"RGBAError: Invalid RichColor value: {value}")
        except Exception:
            raise RGBAError(f"Exception: Invalid RichColor value: {value}")

    @classmethod
    def from_hsl(cls, value: str) -> RGBA:
        """Parse a RGBA instance from a hsl string.
        Args:
            value (str): A hsl string.
        Returns:
            RGBA: An RGBA instance.
        Raises:
            ValueError: If the value is not a valid hsl string.
        """

        def _convert_hsl_match(match: re.Match[str]) -> RGBA:
            hue, saturation, lightness = (float(match.group(i)) for i in range(1, 4))
            _hue = hue / 360
            _saturation = saturation / 100
            _lightness = lightness / 100
            r, g, b = hls_to_rgb(_hue, _lightness, _saturation)
            return cls(r=int(r * 255), g=int(g * 255), b=int(b * 255))

        for regex in (r_hsl, r_hsl_v4_style):
            match = re.match(regex, value)
            if match:
                return _convert_hsl_match(match)
        raise ValueError(f"Invalid HSL value: `{value}`")

    @classmethod
    def from_triplet(cls, value: RGBA_ColorType) -> RGBA:
        """Parse a RGBA instance from a triple, tuple, list, or RGBA.
        Args:
            value (ColorType): A color triplet, tuple, list, or RGBA instance.
        Returns:
            RGBA: An RGBA instance.
        Raises:
            ValueError: If the value is not a valid color triplet, tuple, list, or RGBA instance.
        """
        if isinstance(value, ColorTriplet):
            return cls(value.red, value.green, value.blue)
        elif isinstance(value, (tuple, list)):
            if len(value) == 3:
                r, g, b = value  # type: ignore
                return cls(r, g, b)  # type: ignore
            elif len(value) == 4:
                r, g, b, a = value
                return cls(r, g, b, a)  # type: ignore
        elif isinstance(value, RGBA):
            return value
        raise ValueError("Invalid value for from_triplet")

    @classmethod
    def from_tuple(
        cls, value: tuple[int, int, int] | tuple[int, int, int, float]
    ) -> RGBA:
        """Parse a RGBA instance from a tuple.
        Args:
            value (tuple): A tuple of ints (0-255) or floats (0-1).
        Returns:
            RGBA: An RGBA instance.
        Raises:
            ValueError: If the value is not a valid tuple.
        """
        return cls.from_triplet(value)

    def get_contrast(self, fixed: Optional[str] = None) -> RGBA:
        """Get the contrast color for the current RGBA color.
        Args:
            fixed (str, optional): If "black" or "white", return a fixed color.
                Defaults to None.
        Returns:
            RGBA: The contrast color.
        Raises:
            ValueError: If fixed is not "black" or "white".
        """
        if fixed:
            if fixed not in ["black", "white"]:
                raise ValueError("Fixed color must be 'black' or 'white'")
            return RGBA(0, 0, 0) if fixed == "black" else RGBA(238, 238, 238)
        # Calculate luminance using the formula
        luminance = (
            0.2126 * (self.r / 255) + 0.7152 * (self.g / 255) + 0.0722 * (self.b / 255)
        )
        return RGBA(0, 0, 0) if luminance > 0.5 else RGBA(238, 238, 238)
