import time
from colorsys import hls_to_rgb
from typing import Optional, List, Union, Literal, cast

from rich import get_console as _get_console
from rich.console import Console, JustifyMethod
from rich.live import Live
from rich.text import Text
from rich.segment import Segment
from rich.color import Color
from rich.style import Style
from rich.traceback import install



def get_console(console: Optional[Console] = None) -> Console:
    """Get the console instance."""
    if console is None:
        return _get_console()
    install(console=console)
    global console_width
    console_width = console.width
    return console

def hsl_to_rgb_int(h: float, s: float, l: float) -> tuple[int, int, int]:
    r, g, b = hls_to_rgb(h, l, s)
    return int(r * 255), int(g * 255), int(b * 255)

console: Console = get_console()
console_width: int =  console.width


class Gradient(Text):
    def __init__(
        self,
        text: str,
        colors: Optional[List[str]] = None,
        justify: JustifyMethod = "left",
        spread: float = console_width,
        saturation: float = 1.0,
        lightness: float = 0.5,
        offset: float = 0.0,
    ):
        super().__init__(justify=cast(JustifyMethod, justify))
        self.colors = colors
        self.spread = spread
        self.saturation = saturation
        self.lightness = lightness
        self.offset = offset
        # self.justify: JustifyMethod = cast(JustifyMethod, justify)
        width = int(spread)
        lines = text.splitlines()
        for line_number, line in enumerate(lines):
            padded = line.ljust(width)
            line_text = Text(justify=self.justify)
            for i, char in enumerate(padded):
                color = self.get_color_at(i, width)
                line_text.append(char, style=Style(color=color))
            self.append(line_text)
            self.append("\n")

    def get_color_at(self, index: int, width: int) -> str:
        if self.colors:
            count = len(self.colors)
            left = self.colors[index * count // width % count]
            right = self.colors[(index * count // width + 1) % count]
            return left
        else:
            hue = (self.offset + index / width) % 1.0
            r, g, b = hsl_to_rgb_int(hue, self.saturation, self.lightness)
            return f"#{r:02x}{g:02x}{b:02x}"


def animated_lolcat_multiline(
    text: str,
    duration: float = 10,
    fps: float = 30,
    spread: float = console_width,
    speed: float = 0.01,
    justify: JustifyMethod = "left",
    colors: Optional[List[str]] = None,
    saturation: float = 1.0,
    lightness: float = 0.5,
):
    console = Console()
    offset = 0.0
    start_time = time.time()
    with Live(
        Gradient(
            text,
            colors=colors,
            justify=justify,
            spread=spread,
            saturation=saturation,
            lightness=lightness,
            offset=offset,
        ),
        console=console,
        refresh_per_second=fps,
    ) as live:
        while (time.time() - start_time) < duration:
            offset += speed
            live.update(
                Gradient(
                    text,
                    colors=colors,
                    justify=justify,
                    spread=spread,
                    saturation=saturation,
                    lightness=lightness,
                    offset=offset,
                )
            )
            time.sleep(1 / fps)


# Example usage
if __name__ == "__main__":
    lorem_ipsum = """Lorem ipsum dolor sit amet, consectetur adipiscing elit.
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.
Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""
    sample = """🌈 This is an animated rainbow lolcat
that works across multiple lines!
Enjoy the vibrant colors 🎨
and the beauty of terminal art ✨"""
    long_sample = f"{sample}\n\n{lorem_ipsum}"
    console.print(Gradient(long_sample), justify="center")
