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
)

from rich import get_console
from rich.color import Color as RichColor
from rich.color_triplet import ColorTriplet
from rich.console import Console, ConsoleOptions
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from rich_gradient._color_data import ColorData
from rich_gradient._colors_by_ import (
    COLORS_BY_ANSI,
    COLORS_BY_HEX,
    COLORS_BY_NAME,
    COLORS_BY_RGB,
    SPECTRUM_COLOR_STRS,
)
from rich_gradient._parsers import (
    _r_255,
    _r_alpha,
    _r_comma,
    _r_h,
    _r_sl,
    r_hex_long,
    r_hex_short,
    r_hsl,
    r_hsl_v4_style,
    r_rgb,
    r_rgb_v4_style,
    rads,
    repeat_colors,
)
from rich_gradient._rgba import RGBA, HslColorTuple, RGBA_ColorType
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

ColorType: TypeAlias = Union[RGBA_ColorType, "Color"]

# --- Exports ---
__all__ = ["Color", "ColorError", "ColorType", "RGBA", "ColorData"]


class ColorError(Exception):
    """
    An exception that automatically prefixes the module and function
    where it was raised to the message.
    """

    def __init__(self, message: str) -> None:
        # inspect.stack()[1] is the caller’s frame
        frame_info = inspect.stack()[1]
        module_name = getattr(
            frame_info.frame.f_globals, "__name__", "<unknown module>"
        )
        if not isinstance(module_name, str):
            module_name = "<unknown module>"
        func_name = getattr(frame_info, "function", "<unknown function>")
        line_no = getattr(frame_info, "lineno", -1)
        # Build the full message
        full_message = f"{module_name}.{func_name}:{line_no}: {message}"
        super().__init__(full_message)


class Color:
    """This class is used to represent a color in various formats and provides methods to convert the color to different formats.

    Args:
        value (ColorType): The color value to be represented.

    Raises:
        ColorError: If the input value is not a valid color.

    **An edited version of the `Color` class from the [`pydantic-extra-types`](https://github.com/pydantic/pydantic-extra-types) package.*
    """

    __slots__ = "_original", "_rgba"

    # --- Core Methods ---

    def __init__(self, value: ColorType) -> None:
        self._rgba: RGBA
        self._original = str(ColorType)
        if isinstance(value, (tuple, list)):
            self._rgba = self.parse_tuple(value)
            return
        elif isinstance(value, Color):
            self._rgba = value._rgba
            return
        elif isinstance(value, RGBA):
            self._rgba = value
            return
        elif isinstance(value, ColorTriplet):
            self._rgba = RGBA.from_triplet(value)
            return
        elif isinstance(value, RichColor):
            self._rgba = RGBA.from_rich(value)
            return
        elif isinstance(value, str):
            self._rgba = self.parse_str(value)
            return
        else:
            raise ColorError(
                "Value is not a valid color: value must be a tuple, \
list, string, Color, RGBA, RichColor, or ColorTriplet."
            )
        self.original = value

    def __str__(self) -> str:
        return self.as_named(fallback=True)

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Color) and self.as_rgb_tuple() == other.as_rgb_tuple()

    def __hash__(self) -> int:
        return hash(self.as_rgb_tuple())

    def __rich__(self) -> Text:
        """Return a simple visual block for Console.print()."""
        return Text(f"{'█' * 10}", style=self.style)

    def __repr__(self, *args: Any, **kwds: Any) -> Any:
        return f"Color({self.as_named(fallback=True)})"

    def __rich_repr__(self) -> Text:
        """Return a rich representation of the color."""
        return Text.assemble(
            *[
                Text("Color(", style="bold #ffffff"),
                Text(f"'{self.as_named(fallback=True)}'", style=f"bold {self.hex}"),
                Text(")", style="bold #ffffff"),
            ]
        )

    # --- Properties ---

    @property
    def alpha(self) -> float:
        """Alpha channel as a float, treating None as fully opaque (1.0)."""
        return 1.0 if self._rgba.alpha is None else self._rgba.alpha

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

    @cached_property
    def triplet(self) -> ColorTriplet:
        """The `rich.color_triplet.ColorTriplet` representation \
of the color."""
        return self.as_triplet()

    @cached_property
    def rich(self) -> RichColor:
        """The color as a rich color."""
        return self.as_rich()

    @cached_property
    def style(self) -> Style:
        """The color as a rich style."""
        return self.as_style()

    @cached_property
    def bg_style(self) -> Style:
        """The color as a background style."""
        return self.as_bg_style()

    @property
    def ansi(self) -> int | None:
        """The ANSI color code for the color, or None if not found."""
        ansi = self.as_ansi()
        if ansi is not None and ansi != -1:
            return ansi
        raise KeyError(f"ANSI color code not found for color: {self.hex}")

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

    # --- Conversion Methods ---

    def as_named(self, *, fallback: bool = True) -> str:
        """Returns the name of the color if it matches a known color.

        Args:
            fallback (bool, optional): If True (default), fall \
back to hex representation if name is not found.
                If False, raise ValueError when no name is found.

        Returns:
            str: Named color or hex string.

        Raises:
            ValueError: If no named color exists and fallback is False.
        """
        rgb = self.as_rgb_tuple()
        color_info = COLORS_BY_RGB.get(rgb)
        if color_info and isinstance(color_info, dict):
            name = color_info.get("name")
            if not isinstance(name, str):
                raise ColorError(f"Expected a color name string, got {type(name)}")
            return name
        if fallback:
            return self.as_hex()
        raise ValueError(f"Color {rgb} has no named equivalent.")

    @classmethod
    def default(cls) -> "Color":
        """Returns the default color for the terminal theme.

        Returns:
            Color: The default color for the terminal theme.
        """
        default = RichColor.default().triplet
        return Color.from_triplet(default) if default else Color.from_hex("#000000")

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
        r, g, b, a = (self._rgba.r, self._rgba.g, self._rgba.b, self._rgba.alpha)
        if a == 1.0 or a is None:
            return f"rgb({r}, {g}, {b})"
        return f"rgba({r}, {g}, {b}, {round(self.alpha, 2)})"

    def as_rgb_tuple(self) -> tuple[int, int, int]:
        r, g, b = (c for c in self._rgba[:3])
        return r, g, b

    def as_hsl(self) -> str:
        hsl_tuple = self.as_hsl_tuple()
        h, s, li = hsl_tuple[0], hsl_tuple[1], hsl_tuple[2]
        if self._rgba.alpha is None:
            return f"hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%})"
        else:
            a = self.alpha
            return f"hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%}, {round(a, 2)})"

    def as_hsl_tuple(self) -> HslColorTuple:
        h, l, s = rgb_to_hls(self._rgba.r / 255, self._rgba.g / 255, self._rgba.b / 255)
        return h, s, l

    def as_triplet(self) -> ColorTriplet:
        return ColorTriplet(self._rgba.r, self._rgba.g, self._rgba.b)

    def as_rich(self) -> RichColor:
        try:
            rgb_triplet = self.as_triplet()
            return RichColor.from_triplet(rgb_triplet)
        except ColorError:
            raise ColorError("Unable to parse color")

    def as_style(
        self,
        bgcolor: RichColor | None = None,
        bold: bool | None = None,
        dim: bool | None = None,
        italic: bool | None = None,
        underline: bool | None = None,
        blink: bool | None = None,
        blink2: bool | None = None,
        reverse: bool | None = None,
        conceal: bool | None = None,
        strike: bool | None = None,
        underline2: bool | None = None,
        frame: bool | None = None,
        encircle: bool | None = None,
        overline: bool | None = None,
        link: str | None = None,
        meta: Dict[str, Any] | None = None,
    ) -> Style:
        """
                A terminal style.

        A terminal style consists of the color (color), a background color (bgcolor), and a number of attributes, such
        as bold, italic etc. The attributes have 3 states: they can either be on (True), off (False), or not set (None).

        Args:
            bgcolor (RichColor, optional): Background color. Defaults to None.
            bold (bool, optional): Enable bold text. Defaults to None.
            dim (bool, optional): Enable dim text. Defaults to None.
            italic (bool, optional): Enable italic text. Defaults to None.
            underline (bool, optional): Enable underlined text. Defaults to None.
            blink (bool, optional): Enabled blinking text. Defaults to None.
            blink2 (bool, optional): Enable fast blinking text. Defaults to None.
            reverse (bool, optional): Enabled reverse text. Defaults to None.
            conceal (bool, optional): Enable concealed text. Defaults to None.
            strike (bool, optional): Enable strikethrough text. Defaults to None.
            underline2 (bool, optional): Enable doubly underlined text. Defaults to None.
            frame (bool, optional): Enable framed text. Defaults to None.
            encircle (bool, optional): Enable encircled text. Defaults to None.
            overline (bool, optional): Enable overlined text. Defaults to None.
            link (str, link): Link URL. Defaults to None.

        Returns:
            rich.style.Style: A rich.style.Style with the foreground set to the color.
        """
        rich_color = self.as_rich()
        return Style(
            color=rich_color,
            bgcolor=bgcolor,
            bold=bold,
            dim=dim,
            italic=italic,
            underline=underline,
            blink=blink,
            blink2=blink2,
            reverse=reverse,
            conceal=conceal,
            strike=strike,
            underline2=underline2,
            frame=frame,
            encircle=encircle,
            overline=overline,
            link=link,
            meta=meta,
        )

    def as_bg_style(
        self,
        color: RichColor | None = None,
        bgcolor: RichColor | None = None,
        bold: bool | None = True,
        dim: bool | None = None,
        italic: bool | None = None,
        underline: bool | None = None,
        blink: bool | None = None,
        blink2: bool | None = None,
        reverse: bool | None = None,
        conceal: bool | None = None,
        strike: bool | None = None,
        underline2: bool | None = None,
        frame: bool | None = None,
        encircle: bool | None = None,
        overline: bool | None = None,
        link: str | None = None,
        meta: Dict[str, Any] | None = None,
        *,
        fixed: Optional[str] = None,
    ) -> Style:
        """
                A terminal style.

        A terminal style consists of the color (color), a background color (bgcolor), and a number of attributes, such
        as bold, italic etc. The attributes have 3 states: they can either be on (True), off (False), or not set (None).

        Args:
            color (RichColor, optional): Foreground color. Defaults to None, which will generate a foreground color based on the contrast ratio.
            bold (bool, optional): Enable bold text. Defaults to True.
            dim (bool, optional): Enable dim text. Defaults to None.
            italic (bool, optional): Enable italic text. Defaults to None.
            underline (bool, optional): Enable underlined text. Defaults to None.
            blink (bool, optional): Enabled blinking text. Defaults to None.
            blink2 (bool, optional): Enable fast blinking text. Defaults to None.
            reverse (bool, optional): Enabled reverse text. Defaults to None.
            conceal (bool, optional): Enable concealed text. Defaults to None.
            strike (bool, optional): Enable strikethrough text. Defaults to None.
            underline2 (bool, optional): Enable doubly underlined text. Defaults to None.
            frame (bool, optional): Enable framed text. Defaults to None.
            encircle (bool, optional): Enable encircled text. Defaults to None.
            overline (bool, optional): Enable overlined text. Defaults to None.
            link (str, link): Link URL. Defaults to None.

        Returns:
            Style: The style.
        """
        if color is None:
            color = self.get_contrast(fixed=fixed)
        if bgcolor is None:
            bgcolor = self._rgba.as_rich()
        return Style(
            color=color,
            bgcolor=bgcolor,
            bold=bold,
            dim=dim,
            italic=italic,
            underline=underline,
            blink=blink,
            blink2=blink2,
            reverse=reverse,
            conceal=conceal,
            strike=strike,
            underline2=underline2,
            frame=frame,
            encircle=encircle,
            overline=overline,
            link=link,
            meta=meta,
        )

    def as_ansi(self) -> int | None:
        color_dict: Optional[dict[str, str | Tuple[int, int, int] | int]] = (
            COLORS_BY_HEX.get(self.hex)
        )
        if not color_dict:
            raise KeyError(f"Color not found in COLORS_BY_HEX: {self.hex}")
        ansi = color_dict.get("ansi")
        if ansi != -1:
            assert isinstance(ansi, int), (
                f"Expected ansi to be an int, got {type(ansi)}"
            )
            return ansi
        else:
            return None
        raise KeyError(f"ANSI color code not found for color: {self.hex}")

    @classmethod
    def from_rgba(cls, value: RGBA) -> Color:
        return cls(value)

    @classmethod
    def from_hex(cls, value: str) -> "Color":
        return cls(RGBA.from_hex(value))

    @classmethod
    def from_rgb(cls, value: str) -> "Color":
        return cls(RGBA.from_rgb(value))

    @classmethod
    def from_rgb_tuple(
        cls, value: tuple[int, int, int] | tuple[int, int, int, float]
    ) -> "Color":
        return cls(RGBA.from_tuple(value))

    @classmethod
    def from_hsl(cls, value: str) -> "Color":
        return cls(RGBA.from_hsl(value))

    @classmethod
    def from_hsl_tuple(
        cls, value: tuple[float, float, float] | tuple[float, float, float, float]
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
        """
        if isinstance(value, RichColor):
            if value.triplet is None:
                if value.name in COLORS_BY_NAME:
                    color = COLORS_BY_NAME[value.name]
                    rgb_tuple: Tuple[int, int, int] = color["rgb"]  # type: ignore
                    r, g, b = [int(param) for param in rgb_tuple]
                    return cls.from_rgba(RGBA(r, g, b))
                try:
                    _value = cls(value)
                    return _value
                except ColorError as ce:
                    raise ColorError(
                        f"Color.from_rich({value}) has no triplet: {ce}"
                    ) from ce

            elif isinstance(value, str):
                try:
                    parsed_color = RichColor.parse(value)
                except Exception:
                    try:
                        return cls(value)
                    except ColorError as ce:
                        raise ColorError(
                            f"Unable to parse color in Color.from_rich({value}): {ce}"
                        ) from ce

                if parsed_color.triplet is None:
                    raise ColorError(
                        f"Parsed rich color from string {value} has no triplet"
                    )
                return cls.from_triplet(parsed_color.triplet)
            return cls.from_triplet(value.triplet)
        raise ColorError(f"Unable to parse color in Color.from_rich({value}).")

    @classmethod
    def from_style(cls, style: Style) -> "Color":
        if style.color:
            return cls.from_rich(style.color)
        raise ColorError("Style has no foreground color")

    # --- Parsing Helpers ---

    def parse_str(self, value: str) -> RGBA:
        if isinstance(value, RichColor):
            assert value.triplet is not None, f"Richcolor has no triplet: {value}"
            value_lower: str = value.triplet.hex.lower()
        else:
            value_lower = value.lower()
        if value_lower in COLORS_BY_NAME:
            color_info = COLORS_BY_NAME[value_lower]
            if "rgb" in color_info:
                rgb = color_info["rgb"]
                assert isinstance(rgb, tuple), (
                    f"Expected rgb to be a tuple, got {type(rgb)}"
                )
                r, g, b = rgb
                return RGBA(r, g, b)
        m = re.fullmatch(r_hex_short, value_lower)
        if m:
            *rgb, a = m.groups()
            r, g, b = (int(v * 2, 16) for v in rgb)
            alpha = int(a * 2, 16) / 255 if a else 1.0
            return self.ints_to_rgba(r, g, b, alpha)
        m = re.fullmatch(r_hex_long, value_lower)
        if m:
            *rgb, a = m.groups()
            r, g, b = (int(v, 16) for v in rgb)
            alpha = int(a, 16) / 255 if a else 1.0
            return self.ints_to_rgba(r, g, b, alpha)
        m = re.fullmatch(r_rgb, value_lower) or re.fullmatch(
            r_rgb_v4_style, value_lower
        )
        if m:
            return self.ints_to_rgba(*m.groups())  # type: ignore
        m = re.fullmatch(r_hsl, value_lower) or re.fullmatch(
            r_hsl_v4_style, value_lower
        )
        if m:
            return self.parse_hsl(*m.groups())  # type: ignore
        m = re.fullmatch(r"^(\d+)$", value_lower)
        if m:
            color_info = COLORS_BY_ANSI.get(int(m.group(1)))
            if color_info and "rgb" in color_info:
                rgb = color_info["rgb"]
                assert isinstance(rgb, tuple), (
                    f"Expected rgb to be a tuple, got {type(rgb)}"
                )
                r, g, b = rgb
                return RGBA(r, g, b)
        if value_lower == "default":
            default_rich = RichColor.default()
            if default_rich.triplet is None:
                raise ColorError("Default RichColor has no triplet")
            return RGBA.from_triplet(default_rich.triplet)
        if color_info and "rgb" in color_info:
            rgb = color_info["rgb"]
            assert isinstance(rgb, tuple), (
                f"Expected rgb to be a tuple, got {type(rgb)}"
            )
            r, g, b = rgb
            return RGBA(r, g, b)
        raise ColorError(f"Unable to parse color string: {value}")

    @classmethod
    def parse_tuple(cls, value: tuple[int | float | str, ...] | Color) -> RGBA:
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

            color_index = Text(f"{index: >3}", style=color.as_style(bold=True))
            style = color.as_style(bold=True)
            sample = Text(f"{'█' * 10}", style=style)
            name = Text(f"{key.capitalize(): <20}", style=style)
            hex_str = f" {color.as_hex('long').upper()} "
            hex = Text(f"{hex_str: ^7}", style=color.as_bg_style())
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


if __name__ == "__main__":
    Color.example()
