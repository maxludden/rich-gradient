""""A gradient generator for the Rich library."""
from rich.console import Console
from rich.traceback import install

from rich_gradient.color import RGBA, ColorError, ColorType, Color
# from rich_gradient.color import Color
from rich_gradient.default_styles import DEFAULT_STYLES
from rich_gradient.gradient import Gradient
from rich_gradient.rule import GradientRule
from rich_gradient.spectrum import Spectrum
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

__all__ = [
    "Color",
    "ColorError",
    "ColorType",
    "DEFAULT_STYLES",
    "Gradient",
    "GradientRule",
    "GRADIENT_TERMINAL_THEME",
    "GradientTheme",
    "RGBA",
    "Spectrum",
]

console: Console = Console()
install(console=console)
