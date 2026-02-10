"""rich_gradient"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.traceback import install as tr_install

from rich_gradient._color_ext import get_css_map
from rich_gradient._color_ext import install as rc_install
from rich_gradient._color_ext import is_installed
from rich_gradient._logger import get_logger
from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.animated_markdown import AnimatedMarkdown
from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.animated_rule import AnimatedRule
from rich_gradient.animated_text import AnimatedText
from rich_gradient.config import RichGradientConfig
from rich_gradient.config import config as _config
from rich_gradient.config import reload_config as _reload_config
from rich_gradient.default_styles import DEFAULT_STYLES
from rich_gradient.gradient import ColorType, Gradient
from rich_gradient.markdown import Markdown
from rich_gradient.panel import Panel
from rich_gradient.rule import Rule
from rich_gradient.spectrum import Spectrum
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

if not is_installed():
    rc_install()
tr_install()  # Install rich traceback handler


__all__ = [
    "AnimatedGradient",
    "AnimatedPanel",
    "AnimatedRule",
    "AnimatedMarkdown",
    "AnimatedText",
    "CONFIG",
    "config",
    "reload_config",
    "Console",
    "ColorType",
    "DEFAULT_STYLES",
    "get_css_map",
    "Gradient",
    "RichGradientConfig",
    "Markdown",
    "Text",
    "Panel",
    "Rule",
    "GRADIENT_TERMINAL_THEME",
    "GradientTheme",
    "Spectrum",
]

__version__ = "0.3.11"


# Set up logging
logger = get_logger(False)
logger.disable("rich_gradient")


# Backwards-compatible constant expected by legacy tests/importers
config = _config
CONFIG = config


def reload_config(config_path: Optional[Path] = None) -> RichGradientConfig:
    """Reload runtime configuration and update package-level aliases."""

    updated = _reload_config(config_path)
    globals()["config"] = updated
    globals()["CONFIG"] = updated
    return updated
