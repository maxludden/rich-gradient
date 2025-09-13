from typing import List, cast

import rich.console as _rc
from rich.text import Text as RichText
from rich_color_ext import install

from rich_gradient._logger import get_logger
from rich_gradient.gradient import Gradient
from rich_gradient.rule import Rule
from rich_gradient.spectrum import Spectrum
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

__all__ = [
    "Text",
    "Gradient",
    "Rule",
    "GradientTheme",
    "GRADIENT_TERMINAL_THEME",
    "Spectrum",
]

# Install rich_color_ext
install()

# Set up logging
logger = get_logger(False)
logger.disable("rich_gradient")
