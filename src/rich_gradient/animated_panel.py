"""Animated gradient panels rendered with Rich Live."""

from __future__ import annotations

from re import escape
from typing import Any, List, Mapping, Optional, Sequence, Union

from rich.align import AlignMethod, VerticalAlignMethod
from rich.box import ROUNDED, Box
from rich.console import Console, RenderableType
from rich.panel import Panel as RichPanel
from rich.style import StyleType
from rich.text import Text as RichText

from rich_gradient._logger import logger
from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import ColorType, HighlightRegexType, HighlightWordsType
from rich_gradient.text import Text, TextType

__all__ = ["AnimatedPanel"]


class AnimatedPanel(AnimatedGradient):
    """Animated variant of :class:`rich_gradient.panel.Panel`.

    Args:
        renderable: The renderable to display inside the panel.
        colors: Optional foreground color stops for the gradient.
            [cli option: `-c`, `--colors`]
        bg_colors: Optional background color stops for the gradient.
            [cli option: `-C`, `--bg-colors`]
        hues: Number of hues to generate when auto-selecting colors.
            [cli option: `--hues`]
        rainbow: If True, ignore `colors` and use a rainbow gradient.
            [cli option: `-r`, `--rainbow`]
        repeat_scale: Stretch factor for gradient color stops. Higher values produce
            a more gradual gradient. [cli option: `--repeat-scale`]
        title: Optional panel title renderable. [cli option: `-t`, `--title`]
        title_align: Alignment for the title text. Defaults to ``"center"``.
            [cli option: `--title-align`]
        title_style: Style applied to the highlighted title text.
            [cli option: `--title-style`]
        subtitle: Optional panel subtitle renderable. [cli option: `-s`, `--subtitle`]
        subtitle_align: Alignment for the subtitle text. Defaults to `"right"`.
            [cli option: `--subtitle-align`]
        subtitle_style: Style applied to the highlighted subtitle text.
            [cli option: `--subtitle-style`]
        border_style: Border style for the Rich panel. [cli option: `--border-style`]
        justify: Horizontal justification applied to the animated gradient.
            [cli option: `--justify`]
        vertical_justify: Vertical justification applied to the animated gradient.
            [cli option: `-V`, `--vertical-justify`]
        box: Rich box style for the panel border. Defaults to :data:`ROUNDED`.
            [cli option: `-b`, `--box`]
        padding: Panel padding. Can be a single integer or a tuple of up to four integers.
            [cli option: `-p`,`--padding`]
        expand: Whether the panel expands to available width. [cli option: `-e`, `--expand`]
        style: Base style for panel content. [cli option: `--style`]
        width: Optional explicit panel width. [cli option: `--width`]
        height: Optional explicit panel height. [cli option: `--height`]
        safe_box: Use “safe” box characters if True. [cli option: `--safe-box`]
        highlight_words: Word highlight configuration forwarded to the gradient.
            [cli option: `-w`, `--highlight-words`]
        highlight_regex: Regex highlight configuration forwarded to the gradient.
            [cli option:  `-H`, `--highlight-regex`]
        auto_refresh: Whether `Live` refreshes automatically.
            [cli option: `--auto-refresh`]
        refresh_per_second (optional, float): Target frames per second. Defaults to 20.0
            [cli option: `--rps`]
        console (Optional[Console]): Explicit console to render to. Defaults to None.
            [cli option: `--console`]
        transient (optional, bool): Leave the screen clear after stopping if True.
            [cli option: `-T`,`--transient`]
        redirect_stdout: Redirect stdout into the Live console.
            [cli option: `--redirect-stdout`]
        redirect_stderr: Redirect stderr into the Live console.
            [cli option: `--redirect-stderr`]

        animate (bool | None): Toggle animation on or off. ``None`` defers to the
            global configuration.
        duration: Optional duration in seconds for automatic stop.
    """

    def __init__(
        self,
        renderable: RenderableType,
        colors: Optional[List[ColorType]] = None,
        bg_colors: Optional[List[ColorType]] = None,
        hues: int = 5,
        rainbow: bool = False,
        repeat_scale: float = 4.0,

        # layout args
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        highlight_words: Optional[HighlightWordsType] = None,
        highlight_regex: Optional[HighlightRegexType] = None,
        border_style: StyleType = "",
        box: Box = ROUNDED,
        padding: Union[int, tuple[int, int], tuple[int, int, int, int]] = (0, 1),
        width: Optional[int] = None,
        height: Optional[int] = None,
        style: StyleType = "",
        title: Optional[Text | RichText | TextType] = None,
        title_align: AlignMethod = "center",
        title_style: StyleType = "bold",
        subtitle: Optional[Text | RichText | TextType] = None,
        subtitle_align: AlignMethod = "right",
        subtitle_style: StyleType = "",
        safe_box: bool = False,

        # live args
        console: Optional[Console] = None,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        auto_refresh: bool = True,
        refresh_per_second: float = 20.0,
        transient: bool = False,
        animate: Optional[bool] = None,
        duration: Optional[float] = None,
    ) -> None:
        """Initialize AnimatedPanel instance. See class docstring for details."""
        panel = RichPanel(
            renderable,
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
        self._panel = panel

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
        self._panel = panel

    @property
    def panel(self) -> RichPanel:
        """Access the underlying Rich panel renderable."""
        return self._panel

    @staticmethod
    def _combine_highlight_regex(
        highlight_regex: Optional[HighlightRegexType],
        title: Optional[RenderableType],
        title_style: StyleType,
        subtitle: Optional[RenderableType],
        subtitle_style: StyleType,
        box: Box,
    ) -> Sequence[tuple[Any, StyleType, int]]:
        """Merge user-provided regex highlights with title/subtitle highlights."""
        if highlight_regex is None:
            highlight_list: list[tuple[Any, StyleType, int]] = []
        elif isinstance(highlight_regex, Mapping):
            highlight_list = [
                (pattern, style, 0) for pattern, style in highlight_regex.items()
            ]
        else:
            highlight_list = list(highlight_regex)

        if title:
            title_regex = AnimatedPanel._get_title_regex(box)
            logger.debug("AnimatedPanel title regex: %s", title_regex)
            highlight_list.append((title_regex, title_style or "bold", 0))
        if subtitle:
            subtitle_regex = AnimatedPanel._get_subtitle_regex(box)
            logger.debug("AnimatedPanel subtitle regex: %s", subtitle_regex)
            highlight_list.append((subtitle_regex, subtitle_style, 0))

        return highlight_list

    @staticmethod
    def _get_title_regex(box: Box) -> str:
        """Generate the regex used to highlight the title row."""
        top_left = escape(box.top_left)
        top = escape(box.top)
        top_right = escape(box.top_right)
        return rf"{top_left}{top}+ (.*?) {top}+{top_right}"

    @staticmethod
    def _get_subtitle_regex(box: Box) -> str:
        """Generate the regex used to highlight the subtitle row."""
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
        rainbow=True,
        console=_console,
        padding=(1, 2),
        justify="center",
    )
    try:
        animated_panel.run()
    finally:
        _console.save_svg(
            "docs/img/animated_panel_example.svg",
            title="rich-gradient",
        )
