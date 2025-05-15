from __future__ import annotations

import inspect
from typing import List, Optional, Union
from io import StringIO

from rich.markup import render
from rich.color import blend_rgb
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.text import Span, Text
from rich._wrap import divide_line
from rich.traceback import install

from snoop import snoop
from cheap_repr import register_repr, normal_repr

from rich_gradient.color import ColorType, Color
from rich_gradient.spectrum import Spectrum
from rich_gradient.style import Style, StyleType
from loguru import logger

DEFAULT_JUSTIFY = "default"
DEFAULT_OVERFLOW = "fold"
VERBOSE: bool = True

console: Console = Console()
install(console=console, show_locals=True)


class Gradient(Text):
    """A Text subclass that renders each line with a smooth horizontal gradient."""

    # @snoop(watch="self.renderable, self.styles" )
    def __init__(
        self,
        renderable: Union[str, Text, Gradient],
        styles: Optional[List[StyleType]] = None,
        *,
        rainbow: bool = False,
        hues: int = 5,
        justify: JustifyMethod = DEFAULT_JUSTIFY,
        overflow: OverflowMethod = DEFAULT_OVERFLOW,
        end: str = "\n",
        no_wrap: bool = False,
        angle: float = 1.5  # Reserved for future use
    ) -> None:
        super().__init__("")
        self.console = Console()
        self.console_width = self.console.width
        self.justify = justify
        self.overflow = overflow
        self.no_wrap = no_wrap
        self.end = end
        self.angle = angle
        self.rainbow = rainbow
        self.hues = hues

        self.lines: List[str] = self._extract_lines(renderable)  # type: ignore
        line_count = len([l for l in self.lines if l])

        if styles is None:
            self.hues = line_count
            spectrum = Spectrum(length=self.hues)
            self.styles = [Style(color=color.hex) for color in spectrum]
        elif self.rainbow:
            self.styles = [Style(color=color.hex) for color in Spectrum(18)]
        else:
            self.styles: List[Style] = self._build_styles(styles)  # type: ignore

        self._apply_gradient()  # type: ignore


    def _extract_lines(self, renderable: Union[str, Text, Gradient]) -> List[str]:
        """Wrap the input to console width and preserve original newlines."""
        if VERBOSE:
            console.log(f"Entered Gradient._extract_lines with renderable:\n\n{renderable}")
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
                lines.append(raw_line[start:])
        if VERBOSE:
            for final_index, line in enumerate(lines):
                console.log(f"[b #999] Line {final_index}:[/] [{log_spectrum[index]}]{line!r}[/]")
        return lines




    # @snoop
    def _build_styles(self, styles: Optional[List[StyleType]]) -> List[Style]:
        """Build styles from the provided list or generate a rainbow spectrum."""
        if VERBOSE:
            console.log(
                Text(
                    f"\n\nEntered Gradient._build_styles with styles:\n\n\
{", ".join([str(style) for style in styles]) if styles else "[b red]"}", style="bold #99ff00"))
        if styles is None and self.rainbow:
            return [Style(color=color.hex) for color in Spectrum(18)]

        if not styles:
            spectrum: List[Color] = Spectrum(length=self.hues)

            parsed_styles = [Style(color=color.hex) for color in spectrum]
            if VERBOSE:
                console.log("Parsed styles:")
                for style in parsed_styles:
                    console.print(f"\t\t\t[{style}]{'█' * 10}[/]")
            return parsed_styles

        parsed_styles = [Style.parse(style) if not isinstance(style, Style) else style for style in styles]

        if len(parsed_styles) < 2:
            raise GradientError(
                "Gradient requires at least two styles. "
                "Please provide a list of styles or set the rainbow parameter to True."
            )
        if VERBOSE:
            console.log("[b #fff]Parsed styles:[/]")
            for style in parsed_styles:
                console.print(f"[{style}]{'█' * 10}[/]")

        return parsed_styles

    # @snoop(watch="self._text, self._spans")
    def _apply_gradient(self) -> None:
        self._text = ""
        self._spans.clear()

        width = self.console_width
        hues = len(self.styles)
        justify = self.console.options.justify or DEFAULT_JUSTIFY

        for line in self.lines:
            line_len = len(line)
            if line_len == 0:
                self._text += "\n"
                continue

            padding = self._calculate_padding(justify, width, line_len)
            self._text += " " * padding

            for x, char in enumerate(line):
                visual_column = padding + x
                pos_ratio = visual_column / max(1, width - 1)
                index = pos_ratio * (hues - 1)
                lower = int(index)
                upper = min(lower + 1, hues - 1)
                interp = index - lower

                color1 = self.styles[lower].color or self.styles[0].color
                color2 = self.styles[upper].color or self.styles[-1].color

                c1 = color1.as_triplet()
                c2 = color2.as_triplet()
                blended = blend_rgb(c1, c2, interp)
                hex_color = f"#{blended.red:02x}{blended.green:02x}{blended.blue:02x}"

                style = Style(color=hex_color)
                start = len(self._text)
                self._text += char
                self._spans.append(Span(start, start + 1, style))

            self._text += "\n"

    # @snoop
    def _calculate_padding(self, justify: str, width: int, line_len: int) -> int:
        if justify == "center":
            return max((width - line_len) // 2, 0)
        if justify == "right":
            return max(width - line_len, 0)
        return 0


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
    sample = """
Duis veniam est eiusmod laboris labore ex elit dolore fugiat aliqua qui minim sit. Proident dolore in eu sit. Non in sunt in. Qui proident commodo est minim ex velit consectetur sunt laboris culpa nulla nulla mollit. Dolor velit non aute. Esse voluptate occaecat mollit cupidatat cillum do. Adipisicing est exercitation duis ea commodo amet. Officia non consectetur consectetur anim excepteur culpa.

Eu fugiat exercitation pariatur tempor ullamco duis ullamco in excepteur in incididunt et occaecat duis consequat. Aliquip dolor fugiat esse ad non ad exercitation ea aliquip irure non. Nulla consectetur fugiat tempor Lorem sit quis do voluptate nisi nisi do occaecat veniam. Aliquip sunt ad labore voluptate qui officia aliqua ipsum. Velit nostrud cupidatat aliqua aute proident aliqua officia aliqua adipisicing magna.

Id pariatur sit adipisicing exercitation aute. Ex elit ex tempor exercitation eu consectetur non consectetur irure ut veniam officia ipsum. Tempor ea duis Lorem sint ex eiusmod amet Lorem. Ipsum eiusmod nisi eiusmod in duis enim fugiat aliquip culpa in esse. Ex velit duis nulla non eu nulla do dolor pariatur culpa ullamco adipisicing enim. Elit mollit ea incididunt aliquip dolore magna commodo. Minim occaecat sint tempor sit veniam ullamco nostrud nulla dolor irure ut minim laborum sit anim. Voluptate pariatur culpa aliquip."""

    console.rule("Gradient Examples")
    console.print(Gradient(sample))
    console.print(Gradient(sample, justify="center"), justify="center")
    console.rule("Gradient with Rainbow")
    console.print(Gradient(sample, rainbow=True))
