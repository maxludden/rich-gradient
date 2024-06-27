# ruff: noqa: F401
from pydantic_extra_types.color import ColorType

from rich_gradient.color import Color
from rich_gradient.default_styles import DEFAULT_STYLES
from rich_gradient.gradient import Gradient
from rich_gradient.spectrum import Spectrum
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

__all__ = [
    "Color",
    "ColorType",
    "DEFAULT_STYLES",
    "Gradient",
    "GRADIENT_TERMINAL_THEME",
    "GradientTheme",
    "Spectrum",
]
