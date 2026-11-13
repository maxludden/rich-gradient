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
        json (str): The JSON text to format, e.g.
            ``'{"name": "rich", "tags": [1, 2]}'``.
        indent (int | str | None): Indentation per level: a number of spaces, an indent
            string such as ``"  "``, or ``None`` for compact output. Defaults to 2.
        highlight (bool): Apply Rich's JSON syntax highlighting before the gradient.
            Defaults to True.
        skip_keys (bool): Skip dict keys that are not basic types instead of raising
            ``TypeError``. Defaults to False.
        ensure_ascii (bool): Escape non-ASCII characters. Defaults to False.
        check_circular (bool): Check for circular references. Defaults to True.
        allow_nan (bool): Allow ``NaN`` and ``Infinity`` values. Defaults to True.
        default (Optional[Callable[[Any], Any]]): Function that converts objects
            ``json`` cannot serialize, e.g. ``str``. Defaults to None.
        sort_keys (bool): Sort dictionary keys. Defaults to False.
        colors (Optional[Sequence[ColorType]]): Foreground color stops. Each stop may be
            a color name (Rich/ANSI names such as ``"red"`` keep Rich's meaning; CSS
            names such as ``"tomato"`` also work), a hex string (``"#f00"``,
            ``"#ff0000"``), an ``"rgb(255, 0, 0)"`` string, an ``(r, g, b)`` tuple, or a
            ``rich.color.Color``, e.g. ``["#f00", "orange", (0, 128, 255)]``. If omitted
            and ``rainbow`` is False, ``hues`` colors are taken from the spectrum
            palette. Defaults to None.
        bg_colors (Optional[Sequence[ColorType]]): Background color stops, in the same
            formats as ``colors``, e.g. ``["#000033", "#330033"]``. If omitted, no
            background gradient is applied. Defaults to None.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues``. Defaults to False.
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted (a run of consecutive hues with a random starting point). Valid
            values are 2 to 17. Defaults to 5.
        repeat_scale (Optional[float]): Width of one full color cycle as a multiple of
            the rendered width; larger values give a more gradual gradient, e.g.
            ``1.5``. ``None`` derives it from the stops so one pass runs from the first
            color to the last (1.0 for two colors, 2.0 for three or more). Defaults to
            None.
        expand (bool): Expand the output to the full console width. Defaults to True.
        justify (AlignMethod): Horizontal alignment of the JSON: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the JSON:
            ``"top"``, ``"middle"``, or ``"bottom"``. Defaults to ``"middle"``.
        console (Optional[Console]): Console used for rendering and measurement.
            Defaults to ``rich.get_console()``.
        highlight_words (Optional[HighlightWordsType]): Words to restyle on top of the
            gradient. Accepts a mapping of a word (or a tuple of words) to a style, e.g.
            ``{"error": "bold red", ("warn", "caution"): "yellow"}``; a sequence of
            ``(words, style[, case_sensitive])`` tuples, e.g.
            ``[("error", "bold red"), (("warn", "caution"), "yellow", False)]``; or
            ``HighlightWords`` instances, e.g.
            ``[HighlightWords(words=("error",), style=Style.parse("bold red"))]``.
            Matching is case-sensitive unless ``case_sensitive`` is False. Colors in
            these styles are shown: they replace the gradient on the matched text.
            Defaults to None.
        highlight_regex (Optional[HighlightRegexType]): Regular expressions whose
            matches are restyled on top of the gradient. Accepts a mapping of a pattern
            to a style, e.g. ``{r"[0-9]+": "bold cyan"}``; a sequence of
            ``(pattern, style[, flags])`` tuples, e.g.
            ``[(r"error|fail", "red", re.IGNORECASE)]``; or ``HighlightRegex``
            instances, e.g.
            ``[HighlightRegex(pattern=re.compile(r"[0-9]+"), style=Style.parse("cyan"))]``.
            Colors in these styles are shown: they replace the gradient on the matched
            text. Defaults to None.
        animate (bool): Mark the content as changing between renders, so highlight
            matches are recomputed every frame instead of cached. Static renderables
            never animate on their own; use the ``Animated*`` classes for live
            animation. Defaults to False.
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
        animate: bool = False,
    ) -> None:
        """Initialize a gradient-enabled Rich JSON renderable; see the class docstring for arguments."""
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
            animate=animate,
        )

    @classmethod
    def from_data(cls, data: Any, **kwargs: Any) -> JSON:
        """Build a gradient JSON renderable from a Python object.

        Args:
            data: Object to serialize to JSON, e.g. ``{"name": "rich", "tags": [1, 2]}``.
            **kwargs: Forwarded to the constructor (and the Rich serializer
                options ``indent``, ``skip_keys``, ``sort_keys``, etc.), e.g.
                ``sort_keys=True, colors=["cyan", "magenta"]``.

        Returns:
            A new gradient ``JSON`` renderable.
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
        """The underlying Rich JSON renderable."""
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
