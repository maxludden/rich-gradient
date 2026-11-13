"""Enables rendering of gradients in Rich Panels."""

from collections.abc import Mapping, Sequence
from re import escape
from typing import cast

from rich.align import AlignMethod, VerticalAlignMethod
from rich.box import ROUNDED, Box
from rich.console import Console, ConsoleOptions, RenderableType
from rich.measure import Measurement
from rich.panel import Panel as RichPanel
from rich.style import Style, StyleType
from rich.text import Text as RichText

from rich_gradient._logger import logger
from rich_gradient.gradient import (ColorType, Gradient, HighlightRegexType,
                                    HighlightWordsType)
from rich_gradient.text import Text, TextType
from rich_gradient.theme import GRADIENT_TERMINAL_THEME


class _ExpandingRichPanel(RichPanel):
    """Rich ``Panel`` that measures at the full available width when expanding.

    Rich measures a panel at its content width even with ``expand=True``, so the
    ``Align`` inside ``Gradient`` shrank the panel and left the gradient ramp
    spread over empty space (the border looked styled apart from its content).

    The full-width measurement is only meant for that inner ``Align``. Layouts
    that measure the *outer* gradient panel (``Columns``, ``Table`` cells) must
    see Rich's natural measurement via :meth:`natural_measure`, or every
    expanding panel would demand the whole width and crowd out its siblings.
    """

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        """Report the full available width when expanding without a fixed width.

        Args:
            console: The console used for measurement.
            options: The console options for the current render.

        Returns:
            ``options.max_width`` for both bounds when expanding without a
            fixed width; otherwise Rich's natural measurement.
        """
        if self.expand and self.width is None:
            return Measurement(options.max_width, options.max_width)
        return super().__rich_measure__(console, options)

    def natural_measure(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        """Return Rich's own panel measurement (content width plus chrome).

        Args:
            console: The console used for measurement.
            options: The console options for the current render.

        Returns:
            The measurement a plain Rich ``Panel`` would report.
        """
        return super().__rich_measure__(console, options)


def _normalize_panel_renderable(
    obj: RenderableType,
    *,
    style: StyleType,
    text_justify: AlignMethod,
    resolve_rich: bool = True,
) -> RenderableType:
    """Parse markup strings into justified Rich text, optionally resolving ``__rich__``.

    Shared by :class:`Panel` and :class:`~rich_gradient.animated_panel.AnimatedPanel`
    so both treat string content (markup, ``style``, ``text_justify``) the same way.
    ``AnimatedPanel`` passes ``resolve_rich=False`` so a ``__rich__`` object is
    resolved by Rich on every frame instead of being frozen at construction.

    Args:
        obj: The panel content. Strings are parsed as console markup.
        style: Base style for string content.
        text_justify: Justification for string content: ``"left"``,
            ``"center"``, or ``"right"``.
        resolve_rich: Call ``obj.__rich__()`` once up front, if present.
            Defaults to True.

    Returns:
        A justified Rich ``Text`` for strings; otherwise the (possibly
        resolved) renderable.
    """
    rich_obj = getattr(obj, "__rich__", None) if resolve_rich else None
    if callable(rich_obj):
        try:
            obj = cast(RenderableType, rich_obj())
        except (
            AttributeError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as err:  # pragma: no cover - defensive
            logger.debug(f"Error calling __rich__: {err}")
    if isinstance(obj, str):
        return RichText.from_markup(obj, style=style, justify=text_justify)
    return obj


class Panel(Gradient):
    """A Rich ``Panel`` whose border, title, and content share one gradient.

    Args:
        renderable (RenderableType): Content of the panel. Strings are parsed as console
            markup, e.g. ``"Hello, [b]panel[/b]!"``.
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
        title (Optional[TextType]): Title shown in the top border of the panel: a string
            (parsed as console markup) or a ``Text``. Defaults to None.
        title_align (AlignMethod): Alignment of the title: ``"left"``, ``"center"``, or
            ``"right"``. Defaults to ``"center"``.
        title_style (StyleType): Style layered over the gradient on the title text. A
            style string or ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to
            ``"bold"``.
        subtitle (Optional[TextType]): Subtitle shown in the bottom border of the panel:
            a string (parsed as console markup) or a ``Text``. Defaults to None.
        subtitle_align (AlignMethod): Alignment of the subtitle: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"right"``.
        subtitle_style (StyleType): Style layered over the gradient on the subtitle
            text. A style string or ``rich.style.Style``, e.g. ``"bold #ff8800"``.
            Defaults to ``""``.
        border_style (StyleType): Style of the border, under the gradient. A style
            string or ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to ``""``.
        justify (AlignMethod): Horizontal alignment of the panel: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the panel:
            ``"top"``, ``"middle"``, or ``"bottom"``. Defaults to ``"middle"``.
        box (Box): Box characters for the border, any ``rich.box`` constant, e.g.
            ``rich.box.HEAVY`` or ``rich.box.DOUBLE``. Defaults to ``rich.box.ROUNDED``.
        padding (int | tuple[int, int] | tuple[int, int, int, int]): Padding inside the
            border, CSS-style: ``1`` (all sides), ``(top_bottom, left_right)``, or
            ``(top, right, bottom, left)``, e.g. ``(1, 2)``. Defaults to
            ``(0, 1, 0, 1)``.
        expand (bool): Expand the output to the full available width. Defaults to True.
        text_justify (AlignMethod): Alignment of the text inside the panel (string
            content only): ``"left"``, ``"center"``, or ``"right"``. Defaults to
            ``"left"``.
        style (StyleType): Base style of the panel content. A style string or
            ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to ``""``.
        width (Optional[int]): Fixed width in cells, or ``None`` to size automatically.
            Defaults to None.
        height (Optional[int]): Fixed height in lines, or ``None`` to size
            automatically. Defaults to None.
        safe_box (bool): Use box characters that render on legacy Windows terminals.
            Defaults to False.
        highlight_words (Optional[HighlightWordsType]): Words to restyle on top of the
            gradient. Accepts a mapping of a word (or a tuple of words) to a style, e.g.
            ``{"error": "bold red", ("warn", "caution"): "yellow"}``; a sequence of
            ``(words, style[, case_sensitive])`` tuples, e.g.
            ``[("error", "bold red"), (("warn", "caution"), "yellow", False)]``; or
            ``HighlightWords`` instances, e.g.
            ``[HighlightWords(words=("error",), style=Style.parse("bold red"))]``.
            Matching is case-sensitive unless ``case_sensitive`` is False. Defaults to
            None.
        highlight_regex (Optional[HighlightRegexType]): Regular expressions whose
            matches are restyled on top of the gradient. Accepts a mapping of a pattern
            to a style, e.g. ``{r"[0-9]+": "bold cyan"}``; a sequence of
            ``(pattern, style[, flags])`` tuples, e.g.
            ``[(r"error|fail", "red", re.IGNORECASE)]``; or ``HighlightRegex``
            instances, e.g.
            ``[HighlightRegex(pattern=re.compile(r"[0-9]+"), style=Style.parse("cyan"))]``.
            Defaults to None.
    """

    def __init__(
        self,
        renderable: RenderableType,
        colors: list[ColorType] | None = None,
        bg_colors: list[ColorType] | None = None,
        rainbow: bool = False,
        hues: int = 5,
        title: Text | RichText | TextType | None = None,
        title_align: AlignMethod = "center",
        title_style: StyleType = "bold",
        subtitle: Text | RichText | TextType | None = None,
        subtitle_align: AlignMethod = "right",
        subtitle_style: StyleType = "",
        border_style: StyleType = "",
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        box: Box = ROUNDED,
        padding: int | tuple[int, int] | tuple[int, int, int, int] = (0, 1, 0, 1),
        expand: bool = True,
        text_justify: AlignMethod = "left",
        style: StyleType = "",
        width: int | None = None,
        height: int | None = None,
        safe_box: bool = False,
        highlight_words: HighlightWordsType | None = None,
        highlight_regex: HighlightRegexType | None = None,
    ) -> None:
        """Initialize the gradient panel; see the class docstring for arguments."""
        normalized_renderable = _normalize_panel_renderable(
            renderable, style=style, text_justify=text_justify
        )
        if isinstance(style, Style):
            _style = style
        else:
            _style = Style.parse(style) if style else Style.null()

        panel = _ExpandingRichPanel(
            normalized_renderable,
            title=title,
            title_align=title_align,
            subtitle=subtitle,
            subtitle_align=subtitle_align,
            border_style=border_style,
            box=box,
            padding=padding,
            expand=expand,
            style=_style,
            width=width,
            height=height,
            safe_box=safe_box,
        )

        # Track the underlying Rich Panel so expand setter can propagate to it
        # (Gradient.expand property will attempt to update ``self._panel``).
        self._panel: _ExpandingRichPanel = panel

        # Highlight title and subtitle if they are provided
        ## Normalize highlight_regex into a mutable sequence of tuples (pattern, style, priority)
        highlight_list: list[tuple[str, StyleType, int]] = []
        if highlight_regex is None:
            pass
        elif isinstance(highlight_regex, Mapping):
            # Convert mapping to a list of (pattern, style, priority) tuples
            highlight_list = [
                (str(pattern), cast(StyleType, style), 0)
                for pattern, style in highlight_regex.items()
            ]
        else:
            # Assume it's already a sequence of tuples
            highlight_list = list(
                cast(Sequence[tuple[str, StyleType, int]], highlight_regex)
            )

        if title:
            title_regex = self._get_title_regex(box)
            highlight_list.append((title_regex, title_style or "bold", 0))
        if subtitle:
            subtitle_regex = self._get_subtitle_regex(box)
            highlight_list.append((subtitle_regex, subtitle_style or "", 0))

        super().__init__(
            panel,
            colors=colors,
            bg_colors=bg_colors,
            hues=hues,
            rainbow=rainbow,
            expand=expand,
            justify=justify,
            vertical_justify=vertical_justify,
            highlight_words=highlight_words,
            highlight_regex=highlight_list,
        )

    @staticmethod
    def _get_title_regex(box: Box) -> str:
        """Generate the regex used to highlight the title row.

        Args:
            box: The panel's box characters.

        Returns:
            A pattern capturing the title text in the top border.
        """
        top_left: str = escape(box.top_left)
        top: str = escape(box.top)
        top_right: str = escape(box.top_right)
        title_regex: str = rf"{top_left}{top}+ (.*?) {top}+{top_right}"
        return title_regex

    @staticmethod
    def _get_subtitle_regex(box: Box) -> str:
        """Generate the regex used to highlight the subtitle row.

        Args:
            box: The panel's box characters.

        Returns:
            A pattern capturing the subtitle text in the bottom border.
        """
        bottom_left: str = escape(box.bottom_left)
        bottom: str = escape(box.bottom)
        bottom_right: str = escape(box.bottom_right)
        subtitle_regex: str = rf"{bottom_left}{bottom}+ (.*?) {bottom}+{bottom_right}"
        return subtitle_regex

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        """Measure like a plain Rich ``Panel`` so parent layouts share width fairly.

        Args:
            console: The console used for measurement.
            options: The console options for the current render.

        Returns:
            The natural (non-expanded) width range of the panel.
        """
        return self._panel.natural_measure(console, options)

    @property
    def panel(self) -> RichPanel:
        """The underlying Rich Panel renderable."""
        return self._panel


if __name__ == "__main__":
    console = Console(record=True, width=64)
    console.line()
    console.print(
        Panel(
            """This is a rich_gradient.panel.Panel with highlighting.

The panel's title is bolded, centered, and matches
the gradient by default.

The words `rich_gradient.panel.Panel` is styled
`bold white` and `Panel` is highlighted in `bold cyan`.

The subtitle is simply right-aligned by default :arrow_down:""",
            title="Title",
            subtitle="Subtitle",
            expand=True,
            padding=(1, 2),
            highlight_words={
                "rich_gradient.panel.Panel": "bold white",
                "Panel": "bold cyan",
            },
        ),
        justify="center",
    )
    console.line()
    console.save_svg(
        "docs/img/panel_example.svg",
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME,
    )
