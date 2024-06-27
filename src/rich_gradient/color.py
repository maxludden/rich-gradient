"""
The Color class provides a way to represent colors in a way that can be used in a terminal.

It heavily relies on the `pydantic` library for type checking and validation. It also uses the `rich` library for terminal styling and rendering. This
allow the user to specify colors in 3 or 6 digit hex format, RGB format, or by CSS3 color names in addition to the standard rich colors.

Color definitions are used as per the CSS3
[CSS Color Module Level 3](http://www.w3.org/TR/css3-color/#svg-color) specification.

A few colors have multiple names referring to the sames colors, eg. `grey` and `gray` or `aqua` and `cyan`.

In these cases the _last_ color when sorted alphabetically takes preferences,
eg. `Color((0, 255, 255)).as_named() == 'cyan'` because "cyan" comes after "aqua".
"""

# ruff: noqa: F401
import math
import re
from itertools import cycle
from random import randint
from typing import Any, Dict, Generator, List, Optional, Tuple

from pydantic_extra_types.color import RGBA
from pydantic_extra_types.color import Color as PyColor
from pydantic_extra_types.color import ColorType as PyColorType
from pydantic_core import PydanticCustomError
from rich.color import Color as RichColor
from rich.color import ColorType as RichColorType
from rich.console import Console
from rich.style import Style
from rich.table import Table
from rich.text import Text
from rich.color_triplet import ColorTriplet

class ColorParsingError(Exception):
    pass

class Color(PyColor):
    """A color from which to generate a gradient."""

    def __init__(self, value: PyColorType) -> None:
        """Initialize a color.
        
        Args:
            value (pydantic_extra_types.color.ColorType): The color value.
        """
        try:
            if value in self.COLORS_BY_NAME:
                value = self.COLORS_BY_NAME[str(value)]
        except PydanticCustomError:
            raise ColorParsingError(f"Unable to parse color: {value}")
        super().__init__(value)

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
        except PydanticCustomError:
            raise ColorParsingError(f"Unable to parse color: {self}")

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
        """The `rich.color_triplet.ColorTriplet` respresentation of the color."""
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
                    "docs/img/colors.svg",
                    theme=GRADIENT_TERMINAL_THEME,
                    title="Colors"
                    )
            except TypeError:
                pass

    COLORS_BY_NAME: Dict[str, Tuple[int, int, int]] = {
        "magenta": (255, 0, 255),
        "purple": (175, 0, 255),
        "violet": (95, 0, 255),
        "blue": (0, 0, 255),
        "dodgerblue": (0, 85, 255),
        "deepskyblue": (0, 135, 255),
        "lightskyblue": (0, 195, 255),
        "cyan": (0, 255, 255),
        "springgreen": (0, 255, 175),
        "lime": (0, 255, 0),
        "greenyellow": (175, 255, 0),
        "yellow": (255, 255, 0),
        "orange": (255, 175, 0),
        "darkorange": (255, 135, 0),
        "tomato": (255, 75, 0),
        "red": (255, 0, 0),
        "deeppink": (255, 0, 95),
        "hotpink": (255, 0, 175),
        "aliceblue": (240, 248, 255),
        "antiquewhite": (250, 235, 215),
        "aquamarine": (127, 255, 212),
        "azure": (240, 255, 255),
        "beige": (245, 245, 220),
        "bisque": (255, 228, 196),
        "black": (0, 0, 0),
        "blanchedalmond": (255, 235, 205),
        "brown": (165, 42, 42),
        "burlywood": (222, 184, 135),
        "cadetblue": (95, 158, 160),
        "chartreuse": (127, 255, 0),
        "chocolate": (210, 105, 30),
        "coral": (255, 127, 80),
        "cornflowerblue": (100, 149, 237),
        "cornsilk": (255, 248, 220),
        "crimson": (220, 20, 60),
        "darkblue": (0, 0, 139),
        "darkcyan": (0, 139, 139),
        "darkgoldenrod": (184, 134, 11),
        "darkgray": (169, 169, 169),
        "darkgreen": (0, 100, 0),
        "darkgrey": (169, 169, 169),
        "darkkhaki": (189, 183, 107),
        "darkmagenta": (139, 0, 139),
        "darkolivegreen": (85, 107, 47),
        # "cssdarkorange": (255, 140, 0),
        "darkorchid": (153, 50, 204),
        "darkred": (139, 0, 0),
        "darksalmon": (233, 150, 122),
        "darkseagreen": (143, 188, 143),
        "darkslateblue": (72, 61, 139),
        "darkslategray": (47, 79, 79),
        "darkslategrey": (47, 79, 79),
        "darkturquoise": (0, 206, 209),
        "darkviolet": (148, 0, 211),
        # "deepskyblue_css": (0, 191, 255),
        "dimgray": (105, 105, 105),
        "dimgrey": (105, 105, 105),
        # "dodgerblue_css": (30, 144, 255),
        "firebrick": (178, 34, 34),
        "floralwhite": (255, 250, 240),
        "forestgreen": (34, 139, 34),
        "gainsboro": (220, 220, 220),
        "ghostwhite": (248, 248, 255),
        "gold": (255, 215, 0),
        "goldenrod": (218, 165, 32),
        "gray": (128, 128, 128),
        "green": (0, 128, 0),
        # "greenyellow_css": (173, 255, 47),
        "grey": (128, 128, 128),
        "honeydew": (240, 255, 240),
        # "hotpink_css": (255, 105, 180),
        "indianred": (205, 92, 92),
        "indigo": (75, 0, 130),
        "ivory": (255, 255, 240),
        "khaki": (240, 230, 140),
        "lavender": (230, 230, 250),
        "lavenderblush": (255, 240, 245),
        "lawngreen": (124, 252, 0),
        "lemonchiffon": (255, 250, 205),
        "lightblue": (173, 216, 230),
        "lightcoral": (240, 128, 128),
        "lightcyan": (224, 255, 255),
        "lightgoldenrodyellow": (250, 250, 210),
        "lightgray": (211, 211, 211),
        "lightgreen": (144, 238, 144),
        "lightgrey": (211, 211, 211),
        "lightpink": (255, 182, 193),
        "lightsalmon": (255, 160, 122),
        "lightseagreen": (32, 178, 170),
        # "lightskyblue_css": (135, 206, 250),
        "lightslategray": (119, 136, 153),
        "lightslategrey": (119, 136, 153),
        "lightsteelblue": (176, 196, 222),
        "lightyellow": (255, 255, 224),
        "limegreen": (50, 205, 50),
        "linen": (250, 240, 230),
        "maroon": (128, 0, 0),
        "mediumaquamarine": (102, 205, 170),
        "mediumblue": (0, 0, 205),
        "mediumorchid": (186, 85, 211),
        "mediumpurple": (147, 112, 219),
        "mediumseagreen": (60, 179, 113),
        "mediumslateblue": (123, 104, 238),
        "mediumspringgreen": (0, 250, 154),
        "mediumturquoise": (72, 209, 204),
        "mediumvioletred": (199, 21, 133),
        "midnightblue": (25, 25, 112),
        "mintcream": (245, 255, 250),
        "mistyrose": (255, 228, 225),
        "moccasin": (255, 228, 181),
        "navajowhite": (255, 222, 173),
        "navy": (0, 0, 128),
        "oldlace": (253, 245, 230),
        "olive": (128, 128, 0),
        "olivedrab": (107, 142, 35),
        "orchid": (218, 112, 214),
        "palegoldenrod": (238, 232, 170),
        "palegreen": (152, 251, 152),
        "paleturquoise": (175, 238, 238),
        "palevioletred": (219, 112, 147),
        "papayawhip": (255, 239, 213),
        "peachpuff": (255, 218, 185),
        "peru": (205, 133, 63),
        "pink": (255, 192, 203),
        "plum": (221, 160, 221),
        "powderblue": (176, 224, 230),
        "rosybrown": (188, 143, 143),
        "royalblue": (65, 105, 225),
        "saddlebrown": (139, 69, 19),
        "salmon": (250, 128, 114),
        "sandybrown": (244, 164, 96),
        "seagreen": (46, 139, 87),
        "seashell": (255, 245, 238),
        "sienna": (160, 82, 45),
        "silver": (192, 192, 192),
        "slateblue": (106, 90, 205),
        "slategray": (112, 128, 144),
        "slategrey": (112, 128, 144),
        "snow": (255, 250, 250),
        "steelblue": (70, 130, 180),
        "tan": (210, 180, 140),
        "teal": (0, 128, 128),
        "thistle": (216, 191, 216),
        # "csstomato": (255, 99, 71),
        "turquoise": (64, 224, 208),
        # "violet_css": (238, 130, 238),
        "wheat": (245, 222, 179),
        "white": (255, 255, 255),
        "whitesmoke": (245, 245, 245),
        "yellowgreen": (154, 205, 50),
        "bright_black": (45, 45, 45),
        "bright_red": (210, 0, 0),
        "bright_green": (0, 210, 0),
        "bright_yellow": (210, 210, 0),
        "bright_blue": (0, 0, 210),
        "bright_magenta": (210, 0, 210),
        "bright_cyan": (0, 210, 210),
        "bright_white": (210, 210, 210),
        "grey0": (0, 0, 0),
        "navy_blue": (0, 0, 95),
        "dark_blue": (0, 0, 135),
        "blue3": (0, 0, 215),
        "dark_green": (0, 95, 0),
        "deep_sky_blue4": (0, 95, 175),
        "dodger_blue3": (0, 95, 215),
        "green4": (0, 135, 0),
        "spring_green4": (0, 135, 95),
        "turquoise4": (0, 135, 135),
        "deep_sky_blue3": (0, 135, 215),
        "dark_cyan": (0, 175, 135),
        "light_sea_green": (0, 175, 175),
        "deep_sky_blue2": (0, 175, 215),
        "green3": (0, 215, 0),
        "spring_green3": (0, 215, 95),
        "cyan3": (0, 215, 175),
        "dark_turquoise": (0, 215, 215),
        "turquoise2": (0, 215, 255),
        "spring_green2": (0, 255, 95),
        "cyan2": (0, 255, 215),
        "purple4": (95, 0, 175),
        "purple3": (95, 0, 215),
        "grey37": (95, 95, 95),
        "medium_purple4": (95, 95, 135),
        "slate_blue3": (95, 95, 215),
        "royal_blue1": (95, 95, 255),
        "chartreuse4": (95, 135, 0),
        "pale_turquoise4": (95, 135, 135),
        "steel_blue": (95, 135, 175),
        "steel_blue3": (95, 135, 215),
        "cornflower_blue": (95, 135, 255),
        "dark_sea_green4": (95, 175, 95),
        "cadet_blue": (95, 175, 175),
        "sky_blue3": (95, 175, 215),
        "chartreuse3": (95, 215, 0),
        "sea_green3": (95, 215, 135),
        "aquamarine3": (95, 215, 175),
        "medium_turquoise": (95, 215, 215),
        "steel_blue1": (95, 215, 255),
        "sea_green2": (95, 255, 95),
        "sea_green1": (95, 255, 175),
        "dark_slate_gray2": (95, 255, 255),
        "dark_red": (135, 0, 0),
        "dark_magenta": (135, 0, 175),
        "orange4": (135, 95, 0),
        "light_pink4": (135, 95, 95),
        "plum4": (135, 95, 135),
        "medium_purple3": (135, 95, 215),
        "slate_blue1": (135, 95, 255),
        "wheat4": (135, 135, 95),
        "grey53": (135, 135, 135),
        "light_slate_grey": (135, 135, 175),
        "medium_purple": (135, 135, 215),
        "light_slate_blue": (135, 135, 255),
        "yellow4": (135, 175, 0),
        "dark_sea_green": (135, 175, 135),
        "light_sky_blue3": (135, 175, 215),
        "sky_blue2": (135, 175, 255),
        "chartreuse2": (135, 215, 0),
        "pale_green3": (135, 215, 135),
        "dark_slate_gray3": (135, 215, 215),
        "sky_blue1": (135, 215, 255),
        "light_green": (135, 255, 135),
        "aquamarine1": (135, 255, 215),
        "dark_slate_gray1": (135, 255, 255),
        "deep_pink4": (175, 0, 95),
        "medium_violet_red": (175, 0, 135),
        "dark_violet": (175, 0, 215),
        "medium_orchid3": (175, 95, 175),
        "medium_orchid": (175, 95, 215),
        "dark_goldenrod": (175, 135, 0),
        "rosy_brown": (175, 135, 135),
        "grey63": (175, 135, 175),
        "medium_purple2": (175, 135, 215),
        "medium_purple1": (175, 135, 255),
        "dark_khaki": (175, 175, 95),
        "navajo_white3": (175, 175, 135),
        "grey69": (175, 175, 175),
        "light_steel_blue3": (175, 175, 215),
        "light_steel_blue": (175, 175, 255),
        "dark_olive_green3": (175, 215, 95),
        "dark_sea_green3": (175, 215, 135),
        "light_cyan3": (175, 215, 215),
        "light_sky_blue1": (175, 215, 255),
        "dark_olive_green2": (175, 255, 95),
        "pale_green1": (175, 255, 135),
        "dark_sea_green2": (175, 255, 175),
        "pale_turquoise1": (175, 255, 255),
        "red3": (215, 0, 0),
        "deep_pink3": (215, 0, 135),
        "magenta3": (215, 0, 215),
        "dark_orange3": (215, 95, 0),
        "indian_red": (215, 95, 95),
        "hot_pink3": (215, 95, 135),
        "hot_pink2": (215, 95, 175),
        "orange3": (215, 135, 0),
        "light_salmon3": (215, 135, 95),
        "light_pink3": (215, 135, 135),
        "pink3": (215, 135, 175),
        "plum3": (215, 135, 215),
        "gold3": (215, 175, 0),
        "light_goldenrod3": (215, 175, 95),
        "misty_rose3": (215, 175, 175),
        "thistle3": (215, 175, 215),
        "plum2": (215, 175, 255),
        "yellow3": (215, 215, 0),
        "khaki3": (215, 215, 95),
        "light_yellow3": (215, 215, 175),
        "grey84": (215, 215, 215),
        "light_steel_blue1": (215, 215, 255),
        "yellow2": (215, 255, 0),
        "dark_olive_green1": (215, 255, 135),
        "dark_sea_green1": (215, 255, 175),
        "honeydew2": (215, 255, 215),
        "light_cyan1": (215, 255, 255),
        "magenta2": (255, 0, 215),
        "indian_red1": (255, 95, 135),
        "hot_pink": (255, 95, 215),
        "medium_orchid1": (255, 95, 255),
        "dark_orange": (255, 135, 0),
        "salmon1": (255, 135, 95),
        "light_coral": (255, 135, 135),
        "pale_violet_red1": (255, 135, 175),
        "orchid2": (255, 135, 215),
        "orchid1": (255, 135, 255),
        "sandy_brown": (255, 175, 95),
        "light_salmon1": (255, 175, 135),
        "light_pink1": (255, 175, 175),
        "pink1": (255, 175, 215),
        "plum1": (255, 175, 255),
        "gold1": (255, 215, 0),
        "light_goldenrod2": (255, 215, 135),
        "navajo_white1": (255, 215, 175),
        "misty_rose1": (255, 215, 215),
        "thistle1": (255, 215, 255),
        "light_goldenrod1": (255, 255, 95),
        "khaki1": (255, 255, 135),
        "wheat1": (255, 255, 175),
        "cornsilk1": (255, 255, 215),
        "grey100": (255, 255, 255),
        "grey3": (8, 8, 8),
        "grey7": (18, 18, 18),
        "grey11": (28, 28, 28),
        "grey15": (38, 38, 38),
        "grey19": (48, 48, 48),
        "grey23": (58, 58, 58),
        "grey27": (68, 68, 68),
        "grey30": (78, 78, 78),
        "grey35": (88, 88, 88),
        "grey39": (98, 98, 98),
        "grey42": (108, 108, 108),
        "grey46": (118, 118, 118),
        "grey50": (128, 128, 128),
        "grey54": (138, 138, 138),
        "grey58": (148, 148, 148),
        "grey62": (158, 158, 158),
        "grey66": (168, 168, 168),
        "grey70": (178, 178, 178),
        "grey74": (188, 188, 188),
        "grey78": (198, 198, 198),
        "grey82": (208, 208, 208),
        "grey85": (218, 218, 218),
        "grey89": (228, 228, 228),
        "grey93": (238, 238, 238),
    }


COLORS_BY_VALUE = {v: k for k, v in Color.COLORS_BY_NAME.items()}


if __name__ == "__main__":  # pragma: no cover
    Color.example(record=True)
