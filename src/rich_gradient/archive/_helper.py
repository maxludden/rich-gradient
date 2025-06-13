from colorsys import hls_to_rgb, rgb_to_hls
from functools import lru_cache
from typing import Optional, Union

from loguru import logger
from rich import get_console as _get_console
from rich.console import Console, ConsoleOptions, RenderResult
from rich.live import Live
from rich.segment import Segment, Segments, SegmentLines
from rich.style import Style as RichStyle
from rich.text import Text
from rich.traceback import install as install_tr


__all__ = [
    "get_console",
    "_hsl_to_rgb_hex",
    "_hex_to_rgb",
    "_rgb_to_hex",
]

def get_console(
    console: Optional[Console] = None,
    record: bool = False,
    width: Optional[int] = None
) -> Console:
    """Get the console instance.
    Args:
        console: Optional console instance with rich tracebacks.. \
If not provided, the default console is used.
    Returns:
        Console instance.
    """
    if console is None:
        console = _get_console()
    install_tr(console=console)
    return console

def lorem(paragraphs: int = 3) -> str:
    """Generate a string of Lorem Ipsum text.

    Args:
        paragraphs: Number of paragraphs to generate.

    Returns:
        Lorem Ipsum text.
    """
    from lorem_text import lorem as _lorem
    return _lorem.paragraphs(paragraphs)


def _hsl_to_rgb_hex(h: float, s: float, l: float) -> str:
    """Convert an HSL color to a hex RGB string.

    Args:
        h: Hue component (0–1).
        s: Saturation component (0–1).
        l: Lightness component (0–1).

    Returns:
        Hex RGB color string.
    """
    r, g, b = hls_to_rgb(h, l, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


@lru_cache(maxsize=1024)
def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex color string to an RGB tuple."""
    if hex_color.startswith("#"):
        hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    if len(hex_color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    if any(c not in "0123456789abcdefABCDEF" for c in hex_color):
        raise ValueError(f"Invalid hex color: {hex_color}")
    return (
        int(hex_color[:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:], 16),
    )


@lru_cache(maxsize=1024)
def _rgb_to_hex(rgb: tuple[int, ...]) -> str:
    """
    Convert an RGB tuple to a hex color string.

    Args:
        rgb (tuple[int, int, int]): Tuple with three integer components (0–255).

    Returns:
        str: Hexadecimal color string.
    """
    if len(rgb) != 3 or not all(isinstance(c, int) and 0 <= c <= 255 for c in rgb):
        raise ValueError(f"Invalid RGB tuple: {rgb}")
    return "#{:02x}{:02x}{:02x}".format(*rgb)
