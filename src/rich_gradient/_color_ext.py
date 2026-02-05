"""Compatibility wrapper for :mod:`rich_color_ext` optional helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Callable, Dict, cast

try:
    import rich_color_ext as _rce
except ImportError as exc:  # pragma: no cover - dependency missing
    raise ImportError(
        "rich-gradient requires the 'rich-color-ext' package at runtime."
    ) from exc

__all__ = ["install", "is_installed", "get_css_map"]

def _fetch_callable(name: str, default: Callable[[], object]) -> Callable[[], object]:
    """Return a callable attribute from ``rich_color_ext`` or a default fallback."""
    # Lookup is dynamic because older versions may lack these helpers.
    attr = getattr(_rce, name, None)
    if callable(attr):
        return cast(Callable[[], object], attr)
    return default


def _noop_install() -> None:
    """Fallback install hook for older ``rich_color_ext`` releases."""
    return None


def _default_is_installed() -> bool:
    """Fallback indicating the extension is effectively always installed."""
    return True


install: Callable[[], object] = _fetch_callable("install", _noop_install)
is_installed: Callable[[], object] = _fetch_callable("is_installed", _default_is_installed)


@lru_cache(maxsize=1)
def get_css_map() -> Dict[str, str]:
    """Return the CSS color mapping, falling back gracefully if unavailable."""
    # Prefer the extension's map if present; otherwise degrade to an empty mapping.
    getter = getattr(_rce, "get_css_map", None)
    if callable(getter):
        return cast(Callable[[], Dict[str, str]], getter)()
    # Older releases lacked get_css_map, so return an empty mapping instead of failing.
    return {}
