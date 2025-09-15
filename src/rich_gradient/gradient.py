"""Public Gradient facade and factory.

This module exposes a `Gradient` factory which returns either a static
`BaseGradient` or an `AnimatedGradient` depending on the constructor flag.

Usage examples:
    Gradient("Hello", colors=["#f00", "#0f0"])              -> BaseGradient
    Gradient("Hello", colors=["#f00", "#0f0"], animated=True) -> AnimatedGradient

Keeping the public import stable avoids duplication and hides internal
implementation details.
"""

from __future__ import annotations

from typing import Any

from ._base_gradient import BaseGradient
from ._animated_gradient import AnimatedGradient

__all__ = ["Gradient"]


class Gradient:
    """Factory that returns `BaseGradient` or `AnimatedGradient`.

    If `animated=True` (or `animate=True`) is passed, an `AnimatedGradient`
    instance is constructed; otherwise a `BaseGradient` is returned. All other
    positional and keyword arguments are forwarded to the chosen implementation.
    """

    def __new__(cls, *args: Any, **kwargs: Any):  # type: ignore[override]
        # Support both `animated` (preferred) and `animate` (compat) flags
        animated = bool(kwargs.pop("animated", False) or kwargs.pop("animate", False))
        if animated:
            return AnimatedGradient(*args, **kwargs)
        return BaseGradient(*args, **kwargs)
