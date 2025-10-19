"""Enables rendering of gradients in Rich Panels."""
from typing import (
    List,
    Mapping,
    Optional,
    Union,
)

from re import escape
from rich.console import Console, RenderableType
from rich.panel import Panel as RichPanel
from rich.align import AlignMethod, VerticalAlignMethod
from rich.box import Box, ROUNDED
from rich.style import StyleType
from rich.text import Text as RichText

from rich_gradient.text import Text, TextType
from rich_gradient.gradient import Gradient, ColorType, HighlightWordsType, HighlightRegexType
from rich_gradient._logger import logger
from rich_gradient.theme import GRADIENT_TERMINAL_THEME


class Panel(Gradient):
    """A Rich Panel that supports (animated) gradients as background.

    Args:
        renderable (RenderableType): The renderable to display inside the panel.
        colors (Optional[List[ColorType]]): Foreground color stops for the gradient.
        bg_colors (Optional[List[ColorType]]): Background color stops for the gradient.
        title (Optional[RenderableType]): The title of the panel.
        title_align (AlignMethod): The alignment of the title. Defaults to "left".
        title_style (StyleType): The style of the title. If none, the title will use \
            the bolded gradient colors.
        subtitle (Optional[RenderableType]): The subtitle of the panel.
        subtitle_align (AlignMethod): The alignment of the subtitle. Defaults to "right".
        subtitle_style (StyleType): The style of the subtitle. If none, the subtitle will use \
            the dimmed gradient colors.
        border_style (Union[str, Color]): The style of the panel border.
        box (Optional[Box]): The box style to use for the panel border.
        padding (int | tuple[int, int] | tuple[int, int, int, int]): Padding inside the \
            panel. Defaults to (0, 0, 0, 0).
        expand (bool): Whether to expand the panel to fill available width. Defaults to True.
        style (Union[str, Color]): The style of the panel content. If a color is provided, \
            it will override the gradient style.
        width (Optional[int]): The width of the panel.
        height (Optional[int]): The height of the panel.
        safe_box (bool): Whether to use safe box drawing characters. Defaults to False.
        highlight_words (Optional[HighlightWordsType]): Words to highlight with styles.
        highlight_regex (Optional[HighlightRegexType]): Regex patterns to highlight with styles.
    """

    def __init__(
        self,
        renderable: RenderableType,
        colors: Optional[List[ColorType]] = None,
        bg_colors: Optional[List[ColorType]] = None,
        rainbow: bool = False,
        hues: int = 5,
        title: Optional[Text|RichText|TextType] = None,
        title_align: AlignMethod = "center",
        title_style: StyleType = "bold",
        subtitle: Optional[Text|RichText|TextType] = None,
        subtitle_align: AlignMethod = "right",
        subtitle_style: StyleType = "",
        border_style: StyleType = "",
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        box: Box = ROUNDED,
        padding: Union[int, tuple[int, int], tuple[int, int, int, int]] = (0, 0, 0, 0),
        expand: bool = True,
        style: StyleType = "",
        width: Optional[int] = None,
        height: Optional[int] = None,
        safe_box: bool = False,
        highlight_words: Optional[HighlightWordsType] = None,
        highlight_regex: Optional[HighlightRegexType] = None,
    ) -> None:
        """Initialize the Panel with gradient support."""
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

        # Highlight title and subtitle if they are provided
        # Normalize highlight_regex into a mutable sequence of tuples (pattern, style, priority)
        if highlight_regex is None:
            highlight_list = []
        elif isinstance(highlight_regex, Mapping):
            # Convert mapping to a list of (pattern, style, priority) tuples
            highlight_list = [(pattern, style, 0) for pattern, style in highlight_regex.items()]
        else:
            # Assume it's already a sequence of tuples
            highlight_list = list(highlight_regex)

        if title:
            title_regex = self._get_title_regex(box)
            highlight_list.append((title_regex, title_style or "bold", -1))
        if subtitle:
            subtitle_regex = self._get_subtitle_regex(box)
            highlight_list.append((subtitle_regex, subtitle_style, -1))


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
            highlight_regex=highlight_list
        )


    @staticmethod
    def _get_title_regex(box: Box) -> str:
        """Generate regex patterns for title highlighting."""
        top_left: str = escape(box.top_left)
        top: str = escape(box.top)
        top_right: str = escape(box.top_right)
        title_regex: str = rf"{top_left}{top}+ (.*?) {top}+{top_right}"
        logger.debug(f"Generated title regex: {title_regex}")
        return title_regex

    @staticmethod
    def _get_subtitle_regex(box: Box) -> str:
        """Generate regex patterns for subtitle highlighting."""
        bottom_left: str = escape(box.bottom_left)
        bottom: str = escape(box.bottom)
        bottom_right: str = escape(box.bottom_right)
        subtitle_regex: str = rf"{bottom_left}{bottom}+ (.*?) {bottom}+{bottom_right}"
        logger.debug(f"Generated subtitle regex: {{{subtitle_regex}: ")
        return subtitle_regex

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
            padding=(1,2),
            highlight_words={
                "rich_gradient.panel.Panel": "bold white",
                "Panel": "bold cyan"
            }
        ),
        justify="center"
    )
    console.line()
    console.save_svg(
        "docs/img/panel_example.svg",
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME)
