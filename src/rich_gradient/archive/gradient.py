from typing import List, Optional, Union, Tuple
from enum import Enum

from rich.console import Console, ConsoleRenderable, ConsoleOptions, RenderResult
from rich.color import Color as RichColor
from rich.segment import Segment
from rich.style import Style
from rich.text import Text
from rich.measure import Measurement
from rich.panel import Panel
from lorem_text import lorem

from rich_gradient.spectrum import Spectrum
from rich_gradient.color import Color as Color, ColorError
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

ColorType = Union[str, Color, RichColor, Tuple[int, int, int]] | str


def interpolate_colors(
    colors: List[ColorType] | List[Color], hues: int, rainbow: bool = False
) -> List[Style]:
    """Interpolate a gradient over `steps` positions from the given colors."""
    if rainbow:
        parsed_colors: List[Color] = Spectrum().colors
    elif not colors and hues >= 2:
        parsed_colors = Spectrum(hues).colors
    elif colors:
        if len(colors) < 2:
            raise ValueError(
                "At least two colors are required for gradient interpolation."
            )
        parsed_colors = [
            color if isinstance(color, Color) else Color(color) for color in colors
        ]

    else:
        raise ValueError(
            "No valid colors provided for gradient. Please specify valid colors or set hues > 1."
        )
    if not parsed_colors:
        raise ValueError("No colors provided for gradient interpolation.")
    interpolated = []
    _hues = max(hues, len(parsed_colors))

    for i in range(_hues):
        t = i / max(hues - 1, 1)
        index = int(t * (len(parsed_colors) - 1))
        c1 = parsed_colors[index]
        c2 = parsed_colors[min(index + 1, len(parsed_colors) - 1)]
        if c1._rgba == c2._rgba:
            # If both colors are the same, just use one of them
            interpolated.append(Style(color=c1.hex))
            continue
        r1,g1,b1 = c1.as_rgb_tuple()
        r2,g2,b2 = c2.as_rgb_tuple()
        mix = (t * (len(parsed_colors) - 1)) % 1

        r = int(r1 + (r2 - r1) * mix)
        g = int(g1 + (g2 - g1) * mix)
        b = int(b1 + (b2 - b1) * mix)

        interpolated.append(Style(color=f"#{r:02x}{g:02x}{b:02x}"))

    return interpolated


class Gradient:
    """
    Applies a line-wise offset-based color gradient to a ConsoleRenderable.
    The gradient can be applied horizontally, vertically, or diagonally by
    adjusting the offset and the wrapped renderable. Each line receives a
    shifted gradient, creating smooth color transitions across the output.
    """

    def __init__(
        self,
        renderable: ConsoleRenderable,
        colors: Optional[List[ColorType]] = None,
        hues: int = 5,
        *,
        rainbow: bool = False,
        offset: float = 1.5,
    ) -> None:
        """Initialize a Gradient wrapper for a renderable.
Args:
    renderable (ConsoleRenderable): The renderable to which the \
gradient will be applied.
    colors (Optional[List[ColorType]]]): The list of colors (or color specifiers) \
to interpolate for the gradient.
    hues: Number of hues to use if colors is not provided (minimum 2).
    rainbow: If True, use a full rainbow spectrum.
    offset: Per-line color offset (for diagonal/vertical gradients).
        """
        self.renderable = renderable
        self.colors = self.parse_colors(colors, rainbow, hues)
        self.offset = offset

    def parse_colors(
        self,
        colors: Optional[List[ColorType]] = None,
        rainbow: bool = False,
        hues: int = 5
    ) -> List[Color]:
        """ Parse and validate the colors for the gradient.
Args:
    colors (Optional[List[ColorType]]):  A list of colors to parse and validate.
    rainbow (bool): If True, use the full spectrum of colors.
    hues (int): The number of hues to use if colors is not provided.
        Generates a spectrum of colors containing `hues` colors.
Returns:
    List[Color]: A list of Color to use as the gradient's color stops.
Raises:
    ValueError: If no valid colors are provided for the gradient.
    ColorError: If any of the provided colors are invalid.
        """
        if rainbow:
            return Spectrum().colors
        elif colors is None and hues >= 2:
            return Spectrum(hues).colors
        elif colors:
            parsed_colors: List[Color] = []
            for color in colors:
                try:
                    parsed_colors.append(Color(color))
                except ColorError as ce:
                    raise ColorError(f"Invalid color: {color}") from ce
            return parsed_colors
        else:
            raise ValueError(
                "No valid colors provided for gradient. Please specify valid colors or set hues > 1."
            )

    def _generate_gradient_matrix(
        self, console: Console, options: ConsoleOptions
    ) -> List[List[Tuple[str, Style]]]:
        """
        Render the wrapped renderable into a 2D matrix of (char, Style),
        representing every character and its effective style (after gradient).
        Each row is a list of (character, Style) tuples for that line.
        """
        # 1) Compute the “true” width to wrap at (like Panel does)
        measurement = Measurement.get(console, options, self.renderable)
        desired_width = min(options.max_width, measurement.maximum)

        # 2) Ask Rich to wrap the renderable into lines of Segments
        inner_options = options.update(max_width=desired_width)
        raw_lines: List[List[Segment]] = list(
            console.render_lines(self.renderable, inner_options, pad=False)
        )

        matrix: List[List[Tuple[str, Style]]] = []

        line_count = len(raw_lines)
        gradient_span = int(options.max_width + abs(self.offset) * line_count)

        for row_index, line_segments in enumerate(raw_lines):
            row: List[Tuple[str, Style]] = []
            char_cursor = 0
            gradient_styles = interpolate_colors(self.colors, gradient_span)

            for seg in line_segments:
                seg_text = seg.text
                base_style = (seg.style or Style()).without_color
                for ch in seg_text:
                    col_index = char_cursor % options.max_width
                    grad_index = (col_index + int(self.offset * row_index)) % gradient_span
                    grad_style = gradient_styles[grad_index]
                    applied = base_style + Style(color=grad_style.color)
                    row.append((ch, applied))
                    char_cursor += 1
            matrix.append(row)
        return matrix

    def get_style_matrix(
        self, console: Console, options: ConsoleOptions
    ) -> List[List[Tuple[str, Style]]]:
        """ Returns a 2D matrix of (char(s), Style) for the entire renderable.
Consecutive characters with identical styles are grouped together in each row.
Args:
    console (Console): The console to render to.
    options (ConsoleOptions): The console options for rendering.
Returns:
    List[List[Tuple[str, Style]]]: A 2D matrix where each row is a list of \
    (character(s), Style) tuples."""
        return self.compress_matrix(self._generate_gradient_matrix(console, options))

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions) -> RenderResult:
        """Render the wrapped renderable in gradient colors.
        The gradient is applied per character, per line, with an offset for each line.

Args:
    console (Console): The console to render to.
    options (ConsoleOptions): The console options for rendering.
Returns:
    RenderResult: A generator yielding styled Text objects for each line.
        """
        matrix = self.get_style_matrix(console, options)
        for row in matrix:
            yield Text.assemble(*(Text(chars, style=style) for chars, style in row))

    def get_style_at(
        self,
        console: Console,
        options: ConsoleOptions,
        row: int,
        col: int,
    ) -> Style:
        """ Retrieve the Style for the character at (row, col) in the rendered output.
Args:
    console (Console): The console to render to.
    options (ConsoleOptions): The console options for rendering.
    row (int): The row index in the rendered output.
    col (int): The column index in the rendered output.
Returns:
    Style: The Style of the character at the specified row and column.
Raises:
    IndexError: If the row or column index is out of bounds of the rendered output.
        """
        matrix = self._generate_gradient_matrix(console, options)
        return matrix[row][col][1]

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        return Measurement.get(console, options, self.renderable)

    @staticmethod
    def compress_matrix(matrix: List[List[Tuple[str, Style]]] ) -> List[List[Tuple[str, Style]]]:
        """Group adjacent characters with the same style in each row.
Args:
    matrix (List[List[Tuple[str, Style]]]): The 2D matrix of (char, Style) tuples.
Returns:
    List[List[Tuple[str, Style]]]: A compressed matrix where adjacent \
characters with the same style are grouped.
        """
        compressed: List[List[Tuple[str, Style]]] = []

        for row in matrix:
            if not row:
                compressed.append([])
                continue

            new_row: List[Tuple[str, Style]] = []
            buffer = row[0][0]
            current_style = row[0][1]

            for char, style in row[1:]:
                if style == current_style:
                    buffer += char
                else:
                    new_row.append((buffer, current_style))
                    buffer = char
                    current_style = style

            new_row.append((buffer, current_style))
            compressed.append(new_row)

        return compressed


if __name__ == "__main__":  # pragma: no cover

    console = Console(record=True)
    lorem = lorem.paragraphs(1)

    gradient_panel = Gradient(
        Panel(
            Text(
                lorem,
                justify="full"),
                title="Gradient Example",
                padding=(1, 2),
                width=64,
        )
    )
    console.print(gradient_panel)
    console.save_svg(
        "docs/img/v0.2.1/renderable_gradient.svg",
        title="Gradient Example",
        theme=GRADIENT_TERMINAL_THEME,
    )
    console.line(2)
    console.rule("[bold #ffffff]Gradient Style Matrix[/]")
    console.line(2)
    matrix = gradient_panel.get_style_matrix(console, console.options)
    for row in matrix:
        console.print(
            Text.assemble(
                *(Text('█', style=style) for _, style in row)
            )
        )
