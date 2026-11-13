"""A gradient version of ``rich.inspect`` that stays human readable.

``Inspect`` wraps Rich's own inspector in a gradient ``Panel``: the frame and
title take the gradient, while attribute names, values, signatures, and other
text that Rich has already colored keep their colors so the output stays easy
to scan.
"""

from __future__ import annotations

from typing import Any

from rich._inspect import Inspect as RichInspect
from rich.align import AlignMethod
from rich.box import ROUNDED, Box
from rich.console import Console, Group
from rich.style import Style, StyleType
from rich.text import Text as RichText

from rich_gradient.gradient import ColorType, HighlightRegexType, HighlightWordsType
from rich_gradient.panel import Panel

__all__ = ["Inspect", "inspect"]


class Inspect(Panel):
    """A gradient-framed report on any Python object, like ``rich.inspect``.

    The object is analyzed by Rich's own inspector, so the content (attributes,
    values, signatures, docstrings) matches ``rich.inspect``. The gradient is
    applied to the frame, the title, and any text Rich leaves uncolored (such as
    ``=`` signs and docstrings); text Rich has already colored keeps its color.

    Examples:
        >>> from rich.console import Console
        >>> Console().print(Inspect([1, 2, 3], colors=["#38bdf8", "#a855f7"]))
        >>> Console().print(Inspect(str, methods=True, rainbow=True))

    Args:
        obj (Any): The object to inspect, e.g. ``[1, 2, 3]``, ``str``, or a module.
        title (Optional[str]): Title for the frame. Defaults to None, which uses the
            object's type (or the object itself for classes, callables, and modules).
        help (bool): Show the full docstring instead of only its first paragraph.
            Defaults to False.
        methods (bool): Include callables (methods and functions). Defaults to False.
        docs (bool): Include docstrings. Defaults to True.
        private (bool): Include attributes that start with a single underscore.
            Defaults to False.
        dunder (bool): Include attributes that start with a double underscore.
            Defaults to False.
        sort (bool): Sort attributes alphabetically, callables first, ignoring leading
            and trailing underscores. Defaults to True.
        all (bool): Include every attribute (implies ``private`` and ``dunder``).
            Defaults to False.
        value (bool): Pretty-print the object's value. Defaults to True.
        colors (Optional[list[ColorType]]): Foreground color stops. Each stop may be a
            color name (Rich/ANSI names such as ``"red"`` keep Rich's meaning; CSS names
            such as ``"tomato"`` also work), a hex string (``"#f00"``, ``"#ff0000"``),
            an ``"rgb(255, 0, 0)"`` string, an ``(r, g, b)`` tuple, or a
            ``rich.color.Color``, e.g. ``["#f00", "orange", (0, 128, 255)]``. If omitted
            and ``rainbow`` is False, ``hues`` colors are taken from the spectrum
            palette. Defaults to None.
        bg_colors (Optional[list[ColorType]]): Background color stops, in the same
            formats as ``colors``, e.g. ``["#000033", "#330033"]``. If omitted, no
            background gradient is applied. Defaults to None.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues``. Defaults to False.
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted (a run of consecutive hues with a random starting point). Valid
            values are 2 to 17. Defaults to 5.
        title_style (StyleType): Style layered over the gradient on the title text. A
            style string or ``rich.style.Style``, e.g. ``"dim italic"``. A color here is
            shown, drawn on top of the gradient. Defaults to ``"bold"``.
        border_style (StyleType): Style of the frame, under the gradient. A style string
            or ``rich.style.Style``, e.g. ``"dim italic"``. A foreground color in this
            style is replaced by the gradient; a background color is kept unless
            ``bg_colors`` is set. Defaults to ``""``.
        box (Box): Box characters for the frame, any ``rich.box`` constant, e.g.
            ``rich.box.HEAVY`` or ``rich.box.DOUBLE``. Defaults to ``rich.box.ROUNDED``.
        expand (bool): Expand the frame to the full available width instead of fitting
            the content. Defaults to False.
        justify (AlignMethod): Horizontal alignment of the frame: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        highlight_words (Optional[HighlightWordsType]): Words to restyle on top of the
            gradient, in any shape ``Gradient`` accepts, e.g. ``{"None": "bold red"}``.
            Colors in these styles are shown: they replace the gradient on the matched
            text. Defaults to None.
        highlight_regex (Optional[HighlightRegexType]): Regular expressions whose matches
            are restyled on top of the gradient, in any shape ``Gradient`` accepts, e.g.
            ``{r"[0-9]+": "bold cyan"}``. Colors in these styles are shown: they replace
            the gradient on the matched text. Defaults to None.
        keep_value_colors (bool): Keep the colors Rich gives attribute names, values,
            and signatures, so only the frame, title, and uncolored text take the
            gradient. Set to False to recolor everything with the gradient. Defaults to
            True.
    """

    def __init__(
        self,
        obj: Any,
        *,
        title: str | None = None,
        help: bool = False,
        methods: bool = False,
        docs: bool = True,
        private: bool = False,
        dunder: bool = False,
        sort: bool = True,
        all: bool = False,
        value: bool = True,
        colors: list[ColorType] | None = None,
        bg_colors: list[ColorType] | None = None,
        rainbow: bool = False,
        hues: int = 5,
        title_style: StyleType = "bold",
        border_style: StyleType = "",
        box: Box = ROUNDED,
        expand: bool = False,
        justify: AlignMethod = "left",
        highlight_words: HighlightWordsType | None = None,
        highlight_regex: HighlightRegexType | None = None,
        keep_value_colors: bool = True,
    ) -> None:
        """Initialize the gradient inspector; see the class docstring for arguments.

        Raises:
            ValueError: If ``hues`` is out of range.
            ColorParseError: If a color cannot be parsed.
        """
        # Set before Panel.__init__, which may render-measure through _merge_styles.
        self.keep_value_colors: bool = keep_value_colors
        inspector = RichInspect(
            obj,
            title=title,
            help=help,
            methods=methods,
            docs=docs,
            private=private,
            dunder=dunder,
            sort=sort,
            all=all,
            value=value,
        )
        # Rich highlights the auto-generated title like a repr; use plain text so
        # the title takes the gradient like the rest of the frame.
        raw_title = inspector.title
        plain_title = raw_title.plain if isinstance(raw_title, RichText) else str(raw_title)
        super().__init__(
            # ``_render`` is the content Rich's own ``Inspect.__rich__`` frames.
            Group(*inspector._render()),
            colors=colors,
            bg_colors=bg_colors,
            rainbow=rainbow,
            hues=hues,
            title=RichText(plain_title),
            title_style=title_style,
            border_style=border_style,
            box=box,
            padding=(0, 1),
            expand=expand,
            justify=justify,
            highlight_words=highlight_words,
            highlight_regex=highlight_regex,
        )

    def _merge_styles(self, original: Style, gradient_style: Style) -> Style:
        """Keep text Rich already colored; apply the gradient to everything else.

        Args:
            original: The segment's style from Rich's inspector.
            gradient_style: The gradient color for the segment's position.

        Returns:
            ``original`` unchanged when it has a (non-default) foreground color and
            ``keep_value_colors`` is on; otherwise the merged style.
        """
        color = original.color
        if self.keep_value_colors and color is not None and not color.is_default:
            return original
        return super()._merge_styles(original, gradient_style)


def inspect(
    obj: Any,
    *,
    console: Console | None = None,
    title: str | None = None,
    help: bool = False,
    methods: bool = False,
    docs: bool = True,
    private: bool = False,
    dunder: bool = False,
    sort: bool = True,
    all: bool = False,
    value: bool = True,
    colors: list[ColorType] | None = None,
    bg_colors: list[ColorType] | None = None,
    rainbow: bool = False,
    hues: int = 5,
    keep_value_colors: bool = True,
) -> None:
    """Print a gradient-framed inspection of any Python object, like ``rich.inspect``.

    * ``inspect(obj)`` to see summarized info.
    * ``inspect(obj, methods=True)`` to see methods.
    * ``inspect(obj, help=True)`` to see full (non-abbreviated) help.
    * ``inspect(obj, private=True)`` to see private attributes (single underscore).
    * ``inspect(obj, dunder=True)`` to see attributes beginning with double underscore.
    * ``inspect(obj, all=True)`` to see all attributes.

    Examples:
        >>> from rich_gradient import inspect
        >>> inspect([1, 2, 3], colors=["#38bdf8", "#a855f7"])
        >>> inspect(str, methods=True, rainbow=True)

    Args:
        obj (Any): The object to inspect, e.g. ``[1, 2, 3]``, ``str``, or a module.
        console (Optional[Console]): Console to print to. Defaults to
            ``rich.get_console()``.
        title (Optional[str]): Title for the frame. Defaults to None, which uses the
            object's type (or the object itself for classes, callables, and modules).
        help (bool): Show the full docstring instead of only its first paragraph.
            Defaults to False.
        methods (bool): Include callables (methods and functions). Defaults to False.
        docs (bool): Include docstrings. Defaults to True.
        private (bool): Include attributes that start with a single underscore.
            Defaults to False.
        dunder (bool): Include attributes that start with a double underscore.
            Defaults to False.
        sort (bool): Sort attributes alphabetically, callables first, ignoring leading
            and trailing underscores. Defaults to True.
        all (bool): Include every attribute (implies ``private`` and ``dunder``).
            Defaults to False.
        value (bool): Pretty-print the object's value. Defaults to True.
        colors (Optional[list[ColorType]]): Foreground color stops for the frame, in any
            format ``Gradient`` accepts, e.g. ``["#f00", "orange", (0, 128, 255)]``.
            If omitted and ``rainbow`` is False, ``hues`` colors are taken from the
            spectrum palette. Defaults to None.
        bg_colors (Optional[list[ColorType]]): Background color stops, in the same
            formats as ``colors``, e.g. ``["#000033", "#330033"]``. Defaults to None.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues``. Defaults to False.
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted. Valid values are 2 to 17. Defaults to 5.
        keep_value_colors (bool): Keep the colors Rich gives attribute names, values,
            and signatures. Set to False to recolor everything with the gradient.
            Defaults to True.

    Raises:
        ValueError: If ``hues`` is out of range.
        ColorParseError: If a color cannot be parsed.
    """
    from rich import get_console

    # Like rich.inspect(rich.inspect): inspecting this function shows its full help.
    is_self = obj is inspect
    (console or get_console()).print(
        Inspect(
            obj,
            title=title,
            help=is_self or help,
            methods=is_self or methods,
            docs=is_self or docs,
            private=private,
            dunder=dunder,
            sort=sort,
            all=all,
            value=value,
            colors=colors,
            bg_colors=bg_colors,
            rainbow=rainbow,
            hues=hues,
            keep_value_colors=keep_value_colors,
        )
    )
