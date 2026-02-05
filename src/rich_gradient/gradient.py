# rich_gradient/gradient.py

"""
Gradient module for rich-gradient.

This module defines the Gradient class, which provides the core logic for
rendering color gradients in the terminal using the Rich library. It supports
foreground and background gradients, color interpolation with gamma
correction, and flexible alignment options.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, List, Optional, TypeAlias, Union, cast

from rich import get_console
from rich.align import Align, AlignMethod, VerticalAlignMethod
from rich.cells import get_character_cell_size
from rich.color import Color, ColorParseError
from rich.color_triplet import ColorTriplet
from rich.console import Console, ConsoleOptions, ConsoleRenderable, Group, RenderResult
from rich.jupyter import JupyterMixin
from rich.measure import Measurement
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style, StyleType
from rich.text import Text as RichText

from rich_gradient._highlight import (
    HighlightRegex,
    HighlightRegexType,
    HighlightWords,
    HighlightWordsType,
)
from rich_gradient.spectrum import Spectrum

ColorType: TypeAlias = Union[str, Color, ColorTriplet]


@dataclass(frozen=True)
class _HighlightRule:
    """Instruction describing how to highlight content in the rendered output."""

    kind: str  # "words" or "regex"
    style: Style
    words: tuple[str, ...] = ()
    case_sensitive: bool = True
    pattern: re.Pattern[str] | None = None


class Gradient(JupyterMixin):
    """Initialize a Gradient instance.

    Args:
        renderables (str|ConsoleRenderable|List[ConsoleRenderable]): A single renderable or list \
            of renderable objects to which the gradient will be applied.
        colors (List[str|ColorTriplet], Optional): list of colors for the gradient foreground. \
            If omitted and rainbow is False, a spectrum of `hues` colors is used. Accepts \
            3-digit hex strings ('#0f0'), 6-digit hex strings ('#00ff00'), and CSS color \
            names (e.g., 'lime')
        bg_colors(str|ColorTriplet|List[str|ColorTriplet], Optional): the background color \
            or list of colors for the gradient background. Accepts the same formats as \
            `colors`. If omitted, no background is applied.
        console(rich.console.Console, Optional): A rich Console to render to. Defaults to
            `rich.get_console()`.
        hues(int, Optional): the number of hues to generate if no explicit colors are given. \
            defaults to 5. This parameter is ignored if `colors` is provided.
        rainbow(bool, Optional): If True, ignore `colors` and use a full spectrum of colors. \
            defaults to False.
        expand(bool, Optional): Whether to expand renderables to the full console width. \
            defaults to True.
        justify(str|AlignMethod): Horizontal alignment: 'left', 'center', or 'right'. \
            Defaults to 'left'.
        vertical_justify(str|VerticalAlignMethod): Vertical alignment: 'top', 'center', or \
            'bottom'. Defaults to 'middle'.
        repeat_scale(float, Optional): Scale factor controlling gradient repeat span. \
            defaults to 2.0.
        highlight_words(HighlightWordsType|HighlightWords|Sequence[HighlightWords]\
            , Optional): Optional configurations describing \
            word highlights to apply. Accepts either a mapping of words to styles, or a \
            sequence of tuples describing the highlights.

            Examples:
            - {'error': 'bold italic red', 'warning': '#FFFF00', 'lime': '#0f0'}
            - [('error', 'bold red'), (('warning', 'caution'), 'yellow', False)]
            - [HighlightWords(words=('error',), style=Style(bold=True, color='red'))]
        highlight_regex(HighlightRegexType|HighlightRegex|Sequence[HighlightRegex], Optional):
            Optional configurations describing regex highlights to apply. Accepts either \
            a mapping of regex patterns to styles, or a sequence of tuples describing \
            the highlights.
    """

    # Gamma correction exponent for linear interpolation
    _GAMMA_CORRECTION: float = 2.2

    def __init__(
        self,
        renderables: str | ConsoleRenderable | List[ConsoleRenderable],
        colors: Optional[List[ColorType]] = None,
        bg_colors: Optional[List[ColorType]] = None,
        *,
        console: Optional[Console] = None,
        hues: int = 5,
        rainbow: bool = False,
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        repeat_scale: float = 2.0,
        highlight_words: Optional[
            HighlightWordsType | HighlightWords | Sequence[HighlightWords]
        ] = None,
        highlight_regex: Optional[
            HighlightRegexType | HighlightRegex | Sequence[HighlightRegex]
        ] = None,
        animated: bool = False,
    ) -> None:
        """
        Initialize a Gradient instance.

        Args:
            renderables: A single renderable or list of renderable objects to
                which the gradient will be applied.
            colors: Optional list of colors (strings, Color, or
                ColorTriplet) for the gradient foreground. If omitted and
                rainbow is False, a spectrum of `hues` colors is used.
            bg_colors: Optional list of colors for the gradient
                background. If omitted, no background gradient is applied.
            console: Optional Rich Console to render to. Defaults to
                `rich.get_console()`.
            hues: Number of hues to generate if no explicit colors are given.
            rainbow: If True, ignore `colors` and use a full rainbow.
            expand: Whether to expand renderables to the full console width.
            justify: Horizontal alignment: 'left', 'center', or 'right'.
            vertical_justify: Vertical alignment: 'top', 'center', or 'bottom'.
            repeat_scale: Scale factor controlling gradient repeat span.
            highlight_words: Optional configurations describing word highlights to apply.
            highlight_regex: Optional configurations describing regex highlights to apply.
        """
        self.console: Console = console or get_console()
        self.hues: int = max(hues, 2)
        self.rainbow: bool = rainbow
        self.repeat_scale: float = repeat_scale
        self.phase: float = 0.0
        # Keep a flag if the user requested animated behavior; static
        # Gradient objects ignore animation but tests may construct with
        # animated=True, so store the attribute for parity.
        self.animated: bool = bool(animated)
        # Backing attribute for expand; use property setter to allow
        # propagation to wrapped renderables (e.g., Rich Panel instances).
        self._expand: bool = bool(expand)
        self.justify = justify
        self.vertical_justify = vertical_justify

        # Validate and normalize renderables
        if renderables is None:
            raise ValueError("`renderables` cannot be None...")
        if isinstance(renderables, str):
            self.renderables = [RichText.from_markup(renderables)]
        elif isinstance(renderables, ConsoleRenderable):
            self.renderables = [renderables]
        else:
            self.renderables = renderables

        # Parse and store color stops
        foreground_colors: List[ColorType] = list(colors or [])
        background_colors: List[ColorType] = list(bg_colors or [])
        self.colors = foreground_colors  # type: ignore[assignment]
        # Help type-checkers understand the setter accepts ColorType values
        self.bg_colors = cast(Optional[List[ColorType]], \
            background_colors)  # type: ignore[assignment]
        self._active_stops = self._initialize_color_stops()
        self._highlight_rules: list[_HighlightRule] = []
        self._highlight_map_cache: dict[str, list[Optional[Style]]] = {}
        if highlight_words is not None:
            for word_rule in HighlightWords.from_config(highlight_words):
                self._highlight_rules.append(
                    _HighlightRule(
                        kind="words",
                        words=word_rule.words,
                        style=word_rule.style,
                        case_sensitive=word_rule.case_sensitive,
                    )
                )

        if highlight_regex is not None:
            for regex_rule in HighlightRegex.from_config(highlight_regex):
                self._highlight_rules.append(
                    _HighlightRule(
                        kind="regex",
                        pattern=regex_rule.pattern,
                        style=regex_rule.style,
                    )
                )

        self._invalidate_highlight_cache()

    @property
    def expand(self) -> bool:
        """Whether the gradient expands to the available width/height.

        This property is stored on the instance and when updated will attempt
        to propagate the value to common wrapped renderables (for example,
        a stored Rich Panel under ``self._panel``).
        """
        return bool(getattr(self, "_expand", True))

    @expand.setter
    def expand(self, value: bool) -> None:
        self._expand = bool(value)
        # If we have a tracked underlying Panel-like renderable, try to
        # propagate the expand flag to it so Rich rendering honors the
        # intended expansion behavior.
        # Propagate to any well-known stored renderable attributes.
        for attr in ("_panel", "_table", "_rule"):
            obj = getattr(self, attr, None)
            if obj is not None and hasattr(obj, "expand"):
                try:
                    setattr(obj, "expand", self._expand)
                except (AttributeError, TypeError):
                    # Don't propagate failures to avoid breaking rendering.
                    pass

        # Also attempt best-effort propagation to any renderables we've been
        # given (e.g., Table, Panel objects inside self._renderables).
        try:
            for r in getattr(self, "_renderables", []) or []:
                if hasattr(r, "expand"):
                    try:
                        setattr(r, "expand", self._expand)
                    except (AttributeError, TypeError):
                        # Ignore failures when an individual renderable disallows setting expand.
                        pass
        except (AttributeError, TypeError):
            # Defensive: if internal structures are not yet set, ignore.
            pass

    @property
    def renderables(self) -> List[ConsoleRenderable]:
        """List of renderable objects to which the gradient is applied."""
        return self._renderables

    @renderables.setter
    def renderables(self, value: ConsoleRenderable | List[ConsoleRenderable]) -> None:
        """Set and normalize the list of renderables."""
        render_list = value if isinstance(value, list) else [value]
        normalized: List[ConsoleRenderable] = []
        for item in render_list:
            if isinstance(item, str):
                normalized.append(RichText.from_markup(item))
            else:
                normalized.append(item)
        self._renderables = normalized

    @property
    def colors(self) -> List[ColorTriplet]:
        """List of parsed ColorTriplet objects for gradient foreground."""
        return self._foreground_colors

    @colors.setter
    def colors(self, colors: List[ColorType]) -> None:
        """
        Parse and set the foreground color stops.

        Args:
            colors: List of color strings, Color, or ColorTriplet.
        """
        if self.rainbow:
            triplets = Spectrum().triplets
        elif not colors:
            triplets = Spectrum(self.hues).triplets
        else:
            triplets = self._to_color_triplets(colors)

        # Loop smoothly by appending reversed middle stops
        if len(triplets) > 2:
            # Create an extended list for smooth wrapping; avoid mutating any
            # external reference by building a new list.
            extended = triplets + list(reversed(triplets[:-1]))
            self._foreground_colors = extended
        else:
            self._foreground_colors = triplets
        # Recompute active stops only if background colors have already
        # been initialized. During __init__ the bg setter runs after this
        # setter, so avoid accessing unset attributes.
        if getattr(self, "_background_colors", None) is not None:
            self._active_stops = self._initialize_color_stops()

    @property
    def bg_colors(self) -> List[ColorTriplet]:
        """List of parsed ColorTriplet objects for gradient background."""
        return self._background_colors

    @bg_colors.setter
    def bg_colors(self, colors: Optional[List[ColorType]]) -> None:
        """
        Parse and set the background color stops.

        Args:
            colors: Optional list of color strings, Color, or ColorTriplet.
        """
        if not colors:
            self._background_colors = []
            # Recompute active stops after change
            self._active_stops = self._initialize_color_stops()
            return

        if len(colors) == 1:
            triplet = Color.parse(colors[0]).get_truecolor()
            # repeat single color across hues
            self._background_colors = [triplet] * self.hues
        else:
            triplets = self._to_color_triplets(colors)
            self._background_colors = triplets
        # Recompute active stops after change
        self._active_stops = self._initialize_color_stops()

    @property
    def justify(self) -> AlignMethod:
        """Horizontal alignment method."""
        return self._justify  # type: ignore

    @justify.setter
    def justify(self, method: AlignMethod) -> None:
        """
        Validate and set horizontal alignment.

        Args:
            method: 'left', 'center', or 'right'.

        Raises:
            ValueError: If method is invalid.
        """
        if isinstance(method, str) and method.lower() in {"left", "center", "right"}:
            self._justify = method.lower()  # type: ignore
        else:
            raise ValueError(f"Invalid justify method: {method}")

    @property
    def vertical_justify(self) -> VerticalAlignMethod:
        """Vertical alignment method."""
        return self._vertical_justify  # type: ignore

    @vertical_justify.setter
    def vertical_justify(self, method: VerticalAlignMethod) -> None:
        """Validate and set vertical alignment.

        Args:
            method(VerticalAlignMethod): 'top', 'center', or 'bottom'.

        Raises:
            ValueError: If method is invalid.
        """
        if isinstance(method, str) and method.lower() in {"top", "middle", "bottom"}:
            self._vertical_justify = method.lower()  # type: ignore
        else:
            raise ValueError(f"Invalid vertical justify method: {method}")

    @staticmethod
    def _to_color_triplets(colors: List[ColorType]) -> List[ColorTriplet]:
        """
        Convert a list of color specifications to ColorTriplet instances.

        Args:
            colors: List of color strings, Color, or ColorTriplet.

        Returns:
            List of ColorTriplet.

        Raises:
            TypeError: If unsupported color type encountered.
            ColorParseError: If a color string fails to parse.
        """
        triplets: List[ColorTriplet] = []
        for c in colors:
            if isinstance(c, ColorTriplet):
                triplets.append(c)
            elif isinstance(c, Color):
                triplets.append(c.get_truecolor())
            elif isinstance(c, str):
                color = c.strip()
                if len(color) == 4 and color.startswith("#"):
                    h = color[1:]
                    if all(ch in "0123456789abcdefABCDEF" for ch in h):
                        color = "#" + "".join(ch * 2 for ch in h)
                triplets.append(Color.parse(color).get_truecolor())
            else:
                raise ColorParseError(
                    f"Unsupported color type: {type(c)}\n\tCould not parse color: {c}"
                )
        return triplets

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        """
        Measure the minimum and maximum width for the gradient content.

        Args:
            console(rich.console.Console): Console for measurement.
            options(rich.console.ConsoleOptions): Rendering options.

        Returns:
            Measurement: Combined width constraints.
        """
        measurements = [Measurement.get(console, options, r) for r in self.renderables]
        if not measurements:
            # No renderables — return a reasonable default measurement.
            # Min width is 0; max width is the available maximum from options.
            return Measurement(0, options.max_width or 0)

        min_width = min(m.minimum for m in measurements)
        max_width = max(m.maximum for m in measurements)
        return Measurement(min_width, max_width)

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """
        Render the gradient by applying interpolated colors to each segment.

        Args:
            console: Console to render to.
            options: Rendering options.

        Yields:
            Segment: Colored text segments for gradient effect.
        """
        width = options.max_width
        content = Align(
            Group(*self.renderables),
            align=self.justify,
            vertical=self.vertical_justify,
            width=width,
            pad=self.expand,
        )

        lines = console.render_lines(content, options, pad=True, new_lines=False)
        for line_index, segments in enumerate(lines):
            highlight_map = None
            if self._highlight_rules:
                line_text = "".join(segment.text for segment in segments)
                if self.animated:
                    highlight_map = self._build_highlight_map(line_text)
                else:
                    cached = self._highlight_map_cache.get(line_text)
                    if cached is None:
                        cached = self._build_highlight_map(line_text)
                        self._highlight_map_cache[line_text] = cached
                    highlight_map = cached
            column = 0
            char_index = 0
            for seg in segments:
                text = seg.text
                base_style = seg.style or Style()
                cluster = ""
                cluster_width = 0
                cluster_indices: list[int] = []
                for character in text:
                    current_index = char_index
                    char_index += 1
                    character_width = get_character_cell_size(character)
                    if character_width <= 0:
                        cluster += character
                        cluster_indices.append(current_index)
                        continue
                    if cluster:
                        style = self._get_style_at_position(
                            column - cluster_width, cluster_width, width
                        )
                        merged_style = self._merge_styles(base_style, style)
                        merged_style = self._apply_highlight_style(
                            merged_style, highlight_map, cluster_indices
                        )
                        yield Segment(cluster, merged_style)
                        cluster = ""
                        cluster_width = 0
                        cluster_indices = []
                    cluster = character
                    cluster_width = character_width
                    cluster_indices = [current_index]
                    column += character_width
                if cluster:
                    style = self._get_style_at_position(
                        column - cluster_width, cluster_width, width
                    )
                    merged_style = self._merge_styles(base_style, style)
                    merged_style = self._apply_highlight_style(
                        merged_style, highlight_map, cluster_indices
                    )
                    yield Segment(cluster, merged_style)
            if line_index < len(lines) - 1:
                yield Segment.line()

    def _get_style_at_position(self, position: int, width: int, span: int) -> Style:
        """Compute the Rich Style for a character cluster at a given position.

        Args:
            position(int): Starting cell index of the cluster.
            width(int): Cell width of the cluster.
            span(int): Total available width for gradient calculation.

        Returns:
            Style: rich.style.Style with appropriate foreground and/or background colors.
        """
        frac = self._compute_fraction(position, width, span)

        # Default: apply gradient to foreground; background uses bg_colors if provided.
        fg_style = ""
        bg_style = ""
        if self.colors:
            r, g, b = self._interpolate_color(frac, self.colors)
            fg_style = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        if self.bg_colors:
            r, g, b = self._interpolate_color(frac, self.bg_colors)
            bg_style = f"#{int(r):02x}{int(g):02x}{int(b):02x}"

        return Style(color=fg_style or None, bgcolor=bg_style or None)

    def _compute_fraction(self, position: int, width: int, span: float) -> float:
        """Compute fractional position for gradient interpolation, including phase.

        Args:
            position(int): Starting cell index.
            width(int): Cell width.
            span(float): Total span for gradient.

        Returns:
            float: Fraction between 0.0 and 1.0.
        """
        total_width = (span or 0) * (self.repeat_scale or 1.0)
        if total_width <= 0:
            # Avoid division by zero; return phase-only fraction.
            return self.phase % 1.0

        base = (position + width / 2) / total_width
        return (base + self.phase) % 1.0

    def _interpolate_color(
        self, frac: float, color_stops: list[ColorTriplet]
    ) -> tuple[float, float, float]:
        """Interpolate color in linear light space with gamma correction.

        Args:
            frac(float): Fractional position between 0.0 and 1.0.
            color_stops(List[ColorTriplet]): List of ColorTriplet stops.

        Returns:
            Tuple of (r, g, b) in sRGB space.
        """
        if frac <= 0:
            return color_stops[0]
        if frac >= 1:
            return color_stops[-1]

        # Determine segment and local position
        segment_count = len(color_stops) - 1
        pos = frac * segment_count
        idx = int(pos)
        t = pos - idx

        r0, g0, b0 = color_stops[idx]
        r1, g1, b1 = color_stops[min(idx + 1, segment_count)]

        def to_linear(c: float) -> float:
            return (c / 255.0) ** self._GAMMA_CORRECTION

        def to_srgb(x: float) -> float:
            return (x ** (1.0 / self._GAMMA_CORRECTION)) * 255.0

        lr0, lg0, lb0 = to_linear(r0), to_linear(g0), to_linear(b0)
        lr1, lg1, lb1 = to_linear(r1), to_linear(g1), to_linear(b1)

        lr = lr0 + (lr1 - lr0) * t
        lg = lg0 + (lg1 - lg0) * t
        lb = lb0 + (lb1 - lb0) * t

        return to_srgb(lr), to_srgb(lg), to_srgb(lb)

    @staticmethod
    def _merge_styles(original: Style, gradient_style: Style) -> Style:
        """
        Merge original Style with gradient Style, preserving original attributes.

        Args:
            original: The existing Rich Style.
            gradient_style: Style with gradient colors.

        Returns:
            Combined Style.
        """
        return original + gradient_style if original else gradient_style

    @staticmethod
    def _coerce_highlight_style(style: StyleType) -> Style:
        if isinstance(style, Style):
            return style
        return Style.parse(str(style))

    def highlight_words(
        self,
        words: Sequence[str],
        style: StyleType,
        *,
        case_sensitive: bool = True,
    ) -> "Gradient":
        """
        Highlight occurrences of the provided words with an additional style \
            after gradients are applied.

        Args:
            words(Sequence[str]): Iterable of words to highlight.
            style(StyleType): Style to overlay on matched words.
            case_sensitive(bool): Whether matching is case-sensitive. Defaults to True.

        Returns:
            The gradient instance (for chaining).
        """
        self._invalidate_highlight_cache()
        filtered = tuple(word for word in words if word)
        if not filtered:
            return self
        highlight_style = self._coerce_highlight_style(style)
        self._highlight_rules.append(
            _HighlightRule(
                kind="words",
                style=highlight_style,
                words=filtered,
                case_sensitive=case_sensitive,
            )
        )
        return self

    def highlight_regex(
        self, pattern: str | re.Pattern[str], style: StyleType, flags: int = 0
    ) -> "Gradient":
        """
        Highlight matches of a regex pattern with an additional style after gradients are applied.

        Args:
            pattern(str|re.Pattern[str]): Regex pattern (string or compiled).
            style(StyleType): Style to overlay on matches.
            flags(int): Optional regex flags when pattern is a string. Defaults to 0.

        Returns:
            The gradient instance (for chaining).
        """
        self._invalidate_highlight_cache()
        highlight_style = self._coerce_highlight_style(style)
        compiled = (
            pattern
            if isinstance(pattern, re.Pattern)
            else re.compile(pattern, flags=flags)
        )
        self._highlight_rules.append(
            _HighlightRule(
                kind="regex",
                style=highlight_style,
                pattern=compiled,
            )
        )
        return self

    def _invalidate_highlight_cache(self) -> None:
        """Clear cached highlight maps when highlight rules change."""
        if self._highlight_map_cache:
            self._highlight_map_cache.clear()

    def _build_highlight_map(self, text: str) -> list[Optional[Style]]:
        """Compute per-character highlight styles for a line of text."""
        if not text or not self._highlight_rules:
            return []
        highlight_map: list[Optional[Style]] = [None] * len(text)
        apply_range = self._apply_highlight_range

        def apply_word_rule() -> None:
            haystack = text if rule.case_sensitive else text.lower()
            for word in rule.words:
                target = word if rule.case_sensitive else word.lower()
                if not target:
                    continue
                start = 0
                while True:
                    index = haystack.find(target, start)
                    if index == -1:
                        break
                    end = index + len(target)
                    apply_range(highlight_map, index, end, rule.style)
                    start = end

        def apply_regex_rule() -> None:
            pattern = rule.pattern
            if pattern is None:
                return
            for match in pattern.finditer(text):
                # If the regex contains capture groups, apply highlighting only
                # to those group spans. Otherwise, fall back to the whole match.
                try:
                    groups = match.groups()
                except (AttributeError, TypeError):
                    groups = ()
                if groups:
                    last_index = match.lastindex or 0
                    for gi in range(1, last_index + 1):
                        gstart, gend = match.span(gi)
                        if gstart == -1 or gstart == gend:
                            continue
                        apply_range(highlight_map, gstart, gend, rule.style)
                    continue
                start, end = match.span()
                if start == end:
                    continue
                apply_range(highlight_map, start, end, rule.style)

        for rule in self._highlight_rules:
            if rule.kind == "words":
                apply_word_rule()
            elif rule.kind == "regex":
                apply_regex_rule()
        return highlight_map

    @staticmethod
    def _apply_highlight_range(
        highlight_map: list[Optional[Style]], start: int, end: int, style: Style
    ) -> None:
        """Apply style to a character range in the highlight map.
        Args:
            highlight_map(List[Optional[Style]]): List of per-character highlight styles.
            start(int): Starting index (inclusive).
            end(int): Ending index (exclusive).
            style(Style): Style to apply.
        """
        end = min(end, len(highlight_map))
        if start < 0 or start >= end:
            return
        for index in range(start, end):
            existing = highlight_map[index]
            highlight_map[index] = existing + style if existing else style

    @staticmethod
    def _apply_highlight_style(
        base_style: Style,
        highlight_map: Optional[list[Optional[Style]]],
        indices: Sequence[int],
    ) -> Style:
        """Merge highlight styles for character indices into the base style."""
        if not highlight_map or not indices:
            return base_style
        highlight_style: Optional[Style] = None
        for index in indices:
            if 0 <= index < len(highlight_map):
                style = highlight_map[index]
                if style is None:
                    continue
                highlight_style = highlight_style + style if highlight_style else style
        if highlight_style:
            return base_style + highlight_style
        return base_style

    # -----------------
    # Test helper parity
    # -----------------
    def _initialize_color_stops(self) -> List[ColorTriplet]:
        """Initialize the active color stops based on mode and provided stops.

        If only one stop is provided, duplicate it to create a smooth segment pair.
        """
        # Prefer foreground color stops; fall back to background stops if set
        source: List[ColorTriplet] = self.colors if self.colors else self.bg_colors
        if not source:
            return []
        return [source[0], source[0]] if len(source) == 1 else source

    def _color_at(self, pos: int, width: int, span: int) -> str:
        """Return the hex color at a given position (for tests)."""
        stops = self._active_stops
        if not stops:
            return "#000000"
        frac = self._compute_fraction(pos, width, span)
        r, g, b = self._interpolate_color(frac, stops)
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    def _styled(self, original: Style, color: str) -> Style:
        """Return a Style with the given color or bgcolor, preserving original (for tests)."""
        return (
            original + Style(bgcolor=color)
            if self.bg_colors
            else original + Style(color=color)
        )

    def _interpolated_color(
        self, frac: float, stops: list, _count: Optional[int] = None
    ):
        """Return the interpolated color at a fraction (for tests)."""
        return self._interpolate_color(frac, stops)


if __name__ == "__main__":  # pragma: no cover
    # Example BaseGradient Usage
    _console = Console()
    _console.print(
        Gradient(
            Panel(
                RichText.from_markup(
                    "[b]Gradient[/b] can print any rich.console.ConsoleRenderable \
in [i]smooth[/i], [b]gradient[/b] color.\nIf no explicit colors are given, a spectrum of \
colors is generated based on hue.\n\n[b]Gradient[/b] can parse \
and render gradients from:\n\t- CSS3 named colors ('lime'),\n\t- 3 digit hex colors \
('#0f0'),\n\t- 6 digit hex colors ('#00ff00'),\n\t- RGB triplets ('rgb(0,255,0)')",
                    justify="left",
                ),
                title="Color Parsing",
                title_align="left",
            ),
            highlight_words={
                "'lime'": "bold lime",
                "'#0f0'": "bold #0f0",
                "'#00ff00'": "bold #00ff00",
                "'rgb(0,255,0)'": "bold rgb(0,255,0)",
                "hue": "bold white",
            },
            highlight_regex={r"\w+\.\w+": "bold white", r"\w+\.\w+\.\w+": "bold white"},
            justify="left",
        ),
        justify="center",
    )
# rich_gradient/gradient.py
