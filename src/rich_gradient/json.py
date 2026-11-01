"""Gradient-enabled convenience wrapper for Rich JSON."""

from __future__ import annotations

import json as json_module
from collections.abc import Callable, Sequence
from typing import Any, cast

from rich.align import AlignMethod, VerticalAlignMethod
from rich.console import Console, ConsoleRenderable
from rich.json import JSON as RichJSON

from rich_gradient.gradient import (ColorType, Gradient, HighlightRegexType,
                                    HighlightWordsType)


class JSON(Gradient):
    """Render JSON text with a gradient layered over Rich's JSON formatting.

    Args:
        json: A JSON string to format.
        indent: Indent size, or a string, passed to Rich.
        highlight: Whether Rich should syntax-highlight the output.
        skip_keys: Skip non-basic dict keys instead of raising.
        ensure_ascii: Escape non-ASCII characters.
        check_circular: Check for circular references.
        allow_nan: Allow NaN and infinity values.
        default: Optional serializer for unsupported objects.
        sort_keys: Whether to sort dictionary keys.
        colors: Foreground gradient color stops.
        bg_colors: Background gradient color stops.
        rainbow: Whether to generate a rainbow palette.
        hues: Number of auto-generated hues.
        repeat_scale: Gradient repeat scale; ``None`` derives it from the stops.
        expand: Whether the gradient frame expands.
        justify: Horizontal alignment.
        vertical_justify: Vertical alignment.
        console: Optional Rich console.
        highlight_words: Word highlight configuration.
        highlight_regex: Regex highlight configuration.
    """

    def __init__(
        self,
        json: str,
        *,
        indent: int | str | None = 2,
        highlight: bool = True,
        skip_keys: bool = False,
        ensure_ascii: bool = False,
        check_circular: bool = True,
        allow_nan: bool = True,
        default: Callable[[Any], Any] | None = None,
        sort_keys: bool = False,
        colors: Sequence[ColorType] | None = None,
        bg_colors: Sequence[ColorType] | None = None,
        rainbow: bool = False,
        hues: int = 5,
        repeat_scale: float | None = None,
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        console: Console | None = None,
        highlight_words: HighlightWordsType | None = None,
        highlight_regex: HighlightRegexType | None = None,
    ) -> None:
        """Initialize a gradient-enabled Rich JSON renderable."""
        rich_json = RichJSON(
            json,
            indent=indent,
            highlight=highlight,
            skip_keys=skip_keys,
            ensure_ascii=ensure_ascii,
            check_circular=check_circular,
            allow_nan=allow_nan,
            default=default,
            sort_keys=sort_keys,
        )
        self._json = rich_json
        super().__init__(
            cast(ConsoleRenderable, rich_json),
            colors=list(colors) if colors is not None else None,
            bg_colors=list(bg_colors) if bg_colors is not None else None,
            console=console,
            hues=hues,
            rainbow=rainbow,
            expand=expand,
            justify=justify,
            vertical_justify=vertical_justify,
            repeat_scale=repeat_scale,
            highlight_words=highlight_words,
            highlight_regex=highlight_regex,
        )

    @classmethod
    def from_data(cls, data: Any, **kwargs: Any) -> JSON:
        """Build a gradient JSON renderable from a Python object.

        Args:
            data: Object to serialize to JSON.
            **kwargs: Forwarded to the constructor (and the Rich serializer
                options ``indent``, ``skip_keys``, ``sort_keys``, etc.).
        """
        serializer = {
            k: kwargs.pop(k)
            for k in ("skip_keys", "ensure_ascii", "check_circular", "allow_nan", "default", "sort_keys")
            if k in kwargs
        }
        indent = kwargs.pop("indent", 2)
        dumps_options = {
            ('skipkeys' if k == 'skip_keys' else k): v for k, v in serializer.items()
        }
        text = json_module.dumps(data, indent=indent, **dumps_options)
        return cls(
            text,
            indent=indent,
            **{k: v for k, v in serializer.items()},
            **kwargs,
        )

    @property
    def json(self) -> RichJSON:
        """Return the underlying Rich JSON renderable."""
        return self._json


def demo() -> None:
    """Render a small gradient JSON demo to the terminal."""
    Console(width=60).print(
        JSON.from_data(
            {"name": "rich-gradient", "tags": ["rich", "gradient"], "stable": True},
            colors=["#f43f5e", "#f59e0b", "#22c55e"],
        )
    )


if __name__ == "__main__":
    demo()
