import sys
from functools import lru_cache
from marshal import dumps, loads
from random import randint
from typing import Any, Dict, Iterable, List, Optional, Type, Union, cast

from cheap_repr import normal_repr, register_repr
from rich import errors, get_console
from rich.color import ColorParseError, ColorSystem, blend_rgb
from rich.color import Color as RichColor
from rich.console import Console
from rich.repr import Result, rich_repr
from rich.style import Style as RichStyle
from rich.terminal_theme import DEFAULT_TERMINAL_THEME, TerminalTheme
from snoop import snoop

from rich_gradient._colors import (
    COLORS_BY_ANSI,
    COLORS_BY_HEX,
    COLORS_BY_NAME,
    COLORS_BY_RGB,
)
from rich_gradient._rgb import RGBA
from rich_gradient.color import Color, ColorError

# Style instances and style definitions are often interchangeable
StyleType = Union[str, "Style"]


class _Bit:
    """A descriptor to get/set a style attribute bit."""

    __slots__ = ["bit"]

    def __init__(self, bit_no: int) -> None:
        self.bit = 1 << bit_no

    def __get__(self, obj: "Style", objtype: Type["Style"]) -> Optional[bool]:
        if obj._set_attributes & self.bit:
            return obj._attributes & self.bit != 0
        return None


@rich_repr
class Style():
    """A terminal style.

    A terminal style consists of a color (`color`), a background color (`bgcolor`), and a number of attributes, such
    as bold, italic etc. The attributes have 3 states: they can either be on
    (``True``), off (``False``), or not set (``None``).

    Args:
        color (Union[Color, str], optional): Color of terminal text. Defaults to None.
        bgcolor (Union[Color, str], optional): Color of terminal background. Defaults to None.
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
        link (str, optional): Link URL. Defaults to None.
        meta (Dict[str, Any], optional): Meta information. Defaults to None.
    """

    _color: Optional[Color]
    _bgcolor: Optional[Color]
    _attributes: int
    _set_attributes: int
    _hash: Optional[int]
    _null: bool
    _meta: Optional[bytes]

    __slots__ = [
        "_color",
        "_bgcolor",
        "_attributes",
        "_set_attributes",
        "_link",
        "_link_id",
        "_ansi",
        "_style_definition",
        "_hash",
        "_null",
        "_meta",
    ]

    # maps bits on to SGR parameter
    _style_map = {
        0: "1",
        1: "2",
        2: "3",
        3: "4",
        4: "5",
        5: "6",
        6: "7",
        7: "8",
        8: "9",
        9: "21",
        10: "51",
        11: "52",
        12: "53",
    }

    STYLE_ATTRIBUTES = {
        "dim": "dim",
        "d": "dim",
        "bold": "bold",
        "b": "bold",
        "italic": "italic",
        "i": "italic",
        "underline": "underline",
        "u": "underline",
        "blink": "blink",
        "blink2": "blink2",
        "reverse": "reverse",
        "r": "reverse",
        "conceal": "conceal",
        "c": "conceal",
        "strike": "strike",
        "s": "strike",
        "underline2": "underline2",
        "uu": "underline2",
        "frame": "frame",
        "encircle": "encircle",
        "overline": "overline",
        "o": "overline",
    }

    def __init__(
        self,
        *,
        color: Optional[Union[Color, str]] = None,
        bgcolor: Optional[Union[Color, str]] = None,
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
    ) -> None:
        """
        Initialize a Style instance.

        Args:
            color (Optional[Union[Color, str]]): Foreground color.
            bgcolor (Optional[Union[Color, str]]): Background color.
            bold (Optional[bool]): Bold attribute.
            dim (Optional[bool]): Dim attribute.
            italic (Optional[bool]): Italic attribute.
            underline (Optional[bool]): Underline attribute.
            blink (Optional[bool]): Blink attribute.
            blink2 (Optional[bool]): Fast blink attribute.
            reverse (Optional[bool]): Reverse attribute.
            conceal (Optional[bool]): Conceal attribute.
            strike (Optional[bool]): Strike attribute.
            underline2 (Optional[bool]): Double underline attribute.
            frame (Optional[bool]): Frame attribute.
            encircle (Optional[bool]): Encircle attribute.
            overline (Optional[bool]): Overline attribute.
            link (Optional[str]): Link URL.
            meta (Optional[Dict[str, Any]]): Meta information.
        """
        self._ansi: Optional[str] = None
        self._style_definition: Optional[str] = None

        def _make_color(color: Union[Color, str]) -> Color:
            # Accept Color instance, or a valid color string/hex/rgb/name
            if isinstance(color, Color):
                return color
            elif isinstance(color, str):
                # If the string looks like a Color repr, extract the hex part
                if color.startswith("Color("):
                    import re

                    match = re.search(r"'(#[0-9a-fA-F]{6})'", color)
                    if match:
                        return Color(match.group(1))
                    # fallback: try to extract hex from the string
                    hex_match = re.search(r"(#[0-9a-fA-F]{6})", color)
                    if hex_match:
                        return Color(hex_match.group(1))
                    # fallback: try to extract rgb
                    rgb_match = re.search(r"red=(\d+), green=(\d+), blue=(\d+)", color)
                    if rgb_match:
                        r, g, b = map(int, rgb_match.groups())
                        return Color((r, g, b))
                    # If all fails, raise error
                    raise ColorError(
                        f"Invalid color: {color!r}. Unable to parse string as color in Style._make_color()"
                    )
                try:
                    return Color(color)
                except ColorError as ce:
                    raise ColorError(
                        f"Invalid color: {color!r}. Unable to parse string as color in Style._make_color()"
                    ) from ce
            raise ColorError(f"Invalid color: {color!r}")

        self._color = None if color is None else _make_color(color)
        self._bgcolor = None if bgcolor is None else _make_color(bgcolor)
        self._set_attributes = sum(
            (
                bold is not None,
                dim is not None and 2,
                italic is not None and 4,
                underline is not None and 8,
                blink is not None and 16,
                blink2 is not None and 32,
                reverse is not None and 64,
                conceal is not None and 128,
                strike is not None and 256,
                underline2 is not None and 512,
                frame is not None and 1024,
                encircle is not None and 2048,
                overline is not None and 4096,
            )
        )
        self._attributes = (
            sum(
                (
                    bold and 1 or 0,
                    dim and 2 or 0,
                    italic and 4 or 0,
                    underline and 8 or 0,
                    blink and 16 or 0,
                    blink2 and 32 or 0,
                    reverse and 64 or 0,
                    conceal and 128 or 0,
                    strike and 256 or 0,
                    underline2 and 512 or 0,
                    frame and 1024 or 0,
                    encircle and 2048 or 0,
                    overline and 4096 or 0,
                )
            )
            if self._set_attributes
            else 0
        )

        self._link = link
        self._meta = None if meta is None else dumps(meta)
        self._link_id = (
            f"{randint(0, 999999)}{hash(self._meta)}" if (link or meta) else ""
        )
        self._hash: Optional[int] = None
        self._null = not (self._set_attributes or color or bgcolor or link or meta)

    @classmethod
    def null(cls) -> "Style":
        """Create a 'null' style, equivalent to Style(), but more performant.

        Returns:
            Style: A null Style instance.
        """
        return NULL_STYLE

    @classmethod
    def from_color(
        cls, color: Optional[Color] = None, bgcolor: Optional[Color] = None
    ) -> "Style":
        """Create a new style with colors and no attributes.

        Args:
            color (Optional[Color]): Foreground color.
            bgcolor (Optional[Color]): Background color.

        Returns:
            Style: A new Style instance.
        """
        style: Style = cls.__new__(Style)  # type: ignore
        style._ansi = None
        style._style_definition = None
        style._color = color
        style._bgcolor = bgcolor
        style._set_attributes = 0
        style._attributes = 0
        style._link = None
        style._link_id = ""
        style._meta = None
        style._null = not (color or bgcolor)
        style._hash = None
        return style

    @classmethod
    def from_meta(cls, meta: Optional[Dict[str, Any]]) -> "Style":
        """Create a new style with meta data.

        Args:
            meta (Optional[Dict[str, Any]]): A dictionary of meta data.

        Returns:
            Style: A new Style instance.
        """
        style: Style = cls.__new__(Style)  # type: ignore
        style._ansi = None
        style._style_definition = None
        style._color = None
        style._bgcolor = None
        style._set_attributes = 0
        style._attributes = 0
        style._link = None
        style._meta = dumps(meta)
        style._link_id = f"{randint(0, 999999)}{hash(style._meta)}"
        style._hash = None
        style._null = not (meta)
        return style

    @classmethod
    def on(cls, meta: Optional[Dict[str, Any]] = None, **handlers: Any) -> "Style":
        """Create a blank style with meta information.

        Example:
            style = Style.on(click=self.on_click)

        Args:
            meta (Optional[Dict[str, Any]], optional): An optional dict of meta information.
            **handlers (Any): Keyword arguments are translated in to handlers.

        Returns:
            Style: A Style with meta information attached.
        """
        meta = {} if meta is None else meta
        meta.update({f"@{key}": value for key, value in handlers.items()})
        return cls.from_meta(meta)

    bold = _Bit(0)
    dim = _Bit(1)
    italic = _Bit(2)
    underline = _Bit(3)
    blink = _Bit(4)
    blink2 = _Bit(5)
    reverse = _Bit(6)
    conceal = _Bit(7)
    strike = _Bit(8)
    underline2 = _Bit(9)
    frame = _Bit(10)
    encircle = _Bit(11)
    overline = _Bit(12)

    @property
    def link_id(self) -> str:
        """Get a link id, used in ansi code for links.

        Returns:
            str: The link id.
        """
        return self._link_id

    def __str__(self) -> str:
        """Re-generate style definition from attributes.

        Returns:
            str: The style definition string.
        """
        if self._style_definition is None:
            attributes: List[str] = []
            append = attributes.append
            bits = self._set_attributes
            if bits & 0b0000000001111:
                if bits & 1:
                    append("bold" if self.bold else "not bold")
                if bits & (1 << 1):
                    append("dim" if self.dim else "not dim")
                if bits & (1 << 2):
                    append("italic" if self.italic else "not italic")
                if bits & (1 << 3):
                    append("underline" if self.underline else "not underline")
            if bits & 0b0000111110000:
                if bits & (1 << 4):
                    append("blink" if self.blink else "not blink")
                if bits & (1 << 5):
                    append("blink2" if self.blink2 else "not blink2")
                if bits & (1 << 6):
                    append("reverse" if self.reverse else "not reverse")
                if bits & (1 << 7):
                    append("conceal" if self.conceal else "not conceal")
                if bits & (1 << 8):
                    append("strike" if self.strike else "not strike")
            if bits & 0b1111000000000:
                if bits & (1 << 9):
                    append("underline2" if self.underline2 else "not underline2")
                if bits & (1 << 10):
                    append("frame" if self.frame else "not frame")
                if bits & (1 << 11):
                    append("encircle" if self.encircle else "not encircle")
                if bits & (1 << 12):
                    append("overline" if self.overline else "not overline")
            if self._color is not None:
                append(self._color.hex)
            if self._bgcolor is not None:
                append("on")
                append(self._bgcolor.hex)
            if self._link:
                append("link")
                append(self._link)
            self._style_definition = " ".join(attributes) or "none"
        return self._style_definition

    def __bool__(self) -> bool:
        """A Style is false if it has no attributes, colors, or links.

        Returns:
            bool: True if the style is not null, False otherwise.
        """
        return not self._null

    def _make_ansi_codes(self, color_system: ColorSystem) -> str:
        """Generate ANSI codes for this style.

        Args:
            color_system (ColorSystem): Color system.

        Returns:
            str: String containing codes.
        """

        if self._ansi is None:
            sgr: List[str] = []
            append = sgr.append
            _style_map = self._style_map
            attributes = self._attributes & self._set_attributes
            if attributes:
                if attributes & 1:
                    append(_style_map[0])
                if attributes & 2:
                    append(_style_map[1])
                if attributes & 4:
                    append(_style_map[2])
                if attributes & 8:
                    append(_style_map[3])
                if attributes & 0b0000111110000:
                    for bit in range(4, 9):
                        if attributes & (1 << bit):
                            append(_style_map[bit])
                if attributes & 0b1111000000000:
                    for bit in range(9, 13):
                        if attributes & (1 << bit):
                            append(_style_map[bit])

            if self._color is not None:
                # Ensure we have a RichColor instance
                if isinstance(self._color, Color):
                    rich_color = self._color.rich
                elif isinstance(self._color, RichColor):
                    rich_color = self._color
                else:
                    try:
                        rich_color = Color(self._color).rich
                    except ColorError:
                        raise TypeError(f"Unable to convert _color to Color: {self._color} ({type(self._color)})")
                sgr.extend(rich_color.downgrade(color_system).get_ansi_codes())

            if self._bgcolor is not None:
                # Ensure we have a RichColor instance for background
                if isinstance(self._bgcolor, Color):
                    rich_bgcolor = self._bgcolor.rich
                elif isinstance(self._bgcolor, RichColor):
                    rich_bgcolor = self._bgcolor
                else:
                    try:
                        rich_bgcolor = Color(self._bgcolor).rich
                    except ColorError:
                        raise TypeError(f"Unable to convert _bgcolor to Color: {self._bgcolor} ({type(self._bgcolor)})")
                sgr.extend(
                    rich_bgcolor.downgrade(color_system).get_ansi_codes(foreground=False)
                )
            self._ansi = ";".join(sgr)
        return self._ansi

    @classmethod
    @lru_cache(maxsize=1024)
    def normalize(cls, style: str) -> str:
        """Normalize a style definition so that styles with the same effect have the same string
        representation.

        Args:
            style (str): A style definition.

        Returns:
            str: Normal form of style definition.
        """
        try:
            return str(cls.parse(style))
        except errors.StyleSyntaxError:
            return style.strip().lower()

    @classmethod
    def pick_first(cls, *values: Any) -> Any:
        """Pick first non-None style.

        Args:
            *values (Any): Values to pick from.

        Returns:
            Any: The first non-None value.

        Raises:
            ValueError: If all values are None.
        """
        for value in values:
            if value is not None:
                return value
        raise ValueError("expected at least one non-None style")

    def __rich_repr__(self) -> Result:
        """Rich library representation for debugging.

        Returns:
            Result: Rich representation.
        """
        yield "color", self.color, None
        yield "bgcolor", self.bgcolor, None
        yield "bold", self.bold, None
        yield "dim", self.dim, None
        yield "italic", self.italic, None
        yield "underline", self.underline, None
        yield "blink", self.blink, None
        yield "blink2", self.blink2, None
        yield "reverse", self.reverse, None
        yield "conceal", self.conceal, None
        yield "strike", self.strike, None
        yield "underline2", self.underline2, None
        yield "frame", self.frame, None
        yield "encircle", self.encircle, None
        yield "link", self.link, None
        if self._meta:
            yield "meta", self.meta

    def __eq__(self, other: Any) -> bool:
        """Equality comparison.

        Args:
            other (Any): Object to compare.

        Returns:
            bool: True if equal, False otherwise.
        """
        if isinstance(other, RichStyle):
            return self.as_rich() == other
        elif isinstance(other, str):
            try:
                parsed_other = self.parse(other)
                return self == parsed_other
            except Exception:
                return False
        if not isinstance(other, Style):
            return NotImplemented
        return hash(self) == hash(other)

    def __ne__(self, other: Any) -> bool:
        """Inequality comparison.

        Args:
            other (Any): Object to compare.

        Returns:
            bool: True if not equal, False otherwise.
        """
        return not self.__eq__(other)

    def __hash__(self) -> int:
        """Hash for the style.

        Returns:
            int: Hash value.
        """
        if self._hash is not None:
            return self._hash
        self._hash = hash(
            (
                self._color,
                self._bgcolor,
                self._attributes,
                self._set_attributes,
                self._link,
                self._meta,
            )
        )
        return self._hash

    @property
    def color(self) -> Optional[Color]:
        """The foreground color or None if it is not set.

        Returns:
            Optional[Color]: Foreground color.
        """
        return self._color

    @property
    def bgcolor(self) -> Optional[Color]:
        """The background color or None if it is not set.

        Returns:
            Optional[Color]: Background color.
        """
        return self._bgcolor

    @property
    def link(self) -> Optional[str]:
        """Link text, if set.

        Returns:
            Optional[str]: Link URL.
        """
        return self._link

    @property
    def transparent_background(self) -> bool:
        """Check if the style specified a transparent background.

        Returns:
            bool: True if background is transparent.
        """
        return self.bgcolor is None or self.bgcolor.rich.is_default

    @property
    def background_style(self) -> "Style":
        """A Style with background only.

        Returns:
            Style: Style with only background color.
        """
        return Style(bgcolor=self.bgcolor)

    @property
    def meta(self) -> Dict[str, Any]:
        """Get meta information (can not be changed after construction).

        Returns:
            Dict[str, Any]: Meta information.
        """
        return {} if self._meta is None else cast(Dict[str, Any], loads(self._meta))

    @property
    def without_color(self) -> "Style":
        """Get a copy of the style with color removed.

        Returns:
            Style: Style without color.
        """
        if self._null:
            return NULL_STYLE
        style: Style = self.__new__(Style)  # type: ignore
        style._ansi = None
        style._style_definition = None
        style._color = None
        style._bgcolor = None
        style._attributes = self._attributes
        style._set_attributes = self._set_attributes
        style._link = self._link
        style._link_id = f"{randint(0, 999999)}" if self._link else ""
        style._null = False
        style._meta = None
        style._hash = None
        return style

    @classmethod
    @lru_cache(maxsize=4096)  # type: ignore
    def parse(cls, style_definition: str) -> "Style":
        """Parse a style definition.

        Args:
            style_definition (str): A string containing a style.

        Raises:
            errors.StyleSyntaxError: If the style definition syntax is invalid.

        Returns:
            RichStyle: A Style instance, with colors sanitized to rich.color.Color.
        """
        # Updated handling for null/none styles

        if isinstance(style_definition, Style) and style_definition._null:
            return Style.null()
        if isinstance(style_definition, (Style, RichStyle)):
            return style_definition
        if str(style_definition) == "none":
            return Style.null()
        if isinstance(style_definition, Color):
            style_definition = str(RichStyle.parse(style_definition).color)
        if isinstance(style_definition, RGBA):
            style_definition = style_definition.hex
        # proceed with parsing string definitions manually below
        if not isinstance(style_definition, str):
            raise TypeError(
                f"Style.parse() expected a str, got {type(style_definition).__name__}"
            )
        if not style_definition:
            return cls.null()

        STYLE_ATTRIBUTES = cls.STYLE_ATTRIBUTES
        color: Optional[str] = None
        bgcolor: Optional[str] = None
        attributes: Dict[str, Optional[Any]] = {}
        link: Optional[str] = None

        words = iter(style_definition.split())
        for original_word in words:
            word = original_word.lower()
            if word == "on":
                word = next(words, "")
                if not word:
                    raise errors.StyleSyntaxError("color expected after 'on'")
                try:
                    Color(word)
                except ColorError as error:
                    raise errors.StyleSyntaxError(
                        f"unable to parse {word!r} as background color; {error}"
                    ) from None
                bgcolor = word

            elif word == "not":
                word = next(words, "")
                attribute = STYLE_ATTRIBUTES.get(word)
                if attribute is None:
                    raise errors.StyleSyntaxError(
                        f"expected style attribute after 'not', found {word!r}"
                    )
                attributes[attribute] = False

            elif word == "link":
                word = next(words, "")
                if not word:
                    raise errors.StyleSyntaxError("URL expected after 'link'")
                link = word

            elif word in STYLE_ATTRIBUTES:
                attributes[STYLE_ATTRIBUTES[word]] = True

            else:
                try:
                    Color(word)
                except ColorParseError as error:
                    raise errors.StyleSyntaxError(
                        f"unable to parse {word!r} as color; {error}"
                    ) from None
                color = word
        style = Style(color=color, bgcolor=bgcolor, link=link, **attributes)
        # Ensure that the returned style uses only rich.color.Color in its color and bgcolor
        return style

    @lru_cache(maxsize=1024)
    def get_html_style(self, theme: Optional[TerminalTheme] = None) -> str:
        """Get a CSS style rule.

        Args:
            theme (Optional[TerminalTheme]): Terminal theme.

        Returns:
            str: CSS style string.
        """
        theme = theme or DEFAULT_TERMINAL_THEME
        css: List[str] = []
        append = css.append

        color = self.color
        bgcolor = self.bgcolor
        if self.reverse:
            color, bgcolor = bgcolor, color
        if self.dim:
            foreground_color = (
                theme.foreground_color
                if color is None
                else color.rich.get_truecolor(theme)
            )
            color = Color.from_triplet(
                blend_rgb(foreground_color, theme.background_color, 0.5)
            )
        if color is not None:
            theme_color = color.rich.get_truecolor(theme)
            append(f"color: {theme_color.hex}")
            append(f"text-decoration-color: {theme_color.hex}")
        if bgcolor is not None:
            theme_color = bgcolor.rich.get_truecolor(theme, foreground=False)
            append(f"background-color: {theme_color.hex}")
        if self.bold:
            append("font-weight: bold")
        if self.italic:
            append("font-style: italic")
        if self.underline:
            append("text-decoration: underline")
        if self.strike:
            append("text-decoration: line-through")
        if self.overline:
            append("text-decoration: overline")
        return "; ".join(css)

    @classmethod
    def combine(cls, styles: Iterable[Any]) -> "Style":
        """Combine styles and get result.

        Args:
            styles (Iterable[Any]): Styles to combine.

        Returns:
            Style: A new style instance.
        """
        from functools import reduce
        return reduce(lambda a, b: a + b, styles, Style.null())

    @classmethod
    def chain(cls, *styles: Any) -> "Style":
        """Combine styles from positional arguments into a single style.

        Args:
            *styles (Any): Styles to combine.

        Returns:
            Style: A new style instance.
        """
        return cls.combine(styles)

    def copy(self) -> "Style":
        """Get a copy of this style.

        Returns:
            Style: A new Style instance with identical attributes.
        """
        if self._null:
            return NULL_STYLE
        style: Style = self.__new__(Style)  # type: ignore
        style._ansi = self._ansi
        style._style_definition = self._style_definition
        style._color = self._color
        style._bgcolor = self._bgcolor
        style._attributes = self._attributes
        style._set_attributes = self._set_attributes
        style._link = self._link
        style._link_id = f"{randint(0, 999999)}" if self._link else ""
        style._hash = self._hash
        style._null = False
        style._meta = self._meta
        return style

    @lru_cache(maxsize=128)
    def clear_meta_and_links(self) -> "Style":
        """Get a copy of this style with link and meta information removed.

        Returns:
            Style: New style object.
        """
        if self._null:
            return NULL_STYLE
        style: Style = self.__new__(Style)  # type: ignore
        style._ansi = self._ansi
        style._style_definition = self._style_definition
        style._color = self._color
        style._bgcolor = self._bgcolor
        style._attributes = self._attributes
        style._set_attributes = self._set_attributes
        style._link = None
        style._link_id = ""
        style._hash = self._hash
        style._null = False
        style._meta = None
        return style

    def update_link(self, link: Optional[str] = None) -> "Style":
        """Get a copy with a different value for link.

        Args:
            link (Optional[str]): New value for link.

        Returns:
            Style: A new Style instance.
        """
        style: Style = self.__new__(Style)  # type: ignore
        style._ansi = self._ansi
        style._style_definition = self._style_definition
        style._color = self._color
        style._bgcolor = self._bgcolor
        style._attributes = self._attributes
        style._set_attributes = self._set_attributes
        style._link = link
        style._link_id = f"{randint(0, 999999)}" if link else ""
        style._hash = None
        style._null = False
        style._meta = self._meta
        return style

    def render(
        self,
        text: str = "",
        *,
        color_system: Optional[ColorSystem] = ColorSystem.TRUECOLOR,
        legacy_windows: bool = False,
    ) -> str:
        """Render the ANSI codes for the style.

        Args:
            text (str, optional): A string to style. Defaults to "".
            color_system (Optional[ColorSystem], optional): Color system to render to. Defaults to ColorSystem.TRUECOLOR.
            legacy_windows (bool, optional): Use legacy Windows mode. Defaults to False.

        Returns:
            str: A string containing ANSI style codes.
        """
        if not text or color_system is None:
            return text
        attrs = self._ansi or self._make_ansi_codes(color_system)
        rendered = f"\x1b[{attrs}m{text}\x1b[0m" if attrs else text
        if self._link and not legacy_windows:
            rendered = (
                f"\x1b]8;id={self._link_id};{self._link}\x1b\\{rendered}\x1b]8;;\x1b\\"
            )
        return rendered

    def test(self, text: Optional[str] = None) -> None:
        """Write text with style directly to terminal.

        This method is for testing purposes only.

        Args:
            text (Optional[str], optional): Text to style or None for style name.
        """
        text = text or str(self)
        sys.stdout.write(f"{self.render(text)}\n")

    @lru_cache(maxsize=1024)
    def _add(self, style: Optional["Style"]|Optional[RichStyle]) -> "Style":
        """Combine this style with another style.

        Args:
            style (Optional[Style]): Style to add.

        Returns:
            Style: Combined style.
        """
        if isinstance(style, RichStyle):
            style_string = str(style)
            style = Style.parse(style_string)
        if style is None or style._null:
            return self
        if self._null:
            return style
        new_style: Style = self.__new__(Style)  # type: ignore
        new_style._ansi = None
        new_style._style_definition = None
        new_style._color = style._color or self._color
        new_style._bgcolor = style._bgcolor or self._bgcolor
        new_style._attributes = (self._attributes & ~style._set_attributes) | (
            style._attributes & style._set_attributes
        )
        new_style._set_attributes = self._set_attributes | style._set_attributes
        new_style._link = style._link or self._link
        new_style._link_id = style._link_id or self._link_id
        new_style._null = style._null
        if self._meta and style._meta:
            new_style._meta = dumps({**self.meta, **style.meta})
        else:
            new_style._meta = self._meta or style._meta
        new_style._hash = None
        return new_style

    def __add__(self, style: Optional[Union["Style", RichStyle]]) -> "Style":
        """Add (combine) this style with another.

        Args:
            style (Optional[Union[Style, RichStyle]]): Style to add.

        Returns:
            Style: Combined style.
        """
        if isinstance(style, RichStyle):
            style = Style.from_rich(style)
        combined_style = self._add(style)
        return combined_style.copy() if combined_style.link else combined_style

    @property
    def rich(self) -> RichStyle:
        """Creates a rich.style.Style instance from this Style.

        Returns:
            RichStyle: Equivalent rich.style.Style instance.
        """
        return self.as_rich()

    def as_rich(self) -> RichStyle:
        """Convert this Style into a rich.style.Style instance.

        Returns:
            RichStyle: Equivalent rich.style.Style instance.
        """
        return RichStyle(
            color=self._color.rich if self._color is not None else None,
            bgcolor=self._bgcolor.rich if self._bgcolor is not None else None,
            bold=self.bold,
            dim=self.dim,
            italic=self.italic,
            underline=self.underline,
            blink=self.blink,
            blink2=self.blink2,
            reverse=self.reverse,
            conceal=self.conceal,
            strike=self.strike,
            underline2=self.underline2,
            frame=self.frame,
            encircle=self.encircle,
            overline=self.overline,
        )

    @classmethod
    def from_rich(cls, rich_style: RichStyle) -> "Style":
        """Create a Style from a rich.style.Style instance.

        Args:
            rich_style (RichStyle): Rich style instance.

        Returns:
            Style: New Style instance.
        """
        color = (
            Color.from_triplet(rich_style.color.get_truecolor())
            if rich_style.color
            else None
        )
        bgcolor = (
            Color.from_triplet(rich_style.bgcolor.get_truecolor())
            if rich_style.bgcolor
            else None
        )
        return cls(
            color=color,
            bgcolor=bgcolor,
            bold=rich_style.bold,
            dim=rich_style.dim,
            italic=rich_style.italic,
            underline=rich_style.underline,
            blink=rich_style.blink,
            blink2=rich_style.blink2,
            reverse=rich_style.reverse,
            conceal=rich_style.conceal,
            strike=rich_style.strike,
            underline2=rich_style.underline2,
            frame=rich_style.frame,
            encircle=rich_style.encircle,
            overline=rich_style.overline,
        )


NULL_STYLE = Style()

register_repr(Style)(normal_repr)
register_repr(RichStyle)(normal_repr)


class StyleStack:
    """A stack of styles."""

    __slots__ = ["_stack"]

    def __init__(self, default_style: "Style") -> None:
        self._stack: List[Style] = [default_style]

    def __repr__(self) -> str:
        return f"<Stylestack {self._stack!r}>"

    @property
    def current(self) -> Style:
        """Get the Style at the top of the stack."""
        return self._stack[-1]

    def push(self, style: Style) -> None:
        """Push a new style on to the stack.

        Args:
            style (Style): New style to combine with current style.
        """
        self._stack.append(self._stack[-1] + style)

    def pop(self) -> Style:
        """Pop last style and discard.

        Returns:
            Style: New current style (also available as stack.current)
        """
        self._stack.pop()
        return self._stack[-1]


if __name__ == "__main__":
    # Test the Style class
    style = Style(color="#99ff00", bgcolor="blue", bold=True)
    print(style)
    print(style.render("Hello, World!"))
    print(style.get_html_style())
    print(style.rich)
