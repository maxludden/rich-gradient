from __future__ import annotations

from time import sleep
from typing import List, Optional, Sequence, Tuple

from cheap_repr import normal_repr, register_repr
from lorem_text import lorem
from rich import inspect
from rich.color import Color as RichColor
from rich.color_triplet import ColorTriplet
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.panel import Panel
from rich.text import Span
from rich.text import Text as RichText
from rich.traceback import install as install_tr

from rich_gradient._helper import get_console
from rich_gradient.color import Color, ColorError, ColorType
from rich_gradient.spectrum import Spectrum
from rich_gradient.style import Style, StyleType
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

console = get_console()
install_tr(console=console)

DEFAULT_JUSTIFY: JustifyMethod = "default"
DEFAULT_OVERFLOW: OverflowMethod = "fold"

VERBOSE: bool = False


class Text(RichText):
    """A text object that supports smooth horizontal gradient colors.
    Args:
        text: The string to render.
        colors: Optional list of StyleType elements (e.g. hex strings or Color objects).
        style: A Rich style to apply globally.
        hues: Number of color stops for rainbow spectrum.
        rainbow: Whether to apply rainbow coloring.
        justify: Text justification.
        overflow: Overflow behavior.
        no_wrap: Whether to disable text wrapping.
        end: End string after rendering.
        tab_size: Tab character size.
        spans: Optional custom Rich spans.
        verbose: Whether to print debug info to the console.
    """

    __slots__ = [
        "_text",  # type: str
        "_colors",  # type: List[Color]
        "style",  # type: str
        "justify",  # type: JustifyMethod
        "overflow",  # type: OverflowMethod
        "no_wrap",  # type: bool
        "end",  # type: str
        "tab_size",  # type: int
        "_spans",  # type: List[Span]
        "rich_text",  # type: RichText
        "_cached_substring_indexes",
        "_cached_gradient_spans"
    ]

    def __init__(
        self,
        text: str = "",
        colors: Optional[Sequence[ColorType]] = None,
        style: Optional[StyleType] = None,
        *,
        hues: int = 5,
        rainbow: bool = False,
        justify: JustifyMethod = DEFAULT_JUSTIFY,
        overflow: OverflowMethod = DEFAULT_OVERFLOW,
        no_wrap: bool = False,
        end: str = "\n",
        tab_size: int = 4,
        spans: Optional[List[Span]] = None,
        verbose: bool = VERBOSE,
        markup: bool = True,
    ) -> None:
        """
        Initialize a Text object that supports gradient colors.

        Args:
            text: The string to render.
            colors: Optional list of StyleType elements (e.g. hex strings or Color objects).
            style: A Rich style to apply globally.
            hues: Number of color stops for rainbow spectrum.
            rainbow: Whether to apply rainbow coloring.
            justify: Text justification.
            overflow: Overflow behavior.
            no_wrap: Whether to disable text wrapping.
            end: End string after rendering.
            tab_size: Tab character size.
            spans: Optional custom Rich spans.
            verbose: Whether to print debug info to the console.
        """
        global VERBOSE
        VERBOSE = verbose
        if style is None:
            style = Style.null()
        # Centralize RichText creation logic
        if markup:
            parsed = RichText.from_markup(
                text, style=str(style), justify=justify, overflow=overflow, end=end
            )
        else:
            parsed = RichText(
                text,
                style=str(style),
                justify=justify,
                overflow=overflow,
                no_wrap=no_wrap,
                end=end,
                tab_size=tab_size,
            )
        super().__init__(
            parsed.plain,
            style=str(style),
            justify=justify,
            overflow=overflow,
            no_wrap=no_wrap,
            end=end,
            tab_size=tab_size,
            spans=spans if spans is not None else parsed.spans,
        )
        self.style = str(style)
        self._text = parsed._text
        self._spans = list(parsed.spans)
        self._colors = self._init_colors(colors, rainbow, hues)
        self._apply_gradient_spans()
        self.rich_text = RichText(
            self.plain,
            style=self.style,
            justify=self.justify,
            overflow=self.overflow,
            no_wrap=no_wrap,
            end=end,
            tab_size=tab_size,
            spans=self._spans,
        )

    # Note: parse_colors now duplicates _init_colors logic; consider consolidating usage.
    def _init_colors(
        self, colors: Optional[Sequence[ColorType]], rainbow: bool, hues: int
    ) -> List[Color]:
        # Using same parsing logic as parse_colors for consistency
        """
        Parse a list of colors or styles into Color objects.

        Args:
            colors: A list of valid color definitions.
            rainbow: If True, generate a rainbow color spectrum.
            hues: Number of hues to generate if rainbow is True.

        Returns:
            A list of Color objects.
        """
        if rainbow:
            return Spectrum(18).colors
        if colors is None:
            if hues < 2:
                raise ValueError(
                    "At least two hues are required when no colors provided."
                )
            return Spectrum(hues).colors

        parsed_colors: List[Color] = []
        for color in colors:
            # if isinstance(color, str):
            #     parsed_colors.append(Color(color))
            # elif isinstance(color, Color):
            #     parsed_colors.append(color)
            # elif isinstance(color, RichColor):
            #     parsed_colors.append(Color.from_rich(color))
            # elif isinstance(color, Style):
            #     style_color = color.color
            #     if style_color is None:
            #         raise ValueError("Style color cannot be None")
            #     parsed_colors.append(Color.from_rich(style_color))
            # elif isinstance(color, tuple) and len(color) == 3:
            #     parsed_colors.append(Color.from_triplet(ColorTriplet(*color)))
            # else:
            #     raise TypeError(f"Unsupported color type: {type(color)}")
            try:
                parsed_colors.append(Color(color))
            except ColorError as ce:
                console.log(f"Error parsing color {color}: {ce}")
                raise ValueError(f"Invalid color definition: {color}") from ce
        return parsed_colors

    @staticmethod
    def parse_colors(
        colors: Optional[Sequence[ColorType]],
        rainbow: bool = False,
        hues: int = 5,
    ) -> List[Color]:
        """
        Parse a list of colors or styles into Color objects.

        Args:
            colors: A list of valid color definitions.
            rainbow: If True, generate a rainbow color spectrum.
            hues: Number of hues to generate if rainbow is True.

        Returns:
            A list of Color objects.
        """
        if rainbow:
            return Spectrum(18).colors
        if colors is None:
            if hues < 2:
                raise ValueError(
                    "At least two hues are required when no colors provided."
                )
            return Spectrum(hues).colors

        parsed_colors: List[Color] = []
        for color in colors:
            # if isinstance(color, str):
            #     parsed_colors.append(Color(color))
            # elif isinstance(color, Color):
            #     parsed_colors.append(color)
            # elif isinstance(color, RichColor):
            #     parsed_colors.append(Color.from_rich(color))
            # elif isinstance(color, Style):
            #     style_color = color.color
            #     if style_color is None:
            #         raise ValueError("Style color cannot be None")
            #     parsed_colors.append(Color.from_rich(style_color))
            # elif isinstance(color, tuple) and len(color) == 3:
            #     parsed_colors.append(Color.from_triplet(ColorTriplet(*color)))
            # else:
            #     raise TypeError(f"Unsupported color type: {type(color)}")
            try:
                parsed_colors.append(Color(color))
            except ColorError as ce:
                console.log(f"Error parsing color {color}: {ce}")
                raise ValueError(f"Invalid color definition: {color}") from ce
        return parsed_colors

    def generate_substring_indexes(self) -> List[Tuple[int, int]]:
        """
        Divide text into segments matching color transitions.

        Returns:
            A list of (start, end) index pairs for each text segment.
        """
        if hasattr(self, "_cached_substring_indexes"):
            return self._cached_substring_indexes

        segments = len(self._colors) - 1
        if VERBOSE:
            console.log(f"{segments=}")

        flat_text = self.plain
        if VERBOSE:
            console.log(f"{flat_text=}")

        base, remainder = divmod(len(flat_text), segments)
        substring_indexes: List[Tuple[int, int]] = []
        start_index = 0
        for i in range(segments):
            length = base + (1 if i < remainder else 0)
            end_index = start_index + length
            substring_indexes.append((start_index, end_index))
            if VERBOSE:
                console.log(
                    f"Segment {i}: start={start_index}, end={end_index}, length={length}"
                )
            start_index = end_index
        self._cached_substring_indexes = substring_indexes
        return substring_indexes

    def get_style_at_index(self, index: int) -> Style:
        """
        Get the style at a specific index.

        Args:
            index (int): The index to get the style for.

        Returns:
            Style: The style at the specified index.
        """
        if VERBOSE:
            console.log(f"Getting spans at index {index}")

        if not self._spans:
            return Style.null()

        # Get all spans that cover the specified index
        if spans := [span for span in self._spans if span.start <= index < span.end]:
            styles: list[Style] = [Style.parse(span.style) for span in spans]
            style = Style()
            for span_style in styles:
                style += span_style
        else:
            style = Style.null()

        if VERBOSE:
            console.log(f"Style at index {index}: {style=}")
        return style

    def _apply_gradient_spans(self) -> None:
        """
        Merge parsed spans with gradient spans, combining styles where necessary.
        Gradient spans are cached after first generation for performance.
        """
        gradient_spans = self._generate_gradient_spans()
        self._spans.extend(gradient_spans)

    def _generate_gradient_spans(self) -> List[Span]:
        """
        Generate gradient Rich spans by blending between adjacent color stops.

        Returns:
            A list of spans with blended RGB styles across the text.
        """
        if hasattr(self, "_cached_gradient_spans"):
            if VERBOSE:
                console.log("Using cached gradient spans")
            return self._cached_gradient_spans
        plain_text = self.plain
        num_chars = len(plain_text)
        num_segments = len(self._colors) - 1

        if num_segments < 1 or num_chars == 0:
            return []

        spans: List[Span] = []
        base, remainder = divmod(num_chars, num_segments)

        start = 0
        for i in range(num_segments):
            color1 = self._colors[i]
            color2 = self._colors[i + 1]
            r1, g1, b1 = color1.triplet
            r2, g2, b2 = color2.triplet

            segment_length = base + (1 if i < remainder else 0)

            for j in range(segment_length):
                index = start + j
                t = j / (segment_length - 1) if segment_length > 1 else 0
                r = int(r1 + (r2 - r1) * t)
                g = int(g1 + (g2 - g1) * t)
                b = int(b1 + (b2 - b1) * t)
                hex_color = f"#{r:02x}{g:02x}{b:02x}"

                existing_style = self.get_style_at_index(index)
                blended_style = Style.combine([existing_style, Style(color=hex_color)])
                spans.append(Span(index, index + 1, str(blended_style)))
            start += segment_length

        self._cached_gradient_spans = spans
        return spans

    @property
    def rich(self) -> RichText:
        """Return the underlying RichText object."""
        return self.rich_text

    def __call__(self) -> RichText:
        """
        Call the Text object to return its RichText representation.

        Returns:
            RichText: The RichText representation of this Text object.
        """
        return self.rich_text


# TODO: re-enable repr registration if needed for debugging

if __name__ == "__main__":
    from rich.console import Console

    console = Console(width=64, theme=GradientTheme(), record=True)

    def gradient_example1() -> None:
        """Print the first example with a gradient."""
        colors = [
            Color(color)
            for color in ["yellow", "#9f0", "rgb(0, 255, 0)", "springgreen", "#00FFFF"]
        ]

        def example1_text(colors: List[Color] = colors) -> RichText:
            """Generate example text with a simple two-color gradient."""
            example1_text = Text(
                'rich-gradient makes it easy to create text with smooth multi-color gradients! \
It is built on top of the amazing rich library, subclassing rich.text.Text. As such, you \
can make use of all the features rich.text.Text provides including:\n\n\t- [bold]bold text[/bold]\
\n\t- [italic]italic text[/italic]\n\t- [underline]underline text[/underline]" \
\n\t- [strike]strikethrough text[/strike]\n\t- [reverse]reverse text[/reverse]\n\t- Text alignment\n\t- \
Overflow handling\n\t- Custom styles and spans',
                colors=colors,
            )
            example1_text.highlight_regex(r"rich.text.Text", "bold  cyan")
            example1_text.highlight_regex(r"rich-gradient|\brich", "bold white")
            return example1_text

        def example1_title(colors: List[Color] = colors) -> RichText:
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
        sleep(1)

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
        sleep(1)

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
        sleep(1)

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
    - rich_gradient.color.Color objects
    - rich_gradient.style.Style objects


Just make sure to pass at least two colors... otherwise the gradient \
is superfluous!\n\nThis gradient uses:

    - 'magenta'
    - 'gold1'
    - '#0f0''""",
            colors=[
                "magenta",
                "gold1",
                "#0f0"
            ],
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
            r"rich_gradient\.color\.Color|rich_gradient\.style\.Style|rich\.color\.Color|'|white", style="italic white")
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
        sleep(1)

    gradient_example4()

    # Example 5: Long text with a smooth gradient
    colors5 = ["magenta", "cyan"]
    long_text = (
        "If you are picky about your colors, but prefer simpler gradients, Text will smoothly \
interpolate between two or more colors. This means you can specify a list of colors, or even just \
two colors and Text will generate a smooth gradient between them."
    )
    text5 = Text(
        long_text,
        colors=colors5,
        style="bold",
        justify = "center"
    )
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
