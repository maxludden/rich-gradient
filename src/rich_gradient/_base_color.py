"""**This is an adapted version of the 'Color' class from the [`pydantic-extra-types`](https://github.com/pydantic/pydantic-extra-types) package.*



Color definitions are used as per the CSS3
[CSS Color Module Level 3](http://www.w3.org/TR/css3-color/#svg-color) specification.

A few colors have multiple names referring to the sames colors, eg. `grey` and `gray` or `aqua` and `cyan`.

In these cases the _last_ color when sorted alphabetically takes preferences,
eg. `Color((0, 255, 255)).as_named() == 'cyan'` because "cyan" comes after "aqua".
"""

from __future__ import annotations

import math
import re
from colorsys import hls_to_rgb, rgb_to_hls
from typing import Any, Literal, Tuple, Union, cast, Dict, List, Optional, Generator
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.style import Style
from rich.color_triplet import ColorTriplet
from rich.color import Color as RichColor
from itertools import cycle
from random import randint

ColorTuple = Union[Tuple[int, int, int], Tuple[int, int, int, float]]
ColorType = Union[ColorTuple, str, Tuple[Any, ...]]
HslColorTuple = Union[Tuple[float, float, float], Tuple[float, float, float, float]]


class ColorError(Exception):
    """Base class for color errors."""

    pass


class RGBA:
    """Internal use only as a representation of a color."""

    __slots__ = "r", "g", "b", "alpha", "_tuple"

    def __init__(self, r: float, g: float, b: float, alpha: float | None):
        self.r = r
        self.g = g
        self.b = b
        self.alpha = alpha

        self._tuple: tuple[float, float, float, float | None] = (r, g, b, alpha)

    def __getitem__(self, item: Any) -> Any:
        return self._tuple[item]


# these are not compiled here to avoid import slowdown, they'll be compiled the first time they're used, then cached
_r_255 = r"(\d{1,3}(?:\.\d+)?)"
_r_comma = r"\s*,\s*"
_r_alpha = r"(\d(?:\.\d+)?|\.\d+|\d{1,2}%)"
_r_h = r"(-?\d+(?:\.\d+)?|-?\.\d+)(deg|rad|turn)?"
_r_sl = r"(\d{1,3}(?:\.\d+)?)%"
r_hex_short = r"\s*(?:#|0x)?([0-9a-f])([0-9a-f])([0-9a-f])([0-9a-f])?\s*"
r_hex_long = r"\s*(?:#|0x)?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})?\s*"
# CSS3 RGB examples: rgb(0, 0, 0), rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 50%)
r_rgb = rf"\s*rgba?\(\s*{_r_255}{_r_comma}{_r_255}{_r_comma}{_r_255}(?:{_r_comma}{_r_alpha})?\s*\)\s*"
# CSS3 HSL examples: hsl(270, 60%, 50%), hsla(270, 60%, 50%, 0.5), hsla(270, 60%, 50%, 50%)
r_hsl = rf"\s*hsla?\(\s*{_r_h}{_r_comma}{_r_sl}{_r_comma}{_r_sl}(?:{_r_comma}{_r_alpha})?\s*\)\s*"
# CSS4 RGB examples: rgb(0 0 0), rgb(0 0 0 / 0.5), rgb(0 0 0 / 50%), rgba(0 0 0 / 50%)
r_rgb_v4_style = (
    rf"\s*rgba?\(\s*{_r_255}\s+{_r_255}\s+{_r_255}(?:\s*/\s*{_r_alpha})?\s*\)\s*"
)
# CSS4 HSL examples: hsl(270 60% 50%), hsl(270 60% 50% / 0.5), hsl(270 60% 50% / 50%), hsla(270 60% 50% / 50%)
r_hsl_v4_style = (
    rf"\s*hsla?\(\s*{_r_h}\s+{_r_sl}\s+{_r_sl}(?:\s*/\s*{_r_alpha})?\s*\)\s*"
)

# colors where the two hex characters are the same, if all colors match this the short version of hex colors can be used
repeat_colors = {int(c * 2, 16) for c in "0123456789abcdef"}
rads = 2 * math.pi


class Color:
    """This class is used to represent a color in various formats and provides methods to convert the color to different formats.

    Args:
        value (ColorType): The color value to be represented.

    Raises:
        ColorError: If the input value is not a valid color.

    **An edited version of the `Color` class from the [`pydantic-extra-types`](https://github.com/pydantic/pydantic-extra-types) package.*
    """

    __slots__ = "_original", "_rgba"

    def __init__(self, value: ColorType) -> None:
        self._rgba: RGBA
        self._original: ColorType
        if isinstance(value, (tuple, list)):
            self._rgba = self.parse_tuple(value)
        elif isinstance(value, str):
            self._rgba = self.parse_str(value)
        elif isinstance(value, Color):
            self._rgba = value._rgba
            value = value._original
        else:
            raise ColorError(
                "value is not a valid color: value must be a tuple, list or string",
            )

        # if we've got here value must be a valid color
        self._original = value

    # @classmethod
    # def __get_pydantic_json_schema__(
    #     cls, core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    # ) -> JsonSchemaValue:
    #     field_schema: dict[str, Any] = {}
    #     field_schema.update(type='string', format='color')
    #     return field_schema

    def original(self) -> ColorType:
        """Original value passed to `Color`."""
        return self._original

    def as_named(self, *, fallback: bool = False) -> str:
        """Returns the name of the color if it can be found in `COLORS_BY_VALUE` dictionary,
        otherwise returns the hexadecimal representation of the color or raises `ValueError`.

        Args:
            fallback: If True, falls back to returning the hexadecimal representation of
                the color instead of raising a ValueError when no named color is found.

        Returns:
            The name of the color, or the hexadecimal representation of the color.

        Raises:
            ValueError: When no named color is found and fallback is `False`.
        """
        if self._rgba.alpha is not None:
            return self.as_hex()
        rgb = cast("tuple[int, int, int]", self.as_rgb_tuple())

        if rgb in self.COLORS_BY_VALUE:
            return self.COLORS_BY_VALUE[rgb]
        else:
            if fallback:
                return self.as_hex()
            else:
                raise ValueError(
                    "no named color found, use fallback=True, as_hex() or as_rgb()"
                )

    def as_hex(self, format: Literal["short", "long"] = "short") -> str:
        """Returns the hexadecimal representation of the color.

        Hex string representing the color can be 3, 4, 6, or 8 characters depending on whether the string
        a "short" representation of the color is possible and whether there's an alpha channel.

        Returns:
            The hexadecimal representation of the color.
        """
        values = [self.float_to_255(c) for c in self._rgba[:3]]
        if self._rgba.alpha is not None:
            values.append(self.float_to_255(self._rgba.alpha))

        as_hex = "".join(f"{v:02x}" for v in values)
        if format == "short" and all(c in repeat_colors for c in values):
            as_hex = "".join(as_hex[c] for c in range(0, len(as_hex), 2))
        return f"#{as_hex}"

    def as_rgb(self) -> str:
        """Color as an `rgb(<r>, <g>, <b>)` or `rgba(<r>, <g>, <b>, <a>)` string."""
        if self._rgba.alpha is None:
            return f"rgb({self.float_to_255(self._rgba.r)}, {self.float_to_255(self._rgba.g)}, {self.float_to_255(self._rgba.b)})"
        else:
            return (
                f"rgba({self.float_to_255(self._rgba.r)}, {self.float_to_255(self._rgba.g)}, {self.float_to_255(self._rgba.b)}, "
                f"{round(self._alpha_float(), 2)})"
            )

    def as_rgb_tuple(self, *, alpha: bool | None = None) -> ColorTuple:
        """Returns the color as an RGB or RGBA tuple.

        Args:
            alpha: Whether to include the alpha channel. There are three options for this input:

                - `None` (default): Include alpha only if it's set. (e.g. not `None`)
                - `True`: Always include alpha.
                - `False`: Always omit alpha.

        Returns:
            A tuple that contains the values of the red, green, and blue channels in the range 0 to 255.
                If alpha is included, it is in the range 0 to 1.
        """
        r, g, b = (self.float_to_255(c) for c in self._rgba[:3])
        if (
            alpha is None
            and self._rgba.alpha is None
            or alpha is not None
            and not alpha
        ):
            return r, g, b
        else:
            return r, g, b, self._alpha_float()

    def as_hsl(self) -> str:
        """Color as an `hsl(<h>, <s>, <l>)` or `hsl(<h>, <s>, <l>, <a>)` string."""
        if self._rgba.alpha is None:
            h, s, li = self.as_hsl_tuple(alpha=False)  # type: ignore
            return f"hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%})"
        else:
            h, s, li, a = self.as_hsl_tuple(alpha=True)  # type: ignore
            return f"hsl({h * 360:0.0f}, {s:0.0%}, {li:0.0%}, {round(a, 2)})"

    def as_hsl_tuple(self, *, alpha: bool | None = None) -> HslColorTuple:
        """Returns the color as an HSL or HSLA tuple.

        Args:
            alpha: Whether to include the alpha channel.

                - `None` (default): Include the alpha channel only if it's set (e.g. not `None`).
                - `True`: Always include alpha.
                - `False`: Always omit alpha.

        Returns:
            The color as a tuple of hue, saturation, lightness, and alpha (if included).
                All elements are in the range 0 to 1.

        Note:
            This is HSL as used in HTML and most other places, not HLS as used in Python's `colorsys`.
        """
        h, l, s = rgb_to_hls(self._rgba.r, self._rgba.g, self._rgba.b)  # noqa: E741
        if alpha is None:
            if self._rgba.alpha is None:
                return h, s, l
            else:
                return h, s, l, self._alpha_float()
        return (h, s, l, self._alpha_float()) if alpha else (h, s, l)

    def _alpha_float(self) -> float:
        return 1 if self._rgba.alpha is None else self._rgba.alpha

    # @classmethod
    # def __get_pydantic_core_schema__(
    #     cls, source: type[Any], handler: Callable[[Any], CoreSchema]
    # ) -> core_schema.CoreSchema:
    #     return core_schema.with_info_plain_validator_function(
    #         cls._validate, serialization=core_schema.to_string_ser_schema()
    #     )

    @classmethod
    def _validate(cls, __input_value: Any, _: Any) -> Color:
        return cls(__input_value)

    def __str__(self) -> str:
        return self.as_named(fallback=True)

    # def __repr_args__(self) -> _repr.ReprArgs:
    #     return [(None, self.as_named(fallback=True))] + [('rgb', self.as_rgb_tuple())]

    def __eq__(self, other: Any) -> bool:
        return (
            isinstance(other, Color) and self.as_rgb_tuple() == other.as_rgb_tuple()
        )

    def __hash__(self) -> int:
        return hash(self.as_rgb_tuple())


    def as_rich(self) -> RichColor:
        """Convert the color to a rich color.

        Returns:
            RichColor: The color as a rich color.

        Raises:
            ColorParsingError: If the color cannot be parsed
        """
        try:
            hex = self.as_hex(format="long")
            return RichColor.parse(hex)
        except ColorError:
            raise ColorError(f"Unable to parse color: {self}")

    @property
    def rich(self) -> RichColor:
        """The color as a rich color.

        Returns:
            RichColor: The color as a rich color.
        """
        return self.as_rich()  # type: ignore

    def __rich__(self) -> Text:
        """Return a rich text representation of the color.

        Returns:
            Text: The rich text representation of the color."""
        return Text.assemble(
            *[
                Text("Color", style="bold #ffffff"),
                Text("(", style="bold #ffffff"),
                Text(f"{self.as_named()}", style=f"bold {self.as_hex}"),
                Text(")", style="bold #ffffff"),
            ]
        )

    @property
    def style(self) -> Style:
        """The color as a rich style.

        Returns:
            Style: The color as a rich style."""
        return self.as_style()

    def as_style(
        self,
        bgcolor: Optional[RichColor] = None,
        bold: Optional[bool] = None,
        dim: Optional[bool] = None,
        italic: Optional[bool] = None,
        underline: Optional[bool] = None,
        blink: Optional[bool] = None,
        blink2: Optional[bool] = None,
        reverse: Optional[bool] = None,
        conceal: Optional[bool] = None,
        strike: Optional[bool] = None,
        underline2: Optional[bool] = None,
        frame: Optional[bool] = None,
        encircle: Optional[bool] = None,
        overline: Optional[bool] = None,
        link: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
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

        return Style(
            color=self.rich,
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

    @property
    def bg_style(self) -> Style:
        """The color as a background style.

        Returns:
            Style: The color as a background style.
        """
        return self.as_bg_style()

    def as_bg_style(
        self,
        color: Optional[RichColor] = None,
        bold: Optional[bool] = True,
        dim: Optional[bool] = None,
        italic: Optional[bool] = None,
        underline: Optional[bool] = None,
        blink: Optional[bool] = None,
        blink2: Optional[bool] = None,
        reverse: Optional[bool] = None,
        conceal: Optional[bool] = None,
        strike: Optional[bool] = None,
        underline2: Optional[bool] = None,
        frame: Optional[bool] = None,
        encircle: Optional[bool] = None,
        overline: Optional[bool] = None,
        link: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
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
            color = self.get_contrast()
        return Style(
            color=color,
            bgcolor=self.rich,
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


    @property
    def hex(self) -> str:
        """Return the hex value of the color.

        Returns:
            str: The hex value of the color.
        """
        return self.as_hex("long")

    @property
    def rgb(self) -> str:
        """Return the RGB value of the color.

        Returns:
            str: The RGB value of the color."""
        return self.as_rgb()

    @property
    def triplet(self) -> ColorTriplet:
        """The `rich.color_triplet.ColorTriplet` representation of the color."""
        return self.as_triplet()

    def as_triplet(self) -> ColorTriplet:
        """Convert the color to a `rich.color_triplet.ColorTriplet`.

        Returns:
            ColorTriplet: The color as a color triplet.
        """
        red = int(self._rgba.r * 255)
        green = int(self._rgba.g * 255)
        blue = int(self._rgba.b * 255)
        return ColorTriplet(red, green, blue)

    def get_contrast(self) -> RichColor:
        """Generate a foreground color for the color style.

        Generate a foreground color for the color style based on the color's
        contrast ratio. If the color is dark, the foreground color will be
        white. If the color is light, the foreground color will be black.

        Returns:
            str: The foreground color.
        """
        import colorsys

        def rgb_to_hsv(color: Color) -> Tuple[float, float, float]:
            """Convert an RGB color to HSV.

            Args:
                color (Color): The color to convert.

            Returns:
                Tuple[float, float, float]: The HSV values.
            """
            rgba: RGBA = color._rgba
            h, s, v = colorsys.rgb_to_hsv(r=rgba.r, g=rgba.g, b=rgba.b)
            return h, s, v

        def hsv_to_hsl(hue, saturation, value) -> Tuple[float, float, float]:
            """Convert an HSV color to HSL.

            Args:
                hue (float): The hue value.
                saturation (float): The saturation value.
                value (float): The value value.

            Returns:
                Tuple[float, float, float]: The HSL values.
            """
            lightness = (
                (2 - saturation) * value / 2
                if value <= 0.5
                else saturation * value / (2 - saturation)
            )
            saturation = (
                0
                if lightness == 0 or lightness == 1
                else (value - lightness) / min(lightness, 1 - lightness)
            )
            return hue, saturation, lightness

        def color_distance(color1: Color, color2: Color) -> float:
            """Calculate the distance between two colors.

            Args:
                color1 (Color): The first color.
                color2 (Color): The second color.

            Returns:
                float: The distance between the two colors.
            """
            h1, s1, v1 = rgb_to_hsv(color1)
            h2, s2, v2 = rgb_to_hsv(color2)
            dh: float = min(abs(h1 - h2), 1 - abs(h1 - h2))
            ds: float = abs(s1 - s2)
            dv: float = abs(v1 - v2)
            color_distance: float = dh + ds + dv
            return color_distance

        def find_closest_color(color1: Color, color_list: List[Color]) -> Color:
            """Calculate the closest color in a list.

            Args:
                color1 (Color): The color to compare.
                color_list (List[Color]): The list of colors to compare against.

            Returns:
                Color: The closest color.
            """
            closest_color = None
            min_distance = float("inf")
            for color in color_list:
                distance = color_distance(color1, color)
                if distance < min_distance:
                    min_distance = distance
                    closest_color = color
            assert closest_color is not None, "No closest color found."
            return closest_color

        color_list: List[Color] = [Color("#000000"), Color("#ffffff")]
        closest = find_closest_color(
            self,
            color_list=color_list,
        )
        if closest == Color("#000000"):
            return Color("#ffffff").rich
        else:
            return Color("#000000").rich

    @classmethod
    def colortitle(cls, title: str) -> Text:
        """Manually color a title.

        Args:
            title (str): The title to style.

        Returns:
            Text: The styled title.
        """
        title_list: List[str] = list(title)
        length = len(title)
        COLORS = cycle(
            [
                "#FF00FF",
                "#AF00FF",
                "#5F00FF",
                "#0000FF",
                "#0055FF",
                "#0080FF",
                "#00C0FF",
                "#00FFFF",
                "#00FFAF",
                "#00FF00",
                "#AFFF00",
                "#FFFF00",
                "#FFAF00",
                "#FF8700",
                "#FF4B00",
                "#FF0000",
                "#FF005F",
            ]
        )
        color_title = Text()
        # randomize
        for _ in range(randint(0, 16)):
            next(COLORS)
        for index in range(length):
            char: str = title_list[index]
            color: str = next(COLORS)
            color_title.append(Text(char, style=f"bold {color}"))
        return color_title

    @classmethod
    def generate_table(
        cls, title: str, show_index: bool = True, caption: Optional[Text] = None
    ) -> Table:
        """
        Generate a table to display colors.

        Args:
            title: The title for the table.
            show_index: Whether to show the index column.

        Returns:
            A `rich.table.Table` instance.
        """
        color_title = cls.colortitle(title)
        table = Table(
            title=color_title, expand=False, caption=caption, caption_justify="right"
        )
        if show_index:
            table.add_column(cls.colortitle("Index"), style="bold", justify="right")
        table.add_column(cls.colortitle("Sample"), style="bold", justify="center")
        table.add_column(cls.colortitle("Name"), style="bold", justify="left")
        table.add_column(cls.colortitle("Hex"), style="bold", justify="left")
        table.add_column(cls.colortitle("RGB"), style="bold", justify="left")
        return table

    @classmethod
    def color_table(
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
        table = cls.generate_table(title, show_index, caption)
        for index, (key, _) in enumerate(cls.COLORS_BY_NAME.items()):
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
            r, g, b = color._rgba.r, color._rgba.g, color._rgba.b
            r_int = int(r * 255)
            g_int = int(g * 255)
            b_int = int(b * 255)
            rgb = Text.assemble(
                *[
                    Text("rgb", style=color.as_style(bold=True)),
                    Text("(", style="b #ffffff"),
                    Text(f"{r_int: >3}", style="b #ff0000"),
                    Text(",", style="b #ffffff"),
                    Text(f"{g_int: >3}", style="b #00ff00"),
                    Text(",", style="b #ffffff"),
                    Text(f"{b_int: >3}", style="b #0099ff"),
                    Text(")", style="b #ffffff"),
                ]
            )
            if show_index:
                table.add_row(color_index, sample, name, hex, rgb)
            else:
                table.add_row(sample, name, hex, rgb)
        return table

    @classmethod
    def example(cls, record: bool = False) -> None:
        """Generate a example of the color class.

        Args:
            record (bool): Whether to record the example as an svg.
        """

        from rich_gradient.theme import GRADIENT_TERMINAL_THEME

        console = Console(record=True, width=80) if record else Console()

        def table_generator() -> Generator:
            """Generate the tables for the example."""
            tables: List[Tuple[str, int, int, Optional[Text]]] = [
                (
                    "Gradient Colors",
                    0,
                    17,
                    Text(
                        "These colors have been adapted to make naming easier.",
                        style="i d #ffffff",
                    ),
                ),
                ("CSS3 Colors", 18, 147, None),
                ("Rich Colors", 148, 342, None),
            ]
            for table in tables:
                yield table

        for title, start, end, caption in table_generator():
            console.line(2)
            table = cls.color_table(title, start, end, caption=caption)
            console.print(table, justify="center")
            console.line(2)

        if record:
            try:
                console.save_svg(
                    "docs/img/colors.svg", theme=GRADIENT_TERMINAL_THEME, title="Colors"
                )
            except TypeError:
                pass


    COLORS_BY_NAME: Dict[str, Tuple[int, int, int]] = {
        "magenta": (255, 0, 255), #               # rgb(255, 0, 255)
        "purple": (175, 0, 255), #                # rgb(175, 0, 255)
        "violet": (95, 0, 255), #                 # rgb(95, 0, 255)
        "blue": (0, 0, 255), #                    # rgb(0, 0, 255)
        "dodgerblue": (0, 85, 255), #             # rgb(0, 85, 255)
        "skyblue": (0, 135, 255), #               # rgb(0, 135, 255)
        "lightskyblue": (0, 195, 255), #          # rgb(0, 195, 255)
        "cyan": (0, 255, 255), #                  # rgb(0, 255, 255)
        "aquamarine": (127, 255, 212), #          # rgb(127, 255, 212)
        "lime": (0, 255, 0), #                    # rgb(0, 255, 0)
        "lawngreen": (124, 255, 0), #             # rgb(124, 255, 0)
        "yellow": (255, 255, 0), #                # rgb(255, 255, 0)
        "orange": (255, 175, 0), #                # rgb(255, 175, 0)
        "darkorange": (255, 135, 0), #            # rgb(255, 135, 0)
        "tomato": (255, 75, 0), #                 # rgb(255, 75, 0)
        "red": (255, 0, 0), #                     # rgb(255, 0, 0)
        "deeppink": (255, 0, 95), #               # rgb(255, 0, 95)
        "hotpink": (255, 0, 175), #               # rgb(255, 0, 175)
        "aliceblue": (240, 248, 255), #           # rgb(240, 248, 255)
        "antiquewhite": (250, 235, 215), #        # rgb(250, 235, 215)
        "azure": (240, 255, 255), #               # rgb(240, 255, 255)
        "beige": (245, 245, 220), #               # rgb(245, 245, 220)
        "bisque": (255, 228, 196), #              # rgb(255, 228, 196)
        "black": (0, 0, 0), #                     # rgb(0, 0, 0)
        "blanchedalmond": (255, 235, 205), #      # rgb(255, 235, 205)
        "brown": (165, 42, 42), #                 # rgb(165, 42, 42)
        "burlywood": (222, 184, 135), #           # rgb(222, 184, 135)
        "cadetblue": (95, 158, 160), #            # rgb(95, 158, 160)
        "chartreuse": (127, 255, 0), #            # rgb(127, 255, 0)
        "chocolate": (210, 105, 30), #            # rgb(210, 105, 30)
        "coral": (255, 127, 80), #                # rgb(255, 127, 80)
        "cornflowerblue": (100, 149, 237), #      # rgb(100, 149, 237)
        "cornsilk": (255, 248, 220), #            # rgb(255, 248, 220)
        "crimson": (220, 20, 60), #               # rgb(220, 20, 60)
        "darkblue": (0, 0, 139), #                # rgb(0, 0, 139)
        "darkcyan": (0, 139, 139), #              # rgb(0, 139, 139)
        "darkgoldenrod": (184, 134, 11), #        # rgb(184, 134, 11)
        "darkgray": (169, 169, 169), #            # rgb(169, 169, 169)
        "darkgreen": (0, 100, 0), #               # rgb(0, 100, 0)
        "darkgrey": (169, 169, 169), #            # rgb(169, 169, 169)
        "darkkhaki": (189, 183, 107), #           # rgb(189, 183, 107)
        "darkmagenta": (139, 0, 139), #           # rgb(139, 0, 139)
        "darkolivegreen": (85, 107, 47), #        # rgb(85, 107, 47)
        "darkorange_css": (255, 140, 0), #        # rgb(255, 140, 0)
        "darkorchid": (153, 50, 204), #           # rgb(153, 50, 204)
        "darkred": (139, 0, 0), #                 # rgb(139, 0, 0)
        "darksalmon": (233, 150, 122), #          # rgb(233, 150, 122)
        "darkseagreen": (143, 188, 143), #        # rgb(143, 188, 143)
        "darkslateblue": (72, 61, 139), #         # rgb(72, 61, 139)
        "darkslategray": (47, 79, 79), #          # rgb(47, 79, 79)
        "darkslategrey": (47, 79, 79), #          # rgb(47, 79, 79)
        "darkturquoise": (0, 206, 209), #         # rgb(0, 206, 209)
        "darkviolet": (148, 0, 211), #            # rgb(148, 0, 211)
        "skyblue_css": (0, 191, 255), #             # rgb(0, 191, 255)
        "dimgray": (105, 105, 105), #             # rgb(105, 105, 105)
        "dimgrey": (105, 105, 105), #             # rgb(105, 105, 105)
        "dodgerblue_css": (30, 144, 255), #         # rgb(30, 144, 255)
        "firebrick": (178, 34, 34), #             # rgb(178, 34, 34)
        "floralwhite": (255, 250, 240), #         # rgb(255, 250, 240)
        "forestgreen": (34, 139, 34), #           # rgb(34, 139, 34)
        "gainsboro": (220, 220, 220), #           # rgb(220, 220, 220)
        "ghostwhite": (248, 248, 255), #          # rgb(248, 248, 255)
        "gold": (255, 215, 0), #                  # rgb(255, 215, 0)
        "goldenrod": (218, 165, 32), #            # rgb(218, 165, 32)
        "gray": (128, 128, 128), #                # rgb(128, 128, 128)
        "green": (0, 128, 0), #                   # rgb(0, 128, 0)
        "greenyellow": (173, 255, 47), #          # rgb(173, 255, 47)
        "grey": (128, 128, 128), #                # rgb(128, 128, 128)
        "honeydew": (240, 255, 240), #            # rgb(240, 255, 240)
        "hotpink_css": (255, 105, 180), #           # rgb(255, 105, 180)
        "indianred": (205, 92, 92), #             # rgb(205, 92, 92)
        "indigo": (75, 0, 130), #                 # rgb(75, 0, 130)
        "ivory": (255, 255, 240), #               # rgb(255, 255, 240)
        "khaki": (240, 230, 140), #               # rgb(240, 230, 140)
        "lavender": (230, 230, 250), #            # rgb(230, 230, 250)
        "lavenderblush": (255, 240, 245), #       # rgb(255, 240, 245)
        "lawngreen_css": (124, 252, 0), #           # rgb(124, 252, 0)
        "lemonchiffon": (255, 250, 205), #        # rgb(255, 250, 205)
        "lightblue": (173, 216, 230), #           # rgb(173, 216, 230)
        "lightcoral": (240, 128, 128), #          # rgb(240, 128, 128)
        "lightcyan": (224, 255, 255), #           # rgb(224, 255, 255)
        "lightgoldenrodyellow": (250, 250, 210), ## rgb(250, 250, 210)
        "lightgray": (211, 211, 211), #           # rgb(211, 211, 211)
        "lightgreen": (144, 238, 144), #          # rgb(144, 238, 144)
        "lightgrey": (211, 211, 211), #           # rgb(211, 211, 211)
        "lightpink": (255, 182, 193), #           # rgb(255, 182, 193)
        "lightsalmon": (255, 160, 122), #         # rgb(255, 160, 122)
        "lightseagreen": (32, 178, 170), #        # rgb(32, 178, 170)
        "lightskyblue_css": (135, 206, 250), #      # rgb(135, 206, 250)
        "lightslategray": (119, 136, 153), #      # rgb(119, 136, 153)
        "lightslategrey": (119, 136, 153), #      # rgb(119, 136, 153)
        "lightsteelblue": (176, 196, 222), #      # rgb(176, 196, 222)
        "lightyellow": (255, 255, 224), #         # rgb(255, 255, 224)
        "limegreen": (50, 205, 50), #             # rgb(50, 205, 50)
        "linen": (250, 240, 230), #               # rgb(250, 240, 230)
        "maroon": (128, 0, 0), #                  # rgb(128, 0, 0)
        "mediumaquamarine": (102, 205, 170), #    # rgb(102, 205, 170)
        "mediumblue": (0, 0, 205), #              # rgb(0, 0, 205)
        "mediumorchid": (186, 85, 211), #         # rgb(186, 85, 211)
        "mediumpurple": (147, 112, 219), #        # rgb(147, 112, 219)
        "mediumseagreen": (60, 179, 113), #       # rgb(60, 179, 113)
        "mediumslateblue": (123, 104, 238), #     # rgb(123, 104, 238)
        "mediumspringgreen": (0, 250, 154), #     # rgb(0, 250, 154)
        "mediumturquoise": (72, 209, 204), #      # rgb(72, 209, 204)
        "mediumvioletred": (199, 21, 133), #      # rgb(199, 21, 133)
        "midnightblue": (25, 25, 112), #          # rgb(25, 25, 112)
        "mintcream": (245, 255, 250), #           # rgb(245, 255, 250)
        "mistyrose": (255, 228, 225), #           # rgb(255, 228, 225)
        "moccasin": (255, 228, 181), #            # rgb(255, 228, 181)
        "navajowhite": (255, 222, 173), #         # rgb(255, 222, 173)
        "navy": (0, 0, 128), #                    # rgb(0, 0, 128)
        "oldlace": (253, 245, 230), #             # rgb(253, 245, 230)
        "olive": (128, 128, 0), #                 # rgb(128, 128, 0)
        "olivedrab": (107, 142, 35), #            # rgb(107, 142, 35)
        "orchid": (218, 112, 214), #              # rgb(218, 112, 214)
        "palegoldenrod": (238, 232, 170), #       # rgb(238, 232, 170)
        "palegreen": (152, 251, 152), #           # rgb(152, 251, 152)
        "paleturquoise": (175, 238, 238), #       # rgb(175, 238, 238)
        "palevioletred": (219, 112, 147), #       # rgb(219, 112, 147)
        "papayawhip": (255, 239, 213), #          # rgb(255, 239, 213)
        "peachpuff": (255, 218, 185), #           # rgb(255, 218, 185)
        "peru": (205, 133, 63), #                 # rgb(205, 133, 63)
        "pink": (255, 192, 203), #                # rgb(255, 192, 203)
        "plum": (221, 160, 221), #                # rgb(221, 160, 221)
        "powderblue": (176, 224, 230), #          # rgb(176, 224, 230)
        "rosybrown": (188, 143, 143), #           # rgb(188, 143, 143)
        "royalblue": (65, 105, 225), #            # rgb(65, 105, 225)
        "saddlebrown": (139, 69, 19), #           # rgb(139, 69, 19)
        "salmon": (250, 128, 114), #              # rgb(250, 128, 114)
        "sandybrown": (244, 164, 96), #           # rgb(244, 164, 96)
        "seagreen": (46, 139, 87), #              # rgb(46, 139, 87)
        "seashell": (255, 245, 238), #            # rgb(255, 245, 238)
        "sienna": (160, 82, 45), #                # rgb(160, 82, 45)
        "silver": (192, 192, 192), #              # rgb(192, 192, 192)
        "slateblue": (106, 90, 205), #            # rgb(106, 90, 205)
        "slategray": (112, 128, 144), #           # rgb(112, 128, 144)
        "slategrey": (112, 128, 144), #           # rgb(112, 128, 144)
        "snow": (255, 250, 250), #                # rgb(255, 250, 250)
        "steelblue": (70, 130, 180), #            # rgb(70, 130, 180)
        "tan": (210, 180, 140), #                 # rgb(210, 180, 140)
        "teal": (0, 128, 128), #                  # rgb(0, 128, 128)
        "thistle": (216, 191, 216), #             # rgb(216, 191, 216)
        "tomato_css": (255, 99, 71), #              # rgb(255, 99, 71)
        "aqua": (64, 224, 208), #                 # rgb(64, 224, 208)
        "violet_css": (238, 130, 238), #            # rgb(238, 130, 238)
        "wheat": (245, 222, 179), #               # rgb(245, 222, 179)
        "white": (255, 255, 255), #               # rgb(255, 255, 255)
        "whitesmoke": (245, 245, 245), #          # rgb(245, 245, 245)
        "yellowgreen": (154, 205, 50), #          # rgb(154, 205, 50)
        "bright_black": (45, 45, 45), #             # rgb(45, 45, 45)
        "bright_red": (210, 0, 0), #                # rgb(210, 0, 0)
        "bright_green": (0, 210, 0), #              # rgb(0, 210, 0)
        "bright_yellow": (210, 210, 0), #           # rgb(210, 210, 0)
        "bright_blue": (0, 0, 210), #               # rgb(0, 0, 210)
        "bright_magenta": (210, 0, 210), #          # rgb(210, 0, 210)
        "bright_cyan": (0, 210, 210), #             # rgb(0, 210, 210)
        "bright_white": (210, 210, 210), #          # rgb(210, 210, 210)
        "grey0": (0, 0, 0), #                       # rgb(0, 0, 0)
        "navy_blue": (0, 0, 95), #                  # rgb(0, 0, 95)
        "dark_blue": (0, 0, 135), #                 # rgb(0, 0, 135)
        "blue3": (0, 0, 215), #                     # rgb(0, 0, 215)
        "dark_green": (0, 95, 0), #                 # rgb(0, 95, 0)
        "deep_sky_blue4": (0, 95, 175), #           # rgb(0, 95, 175)
        "dodger_blue3": (0, 95, 215), #             # rgb(0, 95, 215)
        "green4": (0, 135, 0), #                    # rgb(0, 135, 0)
        "spring_green4": (0, 135, 95), #            # rgb(0, 135, 95)
        "turquoise4": (0, 135, 135), #              # rgb(0, 135, 135)
        "deep_sky_blue3": (0, 135, 215), #          # rgb(0, 135, 215)
        "dark_cyan": (0, 175, 135), #               # rgb(0, 175, 135)
        "light_sea_green": (0, 175, 175), #         # rgb(0, 175, 175)
        "deep_sky_blue2": (0, 175, 215), #          # rgb(0, 175, 215)
        "green3": (0, 215, 0), #                    # rgb(0, 215, 0)
        "spring_green3": (0, 215, 95), #            # rgb(0, 215, 95)
        "cyan3": (0, 215, 175), #                   # rgb(0, 215, 175)
        "dark_turquoise": (0, 215, 215), #          # rgb(0, 215, 215)
        "turquoise2": (0, 215, 255), #              # rgb(0, 215, 255)
        "spring_green2": (0, 255, 95), #            # rgb(0, 255, 95)
        "cyan2": (0, 255, 215), #                   # rgb(0, 255, 215)
        "purple4": (95, 0, 175), #                  # rgb(95, 0, 175)
        "purple3": (95, 0, 215), #                  # rgb(95, 0, 215)
        "grey37": (95, 95, 95), #                   # rgb(95, 95, 95)
        "medium_purple4": (95, 95, 135), #          # rgb(95, 95, 135)
        "slate_blue3": (95, 95, 215), #             # rgb(95, 95, 215)
        "royal_blue1": (95, 95, 255), #             # rgb(95, 95, 255)
        "chartreuse4": (95, 135, 0), #              # rgb(95, 135, 0)
        "pale_turquoise4": (95, 135, 135), #        # rgb(95, 135, 135)
        "steel_blue": (95, 135, 175), #             # rgb(95, 135, 175)
        "steel_blue3": (95, 135, 215), #            # rgb(95, 135, 215)
        "cornflower_blue": (95, 135, 255), #        # rgb(95, 135, 255)
        "dark_sea_green4": (95, 175, 95), #         # rgb(95, 175, 95)
        "cadet_blue": (95, 175, 175), #             # rgb(95, 175, 175)
        "sky_blue3": (95, 175, 215), #              # rgb(95, 175, 215)
        "chartreuse3": (95, 215, 0), #              # rgb(95, 215, 0)
        "sea_green3": (95, 215, 135), #             # rgb(95, 215, 135)
        "aquamarine3": (95, 215, 175), #            # rgb(95, 215, 175)
        "medium_turquoise": (95, 215, 215), #       # rgb(95, 215, 215)
        "steel_blue1": (95, 215, 255), #            # rgb(95, 215, 255)
        "sea_green2": (95, 255, 95), #              # rgb(95, 255, 95)
        "sea_green1": (95, 255, 175), #             # rgb(95, 255, 175)
        "dark_slate_gray2": (95, 255, 255), #       # rgb(95, 255, 255)
        "dark_red": (135, 0, 0), #                  # rgb(135, 0, 0)
        "dark_magenta": (135, 0, 175), #            # rgb(135, 0, 175)
        "orange4": (135, 95, 0), #                  # rgb(135, 95, 0)
        "light_pink4": (135, 95, 95), #             # rgb(135, 95, 95)
        "plum4": (135, 95, 135), #                  # rgb(135, 95, 135)
        "medium_purple3": (135, 95, 215), #         # rgb(135, 95, 215)
        "slate_blue1": (135, 95, 255), #            # rgb(135, 95, 255)
        "wheat4": (135, 135, 95), #                 # rgb(135, 135, 95)
        "grey53": (135, 135, 135), #                # rgb(135, 135, 135)
        "light_slate_grey": (135, 135, 175), #      # rgb(135, 135, 175)
        "medium_purple": (135, 135, 215), #         # rgb(135, 135, 215)
        "light_slate_blue": (135, 135, 255), #      # rgb(135, 135, 255)
        "yellow4": (135, 175, 0), #                 # rgb(135, 175, 0)
        "dark_sea_green": (135, 175, 135), #        # rgb(135, 175, 135)
        "light_sky_blue3": (135, 175, 215), #       # rgb(135, 175, 215)
        "sky_blue2": (135, 175, 255), #             # rgb(135, 175, 255)
        "chartreuse2": (135, 215, 0), #             # rgb(135, 215, 0)
        "pale_green3": (135, 215, 135), #           # rgb(135, 215, 135)
        "dark_slate_gray3": (135, 215, 215), #      # rgb(135, 215, 215)
        "sky_blue1": (135, 215, 255), #             # rgb(135, 215, 255)
        "light_green": (135, 255, 135), #           # rgb(135, 255, 135)
        "aquamarine1": (135, 255, 215), #           # rgb(135, 255, 215)
        "dark_slate_gray1": (135, 255, 255), #      # rgb(135, 255, 255)
        "deep_pink4": (175, 0, 95), #               # rgb(175, 0, 95)
        "medium_violet_red": (175, 0, 135), #       # rgb(175, 0, 135)
        "dark_violet": (175, 0, 215), #             # rgb(175, 0, 215)
        "medium_orchid3": (175, 95, 175), #         # rgb(175, 95, 175)
        "medium_orchid": (175, 95, 215), #          # rgb(175, 95, 215)
        "dark_goldenrod": (175, 135, 0), #          # rgb(175, 135, 0)
        "rosy_brown": (175, 135, 135), #            # rgb(175, 135, 135)
        "grey63": (175, 135, 175), #                # rgb(175, 135, 175)
        "medium_purple2": (175, 135, 215), #        # rgb(175, 135, 215)
        "medium_purple1": (175, 135, 255), #        # rgb(175, 135, 255)
        "dark_khaki": (175, 175, 95), #             # rgb(175, 175, 95)
        "navajo_white3": (175, 175, 135), #         # rgb(175, 175, 135)
        "grey69": (175, 175, 175), #                # rgb(175, 175, 175)
        "light_steel_blue3": (175, 175, 215), #     # rgb(175, 175, 215)
        "light_steel_blue": (175, 175, 255), #      # rgb(175, 175, 255)
        "dark_olive_green3": (175, 215, 95), #      # rgb(175, 215, 95)
        "dark_sea_green3": (175, 215, 135), #       # rgb(175, 215, 135)
        "light_cyan3": (175, 215, 215), #           # rgb(175, 215, 215)
        "light_sky_blue1": (175, 215, 255), #       # rgb(175, 215, 255)
        "dark_olive_green2": (175, 255, 95), #      # rgb(175, 255, 95)
        "pale_green1": (175, 255, 135), #           # rgb(175, 255, 135)
        "dark_sea_green2": (175, 255, 175), #       # rgb(175, 255, 175)
        "pale_turquoise1": (175, 255, 255), #       # rgb(175, 255, 255)
        "red3": (215, 0, 0), #                      # rgb(215, 0, 0)
        "deep_pink3": (215, 0, 135), #              # rgb(215, 0, 135)
        "magenta3": (215, 0, 215), #                # rgb(215, 0, 215)
        "dark_orange3": (215, 95, 0), #             # rgb(215, 95, 0)
        "indian_red": (215, 95, 95), #              # rgb(215, 95, 95)
        "hot_pink3": (215, 95, 135), #              # rgb(215, 95, 135)
        "hot_pink2": (215, 95, 175), #              # rgb(215, 95, 175)
        "orange3": (215, 135, 0), #                 # rgb(215, 135, 0)
        "light_salmon3": (215, 135, 95), #          # rgb(215, 135, 95)
        "light_pink3": (215, 135, 135), #           # rgb(215, 135, 135)
        "pink3": (215, 135, 175), #                 # rgb(215, 135, 175)
        "plum3": (215, 135, 215), #                 # rgb(215, 135, 215)
        "gold3": (215, 175, 0), #                   # rgb(215, 175, 0)
        "light_goldenrod3": (215, 175, 95), #       # rgb(215, 175, 95)
        "misty_rose3": (215, 175, 175), #           # rgb(215, 175, 175)
        "thistle3": (215, 175, 215), #              # rgb(215, 175, 215)
        "plum2": (215, 175, 255), #                 # rgb(215, 175, 255)
        "yellow3": (215, 215, 0), #                 # rgb(215, 215, 0)
        "khaki3": (215, 215, 95), #                 # rgb(215, 215, 95)
        "light_yellow3": (215, 215, 175), #         # rgb(215, 215, 175)
        "grey84": (215, 215, 215), #                # rgb(215, 215, 215)
        "light_steel_blue1": (215, 215, 255), #     # rgb(215, 215, 255)
        "yellow2": (215, 255, 0), #                 # rgb(215, 255, 0)
        "dark_olive_green1": (215, 255, 135), #     # rgb(215, 255, 135)
        "dark_sea_green1": (215, 255, 175), #       # rgb(215, 255, 175)
        "honeydew2": (215, 255, 215), #             # rgb(215, 255, 215)
        "light_cyan1": (215, 255, 255), #           # rgb(215, 255, 255)
        "magenta2": (255, 0, 215), #                # rgb(255, 0, 215)
        "indian_red1": (255, 95, 135), #            # rgb(255, 95, 135)
        "hot_pink": (255, 95, 215), #               # rgb(255, 95, 215)
        "medium_orchid1": (255, 95, 255), #         # rgb(255, 95, 255)
        "dark_orange": (255, 135, 0), #             # rgb(255, 135, 0)
        "salmon1": (255, 135, 95), #                # rgb(255, 135, 95)
        "light_coral": (255, 135, 135), #           # rgb(255, 135, 135)
        "pale_violet_red1": (255, 135, 175), #      # rgb(255, 135, 175)
        "orchid2": (255, 135, 215), #               # rgb(255, 135, 215)
        "orchid1": (255, 135, 255), #               # rgb(255, 135, 255)
        "sandy_brown": (255, 175, 95), #            # rgb(255, 175, 95)
        "light_salmon1": (255, 175, 135), #         # rgb(255, 175, 135)
        "light_pink1": (255, 175, 175), #           # rgb(255, 175, 175)
        "pink1": (255, 175, 215), #                 # rgb(255, 175, 215)
        "plum1": (255, 175, 255), #                 # rgb(255, 175, 255)
        "gold1": (255, 215, 0), #                   # rgb(255, 215, 0)
        "light_goldenrod2": (255, 215, 135), #      # rgb(255, 215, 135)
        "navajo_white1": (255, 215, 175), #         # rgb(255, 215, 175)
        "misty_rose1": (255, 215, 215), #           # rgb(255, 215, 215)
        "thistle1": (255, 215, 255), #              # rgb(255, 215, 255)
        "light_goldenrod1": (255, 255, 95), #       # rgb(255, 255, 95)
        "khaki1": (255, 255, 135), #                # rgb(255, 255, 135)
        "wheat1": (255, 255, 175), #                # rgb(255, 255, 175)
        "cornsilk1": (255, 255, 215), #             # rgb(255, 255, 215)
        "grey100": (255, 255, 255), #               # rgb(255, 255, 255)
        "grey3": (8, 8, 8), #                       # rgb(8, 8, 8)
        "grey7": (18, 18, 18), #                    # rgb(18, 18, 18)
        "grey11": (28, 28, 28), #                   # rgb(28, 28, 28)
        "grey15": (38, 38, 38), #                   # rgb(38, 38, 38)
        "grey19": (48, 48, 48), #                   # rgb(48, 48, 48)
        "grey23": (58, 58, 58), #                   # rgb(58, 58, 58)
        "grey27": (68, 68, 68), #                   # rgb(68, 68, 68)
        "grey30": (78, 78, 78), #                   # rgb(78, 78, 78)
        "grey35": (88, 88, 88), #                   # rgb(88, 88, 88)
        "grey39": (98, 98, 98), #                   # rgb(98, 98, 98)
        "grey42": (108, 108, 108), #                # rgb(108, 108, 108)
        "grey46": (118, 118, 118), #                # rgb(118, 118, 118)
        "grey50": (128, 128, 128), #                # rgb(128, 128, 128)
        "grey54": (138, 138, 138), #                # rgb(138, 138, 138)
        "grey58": (148, 148, 148), #                # rgb(148, 148, 148)
        "grey62": (158, 158, 158), #                # rgb(158, 158, 158)
        "grey66": (168, 168, 168), #                # rgb(168, 168, 168)
        "grey70": (178, 178, 178), #                # rgb(178, 178, 178)
        "grey74": (188, 188, 188), #                # rgb(188, 188, 188)
        "grey78": (198, 198, 198), #                # rgb(198, 198, 198)
        "grey82": (208, 208, 208), #                # rgb(208, 208, 208)
        "grey85": (218, 218, 218), #                # rgb(218, 218, 218)
        "grey89": (228, 228, 228), #                # rgb(228, 228, 228)
        "grey93": (238, 238, 238), #                # rgb(238, 238, 238)
    }

    COLORS_BY_VALUE = {v: k for k, v in COLORS_BY_NAME.items()}

    @classmethod
    def parse_tuple(cls, value: tuple[Any, ...]) -> RGBA:
        """Parse a tuple or list to get RGBA values.

        Args:
            value: A tuple or list.

        Returns:
            An `RGBA` tuple parsed from the input tuple.

        Raises:
            ColorError: If tuple is not valid.
        """
        if len(value) == 3:
            r, g, b = (cls.parse_color_value(v) for v in value)
            return RGBA(r, g, b, None)
        elif len(value) == 4:
            r, g, b = (cls.parse_color_value(v) for v in value[:3])
            return RGBA(r, g, b, cls.parse_float_alpha(value[3]))
        else:
            raise ColorError("value is not a valid color: tuples must have length 3 or 4")

    @classmethod
    def parse_str(cls, value: str) -> RGBA:
        """Parse a string representing a color to an RGBA tuple.

        Possible formats for the input string include:

        * named color, see `COLORS_BY_NAME`
        * hex short eg. `<prefix>fff` (prefix can be `#`, `0x` or nothing)
        * hex long eg. `<prefix>ffffff` (prefix can be `#`, `0x` or nothing)
        * `rgb(<r>, <g>, <b>)`
        * `rgba(<r>, <g>, <b>, <a>)`
        * `transparent`

        Args:
            value: A string representing a color.

        Returns:
            An `RGBA` tuple parsed from the input string.

        Raises:
            ValueError: If the input string cannot be parsed to an RGBA tuple.
        """
        value_lower = value.lower()
        if value_lower in cls.COLORS_BY_NAME:
            r, g, b = cls.COLORS_BY_NAME[value_lower]
            return cls.ints_to_rgba(r, g, b, None)

        m = re.fullmatch(r_hex_short, value_lower)
        if m:
            *rgb, a = m.groups()
            r, g, b = (int(v * 2, 16) for v in rgb)
            alpha = int(a * 2, 16) / 255 if a else None
            return cls.ints_to_rgba(r, g, b, alpha)

        m = re.fullmatch(r_hex_long, value_lower)
        if m:
            *rgb, a = m.groups()
            r, g, b = (int(v, 16) for v in rgb)
            alpha = int(a, 16) / 255 if a else None
            return cls.ints_to_rgba(r, g, b, alpha)

        m = re.fullmatch(r_rgb, value_lower) or re.fullmatch(r_rgb_v4_style, value_lower)
        if m:
            return cls.ints_to_rgba(*m.groups())  # type: ignore

        m = re.fullmatch(r_hsl, value_lower) or re.fullmatch(r_hsl_v4_style, value_lower)
        if m:
            return cls.parse_hsl(*m.groups())  # type: ignore

        if value_lower == "transparent":
            return RGBA(0, 0, 0, 0)

        raise ColorError(
            "value is not a valid color: string not recognised as a valid color"
        )

    @classmethod
    def ints_to_rgba(
        cls,
        r: int | str,
        g: int | str,
        b: int | str,
        alpha: float | None = None,
    ) -> RGBA:
        """Converts integer or string values for RGB color and an optional alpha value to an `RGBA` object.

        Args:
            r: An integer or string representing the red color value.
            g: An integer or string representing the green color value.
            b: An integer or string representing the blue color value.
            alpha: A float representing the alpha value. Defaults to None.

        Returns:
            An instance of the `RGBA` class with the corresponding color and alpha values.
        """
        return RGBA(
            cls.parse_color_value(r),
            cls.parse_color_value(g),
            cls.parse_color_value(b),
            cls.parse_float_alpha(alpha),
        )

    @staticmethod
    def parse_color_value(value: int | str, max_val: int = 255) -> float:
        """Parse the color value provided and return a number between 0 and 1.

        Args:
            value: An integer or string color value.
            max_val: Maximum range value. Defaults to 255.

        Raises:
            ColorError: If the value is not a valid color.

        Returns:
            A number between 0 and 1.
        """
        try:
            color = float(value)
        except ValueError as e:
            raise ColorError(
                "value is not a valid color: color values must be a valid number"
            ) from e
        if 0 <= color <= max_val:
            return color / max_val
        else:
            raise ColorError(
                "value is not a valid color: color values must be in the range 0 to {max_val}",
                {"max_val": max_val},
            )

    @staticmethod
    def parse_float_alpha(value: None | str | float | int) -> float | None:
        """Parse an alpha value checking it's a valid float in the range 0 to 1.

        Args:
            value: The input value to parse.

        Returns:
            The parsed value as a float, or `None` if the value was None or equal 1.

        Raises:
            ColorError: If the input value cannot be successfully parsed as a float in the expected range.
        """
        if value is None:
            return None
        try:
            if isinstance(value, str) and value.endswith("%"):
                alpha = float(value[:-1]) / 100
            else:
                alpha = float(value)
        except ValueError as e:
            raise ColorError(
                "value is not a valid color: alpha values must be a valid float",
            ) from e

        if math.isclose(alpha, 1):
            return None
        elif 0 <= alpha <= 1:
            return alpha
        else:
            raise ColorError(
                "value is not a valid color: alpha values must be in the range 0 to 1",
            )

    @classmethod
    def parse_hsl(
        cls, h: str, h_units: str, sat: str, light: str, alpha: float | None = None
    ) -> RGBA:
        """Parse raw hue, saturation, lightness, and alpha values and convert to RGBA.

        Args:
            h: The hue value.
            h_units: The unit for hue value.
            sat: The saturation value.
            light: The lightness value.
            alpha: Alpha value.

        Returns:
            An instance of `RGBA`.
        """
        s_value, l_value = cls.parse_color_value(sat, 100), cls.parse_color_value(light, 100)

        h_value = float(h)
        if h_units in {None, "deg"}:
            h_value = h_value % 360 / 360
        elif h_units == "rad":
            h_value = h_value % rads / rads
        else:
            # turns
            h_value %= 1

        r, g, b = hls_to_rgb(h_value, l_value, s_value)
        return RGBA(r, g, b, cls.parse_float_alpha(alpha))

    @staticmethod
    def float_to_255(c: float) -> int:
        """Converts a float value between 0 and 1 (inclusive) to an integer between 0 and 255 (inclusive).

        Args:
            c: The float value to be converted. Must be between 0 and 1 (inclusive).

        Returns:
            The integer equivalent of the given float value rounded to the nearest whole number.
        """
        return round(c * 255)



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
        console.print(f"[b {hex_color}]This text is [u]{user_input.capitalize()}[/u]![/]")
        console.line(2)
    except Exception as e:
        console.print(f"[b i red]Error:[/] {e}")

if __name__=="__main__":
    Color.example()
