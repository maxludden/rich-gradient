from __future__ import annotations

import inspect
from io import StringIO
from typing import List, Optional, Union, cast

from cheap_repr import normal_repr, register_repr
from loguru import logger
from rich import get_console
from rich._wrap import divide_line
from rich.align import Align, AlignMethod
from rich.color import blend_rgb
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.markup import render
from rich.measure import Measurement, measure_renderables
from rich.segment import Segment
from rich.text import Span, Text
from rich.traceback import install
from snoop import snoop

from rich_gradient.color import Color, ColorType
from rich_gradient.spectrum import Spectrum
from rich_gradient.style import Style, StyleType

DEFAULT_JUSTIFY = "default"
DEFAULT_OVERFLOW = "fold"
VERBOSE: bool = False

console: Console = Console()
install(console=console, show_locals=True)


class Gradient(Text):
    """A Text subclass that renders each line with a smooth horizontal gradient."""

    __slots__ = [
        "_text",
        "_spans",
        "console",
        "console_width",
        "justify",
        "overflow",
        "bold",
        "italic",
        "underline",
        "strike",
        "reverse",
        "no_wrap",
        "end",
        "angle",
        "rainbow",
        "hues",
        "lines",
        "styles",
        "_renderable",
        "_renderable_width",
    ]

    def __init__(
        self,
        renderable: Union[str, Text, Gradient],
        styles: Optional[List[StyleType]] = None,
        *,
        rainbow: bool = False,
        hues: int = 5,
        justify: JustifyMethod = DEFAULT_JUSTIFY,
        overflow: OverflowMethod = DEFAULT_OVERFLOW,
        bold: bool = False,
        italic: bool = False,
        underline: bool = False,
        strike: bool = False,
        reverse: bool = False,
        end: str = "\n",
        no_wrap: bool = False,
        angle: float = 1.5,
        verbose: bool = False,
    ) -> None:
        if verbose:
            global VERBOSE
            VERBOSE = True
            console.log(
                f"[b #ff0]Gradient.__init__[/] with renderable:\n\n{renderable}\n\n"
            )
        super().__init__("")
        self.console = console  # Use the global console
        self.console_width = self.console.width
        self.justify = justify
        self.overflow = overflow
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strike = strike
        self.reverse = reverse
        self.no_wrap = no_wrap
        self.end = end
        self.angle = angle
        self.rainbow = rainbow
        self.hues = hues

        self.lines: List[str] = self._extract_lines(renderable)
        self.styles: List[Style] = self._build_styles(styles)
        self._apply_gradient()

    # @snoop()
    def _extract_lines(self, renderable: Union[str, Text, Gradient]) -> List[str]:
        """Wrap the input to console width and preserve original newlines."""
        if VERBOSE:
            console.log(
                f"Entered Gradient._extract_lines with renderable:\n\n{renderable}"
            )
            log_spectrum = Spectrum()
        if isinstance(renderable, Gradient):
            input = renderable.plain
        elif isinstance(renderable, Text):
            input = renderable.plain
        else:
            input = str(renderable)

        raw_lines = input.split("\n")
        lines: List[str] = []
        for index, raw_line in enumerate(raw_lines, 1):
            if raw_line == "":
                lines.append("")  # Preserve empty line
                continue
            wrapped: List[int] = divide_line(raw_line, self.console_width)
            start = 0
            for end in wrapped:
                lines.append(raw_line[start:end])
                start = end
            if start < len(raw_line):
                lines.append(f"{raw_line[start:]}")
        if VERBOSE:
            for final_index, line in enumerate(lines):
                console.log(
                    f"[b #999] Line {final_index}:[/]{len(line)} | [{log_spectrum[index]}]{line!r}[/]"
                )
        return lines

    def _build_styles(self, styles: Optional[List[StyleType]]) -> List[Style]:
        if self.rainbow:
            spectrum: List[Color] = Spectrum()
            return [
                Style(
                    color=color.hex,
                    bold=self.bold,
                    italic=self.italic,
                    underline=self.underline,
                    strike=self.strike,
                    reverse=self.reverse,
                )
                for color in spectrum
            ]
        if not styles:
            spectrum: List[Color] = Spectrum(length=self.hues)
            return [
                Style(
                    color=color.hex,
                    bold=self.bold,
                    italic=self.italic,
                    underline=self.underline,
                    strike=self.strike,
                    reverse=self.reverse,
                )
                for color in spectrum
            ]
        parsed_styles: List[Style] = []
        for __style in styles:
            if isinstance(__style, str):
                _style = Style.parse(__style) + Style(
                    color=__style,
                    bold=self.bold,
                    italic=self.italic,
                    underline=self.underline,
                    strike=self.strike,
                    reverse=self.reverse,
                )
            elif isinstance(__style, Style):
                _style = __style + Style(
                    bold=self.bold,
                    italic=self.italic,
                    underline=self.underline,
                    strike=self.strike,
                    reverse=self.reverse,
                )
            else:
                _style = Style.parse(str(__style)) + Style(
                    color=__style,
                    bold=self.bold,
                    italic=self.italic,
                    underline=self.underline,
                    strike=self.strike,
                    reverse=self.reverse,
                )
            parsed_styles.append(_style)
        return parsed_styles

    def _apply_gradient(self) -> None:
        self._text = ""
        self._spans.clear()
        width = self.console_width
        hues = len(self.styles)
        for line in self.lines:
            padded_line = self.get_padding(cast(JustifyMethod, self.justify), width, line)
            for i, char in enumerate(padded_line):
                pos_ratio = i / max(1, width - 1)
                index = pos_ratio * (hues - 1)
                lower = int(index)
                upper = min(lower + 1, hues - 1)
                interp = index - lower
                color1 = self.styles[lower].color or self.styles[0].color
                color2 = self.styles[upper].color or self.styles[-1].color
                assert color1 is not None and color2 is not None, f"{color1=}, {color2=}"
                c1 = color1.as_triplet()
                c2 = color2.as_triplet()
                blended = blend_rgb(c1, c2, interp)
                hex_color = f"#{blended.red:02x}{blended.green:02x}{blended.blue:02x}"
                style = Style(color=hex_color)
                start = len(self._text)
                self._text += char
                self._spans.append(Span(start, start + 1, style))
            self._text += "\n"

    # @snoop(watch="line, padded_line")
    def get_padding(self, justify: str, width: int, line: str) -> str:
        line = line.strip()
        if justify == "center":
            return line.center(width)
        elif justify == "right":
            return line.rjust(width)
        elif justify == "left":
            return line.ljust(width)
        else:
            return line.ljust(width)


register_repr(Gradient)(normal_repr)


class GradientError(Exception):
    def __init__(self, message: str, stacklevel: int = 1) -> None:
        frame_info = inspect.stack()[stacklevel]
        module = frame_info.frame.f_globals.get("__name__", "<unknown module>")
        func = frame_info.function
        lineno = frame_info.lineno
        full_message = f"{module}.{func}:Line {lineno}: {message}"
        super().__init__(full_message)


if __name__ == "__main__":
    from rich.console import Console

    console = Console()
    console.rule("Gradient Examples")
    example1 = Gradient(
        "Hello, World! This is a gradient Text example with random colors."
    )
    console.print(example1)
    console.line(2)
    console.rule("Gradient with Rainbow")
    console.print(
        Text(
            "This is a gradient Text example with rainbow colors. \
Note that Gradient's justify argument is set to 'right':",
            style="bold #ff00ff",
            justify="center",
        )
    )
    console.print(
        Gradient(
            """
Ullamco culpa tempor anim duis nulla ad in. Quis ad sint culpa aliquip voluptate magna adipisicing deserunt anim sunt minim eu incididunt sit mollit. Enim incididunt pariatur magna. Sint amet ipsum reprehenderit elit sunt sunt laborum reprehenderit labore. Ipsum dolore laborum et ad commodo consectetur aute Lorem commodo.

Mollit irure aute tempor laborum culpa excepteur duis sit. Ut id sint incididunt ea mollit proident est exercitation dolore tempor eiusmod sint nulla do culpa. Lorem mollit velit laboris id ad irure pariatur excepteur cupidatat ad fugiat occaecat qui enim. Aliquip irure dolore ut sunt sunt non. Eu ut incididunt anim aute non.

Anim reprehenderit ut laboris aute ipsum ex aute ea labore. Non amet duis ad. Consequat non in et elit sit ex fugiat laborum est laborum enim in consectetur ad. Labore quis aliqua officia reprehenderit magna cillum officia. Ullamco fugiat labore adipisicing. Magna aute irure excepteur veniam excepteur et sit sunt. Dolor amet mollit qui est nisi elit enim eu aute. Incididunt est dolor nulla.""",
            rainbow=True,
            justify="right",
        )
    )
