"""Color definitions are used as per the CSS3
[CSS Color Module Level 3](http://www.w3.org/TR/css3-color/#svg-color) specification.

A few colors have multiple names referring to the same colors, eg. `grey` and `gray` or `aqua` and `cyan`.

In these cases the _last_ color when sorted alphabetically takes preferences,
eg. `Color((0, 255, 255)).as_named() == 'cyan'` because "cyan" comes after "aqua".

Adapted from the 'Color' class in the [`pydantic-extra-types`](https://github.com/pydantic/pydantic-extra-types) package.
"""

from __future__ import annotations

import colorsys
import inspect
import math
import re
from colorsys import hls_to_rgb, rgb_to_hls
from functools import cached_property
from itertools import cycle
from random import randint
from typing import (
    Any,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Tuple,
    TypeAlias,
    Union,
    cast,
    TYPE_CHECKING
)

from rich.color import Color as RichColor
from rich.color_triplet import ColorTriplet
from rich.console import Console
from rich.style import Style as RichStyle
from rich.table import Table
from rich.text import Text

from rich_gradient._colors import (
    COLORS_BY_ANSI,
    COLORS_BY_HEX,
    COLORS_BY_NAME,
    COLORS_BY_RGB,
    NAMES,
)
from rich_gradient._parsers import (
    r_hex_long,
    r_hex_short,
    r_hsl,
    r_hsl_v4_style,
    r_rgb,
    r_rgb_v4_style,
    rads,
)
from rich_gradient._rgb import RGBA, HslColorTuple, RGBA_ColorType
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

# Spectrum color names for gradient and display utilities
# Use first 18 color names from COLORS_BY_NAME if NAMES[:18] is not defined or unavailable.
SPECTRUM_COLOR_STRS = list(COLORS_BY_NAME.keys())[:18]


ColorType: TypeAlias = Union[RGBA_ColorType, "Color"]

# --- Exports ---
__all__ = ["Color", "ColorError", "ColorType", "RGBA"]


class ColorError(Exception):
    """
    An exception that automatically prefixes the module and function
    where it was raised to the message.
    """

    def __init__(self, message: str) -> None:
        # inspect.stack()[1] is the caller’s frame
        frame_info = inspect.stack()[1]
        module_name = getattr(
            frame_info.frame.f_globals, "__file__", "<unknown module>"
        )
        if not isinstance(module_name, str):
            module_name = "<unknown module>"
        func_name = getattr(frame_info, "function", "<unknown function>")
        line_no = getattr(frame_info, "lineno", -1)
        # Build the full message
        full_message = f"{module_name}.{func_name}:{line_no}: {message}"
        super().__init__(full_message)


class Color:
    """Represents a color in various formats and provides conversion methods."""

    __slots__ = "_original", "_rgba"

    def __init__(self, value: ColorType) -> None:
        if isinstance(value, Color):
            self._rgba: RGBA = value._rgba
            self._original: str = value._original
        elif isinstance(value, (tuple, list)):
            self._rgba: RGBA = self.parse_tuple(value)
            self._original: str = str(value)
        elif isinstance(value, RGBA):
            self._rgba: RGBA = value
            self._original: str = str(value)
        elif isinstance(value, ColorTriplet):
            self._rgba: RGBA = RGBA.from_triplet(value)
            self._original: str = str(value)
        elif isinstance(value, RichColor):
            self._rgba: RGBA = RGBA.from_rich(value)
            self._original: str = str(value)
        elif isinstance(value, str):
            self._rgba: RGBA = self.parse_str(value.lower())
            self._original: str = value
        else:
            raise ColorError(
                "Value is not a valid color: must be tuple, list, string, Color, RGBA, RichColor, or ColorTriplet."
            )

    def __str__(self) -> str:
        return self.as_named(fallback=True)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Color) and self.as_rgb_tuple() == other.as_rgb_tuple()

    def __hash__(self) -> int:
        return hash(self.as_rgb_tuple())

    def __rich__(self) -> Text:
        """Return a simple visual block for Console.print()."""
        # Apply gradient after justification by calling self.as_rich().stylize(Text("█" * 10))
        return Text(f"{'█' * 10}", style=self.as_hex())

    def __repr__(self, *args: Any, **kwds: Any) -> str:
        return f"Color({self.as_named(fallback=True)})"

    def __rich_repr__(self) -> Text:
        """Return a rich representation of the color."""
        return Text.assemble(
            *[
                Text("Color(", style="bold #ffffff"),
                Text(
                    f"'{self.as_named(fallback=True)}'", style=f"bold {self.as_hex()}"
                ),
                Text(")", style="bold #ffffff"),
            ]
        )

    # --- Properties ---
    @property
    def name(self) -> str:
        """The name of color.
        Returns:
            str: The name of the color.
        """
        return self.as_named(fallback=True)

    @property
    def hex(self) -> str:
        """Return the hex value of the color.

        Returns:
            str: The hex value of the color.
        """
        return self.as_hex(format="long", fallback=True)

    @property
    def rgb(self) -> str:
        """Return the RGB value of the color.

        Returns:
            str: The RGB value of the color."""
        return self.as_rgb()

    @property
    def triplet(self) -> ColorTriplet:
        """The `rich.color_triplet.ColorTriplet` representation \
of the color."""
        return self.as_triplet()

    @property
    def tuple(self) -> Tuple[int, int, int]:
        """The red, green, blue tuple representation of the color."""
        return self.as_rgb_tuple()

    @property
    def rich(self) -> RichColor:
        """The color as a rich color."""
        return self.as_rich()

    @property
    def style(self) -> RichStyle:
        """The color as a rich style."""
        return RichStyle(color=self.as_hex())

    @property
    def bg_style(self) -> RichStyle:
        """The color as a background style."""
        return RichStyle(bgcolor=self.as_hex())

    @property
    def ansi(self) -> int | None:
        """The ANSI color code for the color, or None if not found."""
        ansi = self.as_ansi()
        if ansi is not None and ansi != -1:
            return ansi
        raise KeyError(f"ANSI color code not found for color: {self.as_hex()}")

    @property
    def original(self) -> ColorType:
        """Original value passed to `Color`."""
        return self._original

    @original.setter
    def original(self, value: ColorType) -> None:
        """Set the original value passed to `Color`."""
        if isinstance(value, Color):
            self._original = value._original
        else:
            self._original = str(value)

    @property
    def default(self) -> RGBA:
        """
        Get the default RGBA color.

        Returns:
            RGBA: The default RGBA color.
        """
        return self.as_default()

    @staticmethod
    def as_default() -> RGBA:
        """
        Parse rich.color.Color.default() into an RGBA instance.

        Returns:
            RGBA: The RGBA representation of the default rich color.
        """
        return RGBA.as_default()

    def is_default(self) -> bool:
        """Check if the color is the default color.

        Returns:
            bool: True if the color is the default color, False otherwise.
        """
        return self._rgba == self.default

    # --- Conversion Methods ---

    def as_named(self, *, fallback: bool = True) -> str:
        """Returns the name of the color if it matches a known color.

        Args:
            fallback (bool, optional): If True (default), fall \
back to hex representation if name is not found. If False, raise \
ValueError when no name is found.

        Returns:
            str: Named color or hex string.

        Raises:
            ValueError: If no named color exists and fallback is False.
        """
        if self.as_hex() in COLORS_BY_HEX:
            color_dict = COLORS_BY_HEX[self.as_hex()]
            return str(color_dict["name"])
        else:
            if fallback:
                return self.as_hex()
            raise ValueError(
                f"Color {self.as_hex()} does not have a named representation."
            )

    def as_hex(
        self, format: Literal["short", "long"] = "long", fallback: bool = True
    ) -> str:
        """Returns the hexadecimal representation of the color."""
        r, g, b = (self._rgba.r, self._rgba.g, self._rgba.b)
        hex_str = f"{r:02x}{g:02x}{b:02x}"
        if format == "short":
            if (
                hex_str[0] == hex_str[1]
                and hex_str[2] == hex_str[3]
                and hex_str[4] == hex_str[5]
            ):
                return f"#{hex_str[0]}{hex_str[2]}{hex_str[4]}"
            elif fallback:
                return f"#{hex_str}"
        return f"#{hex_str}"

    def as_rgb(self) -> str:
        """Return the color as an RGB string."""
        r, g, b = (self._rgba.r, self._rgba.g, self._rgba.b)
        return f"rgb({r}, {g}, {b})"

    def as_rich_rgb(self) -> Text:
        """Return the color as a rich RGB string."""
        return self._rgba.__rich__()

    def as_rgb_tuple(self) -> Tuple[int, int, int]:
        """Return the color as an (r, g, b) tuple."""
        r, g, b = (c for c in self._rgba[:3])
        return r, g, b

    def as_hsl(self) -> str:
        hsl_tuple = self.as_hsl_tuple()
        h, s, li = hsl_tuple[0], hsl_tuple[1], hsl_tuple[2]
        return f"hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%})"

    def as_hsl_tuple(self) -> Tuple[float, float, float]:
        h, l, s = rgb_to_hls(self._rgba.r / 255, self._rgba.g / 255, self._rgba.b / 255)
        return h, s, l

    def as_triplet(self) -> ColorTriplet:
        """Return the color as a rich.color_triplet.ColorTriplet."""
        return ColorTriplet(self._rgba.r, self._rgba.g, self._rgba.b)

    def as_rich(self) -> RichColor:
        """Return the color as a rich.color.Color."""
        try:
            rgb_triplet = self.as_triplet()
            return RichColor.from_triplet(rgb_triplet)
        except ColorError:
            raise ColorError("Unable to parse color")

    def _build_style(
        self,
        *,
        color: "Color",
        bgcolor: Optional["Color"] = None,
        **attributes: Any,
    ) -> RichStyle:
        """Helper to construct a Style with shared parameters."""
        if not isinstance(color, Color):
            # If color is not a Color instance, raise an error
            raise TypeError(f"color must be a Color, got {type(color)}")
        if bgcolor is not None and not isinstance(bgcolor, Color):
            raise TypeError(f"bgcolor must be a Color, got {type(bgcolor)}")
        if hasattr(attributes, "reverse"):
            # If attributes has a 'reverse' key, set the bgcolor to the color
            # and the color to #ffffff
            return RichStyle(
                color="#ffffff",
                bgcolor=color.as_hex(),
                reverse=False,
                **{k: v for k, v in attributes.items() if k != "reverse"},
            )
        return RichStyle(color=color.rich, **attributes)

    def as_ansi(self) -> int | None:
        """Return the ANSI color code for the color, or raise KeyError if not found."""
        color_dict: Optional[dict[str, str | Tuple[int, int, int] | int]] = (
            COLORS_BY_HEX.get(self.as_hex())
        )
        if not color_dict:
            raise KeyError(f"Color not found in COLORS_BY_HEX: {self.as_hex()}")
        ansi = color_dict.get("ansi", -1)
        if isinstance(ansi, int) and ansi != -1:
            return ansi
        raise KeyError(f"ANSI color code not found for color: {self.as_hex()}")

    @classmethod
    def from_rgba(cls, value: RGBA) -> "Color":
        return cls(value)

    @classmethod
    def from_hex(cls, value: str | ColorType) -> "Color":
        if not isinstance(value, str):
            raise TypeError(
                f"Expected string for hex value, got {type(value).__name__}"
            )
        return cls(RGBA.from_hex(value))

    @classmethod
    def from_rgb(cls, value: str) -> "Color":
        return cls(RGBA.from_rgb(value))

    @classmethod
    def from_rgb_tuple(
        cls, value: Tuple[int, int, int] | Tuple[int, int, int, float]
    ) -> "Color":
        return cls(RGBA.from_tuple(value))

    @classmethod
    def from_hsl(cls, value: str) -> "Color":
        return cls(RGBA.from_hsl(value))

    @classmethod
    def from_hsl_tuple(
        cls, value: Tuple[float, float, float] | Tuple[float, float, float, float]
    ) -> "Color":
        h, s, l = value[:3]
        a = value[3] if len(value) == 4 else 1.0
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return cls(RGBA(int(r * 255), int(g * 255), int(b * 255), a))

    @classmethod
    def from_triplet(cls, value: ColorTriplet) -> "Color":
        return cls(RGBA.from_triplet(value))

    @classmethod
    def from_rich(cls, value: RichColor) -> "Color":
        """Create a Color from a RichColor.
        Args:
            value (RichColor): The RichColor to convert.
        Returns:
            Color: The converted Color.
        Raises:
            ColorError: If the RichColor has no RGB triplet to convert.
        """
        if isinstance(value, RichColor):
            if value.triplet is None:
                raise ColorError(f"RichColor {value} has no RGB triplet to convert")
            return cls.from_triplet(value.triplet)
        raise ColorError(f"Unable to parse color in Color.from_rich({value}).")

    @classmethod
    def from_style(cls, style: RichStyle) -> "Color":
        """Create a Color from a rich Style object."""
        if style.color:
            return cls.from_rich(style.color)
        raise ColorError("Style has no foreground color")

    # --- Parsing Helpers ---

    def parse_str(self, value: str) -> RGBA:
        """Parse a string into an RGBA or Color.
        Args:
            value (str): The color string to parse. `value` can be a:

            ### `str``
                - hex string: "#FF0000", "ff0"
                - RGB string: "rgb(255, 0, 0)", "rgba(255, 0, 0, 0.5)"
                - HSL string: "hsl(0, 100%, 50%)", "hsla(0, 100%, 50%, 0.5)"
                - the name of a CSS3 color: "red", "tomato"
                - the name of a rich standard color: `grey93`, `gold1`
                - the fuzzy match of any color names in _color_dict.COLORS_BY_NAME
        """
        # Normalize input
        value_lower = value.strip().lower()

        # Direct name lookup (with underscore/hyphen normalization)
        name_key: str | None = None
        if value_lower in COLORS_BY_NAME:
            name_key = value_lower
        else:
            alias = value_lower.replace("_", "").replace("-", "")
            if alias in COLORS_BY_NAME:
                name_key = alias
        if name_key:
            color_name_info = COLORS_BY_NAME[name_key]
            rgb: Tuple[int, int, int] = color_name_info.get(
                "tuple"
            ) or color_name_info.get("rgb")  # type: ignore
            if len(rgb) == 3:
                r, g, b = rgb
            else:
                raise ColorError(f"Expected 3 RGB values, got {len(rgb)}: {rgb}")
            return RGBA(int(r), int(g), int(b))

        # Fuzzy-match fallback
        try:
            from thefuzz import process

            match_result = process.extractOne(value_lower, COLORS_BY_NAME.keys())
            if match_result:
                best_match, score = match_result[0], match_result[1]
                if score >= 80:
                    fzf_color_info = COLORS_BY_NAME[best_match]
                    rgb: Tuple[int, int, int] = fzf_color_info.get(
                        "tuple"
                    ) or fzf_color_info.get("rgb")  # type: ignore
                    if len(rgb) == 3:
                        r, g, b = rgb
                    else:
                        raise ColorError(
                            f"Expected 3 RGB values, got {len(rgb)}: {rgb}"
                        )
                    return RGBA(int(r), int(g), int(b))
        except ImportError:
            pass

        # Handle hex color strings (short form, e.g. "#f0a" or "f0a")
        m = re.fullmatch(r_hex_short, value_lower)
        if m:
            _r, _g, _b, a = m.groups()
            _rgb = (_r, _g, _b)
            # duplicate each hex digit and parse
            r, g, b = (int(v * 2, 16) for v in _rgb)
            alpha = int(a * 2, 16) / 255 if a else 1.0
            return self.ints_to_rgba(r, g, b, alpha)
        m = re.fullmatch(r_hex_long, value_lower)
        if m:
            r_str, g_str, b_str, a = m.groups()
            r = int(r_str, 16)
            g = int(g_str, 16)
            b = int(b_str, 16)
            alpha = int(a, 16) / 255 if a else 1.0
            return self.ints_to_rgba(r, g, b, alpha)

        # Handle RGB color strings
        m = re.fullmatch(r_rgb, value_lower) or re.fullmatch(
            r_rgb_v4_style, value_lower
        )
        if m:
            return self.ints_to_rgba(*m.groups())  # type: ignore

        # Handle HSL color strings
        m = re.fullmatch(r_hsl, value_lower) or re.fullmatch(
            r_hsl_v4_style, value_lower
        )
        if m:
            return self.parse_hsl(*m.groups())  # type: ignore

        # Handle ANSI color codes
        m = re.fullmatch(r"^(\d+)$", value_lower)
        if m:
            _ansi = int(m.group(1))
            color_info: Dict[str, Tuple[int, int, int] | str] | None = (
                COLORS_BY_ANSI.get(_ansi)
            )
            if color_info and "rgb" in color_info:
                _rgb = color_info["rgb"]
                assert isinstance(_rgb, tuple), (
                    f"Expected rgb to be a tuple, got {type(_rgb)}"
                )
                r, g, b = _rgb
                return RGBA(r, g, b)
        if value_lower in {"default", "none"}:
            return self.default

        # RichColor parsing
        rich_color = RichColor.parse(value_lower)
        if rich_color:
            color_triplet = rich_color.get_truecolor()
            if color_triplet:
                return RGBA.from_triplet(color_triplet)

        raise ColorError(f"Unable to parse color string: {value}")

    @classmethod
    def _lookup_color(cls, value: ColorType) -> Optional[RGBA]:
        """Lookup a color in the color data.

        Args:
            value (ColorType): The color value to lookup.

        Returns:
            Optional[Color]: The Color instance if found, else None.
        """
        color_dicts: List[Dict] = [
            COLORS_BY_NAME,
            COLORS_BY_RGB,
            COLORS_BY_HEX,
            COLORS_BY_ANSI,
        ]
        for color_dict in color_dicts:
            if value not in color_dict:
                continue

            # value in color dict
            color_info: Dict = color_dict[value]
            if color_info["hex"]:
                hex_value = color_info["hex"]
                if isinstance(hex_value, str):
                    return RGBA.from_hex(hex_value)
            else:
                return RGBA.from_hex(str(value))

    @classmethod
    def parse_tuple(cls, value: Tuple[int | float | str, ...] | "Color") -> RGBA:
        """
        Parse a tuple of RGB or RGBA values where each can be int, float, or numeric string.
        Returns an RGBA instance with 0-255 channels and alpha.
        """
        if isinstance(value, Color):
            return value._rgba
        value_tuple = cast(tuple, value)
        length = len(value_tuple)
        if length not in (3, 4):
            raise ColorError(
                "value is not a valid color: tuples must have length 3 or 4"
            )

        # Helper to convert each component to 0-255 int
        def to_int(comp: int | float | str) -> int:
            if isinstance(comp, int):
                return comp
            # float or numeric string: normalize to 0..1 then scale
            frac = cls.parse_color_value(comp)  # returns 0..1
            return round(frac * 255)

        r = to_int(value_tuple[0])
        g = to_int(value_tuple[1])
        b = to_int(value_tuple[2])
        alpha = cls.parse_float_alpha(value_tuple[3]) if length == 4 else 1.0
        return RGBA(r, g, b, alpha)

    @classmethod
    def parse_hsl(
        cls, h: str, h_units: str, sat: str, light: str, alpha: float | None = None
    ) -> RGBA:
        s_value = cls.parse_color_value(sat, 100)
        l_value = cls.parse_color_value(light, 100)
        h_value = float(h)
        if h_units in {None, "deg"}:
            h_value = h_value % 360 / 360
        elif h_units == "rad":
            h_value = h_value % rads / rads
        else:
            h_value %= 1
        r, g, b = hls_to_rgb(h_value, l_value, s_value)
        return RGBA(
            round(r * 255), round(g * 255), round(b * 255), cls.parse_float_alpha(alpha)
        )

    @classmethod
    def ints_to_rgba(
        cls,
        r: int | str,
        g: int | str,
        b: int | str,
        alpha: float = 1.0,
    ) -> RGBA:
        r_val = r if isinstance(r, int) else cls.parse_color_value(r)
        g_val = g if isinstance(g, int) else cls.parse_color_value(g)
        b_val = b if isinstance(b, int) else cls.parse_color_value(b)
        a_val = cls.parse_float_alpha(alpha)
        return RGBA(
            r_val if isinstance(r_val, int) else round(r_val * 255),
            g_val if isinstance(g_val, int) else round(g_val * 255),
            b_val if isinstance(b_val, int) else round(b_val * 255),
            a_val,
        )

    @staticmethod
    def parse_color_value(value: int | float | str, max_val: int = 255) -> float:
        """
        Parse a color value for a channel (r, g, b, etc.) to a float in 0..1.
        Returns the normalized value.
        """
        try:
            color = float(value)
        except (ValueError, TypeError) as e:
            raise ColorError("Value is not a valid number for a color channel.") from e
        if 0 <= color <= max_val:
            return color / max_val
        raise ColorError(f"Color value {color} is out of range 0 to {max_val}.")

    @staticmethod
    def parse_float_alpha(value: None | str | float | int) -> float:
        if value is None:
            return 1.0
        try:
            if isinstance(value, str):
                if value.endswith("%"):
                    alpha = float(value[:-1]) / 100
                else:
                    alpha = float(value)
            else:
                alpha = float(value)
        except (ValueError, TypeError) as e:
            raise ColorError("Value is not a valid number for alpha channel.") from e
        if math.isclose(alpha, 1):
            return 1.0
        if 0 <= alpha <= 1:
            return alpha
        raise ColorError("Alpha value must be between 0 and 1.")

    @staticmethod
    def float_to_255(param: float) -> int:
        if isinstance(param, float):
            return round(param * 255)
        elif isinstance(param, int):
            if 0 <= param <= 255:
                return param
            raise ValueError("Integer value must be between 0 and 255.")
        elif isinstance(param, str):
            try:
                param = int(param)
            except ValueError:
                raise ValueError("String value must be convertible to a float.")
            return param

    # --- Utility ---

    def get_contrast(self, fixed: Optional[str] = None) -> RichColor:
        """Get the contrast color for the current color.
        Args:
            fixed (Optional[Literal["white", "black"]], optional): If set, \
                the contrast color will be either white or black. Defaults to None.
        Returns:
            RichColor: The contrast color.
        """
        if fixed is not None:
            if fixed == "white":
                return RichColor.parse("#EEEEEE")
            elif fixed == "black":
                return RichColor.parse("#000000")
            else:
                raise ValueError("Fixed must be either 'white' or 'black'")
        r, g, b = (self.float_to_255(c) for c in self._rgba[:3])
        brightness = 0.299 * r + 0.587 * g + 0.114 * b
        # Should return white if dark, black if bright
        return (
            RichColor.parse("#EEEEEE")
            if brightness < 127.5
            else RichColor.parse("#000000")
        )

    # --- Display Utilities

    @classmethod
    def gradient_title(cls, title: str) -> Text:
        """Manually color a title.

        Args:
            title (str): The title to style.

        Returns:
            Text: The styled title.
        """
        title_list: List[str] = list(title)
        length = len(title)
        SPECTRUM_COLORS = [cls(color) for color in SPECTRUM_COLOR_STRS]
        COLORS: cycle = cycle(SPECTRUM_COLORS)
        color_title = Text()
        for _ in range(randint(0, 18)):
            next(COLORS)
        for index in range(length):
            char: str = title_list[index]
            color: str = next(COLORS)
            color_title.append(Text(char, style=f"bold {color}"))
        return color_title

    @classmethod
    def _generate_table(
        cls, title: str, show_index: bool = True, caption: Optional[Text] = None
    ) -> Table:
        """
        Generate a table to display colors.

        Args:
            title: The title for the table.
            show_index: Whether to show the index column.
            caption: The caption for the table.

        Returns:
            A `rich.table.Table` instance.
        """
        color_title = cls.gradient_title(title)
        table = Table(
            title=color_title, expand=False, caption=caption, caption_justify="right"
        )
        if show_index:
            table.add_column(cls.gradient_title("Index"), style="bold", justify="right")
        table.add_column(cls.gradient_title("Sample"), style="bold", justify="center")
        table.add_column(cls.gradient_title("Name"), style="bold", justify="left")
        table.add_column(cls.gradient_title("Hex"), style="bold", justify="left")
        table.add_column(cls.gradient_title("RGB"), style="bold", justify="left")
        return table

    @classmethod
    def _color_table(
        cls,
        title: str,
        start: int,
        end: int,
        caption: Optional[Text] = None,
        *,
        show_index: bool = False,
    ) -> Table:
        """Generate a table of colors.

        Args:
            title (str): The title of the color table.
            start (int): The starting index.
            end (int): The ending index.
            caption (Optional[Text], optional): The caption of the color table. Defaults to None.
            show_index (bool, optional): Whether to show the index of the color. Defaults to False.

        Returns:
            Table: The color table.
        """
        table = cls._generate_table(title, show_index, caption)
        for index, (key, _) in enumerate(COLORS_BY_NAME.items()):
            if index < start:
                continue
            elif index > end:
                break
            color = Color(key)

            color_index = Text(f"{index: >3}", style=f"bold {color.hex}")
            style = RichStyle(color=color.hex, bold=True)
            sample = Text(f"{'█' * 10}", style=style)
            name = Text(f"{key.capitalize(): <20}", style=style)
            hex_str = f" {color.as_hex('long').upper()} "
            hex = Text(f"{hex_str: ^7}", style=f"bold on {color.hex}")
            rgb = color._rgba
            if show_index:
                table.add_row(color_index, sample, name, hex, rgb)
            else:
                table.add_row(sample, name, hex, rgb)
        return table

    @classmethod
    def example(cls, record: bool = False) -> None:
        """Generate an example of the color class.

        Args:
            record (bool): Whether to record the example as an svg.
        """
        console = Console(record=True, width=80) if record else Console()

        def table_generator() -> Generator[
            tuple[str, int, int, Optional[Text]], None, None
        ]:
            """Generate the tables for the example."""
            tables: list[tuple[str, int, int, Optional[Text]]] = [
                (
                    "Spectrum Colors",
                    0,
                    17,
                    Text(
                        "These colors have been adapted to make naming easier.",
                        style="i d #ffffff",
                    ),
                ),
                ("CSS3 Colors", 18, 148, None),
                ("Rich Colors", 149, 342, None),
            ]
            for table in tables:
                yield table

        for title, start, end, caption in table_generator():
            console.line(2)
            table = cls._color_table(title, start, end, caption=caption)
            console.print(table, justify="center")
            console.line(2)

        if record:
            try:
                console.save_svg(
                    "docs/img/colors.svg", theme=GRADIENT_TERMINAL_THEME, title="Colors"
                )
            except TypeError:
                pass


def color_prompt() -> None:
    """Prompt the user to enter a color and display the color as a Rich text."""
    from rich.prompt import Prompt

    console = Console()
    console.clear()
    user_input = Prompt.ask("[b #aaffaa]Enter a color[/]")
    try:
        color = Color(user_input)
        hex_color = color.as_hex(format="long")
        console.line(4)
        console.print(
            f"[b {hex_color}]This text is [u]{user_input.capitalize()}[/u]![/]"
        )
        console.line(2)
    except Exception as e:
        console.print(f"[b i red]Error:[/] {e}")


# Utility method to render a RichRenderable (like Text) into stylized Text without printing


if TYPE_CHECKING:
    from rich.console import Console as RichConsole
    from rich.console import RenderableType
    from rich.text import Text
else:
    RenderableType = Any
    RichConsole = Console
    Text = Text


class _ColorUtils:
    @staticmethod
    def render_renderable(
        renderable: "RenderableType", console: Optional[Console] = None
    ) -> Text:
        from io import StringIO

        from rich.console import Console as RichConsole

        console = console or RichConsole()
        with console.capture() as capture:
            console.print(renderable, end="")
        rendered = capture.get()
        return Text.from_ansi(rendered)


if __name__ == "__main__":
    Color.example()
