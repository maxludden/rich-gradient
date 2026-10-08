"""Thin wrapper around :mod:`rich_color_ext` (>= 3.0.0).

rich-color-ext extends ``rich.color.Color.parse`` with 3-digit hex codes and CSS
color names by monkey-patching Rich. This module centralizes that dependency so
the rest of the package never touches the patch state directly.
"""

from __future__ import annotations

from rich.color import Color, ColorParseError

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
    """Parse a color string the way rich-color-ext >= 3.0 does: Rich first.

    Rich's own parser always runs first, so anything Rich understands (including
    its ANSI names such as ``red``, ``blue`` or ``purple``) resolves exactly as
    ``rich.color.Color.parse`` does. Only if Rich rejects the input are CSS
    color names and ``#abc`` hex codes tried.

    With rich-color-ext installed ``Color.parse`` already does this; the explicit
    fallback keeps CSS names working when the patch has been removed (e.g. after
    ``rich_color_ext.uninstall()``) without re-patching Rich behind the
    application's back.

    Raises:
        ColorParseError: If ``value`` is not a valid color in any supported form.
    """
    try:
        return Color.parse(value)
    except ColorParseError:
        key = value.strip().lower()
        if len(key) == 4 and key[0] == "#" and _HEX_DIGITS.issuperset(key[1:]):
            return Color.parse("#" + "".join(ch * 2 for ch in key[1:]))
        css_hex = get_css_map().get(key)
        if css_hex is not None:
            return Color.parse(css_hex)
        raise
