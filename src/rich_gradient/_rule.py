from typing import Union
from rich.console import Console, ConsoleOptions, RenderResult
from rich.jupyter import JupyterMixin
from rich.rule import Rule
from rich.segment import Segment
from rich.text import Text
from rich_gradient.gradient import Gradient
from rich_gradient.spectrum import Spectrum

# File: rich_gradient/_rule.py





class GradientRule(JupyterMixin):
    """
    A renderable that draws a horizontal rule with a gradient.
    """

    def __init__(
        self,
        title: Union[str, Text] = "",
        *,
        characters: str = "─",
        color_steps: int = 10,
    ) -> None:
        self.title = title
        self.characters = characters
        # build a spectrum of colors for the gradient
        self.styles = Spectrum(color_steps)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        # First render a standard Rule to segments
        rule = Rule(self.title, characters=self.characters)
        segments = console.render(rule, options)

        # Collect text and existing styles into a Text buffer
        text = Text()
        for segment in segments:
            text.append(segment.text, style=segment.style)

        # Ensure it exactly fits the console width
        width = options.max_width
        plain = text.plain
        if len(plain) < width:
            plain = plain.ljust(width)
        else:
            plain = plain[:width]

        # Yield as a Gradient, cycling through our styles
        yield Gradient(plain, styles=self.styles)
