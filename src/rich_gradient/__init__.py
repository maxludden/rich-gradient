"""rich_gradient"""

from __future__ import annotations

from rich.console import Console
from rich.traceback import install as tr_install
from rich_color_ext import install as rc_install

from rich_gradient._logger import get_logger
from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.animated_markdown import AnimatedMarkdown
from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.animated_rule import AnimatedRule
from rich_gradient.default_styles import DEFAULT_STYLES
from rich_gradient.gradient import ColorType, Gradient
from rich_gradient.markdown import Markdown
from rich_gradient.panel import Panel
from rich_gradient.rule import Rule
from rich_gradient.spectrum import Spectrum
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

# Monkeypatch rich.color.Color to support CSS color names and 3-digit hex codes
rc_install()
tr_install()

__all__ = [
    "AnimatedGradient",
    "AnimatedPanel",
    "AnimatedRule",
    "AnimatedMarkdown",
    "Console",
    "ColorType",
    "DEFAULT_STYLES",
    "Gradient",
    "Markdown",
    "Text",
    "Panel",
    "Rule",
    "GRADIENT_TERMINAL_THEME",
    "GradientTheme",
    "Spectrum",
]

__version__ = "0.3.8"


# Set up logging
logger = get_logger(False)
logger.disable("rich_gradient")
