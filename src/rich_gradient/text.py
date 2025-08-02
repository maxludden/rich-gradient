from typing import List, Optional, Sequence, Tuple, TypeAlias, Union

from rich import get_console
from rich.color import Color, ColorParseError
from rich.color_triplet import ColorTriplet
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.control import strip_control_codes
from rich.panel import Panel
from rich.style import Style, StyleType
from rich.text import Span
from rich.text import Text as RichText
from rich.text import TextType
from rich_color_ext import install

from rich_gradient.spectrum import Spectrum
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

ColorType: TypeAlias = Union[str, Color, ColorTriplet, Tuple[int, int, int]]
install()


class Text(RichText):
    """A rich text class that supports gradient colors and styles."""

    def __init__(
        self,
        text: TextType = "",
        colors: Optional[Sequence[ColorType]] = None,
        *,
        rainbow: bool = False,
        hues: int = 5,
        style: StyleType = "",
        justify: JustifyMethod = "default",
        overflow: OverflowMethod = "fold",
        no_wrap: bool = False,
        end: str = "\n",
        tab_size: int = 4,
        bgcolors: Optional[Sequence[ColorType]] = None,
        markup: bool = True,
        spans: Optional[Sequence[Span]] = None,
    ):
        """Initialize the Text with gradient colors and styles.
        Args:
            text (TextType): The text content.
            colors (Optional[List[ColorType]]): A list of colors as Color instances or strings.
            rainbow (bool): If True, generate a rainbow spectrum.
            hues (int): The number of hues to generate if colors are not provided.
            style (StyleType): The style of the text.
            justify (JustifyMethod): Justification method for the text.
            overflow (OverflowMethod): Overflow method for the text.
            no_wrap (bool): If True, disable wrapping of the text.
            end (str): The string to append at the end of the text. Default is a newline.
            tab_size (int): The number of spaces for a tab character.
            bgcolors (Optional[List[ColorType]]): A list of background colors as Color instances
            markup (bool): If True, parse Rich markup tags in the input text.
            spans (Optional[Sequence[Span]]): A list of spans to apply to the text.
        """
        if markup:
            parsed_text = RichText.from_markup(
                text=str(text), style=style, justify=justify, overflow=overflow
            )
        else:
            parsed_text = RichText(
                strip_control_codes(str(text)),
                style=style,
                justify=justify,
                overflow=overflow,
            )
        plain = parsed_text.plain
        parsed_justify = parsed_text.justify
        parsed_overflow = parsed_text.overflow
        parsed_spans = parsed_text._spans

        super().__init__(
            plain,
            style=style,
            justify=parsed_justify,
            overflow=parsed_overflow,
            no_wrap=no_wrap,
            end=end,
            tab_size=tab_size,
            spans=parsed_spans,
        )
        self.colors = self.parse_colors(colors, hues, rainbow)
        self.bgcolors = self.parse_bgcolors(bgcolors, hues)

        # Handle the single-color and single-background case: apply style directly and return early
        if len(self.colors) == 1 and len(self.bgcolors) == 1:
            # Apply the single color style directly
            style_with_color = Style(
                color=self.colors[0], bgcolor=self.bgcolors[0]
            ) + Style.parse(style)
            for index in range(len(self.plain)):
                self.stylize(style_with_color, index, index + 1)
            return

        # Apply the gradient coloring
        self.apply_gradient()

    @property
    def colors(self) -> list[Color]:
        """Return the list of colors in the gradient."""
        return list(self._colors) if self._colors else []

    @colors.setter
    def colors(self, value: Optional[Sequence[Color]]) -> None:
        """Set the list of colors in the gradient."""
        self._colors = list(value) if value else []

    @property
    def bgcolors(self) -> list[Color]:
        """Return the list of background colors in the gradient."""
        return list(self._bgcolors) if self._bgcolors else []

    @bgcolors.setter
    def bgcolors(self, value: Optional[Sequence[Color]]) -> None:
        """Set the list of background colors in the gradient."""
        self._bgcolors = list(value) if value else []

    @staticmethod
    def parse_colors(
        colors: Optional[Sequence[ColorType]] = None,
        hues: int = 5,
        rainbow: bool = False,
    ) -> List[Color]:
        """Parse and return a list of colors for the gradient.
        Supports 3-digit hex colors (e.g., '#f00', '#F90'), 6-digit hex, CSS names, and Color objects.
        Args:
            colors (Optional[Sequence[ColorType | Color]]): A list of colors as Color instances or strings.
            hues (int): The number of hues to generate if colors are not provided.
            rainbow (bool): If True, generate a rainbow spectrum.
        Returns:
            List[Color]: A list of Color objects.
        """
        if rainbow:
            return Spectrum(hues=18).colors
        if colors is None or len(colors) == 0:
            return Spectrum(hues).colors
        # Support 3-digit hex colors and all string representations via Color.parse
        return [c if isinstance(c, Color) else Color.parse(c) for c in colors]

    def parse_bgcolors(
        self, bgcolors: Optional[Sequence[ColorType]] = None, hues: int = 5
    ) -> List[Color]:
        """Parse and return a list of background colors for the gradient.
        Supports 3-digit hex colors (e.g., '#f00', '#F90'), 6-digit hex, CSS names, and Color objects.
        Args:
            bgcolors (Optional[Sequence[ColorType | Color]]): A list of background colors as Color instances or strings.
            hues (int): The number of hues to generate if bgcolors are not provided.
        Returns:
            List[Color]: A list of Color objects for background colors.
        """
        if bgcolors is None or len(bgcolors) == 0:
            self._interpolate_bgcolors = False
            return [Color.parse("default")] * len(self.colors)

        if len(bgcolors) == 1:
            # If only one background color is provided, repeat it for each character
            self._interpolate_bgcolors = False
            return [Color.parse(bgcolors[0])] * len(self.colors)
        # Support 3-digit hex colors and all string representations via Color.parse
        self._interpolate_bgcolors = True
        return [c if isinstance(c, Color) else Color.parse(c) for c in bgcolors]

    def interpolate_colors(
        self, colors: Optional[Sequence[Color]] = None
    ) -> list[Color]:
        """Interpolate colors in the gradient."""
        colors = list(colors) if colors is not None else self.colors
        if not colors:
            raise ValueError("No colors to interpolate")
        # Prepare the text and handle edge cases

        text = self.plain
        length = len(text)
        if length == 0:
            return []
        num_colors = len(colors)
        if num_colors == 1:
            return [colors[0]] * length

        # Compute number of segments between colors
        segments = num_colors - 1
        result: List[Color] = []

        # For each character, determine its position and blend accordingly
        for i in range(length):
            # Normalized position along the entire text
            pos = i / (length - 1) if length > 1 else 0.0
            # Determine which two colors to blend between
            float_index = pos * segments
            index = int(float_index)
            # Clamp to valid segment range
            if index >= segments:
                index = segments - 1
                t = 1.0
            else:
                t = float_index - index

            start = colors[index]
            end = colors[index + 1]
            triplet1 = start.get_truecolor()
            triplet2 = end.get_truecolor()

            # Interpolate each RGB component
            r = int(triplet1.red + (triplet2.red - triplet1.red) * t)
            g = int(triplet1.green + (triplet2.green - triplet1.green) * t)
            b = int(triplet1.blue + (triplet2.blue - triplet1.blue) * t)

            result.append(Color.from_rgb(r, g, b))

        return result

    def apply_gradient(self) -> None:
        """Apply interpolated colors as spans to each character in the text."""
        # Generate a color for each character
        colors = self.interpolate_colors(self.colors)
        if self._interpolate_bgcolors:
            # Generate a background color for each character if bgcolors are interpolated
            bgcolors = self.interpolate_colors(self.bgcolors)
        else:
            # If not interpolating background colors, use the first bgcolor for all characters
            bgcolors = [self.bgcolors[0]] * len(colors)
        # Apply a style span for each character with its corresponding color
        for index, (color, bgcolor) in enumerate(zip(colors, bgcolors)):
            # Build a style with the interpolated color
            span_style = Style(color=color, bgcolor=bgcolor)
            # Stylize the single character range
            self.stylize(span_style, index, index + 1)


if __name__ == "__main__":
    # Example usage
    console = Console()

    def gradient_example1() -> None:
        """Print the first example with a gradient."""
        colors = ["#ff0", "#9f0", "rgb(0, 255, 0)", "springgreen", "#00FFFF"]

        def example1_text(colors: Sequence[ColorType] = colors) -> RichText:
            """Generate example text with a simple two-color gradient."""
            example1_text = Text(
                'rich-gradient makes it easy to create text with smooth multi-color gradients! \
It is built on top of the amazing rich library, subclassing rich.text.Text. As such, you \
can make use of all the features rich.text.Text provides including:\n\n\t- [bold]bold text[/bold]\
\n\t- [italic]italic text[/italic]\n\t- [underline]underline text[/underline]" \
\n\t- [strike]strikethrough text[/strike]\n\t- [reverse]reverse text[/reverse]\n\t- Text alignment\n\t- \
Overflow handling\n\t- Custom styles and spans',
                colors=colors,
                bgcolors=["#000"],
            )
            example1_text.highlight_regex(r"rich.text.Text", "bold  cyan")
            example1_text.highlight_regex(r"rich-gradient|\brich", "bold white")
            return example1_text

        def example1_title(colors: Sequence[ColorType] = colors) -> RichText:
            """Generate example title text with a gradient."""
            example1_title = Text(
                "Example 1",
                colors=colors,
                style="bold",
                justify="center",
            )
            return example1_title

        console.print(
            Panel(
                example1_text(),
                width=64,
                title=example1_title(),
                padding=(1, 4),
            )
        )
        console.save_svg(
            "docs/img/v0.2.1/gradient_example1.svg",
            title="gradient_example_1",
            unique_id="gradient_example_1",
            theme=GRADIENT_TERMINAL_THEME,
        )

    gradient_example1()

    def gradient_example2() -> None:
        """Print the second example with a random gradient."""
        console.print(
            Panel(
                Text(
                    "To generate a [u]rich_gradient.text.Text[/u] instance, all you need \
is to pass it a string. If no colors are specified it will automatically \
generate a random gradient for you. Random gradients are generated from a \
[b]Spectrum[/b] which is a cycle of 18 colors that span the full RGB color space. \
Automatically generated gradients are always generated with consecutive colors.",
                ),
                title=Text(
                    "Example 2",
                    style="bold",
                ),
                padding=(1, 4),
                width=64,
            )
        )
        console.save_svg(
            "docs/img/v0.2.1/gradient_example2.svg",
            title="gradient_example_2",
            unique_id="gradient_example_2",
            theme=GRADIENT_TERMINAL_THEME,
        )

    gradient_example2()

    def gradient_example3() -> None:
        """Print the third example with a rainbow gradient."""
        console.print(
            Panel(
                Text(
                    "If you like lots of colors, but don't want to write them all yourself... \
Good News! You can also generate a rainbow gradient by passing the `rainbow` \
argument to the `rich_gradient.text.Text` constructor. \
This will generate a gradient with the full spectrum of colors.",
                    rainbow=True,
                ),
                title=Text(
                    "Example 3",
                    style="bold",
                ),
                padding=(1, 4),
                width=64,
            )
        )
        console.save_svg(
            "docs/img/v0.2.1/gradient_example3.svg",
            title="gradient_example_3",
            unique_id="gradient_example_3",
            theme=GRADIENT_TERMINAL_THEME,
        )

    gradient_example3()
    # Example 4: Custom color stops with hex codes

    def gradient_example4() -> None:
        """Print the fourth example with custom color stops."""
        specified_colors: Text = Text(
            text="""If you like to specify your own \
colors, you can specify a list of colors. Colors can be specified \
as:

    - 3 and 6 digit hex strings:
        - '#ff0000'
        - '#9F0'
    - RGB tuples or strings:
        - (255, 0, 0)
        - 'rgb(95, 0, 255)'
    - CSS3 Color names:
        - 'red'
        - 'springgreen'
        - 'dodgerblue'
    - rich.color.Color names:
        - 'grey0'
        - 'purple4'
    - rich.color.Color objects

Just make sure to pass at least two colors... otherwise the gradient \
is superfluous!\n\nThis gradient uses:

    - 'magenta'
    - 'gold1'
    - '#0f0'""",
            colors=["magenta", "gold1", "#0f0"],
        )
        specified_colors.highlight_regex(r"magenta", "#ff00ff")
        specified_colors.highlight_regex(r"#9F0", "#99fF00")
        specified_colors.highlight_words(["gold1"], style="gold1")
        specified_colors.highlight_regex(r"springgreen", style="#00FF7F")
        specified_colors.highlight_regex(r"dodgerblue", style="#1E90FF")
        specified_colors.highlight_regex(r"grey0", style="grey0")
        specified_colors.highlight_regex(r"purple4", style="purple4")
        specified_colors.highlight_regex(r"#f09", style="#f09")
        specified_colors.highlight_regex(r"red|#ff0000|\(255, 0, 0\)", style="red")
        specified_colors.highlight_regex(r"#00FFFF", style="#00FFFF")
        specified_colors.highlight_regex(
            r"rich_gradient\.color\.Color|rich_gradient\.style\.Style|rich\.color\.Color|'|white",
            style="italic white",
        )
        console.print(
            Panel(
                specified_colors,
                title=Text(
                    "Example 4",
                    style="bold",
                ),
                padding=(1, 4),
                width=64,
            )
        )
        console.save_svg(
            "docs/img/v0.2.1/gradient_example4.svg",
            title="gradient_example_4",
            unique_id="gradient_example_4",
            theme=GRADIENT_TERMINAL_THEME,
        )

    gradient_example4()

    # Example 5: Long text with a smooth gradient
    colors5 = ["magenta", "cyan"]
    long_text = (
        "If you are picky about your colors, but prefer simpler gradients, Text will smoothly \
interpolate between two or more colors. This means you can specify a list of colors, or even just \
two colors and Text will generate a smooth gradient between them."
    )
    text5 = Text(long_text, colors=colors5, style="bold", justify="center")

    console.print(
        Panel(
            text5,
            padding=(1, 4),
            width=64,
            title=Text(
                "Example 5",
                style="bold white",
            ),
            border_style="bold cyan",
        )
    )
    console.save_svg(
        "docs/img/v0.2.1/gradient_example5.svg",
        title="gradient_example_5",
        unique_id="gradient_example_5",
        theme=GRADIENT_TERMINAL_THEME,
    )
