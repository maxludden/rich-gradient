"""rich_gradient"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.traceback import install as tr_install

from ._color_ext import get_css_map
from ._color_ext import install as rc_install
from ._color_ext import is_installed

from ._logger import get_logger
from .animated_gradient import AnimatedGradient
from .animated_markdown import AnimatedMarkdown
from .animated_panel import AnimatedPanel
from .animated_rule import AnimatedRule
from .config import RichGradientConfig
from .config import config as _config
from .config import reload_config as _reload_config
from .default_styles import DEFAULT_STYLES
from .gradient import ColorType, Gradient
from .markdown import Markdown
from .panel import Panel
from .rule import Rule
from .spectrum import Spectrum
from .text import Text
from .theme import GRADIENT_TERMINAL_THEME, GradientTheme

if not is_installed():
    rc_install()
tr_install()  # Install rich traceback handler


__all__ = [
    "AnimatedGradient",
    "AnimatedPanel",
    "AnimatedRule",
    "AnimatedMarkdown",
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

__version__ = "0.3.9"


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
