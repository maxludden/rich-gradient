"""
rich_gradient.text
~~~~~~~~~~~~~~~~~~
This module provides a Rich-compatible Text subclass that adds per-character
gradient coloring and optional background-color gradients on top of the
rich.text.Text functionality. It preserves all of rich.text.Text's features
(spans, markup parsing, justification, overflow handling, highlighting, etc.)
while enabling smooth multi-stop gradients, rainbow generation, and single-color
optimizations.
"""
from typing import Iterable, List, Optional, Sequence, Tuple, TypeAlias, Union

from rich.color import Color, ColorParseError
from rich.color_triplet import ColorTriplet
from rich.console import Console, JustifyMethod, OverflowMethod
from rich.control import strip_control_codes
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style, StyleType
from rich.text import Span, TextType
from rich.text import Text as RichText

from rich_gradient.spectrum import Spectrum
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

ColorType: TypeAlias = Union[str, Color, ColorTriplet, Tuple[int, int, int]]


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
            justify (JustifyMethod): Justification method for the text. Defaults to `default`.
            overflow (OverflowMethod): Overflow method for the text. Defaults to `fold`.
            no_wrap (bool): If True, disable wrapping of the text. Defaults to False.
            end (str): The string to append at the end of the text. Default is a newline (`\\n`).
            tab_size (int): The number of spaces for a tab character. Defaults to 4.
            bgcolors (Optional[List[ColorType]]): A list of background colors as Color \
instances. Defaults to None.
            markup (bool): If True, parse Rich markup tags in the input text. Defaults to True.
            spans (Optional[Sequence[Span]]): A list of spans to apply to the text. Defaults to None.
        """

        # Parse the input text with or without markup
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

        # Extract parsed attributes
        plain = parsed_text.plain
        parsed_justify = parsed_text.justify
        parsed_overflow = parsed_text.overflow
        parsed_spans = parsed_text._spans

        # Initialize the parent class
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
        self._interpolate_bgcolors = False  # Ensure flag is always initialized
        # Normalize color inputs into rich.color.Color instances
        self.colors = self.parse_colors(colors, hues, rainbow)
        self.bgcolors = self.parse_bgcolors(bgcolors, hues)

        # Handle the single-color and single-background case: apply style directly and return early
        if len(self.colors) == 1 and len(self.bgcolors) == 1:
            # Apply the single color style directly. Parse the provided style only once.
            if isinstance(style, str):
                parsed_style = Style.parse(style)
            elif isinstance(style, Style):
                parsed_style = style
            else:
                parsed_style = Style.parse(str(style))
            style_with_color = (
                Style(color=self.colors[0], bgcolor=self.bgcolors[0]) + parsed_style
            )
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
    def _normalize_color(value: ColorType) -> Color:
        """Normalize a single color-like value to a rich.color.Color.
        Accepts: Color, ColorTriplet, 3-tuple of ints, or string parsable
        by Color.parse. Note that rich-color-ext expands what is considered
        a valid color input.

        Args:
            value (ColorType): The color-like value to normalize.
        Returns:
            Color: The normalized Color instance.
        Raises:
            ColorParseError: If the color value cannot be parsed.
        """
        try:
            if isinstance(value, Color):
                return value
            elif isinstance(value, ColorTriplet):
                return Color.from_rgb(value.red, value.green, value.blue)
            elif isinstance(value, tuple) and len(value) == 3:
                r, g, b = value
                return Color.from_rgb(int(r), int(g), int(b))
            else:
                return Color.parse(str(value))
        except ColorParseError as cpe:
            raise ColorParseError(
                f"Failed to parse and normalize color: {value}"
            ) from cpe

    @staticmethod
    def parse_colors(
        colors: Optional[Sequence[ColorType]] = None,
        hues: int = 5,
        rainbow: bool = False,
    ) -> List[Color]:
        """Parse and return a list of colors for the gradient.
        Supports:
        - rgb colors (e.g. `'rgb(255, 0, 0)'`)
        - rgb tuples (e.g., `(255, 0, 0)`)
        - 3-digit hex colors (e.g., `'#f00'`, `'#F90'`)
        - 6-digit hex colors (e.g., `'#ff0000'`, `'#00FF00'`)
        - CSS names (e.g., `'red'`, `'aliceblue'`)
        - rich.color.Color objects (e.g., `Color.parse('#FF0000')`)
        Args:
            colors (Optional[Sequence[ColorType | Color]]): A list of colors as Color
                instances, tuples of integers, or strings.
            hues (int): The number of hues to generate if colors are not provided. Defaults to 5.
            rainbow (bool): Whether to generate a rainbow spectrum. Note that rainbow overrides
                any colors or hues provided. Defaults to False
        Raises:
            ColorParseError: If any color value cannot be parsed.
            ValueError: If no colors are provided, rainbow is False, and hues < 2.
        Returns:
            List[rich.color.Color]: A list of Color objects.
        """
        # When rainbow is True, we use a full 17-color spectrum
        if rainbow:
            return Spectrum(hues=17).colors

        # If no colors are provided, fall back to Spectrum with the specified hues
        if colors is None or len(colors) == 0:
            if hues < 2:
                raise ValueError(
                    f"If `rainbow=False` and no colors are provided, hues must be \
at least 2. Invalid hues value: {hues}"
                )
            return Spectrum(hues).colors

        # If we have colors, parse and normalize them
        parsed: List[Color] = []
        for c in colors:
            try:
                parsed.append(Text._normalize_color(c))
            except Exception as exc:  # pragma: no cover - defensive
                raise ColorParseError(f"Unsupported color value: {c}") from exc
        return parsed

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
            # Default to transparent/default background per character count
            return [Color.parse("default")] * max(1, len(self.colors))

        if len(bgcolors) == 1:
            # If only one background color is provided, do not interpolate
            self._interpolate_bgcolors = False
            c = bgcolors[0]
            try:
                normalized = Text._normalize_color(c)
            except Exception as exc:  # pragma: no cover - defensive
                raise ColorParseError(f"Unsupported background color: {c}") from exc
            return [normalized] * max(1, len(self.colors))

        # Multiple bgcolors: interpolate across provided stops
        self._interpolate_bgcolors = True
        parsed_bg: List[Color] = []
        for c in bgcolors:
            try:
                parsed_bg.append(Text._normalize_color(c))
            except Exception as exc:  # pragma: no cover - defensive
                raise ColorParseError(f"Unsupported background color: {c}") from exc
        return parsed_bg

    def interpolate_colors(
        self, colors: Optional[Sequence[Color]] = None
    ) -> list[Color]:
        """Interpolate colors across the text using gamma-correct blending."""
        colors = list(colors) if colors is not None else self.colors
        if not colors:
            raise ValueError("No colors to interpolate")

        text = self.plain
        length = len(text)
        if length == 0:
            return []
        num_colors = len(colors)
        if num_colors == 1:
            return [colors[0]] * length

        segments = num_colors - 1
        result: List[Color] = []

        GAMMA = 2.2

        def to_linear(v: int) -> float:
            return (v / 255.0) ** GAMMA

        def to_srgb(x: float) -> int:
            return int(((x ** (1.0 / GAMMA)) * 255.0))

        for i in range(length):
            pos = i / (length - 1) if length > 1 else 0.0
            fidx = pos * segments
            idx = int(fidx)
            if idx >= segments:
                idx = segments - 1
                t = 1.0
            else:
                t = fidx - idx

            c0 = colors[idx].get_truecolor()
            c1 = colors[idx + 1].get_truecolor()

            lr = to_linear(c0.red) + (to_linear(c1.red) - to_linear(c0.red)) * t
            lg = to_linear(c0.green) + (to_linear(c1.green) - to_linear(c0.green)) * t
            lb = to_linear(c0.blue) + (to_linear(c1.blue) - to_linear(c0.blue)) * t

            r, g, b = to_srgb(lr), to_srgb(lg), to_srgb(lb)
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


    def as_rich(self) -> RichText:
        """Return a plain ``rich.text.Text`` with styles and spans applied.

        This converts the current gradient-aware ``Text`` into a base
        ``rich.text.Text`` carrying the same plain content and span/style
        information. Useful when a consumer specifically needs the base type.
        """
        # Create a plain RichText that mirrors the source content and layout
        rich_text = RichText(
            self.plain,
            style=self.style,
            justify=self.justify,
            overflow=self.overflow,
            no_wrap=self.no_wrap,
            end=self.end,
            tab_size=self.tab_size,
        )

        # Copy internal spans from the source into the returned RichText.
        # Using the internal _spans attribute is acceptable here since both
        # classes share the same underlying implementation in rich.
        for span in getattr(self, "_spans", []):
            rich_text._spans.append(span)

        return rich_text

    @property
    def rich(self) -> RichText:
        """Return the underlying RichText instance."""
        return self.as_rich()

    def __rich_console__(self, console: Console, options) -> Iterable[Segment]:
        """Render Text while suppressing any output for empty content.

        For empty plain text, yield no segments at all (no stray newlines).
        Otherwise, delegate to the parent implementation and filter a final
        trailing `end` segment as required.
        """
        if self.plain == "":
            return
        for render_output in super().__rich_console__(console, options):
            if isinstance(render_output, Segment):
                # For empty Text, filter out both the empty text Segment and the trailing end Segment.
                if self.plain == "" and render_output.text in ("", self.end):
                    continue
                yield render_output
            else:
                # Render nested renderable to segments, filter as needed
                for seg in console.render(render_output, options):
                    if self.plain == "" and seg.text in ("", self.end):
                        continue
                    yield seg


if __name__ == "__main__":
    # Example usage
    console = Console(record=True, width=64)

    def gradient_text_example1() -> None:
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
                "Built on rich.text.Text",
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
            "docs/img/v0.3.4/built_on_rich_text.svg",
            title="rich-gradient",
            unique_id="text_example_1",
            theme=GRADIENT_TERMINAL_THEME,
        )

    gradient_text_example1()

    def gradient_text_basic_usage() -> None:
        """Print the second example with a random gradient."""
        console.print(
            Panel(
                Text(
                    "To generate a [u]rich_gradient.text.Text[/u] instance, all you need \
is to pass it a string. If no colors are specified it will automatically \
generate a random gradient for you. Random gradients are generated from a \
[b]Spectrum[/b] which is a cycle of 17 colors that span the full RGB color space. \
Automatically generated gradients are always generated with consecutive colors.",
                ),
                title=Text(
                    "Basic Text Usage",
                    style="bold",
                ),
                padding=(1, 4),
                width=64,
            )
        )
        console.save_svg(
            "docs/img/v0.3.4/gradient_text_basic_usage.svg",
            title="rich-gradient",
            unique_id="text_example_2",
            theme=GRADIENT_TERMINAL_THEME,
        )

    gradient_text_basic_usage()

    def gradient_text_rainbow_example() -> None:
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
                    "Rainbow Text",
                    style="bold",
                ),
                padding=(1, 4),
                width=64,
            )
        )
        console.save_svg(
            "docs/img/v0.3.4/gradient_text_rainbow_example.svg",
            title="rich-gradient",
            unique_id="text_example_3",
            theme=GRADIENT_TERMINAL_THEME,
        )

    gradient_text_rainbow_example()

    # Example 4: Custom color stops with hex codes
    def gradient_text_custom_colors(save: bool = True) -> None:
        """Print the text in a gradient with custom color stops."""
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
        console = Console(record=True, width=64) if save else Console(width=64)
        console.print(
            Panel(
                specified_colors,
                title=Text(
                    "Color Formats",
                    style="bold",
                ),
                padding=(1, 4),
                width=64,
            )
        )
        console.save_svg(
            "docs/img/v0.3.4/gradient_text_custom_colors.svg",
            title="rich-gradient",
            unique_id="text_example_4",
            theme=GRADIENT_TERMINAL_THEME,
        )

    gradient_text_custom_colors()

    def long_text_example() -> None:
        """Example 5: Long text with a smooth gradient."""
        long_text_colors = ["magenta", "cyan"]
        long_text_str = (
            "If you are picky about your colors, but prefer simpler gradients, Text will smoothly \
interpolate between two or more colors. This means you can specify a list of colors, or even just \
two colors and Text will generate a smooth gradient between them.\n\nCillum proident deserunt \
est exercitation laborum eu incididunt ex est in aute enim tempor magna. Do nisi sint anim. \
Sint ipsum amet consequat proident magna consectetur amet aliquip commodo Lorem labore. \
Consectetur adipisicing aute laborum cillum amet voluptate consectetur aliqua mollit eiusmod \
nostrud ut. Elit ex cupidatat ex aliquip id magna incididunt dolor veniam. Ex Lorem duis ut \
ullamco laborum fugiat consequat do amet ullamco. Occaecat ut aliqua irure excepteur minim \
excepteur voluptate duis exercitation occaecat."
        )

        long_text = Text(
            long_text_str, colors=long_text_colors, style="bold", justify="center"
        )

        console.print(
            Panel(
                long_text,
                padding=(1, 4),
                width=64,
                title=Text(
                    "Two Color Gradient Text",
                    style="bold white",
                ),
                border_style="bold cyan",
            )
        )
        console.save_svg(
            "docs/img/v0.3.4/long_text_with_two_color_gradient.svg",
            title="rich-gradient",
            unique_id="text_example_5",
            theme=GRADIENT_TERMINAL_THEME,
        )
