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

import re
import inspect
from typing import Any, TypeAlias, Tuple, Union, Optional
from functools import cached_property
from colorsys import hls_to_rgb, rgb_to_hls

from rich.color import Color as RichColor
from rich.color_triplet import ColorTriplet
from rich.text import Text
from rich.style import Style

from rich_gradient._parsers import (
    r_hex_short,
    r_hex_long,
    r_rgb,
    r_rgb_v4_style,
    r_hsl,
    r_hsl_v4_style,
    repeat_colors,
    rads
)

ColorTuple: TypeAlias = Union[Tuple[int, int, int], Tuple[int, int, int, float]]
HslColorTuple: TypeAlias = Union[
    Tuple[float, float, float], Tuple[float, float, float, float]
]
RGBA_ColorType: TypeAlias = Union[
    ColorTuple,
    str, Tuple[Any, ...],
    ColorTriplet,
    RichColor,
    "RGBA"
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
    __slots__ = "r", "g", "b", "alpha", "_tuple"

    def __init__(self, r: int, g: int, b: int, alpha: float = 1.0) -> None:
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)
        if not (0.0 <= alpha <= 1.0):
            raise RGBAError("Alpha must be between 0.0 and 1.0")
        self.alpha = float(alpha)
        self._tuple = (self.r, self.g, self.b, self.alpha)

    def __getitem__(self, item: Any) -> Any:
        return self._tuple[item]

    @property
    def red(self) -> int:
        return self.r

    @red.setter
    def red(self, value: int | float) -> None:
        self.r = int(round(value * 255)) if isinstance(value, float) and 0 <= value <= 1 else int(value)

    @property
    def green(self) -> int:
        return self.g

    @green.setter
    def green(self, value: int | float) -> None:
        self.g = int(round(value * 255)) if isinstance(value, float) and 0 <= value <= 1 else int(value)
    @property
    def blue(self) -> int:
        return self.b


    @blue.setter
    def blue(self, value: int | float) -> None:
        self.b = int(round(value * 255)) if isinstance(value, float) and 0 <= value <= 1 else int(value)

    def __repr__(self) -> str:
        return f"RGBA({self.r}, {self.g}, {self.b}, {self.alpha})"
    def __str__(self) -> str:
        return self.as_hex()
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RGBA):
            return NotImplemented
        return (self.r, self.g, self.b, self.alpha) == (other.r, other.g, other.b, other.alpha)
    def __ne__(self, other: object) -> bool:
        return not self == other
    def __hash__(self) -> int:
        return hash((self.r, self.g, self.b, self.alpha))
    def __add__(self, other: "RGBA") -> "RGBA":
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
        style = Style(color=self.as_rgb(), bold=True)
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

    @classmethod
    def default(cls) -> RGBA:
        default = RichColor.default().triplet
        return cls.from_triplet(default) if default else cls.from_hex("#000000")

    @property
    def _alpha(self) -> float:
        return 1.0 if self.alpha == 1.0 else self.alpha

    @cached_property
    def triplet(self) -> ColorTriplet:
        return self.as_triplet()

    def as_triplet(self) -> ColorTriplet:
        return ColorTriplet(self.r, self.g, self.b)

    @cached_property
    def tuple(self) -> Tuple[int, int, int]:
        return self.as_tuple()

    def as_tuple(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    @cached_property
    def rich(self) -> RichColor:
        return self.as_rich()

    def as_rich(self) -> RichColor:
        return RichColor.from_triplet(self.as_triplet())

    @classmethod
    def from_hex(cls, value: str) -> "RGBA":
        for regex in (r_hex_short, r_hex_long, r_rgb, r_rgb_v4_style):
            match = re.match(regex, value)
            if match:
                if "x" in regex:
                    r, g, b = (int(match.group(i), 16) for i in range(1, 4))
                else:
                    r, g, b = (int(match.group(i)) for i in range(1, 4))
                return cls(r, g, b)
        raise ValueError(f"Invalid hex value: `{value}`")

    @classmethod
    def from_rgb(cls, value: str) -> "RGBA":
        return cls.from_hex(value)

    @classmethod
    def from_rich(cls, value: RichColor) -> RGBA:
        try:
            triplet = value.triplet if value.triplet else RichColor.parse(value).triplet
            if triplet:
                return cls.from_triplet(triplet)
            raise ValueError("Unable to parse RichColor")
        except Exception as e:
            raise e

    @classmethod
    def from_hsl(cls, value: str) -> "RGBA":
        def _convert_hsl_match(match: re.Match) -> RGBA:
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
    ) -> "RGBA":
        return cls.from_triplet(value)

    # blend_rgb moved to color_utils.py

    def get_contrast(self, fixed: Optional[str] = None) -> "RGBA":
        if fixed:
            if fixed not in ["black", "white"]:
                raise ValueError("Fixed color must be 'black' or 'white'")
            return RGBA(0, 0, 0) if fixed == "black" else RGBA(238, 238, 238)
        # Calculate luminance using the formula
        luminance = (
            0.2126 * (self.r / 255) + 0.7152 * (self.g / 255) + 0.0722 * (self.b / 255)
        )
        return RGBA(0, 0, 0) if luminance > 0.5 else RGBA(238, 238, 238)
