"""Animated gradient panels rendered with Rich Live."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from re import escape
from typing import Any

from rich.align import AlignMethod, VerticalAlignMethod
from rich.box import ROUNDED, Box
from rich.console import Console, ConsoleOptions, RenderableType
from rich.measure import Measurement
from rich.panel import Panel as RichPanel
from rich.style import Style, StyleType
from rich.text import Text as RichText

from rich_gradient._logger import logger
from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import (ColorType, HighlightRegexType,
                                    HighlightWordsType)
from rich_gradient.panel import (_ExpandingRichPanel,
                                 _normalize_panel_renderable)
from rich_gradient.text import Text, TextType

__all__ = ["AnimatedPanel"]

_RegexHighlight = tuple[Any, str | Style, int]


class AnimatedPanel(AnimatedGradient):
    """Animated variant of :class:`rich_gradient.panel.Panel`.

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
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted (a run of consecutive hues with a random starting point). Valid
            values are 2 to 17. Defaults to 5.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues``. Defaults to False.
        repeat_scale (float): Width of one full color cycle as a multiple of the
            rendered width; larger values give a more gradual gradient. Defaults to 4.0.
        expand (bool): Expand the output to the full available width. Defaults to True.
        justify (AlignMethod): Horizontal alignment of the panel: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the panel:
            ``"top"``, ``"middle"``, or ``"bottom"``. Defaults to ``"middle"``.
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
            Title and subtitle rules are appended to these. Defaults to None.
        border_style (StyleType): Style of the border, under the gradient. A style
            string or ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to ``""``.
        box (Box): Box characters for the border, any ``rich.box`` constant, e.g.
            ``rich.box.HEAVY`` or ``rich.box.DOUBLE``. Defaults to ``rich.box.ROUNDED``.
        padding (int | tuple[int, int] | tuple[int, int, int, int]): Padding inside the
            border, CSS-style: ``1`` (all sides), ``(top_bottom, left_right)``, or
            ``(top, right, bottom, left)``, e.g. ``(1, 2)``. Defaults to ``(0, 1)``.
        width (Optional[int]): Fixed width in cells, or ``None`` to size automatically.
            Defaults to None.
        height (Optional[int]): Fixed height in lines, or ``None`` to size
            automatically. Defaults to None.
        style (StyleType): Base style of the panel content. A style string or
            ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to ``""``.
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
        safe_box (bool): Use box characters that render on legacy Windows terminals.
            Defaults to False.
        console (Optional[Console]): Console used for rendering and measurement.
            Defaults to ``rich.get_console()``.
        redirect_stdout (bool): Redirect ``sys.stdout`` into the Live display so prints
            appear above it. Defaults to False.
        redirect_stderr (bool): Redirect ``sys.stderr`` into the Live display so prints
            appear above it. Defaults to False.
        auto_refresh (bool): Let ``Live`` refresh the display on its own timer. Defaults
            to True.
        refresh_per_second (float): Live refresh and animation frame rate, in frames per
            second. Must be positive. Defaults to 20.0.
        transient (bool): Clear the output from the terminal when the animation stops.
            Defaults to False.
        animate (Optional[bool]): Whether to animate. ``None`` defers to
            ``config.animation_enabled`` (the ``RICH_GRADIENT_ANIMATE`` setting);
            ``False`` renders a single static frame. Defaults to None.
        duration (Optional[float]): Seconds after which a running animation stops on its
            own, e.g. ``5.0``. Must be positive. ``None`` runs until stopped. Defaults
            to None.
        text_justify (AlignMethod): Alignment of the text inside the panel (string
            content only, keyword-only): ``"left"``, ``"center"``, or ``"right"``.
            Defaults to ``"left"``.

    Raises:
        ValueError: If a ``highlight_regex`` tuple has fewer than two items, ``hues``
            < 2, or ``refresh_per_second``/``duration`` is not positive.
    """

    def __init__(
        self,
        renderable: RenderableType,
        colors: list[ColorType] | None = None,
        bg_colors: list[ColorType] | None = None,
        hues: int = 5,
        rainbow: bool = False,
        repeat_scale: float = 4.0,
        # layout args
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        highlight_words: HighlightWordsType | None = None,
        highlight_regex: HighlightRegexType | None = None,
        border_style: StyleType = "",
        box: Box = ROUNDED,
        padding: int | tuple[int, int] | tuple[int, int, int, int] = (0, 1),
        width: int | None = None,
        height: int | None = None,
        style: StyleType = "",
        title: Text | RichText | TextType | None = None,
        title_align: AlignMethod = "center",
        title_style: StyleType = "bold",
        subtitle: Text | RichText | TextType | None = None,
        subtitle_align: AlignMethod = "right",
        subtitle_style: StyleType = "",
        safe_box: bool = False,
        # live args
        console: Console | None = None,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        auto_refresh: bool = True,
        refresh_per_second: float = 20.0,
        transient: bool = False,
        animate: bool | None = None,
        duration: float | None = None,
        *,
        text_justify: AlignMethod = "left",
    ) -> None:
        """Initialize the animated panel; see the class docstring for arguments.

        Raises:
            ValueError: If a ``highlight_regex`` tuple has fewer than two items,
                ``hues`` < 2, or ``refresh_per_second``/``duration`` is not positive.
        """
        panel = _ExpandingRichPanel(
            _normalize_panel_renderable(
                renderable,
                style=style,
                text_justify=text_justify,
                resolve_rich=False,
            ),
            title=title,
            title_align=title_align,
            subtitle=subtitle,
            subtitle_align=subtitle_align,
            border_style=border_style,
            box=box,
            padding=padding,
            expand=expand,
            style=style,
            width=width,
            height=height,
            safe_box=safe_box,
        )

        # Track underlying panel so expand setter on Gradient can propagate
        # changes to the Rich Panel instance.
        self._panel: _ExpandingRichPanel = panel

        highlight_list = self._combine_highlight_regex(
            highlight_regex, title, title_style, subtitle, subtitle_style, box
        )

        super().__init__(
            renderables=panel,
            colors=colors,
            bg_colors=bg_colors,
            auto_refresh=auto_refresh,
            refresh_per_second=refresh_per_second,
            console=console,
            transient=transient,
            redirect_stdout=redirect_stdout,
            redirect_stderr=redirect_stderr,
            expand=expand,
            justify=justify,
            vertical_justify=vertical_justify,
            hues=hues,
            rainbow=rainbow,
            repeat_scale=repeat_scale,
            highlight_words=highlight_words,
            highlight_regex=highlight_list,
            animate=animate,
            duration=duration,
        )

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
        """The underlying Rich panel renderable."""
        return self._panel

    @staticmethod
    def _combine_highlight_regex(
        highlight_regex: HighlightRegexType | None,
        title: RenderableType | None,
        title_style: StyleType,
        subtitle: RenderableType | None,
        subtitle_style: StyleType,
        box: Box,
    ) -> Sequence[_RegexHighlight]:
        """Merge user-provided regex highlights with title/subtitle highlights.

        Args:
            highlight_regex: User-supplied regex highlight rules, if any.
            title: The panel title; when truthy, a title-row rule is added.
            title_style: Style for the title-row rule (falls back to "bold").
            subtitle: The panel subtitle; when truthy, a subtitle-row rule is added.
            subtitle_style: Style for the subtitle-row rule.
            box: The panel's box, used to build the border-row patterns.

        Returns:
            A list of ``(pattern, style, flags)`` tuples.

        Raises:
            ValueError: If a sequence entry has fewer than two items.
        """

        def normalize_style(value: object) -> str | Style:
            """Keep ``Style`` objects as-is and stringify anything else.

            Args:
                value: A style or style-like value.

            Returns:
                The ``Style`` unchanged, or ``str(value)``.
            """
            return value if isinstance(value, Style) else str(value)

        if highlight_regex is None:
            highlight_list: list[_RegexHighlight] = []
        elif isinstance(highlight_regex, Mapping):
            highlight_list = [
                (pattern, normalize_style(style), 0)
                for pattern, style in highlight_regex.items()
            ]
        else:
            highlight_list = []
            for entry in highlight_regex:
                if len(entry) < 2:
                    raise ValueError(
                        "Highlight regex tuples must be (pattern, style[, flags])."
                    )
                pattern = entry[0]
                style = entry[1]
                flags = entry[2] if len(entry) > 2 else 0
                highlight_list.append((pattern, normalize_style(style), int(flags)))

        if title:
            title_regex = AnimatedPanel._get_title_regex(box)
            logger.debug("AnimatedPanel title regex: %s", title_regex)
            highlight_list.append(
                (title_regex, normalize_style(title_style or "bold"), 0)
            )
        if subtitle:
            subtitle_regex = AnimatedPanel._get_subtitle_regex(box)
            logger.debug("AnimatedPanel subtitle regex: %s", subtitle_regex)
            highlight_list.append((subtitle_regex, normalize_style(subtitle_style), 0))
        return highlight_list

    @staticmethod
    def _get_title_regex(box: Box) -> str:
        """Generate the regex used to highlight the title row.

        Args:
            box: The panel's box characters.

        Returns:
            A pattern capturing the title text in the top border.
        """
        top_left = escape(box.top_left)
        top = escape(box.top)
        top_right = escape(box.top_right)
        return rf"{top_left}{top}+ (.*?) {top}+{top_right}"

    @staticmethod
    def _get_subtitle_regex(box: Box) -> str:
        """Generate the regex used to highlight the subtitle row.

        Args:
            box: The panel's box characters.

        Returns:
            A pattern capturing the subtitle text in the bottom border.
        """
        bottom_left = escape(box.bottom_left)
        bottom = escape(box.bottom)
        bottom_right = escape(box.bottom_right)
        return rf"{bottom_left}{bottom}+ (.*?) {bottom}+{bottom_right}"


if __name__ == "__main__":
    _console = Console(record=True, width=64)
    animated_panel = AnimatedPanel(
        "Rainbow [i]AnimatedPanel[/i] in motion",
        title="Animated Panel",
        title_style="bold white",
        subtitle="Ctrl+C to stop",
        # rainbow=True,
        console=_console,
        padding=(1, 4),
        justify="center",
    )
    try:
        animated_panel.run()
    finally:
        _console.save_svg(
            "docs/img/animated_panel_example.svg",
            title="rich-gradient",
        )
