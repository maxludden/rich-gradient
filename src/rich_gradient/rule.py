from typing import List, Optional, Sequence, Tuple, cast

from rich.align import AlignMethod
from rich.color import Color, ColorParseError
from rich.color_triplet import ColorTriplet
from rich.console import Console, ConsoleOptions, RenderResult
from rich.rule import Rule as RichRule
from rich.style import NULL_STYLE, Style, StyleType
from rich.text import Text as RichText
from rich.traceback import install as tr_install

from rich_gradient.spectrum import Spectrum
from rich_gradient.text import ColorType, Text

console = Console()
tr_install(console=console, width=64)


CHARACTER_MAP = {
    0: "─",
    1: "═",
    2: "━",
    3: "█",
}
up_arrow: Text = Text(" ↑ ", style="bold white")


class Rule(RichRule):
    """A Rule with a gradient background.

    Args:
        title (Optional[str]): The text to display as the title.
        title_style (StyleType, optional): The style to apply to the title text. Defaults to NULL_STYLE.
        colors (Sequence[ColorType], optional): A sequence of colors for the gradient. Each color may be a
            string understood by ``rich.color.Color.parse`` (e.g., "red", "#ff0000"), a ``Color`` instance,
            or an RGB tuple. Defaults to empty list.
        thickness (int, optional): Thickness level of the rule (0 to 3). Defaults to 2.
        style (StyleType, optional): The style of the rule line. Defaults to NULL_STYLE.
        rainbow (bool, optional): If True, use a rainbow gradient regardless of colors. Defaults to False.
        hues (int, optional): Number of hues in the gradient if colors are not provided. Defaults to 10.
        end (str, optional): End character after the rule. Defaults to newline.
        align (AlignMethod, optional): Alignment of the rule. Defaults to "center".
    """

    def __init__(
        self,
        title: Optional[str],
        title_style: StyleType = Style.parse("bold"),
        colors: Optional[Sequence[ColorType]] = None,
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
        base_rule = RichRule(
            title=self.title or "",
            characters=self.characters,
            style=NULL_STYLE,
            end=self.end,
            align=cast(AlignMethod, self.align),
        )
        # Render the base rule to get segments
        rule_segments = console.render(base_rule, options=options)
        # Concatenate segment texts to form the full rule text (filter to Segment-like objects)
        rule_text_parts: List[str] = []
        for seg in rule_segments:
            try:
                text = seg.text
            except Exception:
                continue
            rule_text_parts.append(text)
        rule_text = "".join(rule_text_parts)

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
        colors: Sequence[ColorType],
        rainbow: bool,
        hues: int,
    ) -> List[str]:
        """Parse colors for the gradient.

        Args:
            colors (Sequence[ColorType]): A sequence of colors supplied as strings, ``Color`` objects,
                ``ColorTriplet`` instances or RGB tuples.
            rainbow (bool): If True, use a rainbow gradient.
            hues (int): Number of hues in the gradient.

        Raises:
            ValueError: If fewer than two colors are provided when colors are specified.
            ColorParseError: If a provided color value cannot be interpreted.

        Returns:
            List[str]: A list of hex color strings for the gradient.
        """
        if rainbow:
            return Spectrum(hues).hex

        if colors and len(colors) < 2:
            raise ValueError(
                f"At least two colors are required for a gradient. Please provide at least two color values. Received: {colors!r}"
            )

        if not colors:
            return Spectrum(hues).hex

        _colors: List[str] = []
        for color in colors:
            try:
                if isinstance(color, Color):
                    _colors.append(color.get_truecolor().hex)
                elif isinstance(color, ColorTriplet):
                    _colors.append(color.hex)
                elif isinstance(color, tuple) and len(color) == 3:
                    _colors.append(ColorTriplet(*color).hex)
                else:
                    _colors.append(Color.parse(color).get_truecolor().hex)
            except (ColorParseError, TypeError, ValueError) as ce:
                raise ValueError(
                    f"Invalid color: {color}. Please provide a valid color value."
                ) from ce
        return _colors


def example():
    console = Console(width=80, record=True)
    comment_style = Style.parse("dim italic")
    console.line(2)
    console.print(Rule(title="Centered Rule", rainbow=True, thickness=0))
    console.print(
        Text(
            "↑ This Rule is centered, with a thickness of 0. \
When no colors are provided, it defaults to a random gradient. ↑",
            style="dim italic",
        ),
        justify="center",
    )
    console.line(3)

    # left
    console.print(
        Rule(
            title="[bold]Left-aligned Rule[/bold]",
            thickness=1,
            colors=["#F00", "#F90", "#FF0"],
            align="left",
        )
    )
    console.print(
        Text.assemble(*[
            Text(
                "↑ This Rule is left-aligned, with a thickness of 1. When colors are provided, the gradient is generated using the provided colors: ",
                colors=["#F00", "#F90", "#FF0"],
                style="dim italic",
            ),
            RichText("#F00", style=Style.parse("bold italic #ff0000"), end=""),
            RichText(", ", style=comment_style, end=""),
            RichText("#F90", style=Style.parse("bold italic #FF9900"), end=""),
            RichText(", ", style=comment_style, end=""),
            RichText("#FF0", style=Style.parse("bold italic #FFFF00"), end=""),
        ]),
        justify="left",
    )
    console.line(3)

    COLORS3 = ["deeppink", "purple", "violet", "blue", "dodgerblue"]

    console.print(
        Rule(
            title="Right-aligned Rule",
            align="right",
            thickness=2,
            colors=list(COLORS3),
        )
    )
    purple_explanation = Text.assemble(*[
        Text(
            "↑  This Rule is right-aligned, with a thickness of 2. When colors are \
provided, the gradient is generated using the provided colors: ",
            colors=list(COLORS3),
            style="dim italic",
            end=" ",
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
    ])
    console.print(purple_explanation, justify="right")

    console.line(3)
    console.print(
        Rule(
            title="Centered Rule",
            rainbow=True,
            thickness=3,
            title_style="b u white",
        )
    )

    center_desc: Text = Text(
        "↑ [i]This rule is[/i] [b]centered[/b][i], with a[/i] [b]thickness[/b] [i]of[/i] [b]3.[/b]\n\
When `rainbow=True`, a full-spectrum Rainbow gradient is generated. ",
        style="dim",
    )
    center_desc.highlight_words(
        ["centered", "thickness", "3", "rainbow"], style=Style.parse("not dim")
    )
    center_desc.highlight_words(["=", "`"], style=Style.parse("bold not dim orange"))
    center_desc.highlight_words(["True"], style=Style.parse("bold not dim white"))
    console.print(center_desc, justify="center")
    console.line(3)

    console.print(
        Rule(
            title="",  # No title
            colors=["#F00", "#F90", "#FF0"],
            thickness=1,
            align="left",
        )
    )
    console.print(
        Text(
            "↑ This Rule has no title, but still has a gradient rule. ↑",
            colors=["#F00", "#F90", "#FF0"],
            style="dim italic",
        ),
        justify="center",
    )
    console.line(3)

    console.save_svg("docs/img/rule.svg", title="Rule Example")


if __name__ == "__main__":
    example()
