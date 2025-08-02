""" "A gradient generator for the Rich library."""

from rich.color import Color, ColorParseError, ColorType
from rich.console import Console
from rich.traceback import install as tr_install

from rich_color_ext import install
from rich_gradient.default_styles import DEFAULT_STYLES
from rich_gradient.gradient import Gradient
from rich_gradient.rule import Rule
from rich_gradient.spectrum import Spectrum
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

__all__ = [
    "Console",
    "Color",
    "ColorParseError",
    "ColorType",
    "DEFAULT_STYLES",
    "Gradient",
    "Rule",
    "GRADIENT_TERMINAL_THEME",
    "GradientTheme",
    "Spectrum",
    "tr_install",
    "install",
]

