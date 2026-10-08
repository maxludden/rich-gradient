"""Thin wrapper around :mod:`rich_color_ext` (>= 2.0.0).

rich-color-ext extends ``rich.color.Color.parse`` with 3-digit hex codes and CSS
color names by monkey-patching Rich. This module centralizes that dependency so
the rest of the package never touches the patch state directly.
"""

from __future__ import annotations

from rich.color import Color, ColorParseError

try:
    from rich_color_ext import get_css_map, install, is_installed
    from rich_color_ext.hex_utils import expand_3digit_hex, is_3digit_hex
except ImportError as exc:  # pragma: no cover - dependency missing/too old
    raise ImportError(
        "rich-gradient requires 'rich-color-ext>=2.0.0' at runtime."
    ) from exc

__all__ = ["ensure_installed", "get_css_map", "install", "is_installed", "parse_color"]


def ensure_installed() -> None:
    """Install the ``Color.parse`` extension if it is not already active."""
    if not is_installed():
        install()


def parse_color(value: str) -> Color:
    """Parse a color string, accepting CSS names and 3-digit hex codes.

    ``Color.parse`` already understands these once rich-color-ext is installed.
    If the patch was removed (e.g. someone called ``rich_color_ext.uninstall()``),
    resolve them directly so gradients keep working without re-patching Rich
    behind the application's back.

    Raises:
        ColorParseError: If ``value`` is not a valid color in any supported form.
    """
    try:
        return Color.parse(value)
    except ColorParseError:
        key = value.strip().lower()
        if is_3digit_hex(key):
            return Color.parse(expand_3digit_hex(key))
        css_hex = get_css_map().get(key)
        if css_hex is not None:
            return Color.parse(css_hex)
        raise
