"""Compatibility wrapper for :mod:`rich_color_ext` optional helpers."""

from __future__ import annotations

import sys
from collections.abc import Callable
from functools import lru_cache
from typing import cast

# rich_color_ext (<=0.1.x) installs Rich's traceback handler as an import side
# effect; restore whatever excepthook the host application had once the import
# completes. Caveats: under IPython/Jupyter, rich.traceback.install patches the
# shell's showtraceback rather than sys.excepthook, so this restore cannot
# undo it there; and a hook installed by another thread between snapshot and
# restore would be clobbered. rich-color-ext >= 0.2.0 removes the side effect
# at the source, making this a defensive no-op.
_previous_excepthook = sys.excepthook
try:
    import rich_color_ext as _rce
except ImportError as exc:  # pragma: no cover - dependency missing
    raise ImportError(
        "rich-gradient requires the 'rich-color-ext' package at runtime."
    ) from exc
finally:
    sys.excepthook = _previous_excepthook
del _previous_excepthook

__all__ = ["get_css_map", "install", "is_installed"]

def _fetch_callable(name: str, default: Callable[[], object]) -> Callable[[], object]:
    """Return a callable attribute from ``rich_color_ext`` or a default fallback."""
    # Lookup is dynamic because older versions may lack these helpers.
    attr = getattr(_rce, name, None)
    if callable(attr):
        return cast(Callable[[], object], attr)
    return default


def _noop_install() -> None:
    """Fallback install hook for older ``rich_color_ext`` releases."""


def _default_is_installed() -> bool:
    """Fallback indicating the extension is effectively always installed."""
    return True


install: Callable[[], object] = _fetch_callable("install", _noop_install)
is_installed: Callable[[], object] = _fetch_callable("is_installed", _default_is_installed)


@lru_cache(maxsize=1)
def get_css_map() -> dict[str, str]:
    """Return the CSS color mapping, falling back gracefully if unavailable."""
    # Prefer the extension's map if present; otherwise degrade to an empty mapping.
    getter = getattr(_rce, "get_css_map", None)
    if callable(getter):
        return cast(Callable[[], dict[str, str]], getter)()
    # Older releases lacked get_css_map, so return an empty mapping instead of failing.
    return {}
