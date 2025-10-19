"""Enables rendering of (animated) gradients in Rich Panels."""
from typing import (
    Any,
    List,
    Optional,
    TypeAlias,
    Union,
)
from rich.console import Console, ConsoleRenderable, RenderableType
from rich.panel import Panel as RichPanel
from rich.align import AlignMethod, VerticalAlignMethod
from rich.box import Box

from rich_gradient.gradient import Gradient, ColorType

class Panel(RichPanel):
    """A Rich Panel that supports (animated) gradients as background.

    Args:
        renderable (RenderableType): The renderable to display inside the panel.
        colors (Optional[List[Union[str, "Color", "ColorTriplet"]]]): Foreground \
            color stops for the gradient.
        bg_colors (Optional[List[Union[str, "Color", "ColorTriplet"]]]): \
            Background color stops for the gradient.
        title (Optional[RenderableType]): The title of the panel.
        title_align (AlignMethod): The alignment of the title. Defaults to "left".
        title_style (StyleType): The style of the title. If none, the title will use \
            the bolded gradient colors.
        subtitle (Optional[RenderableType]): The subtitle of the panel.
        subtitle_align (AlignMethod): The alignment of the subtitle. Defaults to "right".
        border_style (Union[str, Color]): The style of the panel border.
        box (Optional[Box]): The box style to use for the panel border.
        padding (Union[int, tuple[int, int], tuple[int, int, int, int]]): Padding inside the panel.
        expand (bool): Whether to expand the panel to fill available width. Defaults to True.
        style (Union[str, Color]): The style of the panel content.
        width (Optional[int]): The width of the panel.
        height (Optional[int]): The height of the panel.
        safe_box (bool): Whether to use safe box drawing characters. Defaults to False.
    """

    def __init__(
        self,
        renderable: RenderableType,
        colors: Optional[List[ColorType]] = None,
        bg_colors: Optional[List[ColorType]] = None,
        title: Optional[RenderableType] = None,
        title_align: AlignMethod = "left",
        subtitle: Optional[RenderableType] = None,
        subtitle_align: AlignMethod = "right",
        border_style: Union[str, "Color"] = "",
        box: Optional["Box"] = None,
        padding: Union[int, tuple[int, int], tuple[int, int, int, int]] = 1,
        expand: bool = True,
        style: Union[str, "Color"] = "",
        width: Optional[int] = None,
        height: Optional[int] = None,
        safe_box: bool = False,
    ) -> None:
        super().__init__(
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
        self.gradient = gradient
