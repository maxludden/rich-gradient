from typing import Iterable, List, Literal, Optional, Sequence, Union, cast

import rich_color_ext
from cheap_repr import normal_repr, register_repr
from rich.align import AlignMethod
from rich.color import Color
from rich.color import Color as RichColor
from rich.color import ColorParseError, ColorType
from rich.console import Console, ConsoleOptions, RenderResult
from rich.rule import Rule
from rich.segment import Segment
from rich.style import NULL_STYLE, Style, StyleType
from rich.text import Text as RichText
from rich.traceback import install
from snoop import snoop

from rich_gradient.gradient import Gradient
from rich_gradient.spectrum import Spectrum
from rich_gradient.text import ColorInputType, Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

console = Console()
install(console=console, width=64)

CHARACTER_MAP = {
    0: "─",
    1: "═",
    2: "━",
    3: "█",
}
up_arrow: Text = Text(" ↑ ", style="bold white")


class GradientRule(Rule):
    """A Rule with a gradient background.

    Args:
        title (Optional[str]): The text to display as the title.
        title_style (StyleType, optional): The style to apply to the title text. Defaults to NULL_STYLE.
        colors (List[ColorType], optional): A list of color strings for the gradient. Defaults to empty list.
        thickness (int, optional): Thickness level of the rule (0 to 3). Defaults to 2.
        style (StyleType, optional): The style of the rule line. Defaults to NULL_STYLE.
        rainbow (bool, optional): If True, use a rainbow gradient regardless of colors. Defaults to False.
        hues (int, optional): Number of hues in the gradient if colors are not provided. Defaults to 10.
        end (str, optional): End character after the rule. Defaults to newline.
        align (AlignMethod, optional): Alignment of the rule. Defaults to "center".
    """

    # @snoop()
    def __init__(
        self,
        title: Optional[str],
        title_style: StyleType = NULL_STYLE,
        colors: Optional[List[ColorInputType]] = None,
        thickness: int = 2,
        style: StyleType = NULL_STYLE,
        rainbow: bool = False,
        hues: int = 10,
        end: str = "\n",
        align: AlignMethod = "center",
    ) -> None:
        # Validate thickness input
        if thickness < 0 or thickness > 3:
            raise ValueError(
                f"Invalid thickness: {thickness}. Thickness must be between 0 and 3."
            )
        # Validate type
        if title is not None and not isinstance(title, str):
            raise TypeError(f"title must be str, got {type(title).__name__}")

        if not isinstance(title_style, (str, Style)):
            raise TypeError(
                f"title_style must be str or Style, got {type(title_style).__name__}"
            )
        if not isinstance(style, (str, Style)):
            raise TypeError(f"style must be str or Style, got {type(style).__name__}")
        # Determine character based on thickness
        self.characters = CHARACTER_MAP.get(thickness, "━")
        # Parse and store the title style
        self.title_style = Style.parse(str(title_style))
        # Initialize the base Rule with provided parameters
        super().__init__(
            title=title or "",
            characters=self.characters,
            style=Style.parse(str(style)),
            end=end,
            align=align,
        )
        # Parse and store the gradient colors
        self.colors = self._parse_colors(
            colors if colors is not None else [], rainbow, hues
        )

    # @snoop(watch=["title_style", "style"])
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Render the gradient rule.

        Args:
            console (Console): The console to render to.
            options (ConsoleOptions): The console options.

        Yields:
            RenderResult: The rendered segments of the gradient rule.
        """
        # Prepare a base rule with no style to extract segments
        base_rule = Rule(
            title=self.title or "",
            characters=self.characters,
            style=NULL_STYLE,
            end=self.end,
            align=cast(AlignMethod, self.align),
        )
        # Render the base rule to get segments
        rule_segments = console.render(base_rule, options=options)
        # Concatenate segment texts to form the full rule text
        rule_text = "".join(seg.text for seg in rule_segments)

        # If no title style, render the gradient text directly
        if self.title_style == NULL_STYLE:
            gradient_rule = Text(rule_text, colors=self.colors)
            yield from console.render(gradient_rule, options)
            return
        # Create gradient text for the rule
        gradient_rule = Text(rule_text, colors=self.colors)

        # Extract the title string for highlighting
        title = self.title.plain if isinstance(self.title, Text) else str(self.title)

        # Apply the title style highlight after gradient generation
        if title and self.title_style != NULL_STYLE:
            gradient_rule.highlight_words([title], style=self.title_style)

        # Yield the styled gradient text
        yield from console.render(gradient_rule, options)

    def _parse_colors(
        self,
        colors: Sequence[ColorInputType],
        rainbow: bool,
        hues: int,
    ) -> List[str]:
        """Parse colors for the gradient.

        Args:
            colors (List[ColorType]): A list of color strings.
            rainbow (bool): If True, use a rainbow gradient.
            hues (int): Number of hues in the gradient.
        Raises:
            ValueError: If any color is not a valid string.
            ColorParseError: If a color string cannot be parsed.

        Returns:
            List[str]: A list of hex color strings for the gradient.
        """
        # Use full rainbow spectrum if rainbow flag is set, or if insufficient colors
        if rainbow:
            return Spectrum(hues).hex
        _colors: List[str] = []
        if len(colors) < 2:
            raise ValueError(
                "At least two colors are required for a gradient. "
                "Please provide a list of at least two color strings."
            )
        for color in colors:
            # Validate color is a string
            if not isinstance(color, str):
                raise ValueError(
                    f"Invalid color: {color}. Please provide a valid color string."
                )
            try:
                # Convert color string to hex format
                _colors.append(Color.parse(color).get_truecolor().hex)
            except ColorParseError as ce:
                raise ColorParseError(
                    f"Invalid color: {color}. Please provide a valid color string."
                ) from ce
        return _colors

    # def get_title(self, title: Optional[str], title_style: StyleType) -> str:
    #     """Get the title for the rule.

    #     Args:
    #         title (Optional[str]): The title string.
    #         title_style (StyleType): The style for the title.

    #     Returns:
    #         str: The formatted title string.
    #     """


register_repr(GradientRule)(normal_repr)


# @snoop(watch=["title_style", "style"])
def example():
    console = Console(width=80, record=True)
    comment_style = Style.parse("dim italic")
    console.line(2)
    console.print(
        GradientRule(title="Centered GradientRule", rainbow=True, thickness=0)
    )
    console.print(
        Text(
            "↑ This GradientRule is centered, with a thickness of 0. \
When no colors are provided, it defaults to a random gradient. ↑",
            style="dim italic",
        ),
        justify="center",
    )
    console.line(3)

    # left
    console.print(
        GradientRule(
            title="[bold]Left-aligned GradientRule[/bold]",
            thickness=1,
            colors=["#F00", "#F90", "#FF0"],
            align="left",
        )
    )
    console.print(
        Text.assemble(*[
            RichText(
                "↑ This GradientRule is left-aligned, with a thickness of 1. ↑",
                style=comment_style,
                end="\n\n",
            ),
            RichText(
                " \n\nWhen colors are provided, the gradient is generated using the provided colors: ",
                style=comment_style,
                end="",
            ),
            RichText("#F00", style=Style.parse("bold italic #ff0000"), end=""),
            RichText(", ", style=comment_style, end=""),
            RichText("#F90", style=Style.parse("bold italic #FF9900"), end=""),
            RichText(", ", style=comment_style, end=""),
            RichText("#FF0", style=Style.parse("bold italic #FFFF00"), end=""),
            RichText(" ↑", style=comment_style),
        ]),
        justify="left",
    )
    console.line(3)

    console.print(
        GradientRule(
            title="Right-aligned GradientRule",
            align="right",
            thickness=2,
            colors=["deeppink", "purple", "violet", "blue", "dodgerblue"],
        )
    )
    purple_explanation = Text.assemble(*[
        RichText("↑ ", style="bold white", end=" "),
        RichText(
            "This GradientRule is right-aligned, with a thickness of 2. ",
            style=comment_style,
            end=" ",
        ),
        RichText("↑ ", style="bold white", end=" "),
        RichText(
            "\n\nWhen colors are provided, the gradient is generated using the provided colors: ",
            style=comment_style,
            end="",
        ),
        RichText("deeppink", style=Style.parse("bold italic deeppink"), end=""),
        RichText(", ", style=comment_style, end=""),
        RichText("purple", style=Style.parse("bold italic purple"), end=""),
        RichText(", ", style=comment_style, end=""),
        RichText("violet", style=Style.parse("bold italic violet"), end=""),
        RichText(", ", style=comment_style, end=""),
        RichText("blue", style=Style.parse("bold italic blue"), end=""),
        RichText(", ", style=comment_style, end=""),
        RichText("dodgerblue", style=Style.parse("bold italic dodgerblue"), end=""),
        RichText(" ↑ ", style=comment_style),
    ])
    console.print(purple_explanation, justify="right")

    console.line(3)
    console.print(
        GradientRule(
            title="Centered GradientRule",
            rainbow=True,
            thickness=3,
            title_style="b u white",
        )
    )
    console.print(
        RichText(
            "↑ This GradientRule is centered, with a thickness of 3. \
When `rainbow=True`, a full-spectrum Rainbow gradient is generated. ↑",
            style="dim italic",
        ),
        justify="center",
    )
    console.line(3)

    console.print(
        GradientRule(
            title="",  # No title
            colors=["#F00", "#F90", "#FF0"],
            thickness=1,
            align="left",
        )
    )
    console.print(
        RichText(
            "↑ This GradientRule has no title, but still has a gradient rule. ↑",
            style=comment_style,
        ),
        justify="left",
    )
    console.line(3)

    console.save_svg("docs/img/rule.svg", title="GradientRule Example")


if __name__ == "__main__":
    example()
