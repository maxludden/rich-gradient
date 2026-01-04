"""Compatibility wrapper for :mod:`rich_color_ext` optional helpers."""

from __future__ import annotations

from functools import lru_cache
from typing import Callable, Dict

try:
    import rich_color_ext as _rce
except ImportError as exc:  # pragma: no cover - dependency missing
    raise ImportError(
        "rich-gradient requires the 'rich-color-ext' package at runtime."
    ) from exc

def _fetch_callable(name: str, default: Callable[[], object]) -> Callable:
    attr = getattr(_rce, name, None)
    if callable(attr):
        return attr
    return default


def _noop_install() -> None:
    return None


def _default_is_installed() -> bool:
    return True


install = _fetch_callable("install", _noop_install)
is_installed = _fetch_callable("is_installed", _default_is_installed)


@lru_cache(maxsize=1)
def get_css_map() -> Dict[str, str]:
    """Return the CSS color mapping, falling back gracefully if unavailable."""
    getter = getattr(_rce, "get_css_map", None)
    if callable(getter):
        return getter() # type: ignore
    # Older releases lacked get_css_map, so return an empty mapping instead of failing.
    return {}


__all__ = ["install", "is_installed", "get_css_map"]
