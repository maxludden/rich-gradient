"""Gradient is the highlevel class that allows the automation of printing to the \
console in gradient color."""

# ruff: noqa: F401
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Literal, Optional, Tuple, TypeAlias, Union

import numpy as np
from pydantic_core import PydanticCustomError
from pydantic_extra_types.color import ColorType
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.control import strip_control_codes
from rich.panel import Panel
from rich.style import Style, StyleType
from rich.text import Span, Text, TextType

from rich_gradient.color import Color
from rich_gradient.spectrum import Spectrum
from rich_gradient.theme import GRADIENT_TERMINAL_THEME
from rich_gradient._simple_gradient import SimpleGradient

GradientMode = Literal["default", "list", "mono", "rainbow"]
GradientColors: TypeAlias = Union[
    Optional[List[ColorType]], Optional[list[Color]], Optional[List[str]]
]
DEFAULT_JUSTIFY: JustifyMethod = "default"
DEFAULT_OVERFLOW: OverflowMethod = "fold"
DEFAULT_GRADIENT_MODE: GradientMode = "default"
WHITESPACE_REGEX = re.compile(r"^\s+$")


class Gradient(Text):
    """Text styled with gradient color.

    Args:
        text ( `str` | `rich.text.Text` ): The text to print. Defaults to `""`.
        colors ( `GradientColors`, optional ): An optional list of colors [1]_ from
            which to make the Gradient. Defaults to None.
        rainbow ( `bool` ): Whether to print the gradient text in rainbow colors
            across the spectrum. Defaults to False.
        hues ( `int` ): The number of colors in the gradient. Defaults to `3`.
        style ( `StyleType` ): The style of the gradient text. Defaults to None.
        verbose ( `bool` ): Whether to print verbose output. Defaults to False.
        justify ( `JustifyMethod`, optional): Justify method: "left", "center",
            "full", "right". Defaults to None.
        overflow (Optional[OverflowMethod]):  Overflow method: "crop", "fold",
            "ellipsis". Defaults to None.
        end (str, optional): Character to end text with. Defaults to "\\\\n".
        no_wrap (bool, optional): Disable text wrapping, or None for default.
            Defaults to None.
        tab_size (int): Number of spaces per tab, or `None` to use
            `console.tab_size`. Defaults to 4.
        spans (List[Span], optional): A list of predefined style spans.
            Defaults to None.


            .. [1] colors: List[Optional[Color|Tuple|str|int]
    """

    __slots__ = [
        "_colors",
        "_text",
        "_length",
        "length",
        "_end",
        "_hues",
        "_justify",
        "_no_wrap",
        "overflow",
        "_overflow",
        "style",
        "_style",
        "_spans",
        "_rainbow",
        "verbose",
    ]

    def __init__(
        self,
        text: str | Text = "",
        colors: GradientColors = None,
        *,
        rainbow: bool = False,
        hues: int = 4,
        style: StyleType = Style.null(),
        justify: Optional[JustifyMethod] = DEFAULT_JUSTIFY,
        overflow: Optional[OverflowMethod] = DEFAULT_OVERFLOW,
        no_wrap: Optional[bool] = None,
        end: str = "\n",
        tab_size: Optional[int] = 4,
        verbose: bool = False,
        spans: Optional[List[Span]] = None,
    ) -> None:
        """
        Text styled with gradient color.

        Args:
            text (text): The text to print. Defaults to `""`.\n
            colors (List[Optional[Color|Tuple|str|int]]): A list of colors to use \
                for the gradient. Defaults to None.\n
            rainbow (bool): Whether to print the gradient text in rainbow colors\
                  across the spectrum. Defaults to False.\n
            hues (int): The number of colors in the gradient. Defaults to `4`.\n
            style (StyleType): The style of the gradient text. Defaults to None.\n
            verbose (bool): Whether to print verbose output. Defaults to False.
            justify (Optional[JustifyMethod]): Justify method: "left", "center",\
                "full", "right". Defaults to None.\n
            overflow (Optional[OverflowMethod]):  Overflow method: "crop", "fold", \
                "ellipsis". Defaults to None.\n
            end (str, optional): Character to end text with. Defaults to "\\\\n".\n
            no_wrap (bool, optional): Disable text wrapping, or None for default.\
                Defaults to None.\n
            tab_size (int): Number of spaces per tab, or `None` to use\
                `console.tab_size`. Defaults to 4.\n
            spans (List[Span], optional): A list of predefined style spans.\
                Defaults to None.\n

        """

        self.verbose = verbose or False
        self.text = text  # type: ignore
        self.hues = hues
        self.justify = justify or DEFAULT_JUSTIFY
        self.overflow = overflow or DEFAULT_OVERFLOW
        self.style = Style.parse(style) if isinstance(style, str) else style
        self.colors = self.validate_colors(colors or [], rainbow=rainbow)  # type: ignore
        if len(self.colors) > 2:
            self.hues = len(self.colors)
        else:
            self.hues = hues
        self.verbose = verbose

        super().__init__(
            text=self.text,
            style=style,
            justify=justify,
            overflow=overflow,
            no_wrap=no_wrap,
            end=end,
            tab_size=tab_size or 4,
            spans=spans,
        )
        indexes = self.generate_indexes()
        substrings = self.generate_substrings(indexes)
        subgradients = self.generate_subgradients(substrings)
        self._spans = self.join_subgradients(subgradients).spans

    @property
    def text(self) -> str:
        """
        Returns the concatenated string representation of the `_text` attribute.

        Returns:
            str: The concatenated string representation of the `_text` attribute.
        """
        return "".join(self._text) if isinstance(self._text, list) else self._text

    @text.setter
    def text(self, value: Optional[str] | Optional[Text]) -> None:
        """
        Setter for the text attribute.

        Args:
            value (str|Text): The value to set for the text attribute.

        Returns:
            None
        """
        if isinstance(value, Text):
            self._length = value._length
            self._text = value._text
            self._spans = value.spans
        elif isinstance(value, str):
            sanitized_text = strip_control_codes(value)
            self._length = len(sanitized_text)
            self._text = list(sanitized_text)
        elif value is None:
            raise ValueError("Text cannot be None.")
        else:
            raise TypeError(f"Text must be a string or Text, not {type(value)}")

    @property
    def hues(self) -> int:
        """The number of colors in the gradient."""
        return self._hues

    @hues.setter
    def hues(self, hues: int) -> None:
        """Set the number of colors in the gradient.

        Args:
            hues (int): The number of colors in the gradient. Defaults to `4`.
        """
        if hues < 2:
            raise ValueError("Gradient must have at least two colors.")
        self._hues = hues

    @property  # type: ignore
    def justify(self) -> JustifyMethod:
        """The justify method of the gradient."""
        if not hasattr(self, "_justify"):
            return DEFAULT_JUSTIFY
        return self._justify  # type: ignore

    @justify.setter
    def justify(self, justify: JustifyMethod) -> None:
        """Set the justify method of the gradient.

        Args:
            justify (JustifyMethod): The justify method of the gradient.
        """
        self._justify = justify

    @property
    def no_wrap(self) -> Optional[bool]:
        """Whether to wrap the gradient text."""
        try:
            return self._no_wrap
        except AttributeError:
            return None

    @no_wrap.setter
    def no_wrap(self, no_wrap: Optional[bool]) -> None:
        """Set whether to wrap the gradient text.

        Args:
            no_wrap (bool): Whether to wrap the gradient text.
        """
        self._no_wrap = no_wrap

    @property
    def colors(self) -> List[Color]:
        """The colors in the gradient."""
        return self._colors

    @colors.setter
    def colors(self, values: Optional[List[ColorType]] | Optional[List[Color]]) -> None:
        """Set the colors in the gradient.

        Args:
            colors (List[Color]): The colors in the gradient.
        """
        self._colors = self.validate_colors(values)
        self._hues = len(self._colors)

    def validate_colors(
        self,
        colors: Optional[List[ColorType]] | Optional[List[Color]],
        rainbow: bool = False,
    ) -> List[Color]:
        """Validate input colors, and convert them into `Color` objects.

        Colors may be passed in as strings or tuples, names, or Color objects.
        If no colors are provided, a random gradient will be generated.

        Args:
            colors (List[ColorType]): The colors to validate and convert

        Returns:
            List[Color]: The validated colors.

        Raises:
            PydanticCustomError: If any of the colors are invalid.
        """
        _colors: List[Color] = []
        if colors is None or colors == []:
            if not rainbow:
                color_list = Spectrum()
                for index, color in enumerate(color_list):
                    _colors.append(color)
                    if index == self.hues - 1:
                        break
                return _colors
            else:
                self.hues = 20
                if self._length < 20:
                    self.hues = self._length
                color_list = Spectrum()
                for index, color in enumerate(color_list):
                    _colors.append(color)
                    if index == self.hues - 1:
                        break
                return _colors
        elif isinstance(colors, tuple):
            for color in colors:
                try:
                    color = Color(color)
                except PydanticCustomError as pce:
                    raise pce
                else:
                    _colors.append(color)
            assert len(_colors) >= 2, "Gradient must have at least two colors."
            return _colors
        elif isinstance(colors, list):
            for color in colors:  # type: ignore
                try:
                    color = Color(color)
                except PydanticCustomError as pce:
                    raise pce
                else:
                    _colors.append(color)
            assert len(_colors) >= 2, "Gradient must have at least two colors."
            return _colors
        else:
            raise TypeError(f"Colors must be a list or tuple, not {type(colors)}.")

    def _base_span(self) -> None:
        if not hasattr(self, "_spans"):
            self._spans = [Span(0, self._length - 1, self.style)]

    @property
    def spans(self) -> List[Span]:
        """The spans of the gradient."""
        self._base_span()
        return self._spans

    @spans.setter
    def spans(self, spans: List[Span]) -> None:
        """Set the spans of the gradient.

        Args:
            spans (List[Span]): The spans of the gradient.
        """
        self._spans = spans

    def generate_indexes(self) -> List[List[int]]:
        """Chunk the text into a list of strings.

        Returns:
            List[str]: The list of strings.
        """
        # if self.verbose:
        #     console.log(f"Text: {self.text}")
        #     console.log(f"Length: {self._length}")
        #     console.log(f"Hues: {self.hues}")
        result = np.array_split(np.arange(self._length), self.hues - 1)  # noqa: F722

        indexes: List[List[int]] = [sublist.tolist() for sublist in result]
        # if self.verbose:
        #     index_text = Text(" ".join([f"{index}" for index in indexes]))
        #     console.print(index_text)
        return indexes

    def generate_substrings(self, indexes: List[List[int]]) -> List[str]:
        """Split the text into substrings based on the indexes.

        Args:
            indexes (List[List[int]]): The indexes to split the text on.

        Returns:
            List[str]: The list of substrings.
        """
        substrings: List[str] = []
        slices: List[Tuple[int, int]] = []

        # For each index get the first and last element
        for index in indexes:
            start = index[0]
            end = index[-1] + 1
            slices.append((start, end))  #  # Slice the text

        # If the text is a list, join it into a single string
        if isinstance(self.text, list):
            text = " ".join(self.text)
        elif isinstance(self.text, str):
            text = self.text
        else:
            raise TypeError(f"Text must be a string or list, not {type(self.text)}")

        # split the text into substrings
        for index, (start, end) in enumerate(slices, 1):  # type: ignore
            substring = text[start:end]
            substrings.append(substring)
        return substrings

    def generate_subgradients(self, substrings: List[str]) -> List[SimpleGradient]:
        """Generate simple gradients.

        Args:
            substrings (List[str]): The substrings to generate gradients for.

        Returns:
            List[SimpleGradient]: The list of simple gradients.
        """
        subgradients: List[SimpleGradient] = []

        for index, substring in enumerate(substrings):
            # Get the colors for the gradient
            color_1 = self.colors[index]
            color_2 = self.colors[index + 1]

            assert self.overflow is not None, "Overflow must be set."

            # Create a simple gradient
            gradient = SimpleGradient(
                substring,  # type: ignore
                color1=color_1.hex,
                color2=color_2.hex,
                justify=self.justify,
                overflow=self.overflow,
                style=self.style,
                no_wrap=self.no_wrap or False,
                end=self.end or "\n",
                spans=self.spans,
            )

            subgradients.append(gradient)
        return subgradients

    def join_subgradients(self, subgradients: List[SimpleGradient]) -> Text:
        """Join the subgradients into a single gradient.

        Args:
            subgradients (List[SimpleGradient]): The list of subgradients.

        Returns:
            Text: The joined gradient.
        """
        result = Text()
        for gradient in subgradients:
            result.append(gradient)
        return result

    def as_text(self) -> Text:
        """Convert the gradient to a `Text`.

        Returns:
            Text: The gradient as a `rich.text.Text` object.
        """
        overflow: OverflowMethod = DEFAULT_OVERFLOW
        justify: JustifyMethod = DEFAULT_JUSTIFY
        if self.justify is None:
            justify = DEFAULT_JUSTIFY
        if self.overflow is None:
            overflow = DEFAULT_OVERFLOW
        return Text(
            text=self.text,
            style=self.style,
            justify=justify,
            overflow=overflow,
            no_wrap=self.no_wrap,
            end=self.end or "\n",
            tab_size=self.tab_size,
            spans=self._spans,
        )

    @classmethod
    def named_gradient_example(
        cls,
        save: bool = False,
        path: str = str(Path.cwd() / "docs" / "img" / "named_gradient_example.svg"),
    ) -> None:
        """
        Generate an example of a gradient with defined colors.
    
        Args:
            save (bool, optional): Whether to save the gradient to a file. Defaults to False.
            path (Optional[Path], optional): The filename to save the gradient to. Defaults \
        to Path("/Users/maxludden/dev/py/MaxGradient/docs/img/named_gradient_example.svg").
                console (Console, optional): The console to print the gradient to. Defaults to console.
        """
        if save:
            console = Console(width=60, record=True)
        else:
            console = Console(width=60)
        gradient = Gradient(
            "The quick brown fox jumps over the lazy dog.",
            colors=["magenta", "purple", "violet"],
        )
        panel_content = Text.assemble(
            gradient,
            Text("\n\nThis gradient starts with "),
            Text("magenta", style="b #ff00ff"),
            Text(". It fades to "),
            Text("purple", style="b #af00ff"),
            Text(", and ends in "),
            Text("violet", style="b #5f00ff"),
            Text("."),
            justify="center",
        )
        console.line(2)
        console.print(
            Panel(panel_content, title="[b #ffffff]Named Gradient[/]", padding=(1, 4)),
            justify="center",
        )
        console.print(
            "[dim i]Named gradients are graidents that have user \
specified colors[/]",
            justify="center",
        )
        if save:
            console.save_svg(path, title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)

    @classmethod
    def random_gradient_example(
        cls,
        save: bool = False,
        path: str = str(Path.cwd() / "docs" / "img" / "random_gradient_example.svg"),
    ) -> None:
        """
        Generate an example of a gradient with random adjacent colors.
    
        Args:
            save (bool, optional): Whether to save the gradient to a file. Defaults to False.
            path (Optional[Path], optional): The filename to save the gradient to. Defaults \
        to Path("/Users/maxludden/dev/py/MaxGradient/docs/img/named_gradient_example.svg").
                console (Console, optional): The console to print the gradient to. Defaults to console.
        """
        if save:
            console = Console(width=60, record=True)
        else:
            console = Console(width=60)
        console.line()
        console.print(
            Panel(
                Gradient(
                    text="The quick brown fox jumps over the lazy dog.",
                    justify="center",
                ),
                title="[b #ffffff]Random Gradient[/b #ffffff]",
                padding=(1, 4),
            ),
            justify="center",
        )
        console.print(
            "[i dim]Random gradients are randomly generated by \
gradient automatically.[/]",
            justify="center",
        )
        console.line()
        if save:
            console.save_svg(path, title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)

    @classmethod
    def rainbow_gradient_example(
        cls,
        save: bool = False,
        path: str = str(Path.cwd() / "docs" / "img" / "rainbow_gradient_example.svg"),
    ) -> None:
        """
        Generate an example of a gradient with the whole spectrum of colors.
    
        Args:
            save (bool, optional): Whether to save the gradient to a file. Defaults to False.
            path (Optional[Path], optional): The filename to save the gradient to. Defaults \
        to Path("/Users/maxludden/dev/py/MaxGradient/docs/img/named_gradient_example.svg").
                console (Console, optional): The console to print the gradient to. Defaults to console.
        """
        if save:
            console = Console(width=60, record=True)
        else:
            console = Console(width=60)

        console.line(1)
        console.print(
            Panel(
                Gradient(
                    text="The quick brown fox jumps over the lazy dog.",
                    rainbow=True,
                    justify="center",
                ),
                title=Gradient("Rainbow Gradient", rainbow=True),
                padding=(1, 4),
            ),
            justify="center",
        )
        console.print(
            "[dim i]Rainbow gradients are also automated and will randomly\
span a gradient from one point on the spectrum (randomly) all the way around \
until it returns to it's starting color.",
            justify="center",
        )
        console.line(1)
        if save:
            console.save_svg(path, title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)

    @classmethod
    def example(cls) -> None:
        Gradient.named_gradient_example(True)
        Gradient.random_gradient_example(True)
        Gradient.rainbow_gradient_example(True)


if __name__ == "__main__":  # pragma: no cover
    from rich.console import Console
    from rich.traceback import install as tr_install
    from rich_gradient.theme import GRADIENT_TERMINAL_THEME


    Gradient.example()
