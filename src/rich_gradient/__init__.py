"""Public package interface for rich-gradient."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from rich.console import Console
from rich.traceback import install as tr_install

from rich_gradient._color_ext import get_css_map, is_installed
from rich_gradient._color_ext import install as rc_install
from rich_gradient._logger import get_logger
from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.animated_markdown import AnimatedMarkdown
from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.animated_rule import AnimatedRule
from rich_gradient.animated_text import AnimatedText
from rich_gradient.columns import Columns
from rich_gradient.config import RichGradientConfig
from rich_gradient.config import config as _config
from rich_gradient.config import reload_config as _reload_config
from rich_gradient.default_styles import DEFAULT_STYLES
from rich_gradient.gradient import ColorType, Gradient
from rich_gradient.markdown import Markdown
from rich_gradient.panel import Panel
from rich_gradient.pretty import Pretty
from rich_gradient.rule import Rule
from rich_gradient.spectrum import Spectrum
from rich_gradient.syntax import Syntax
from rich_gradient.table import Table
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme
from rich_gradient.tree import Tree

if not is_installed():
    rc_install()


def install_tracebacks(**kwargs: Any) -> None:
    """Install Rich's pretty traceback handler for uncaught exceptions.

    This replaces ``sys.excepthook`` process-wide, so rich-gradient no longer
    does it automatically on import. Call this once from your application if
    you want Rich-formatted tracebacks, or set the environment variable
    ``RICH_GRADIENT_TRACEBACKS=1`` before import to restore the old automatic
    behavior.

    Args:
        **kwargs: Forwarded to :func:`rich.traceback.install`
            (e.g. ``show_locals=True``, ``width``, ``suppress``).
    """
    tr_install(**kwargs)


# Opt-in escape hatch: restore the pre-0.4.0 automatic install without a
# code change. Accepts the same truthy values as RICH_GRADIENT_ANIMATE.
if os.environ.get("RICH_GRADIENT_TRACEBACKS", "").lower() in ("1", "true", "yes", "on"):
    install_tracebacks()


__all__ = [
    "CONFIG",
    "DEFAULT_STYLES",
    "GRADIENT_TERMINAL_THEME",
    "AnimatedGradient",
    "AnimatedMarkdown",
    "AnimatedPanel",
    "AnimatedRule",
    "AnimatedText",
    "ColorType",
    "Columns",
    "Console",
    "Gradient",
    "GradientTheme",
    "Markdown",
    "Panel",
    "Pretty",
    "RichGradientConfig",
    "Rule",
    "Spectrum",
    "Syntax",
    "Table",
    "Text",
    "Tree",
    "config",
    "get_css_map",
    "get_logger",
    "install_tracebacks",
    "reload_config",
]

__version__ = "0.3.15"


# Set up logging
logger: Any = get_logger(enabled=False)
logger.disable("rich_gradient")


# Backwards-compatible constant expected by legacy tests/importers
config = _config
CONFIG = config


def reload_config(config_path: Path | None = None) -> RichGradientConfig:
    """Reload runtime configuration and update package-level aliases.

    Args:
        config_path: Optional path to a configuration file.

    Returns:
        The reloaded runtime configuration.
    """

    updated: RichGradientConfig = _reload_config(config_path)
    globals()["config"] = updated
    globals()["CONFIG"] = updated
    return updated
