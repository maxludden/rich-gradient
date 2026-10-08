"""Thin wrapper around :mod:`rich_color_ext` (>= 3.0.0).

rich-color-ext extends ``rich.color.Color.parse`` with 3-digit hex codes and CSS
color names by monkey-patching Rich. This module centralizes that dependency so
the rest of the package never touches the patch state directly.
"""

from __future__ import annotations

from rich.color import Color

try:
    from rich_color_ext import get_css_map, install, is_installed
except ImportError as exc:  # pragma: no cover - dependency missing/too old
    raise ImportError(
        "rich-gradient requires 'rich-color-ext>=3.0.0' at runtime."
    ) from exc

__all__ = ["ensure_installed", "get_css_map", "install", "is_installed", "parse_color"]

_HEX_DIGITS = frozenset("0123456789abcdef")


def ensure_installed() -> None:
    """Install the ``Color.parse`` extension if it is not already active."""
    if not is_installed():
        install()


def parse_color(value: str) -> Color:
    """Parse a gradient color string, resolving CSS names and ``#abc`` hex first.

    rich-color-ext >= 3.0 lets Rich's own parser win, so names that Rich also
    defines (``red``, ``blue``, ``purple``, ``yellow``, ...) resolve to the
    terminal-dependent ANSI palette. Gradient stops need exact, theme-independent
    colors, so CSS names and 3-digit hex codes are resolved here, before
    ``Color.parse``. This also keeps gradients working when the patch is not
    installed (e.g. after ``rich_color_ext.uninstall()``) without re-patching
    Rich behind the application's back.

    Anything else (6-digit hex, ``rgb(...)``, ``color(n)``, ``default``) is
    delegated to ``Color.parse``.

    Raises:
        ColorParseError: If ``value`` is not a valid color in any supported form.
    """
    key = value.strip().lower()
    css_hex = get_css_map().get(key)
    if css_hex is not None:
        return Color.parse(css_hex)
    if len(key) == 4 and key[0] == "#" and _HEX_DIGITS.issuperset(key[1:]):
        return Color.parse("#" + "".join(ch * 2 for ch in key[1:]))
    return Color.parse(value)
