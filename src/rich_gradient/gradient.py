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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, List, Optional, TypeAlias, Union, Tuple

from rich import get_console
from rich.align import Align, AlignMethod, VerticalAlignMethod
from rich.cells import get_character_cell_size
from rich.color import Color, ColorParseError
from rich.color_triplet import ColorTriplet
from rich.console import (
    Console,
    ConsoleOptions,
    ConsoleRenderable,
    Group,
    RenderResult,
)
from rich.jupyter import JupyterMixin
from rich.measure import Measurement
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style, StyleType
from rich.text import Text as RichText

from rich_gradient.spectrum import Spectrum

# Type alias for accepted color inputs
ColorType: TypeAlias = Union[str, Color, ColorTriplet]


@dataclass(frozen=True)
class _HighlightRule:
    """Instruction describing how to highlight content in the rendered output."""

    kind: str  # "words" or "regex"
    style: Style
    words: tuple[str, ...] = ()
    case_sensitive: bool = False
    pattern: re.Pattern[str] | None = None

HighlightWordsType: TypeAlias = Union[
    Mapping[str, StyleType],
    Sequence[Tuple[str | Sequence[str], StyleType, bool]],
]
HighlightRegexType: TypeAlias = Union[
    Mapping[str | re.Pattern, StyleType],
    Sequence[Tuple[str | re.Pattern, StyleType, int]],
]


class Gradient(JupyterMixin):
    """
    Base class for rendering color gradients in the terminal using Rich.

    This class applies a smoothly interpolated gradient of foreground and/or
    background colors across supplied renderable content.

    Attributes:
        console: Console instance used for rendering.
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
        expand: bool = False,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "top",
        repeat_scale: float = 2.0,
        highlight_words: Optional[HighlightWordsType] = None,
        highlight_regex: Optional[HighlightRegexType] = None,
    ) -> None:
        """
        Initialize a BaseGradient instance.

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
        self.expand: bool = expand
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
        self.colors = foreground_colors
        self.bg_colors = background_colors
        self._active_stops = self._initialize_color_stops()
        self._highlight_rules: list[_HighlightRule] = []
        if highlight_words:
            self._ingest_init_highlight_words(highlight_words)
        if highlight_regex:
            self._ingest_init_highlight_regex(highlight_regex)

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
            # Append reversed stops excluding final stop so gradient wraps smoothly
            triplets += list(reversed(triplets[:-1]))
        self._foreground_colors = triplets

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
            return

        if len(colors) == 1:
            triplet = Color.parse(colors[0]).get_truecolor()
            # repeat single color across hues
            self._background_colors = [triplet] * self.hues
        else:
            triplets = self._to_color_triplets(colors)
            self._background_colors = triplets

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
        """
        Validate and set vertical alignment.

        Args:
            method: 'top', 'center', or 'bottom'.

        Raises:
            ValueError: If method is invalid.
        """
        if isinstance(method, str) and method.lower() in {"top", "center", "bottom"}:
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
                triplets.append(Color.parse(c).get_truecolor())
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
            console: Console for measurement.
            options: Rendering options.

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
                highlight_map = self._build_highlight_map(line_text)
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
        """
        Compute the Rich Style for a character cluster at a given position.

        Args:
            position: Starting cell index of the cluster.
            width: Cell width of the cluster.
            span: Total available width for gradient calculation.

        Returns:
            Style with appropriate foreground and/or background colors.
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
        """
        Compute fractional position for gradient interpolation, including phase.

        Args:
            position: Starting cell index.
            width: Cell width.
            span: Total span for gradient.

        Returns:
            Fraction between 0.0 and 1.0.
        """
        total_width = (span or 0) * (self.repeat_scale or 1.0)
        if total_width <= 0:
            # Avoid division by zero; return phase-only fraction.
            return self.phase % 1.0

        base = (position + width / 2) / total_width
        return (base + self.phase) % 1.0

    def _interpolate_color(
        self,
        frac: float,
        color_stops: list[ColorTriplet]
    ) -> tuple[float, float, float]:
        """
        Interpolate color in linear light space with gamma correction.

        Args:
            frac: Fractional position between 0.0 and 1.0.
            color_stops: List of ColorTriplet stops.

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

    # -----------------
    # Highlight helpers
    # -----------------
    def _ingest_init_highlight_words(
        self, config: Mapping[Any, Any] | Sequence[Any]
    ) -> None:
        """Ingest highlight word configuration supplied to __init__."""
        for words, style, case_sensitive in self._iter_highlight_word_entries(config):
            self.highlight_words(words, style, case_sensitive=case_sensitive)

    def _iter_highlight_word_entries(
        self, config: Mapping[Any, Any] | Sequence[Any]
    ) -> Sequence[tuple[tuple[str, ...], StyleType, bool]]:
        """Yield normalized (words, style, case_sensitive) tuples."""
        entries: list[tuple[tuple[str, ...], StyleType, bool]] = []
        if isinstance(config, Mapping):
            for words_spec, payload in config.items():
                entries.append(self._normalize_word_mapping_entry(words_spec, payload))
        elif isinstance(config, Sequence) and not isinstance(config, (str, bytes)):
            for entry in config:
                entries.append(self._normalize_word_sequence_entry(entry))
        else:
            raise TypeError(
                "highlight_words must be a mapping or sequence of highlight definitions."
            )
        return entries

    def _normalize_word_mapping_entry(
        self, words_spec: Any, payload: Any
    ) -> tuple[tuple[str, ...], StyleType, bool]:
        words = self._normalize_words_spec(words_spec)
        if isinstance(payload, Mapping):
            if "style" not in payload:
                raise ValueError("highlight word mapping payload must include 'style'.")
            style: StyleType = payload["style"]
            case_sensitive = bool(payload.get("case_sensitive", False))
        elif isinstance(payload, (list, tuple)):
            if not payload:
                raise ValueError("highlight word tuple payload cannot be empty.")
            style = payload[0]
            case_sensitive = bool(payload[1]) if len(payload) > 1 else False
        else:
            style = payload
            case_sensitive = False
        return words, style, case_sensitive

    def _normalize_word_sequence_entry(
        self, entry: Any
    ) -> tuple[tuple[str, ...], StyleType, bool]:
        if isinstance(entry, Mapping):
            if "words" not in entry or "style" not in entry:
                raise ValueError(
                    "Each highlight word dict must include 'words' and 'style' keys."
                )
            words = self._normalize_words_spec(entry["words"])
            style: StyleType = entry["style"]
            case_sensitive = bool(entry.get("case_sensitive", False))
            return words, style, case_sensitive
        if isinstance(entry, (list, tuple)):
            if len(entry) < 2 or len(entry) > 3:
                raise ValueError(
                    "Each highlight word tuple must be (words, style[, case_sensitive])."
                )
            words = self._normalize_words_spec(entry[0])
            style: StyleType = entry[1]
            case_sensitive = bool(entry[2]) if len(entry) == 3 else False
            return words, style, case_sensitive
        raise TypeError(
            "highlight_words sequence entries must be dicts or tuples describing the highlight."
        )

    @staticmethod
    def _normalize_words_spec(words: Any) -> tuple[str, ...]:
        """Normalize a word or sequence of words to a tuple of strings."""
        if isinstance(words, str):
            return (words,)
        if isinstance(words, Sequence) and not isinstance(words, (str, bytes)):
            normalized = tuple(str(word) for word in words if str(word))
            if not normalized:
                raise ValueError("Word sequences must contain at least one non-empty string.")
            return normalized
        raise TypeError("Highlight words must be a string or a sequence of strings.")

    def _ingest_init_highlight_regex(
        self, config: Mapping[Any, Any] | Sequence[Any]
    ) -> None:
        """Ingest highlight regex configuration supplied to __init__."""
        for pattern, style, flags in self._iter_highlight_regex_entries(config):
            self.highlight_regex(pattern, style, flags=flags)

    def _iter_highlight_regex_entries(
        self, config: Mapping[Any, Any] | Sequence[Any]
    ) -> Sequence[tuple[str | re.Pattern[str], StyleType, int]]:
        entries: list[tuple[str | re.Pattern[str], StyleType, int]] = []
        if isinstance(config, Mapping):
            for pattern_spec, payload in config.items():
                entries.append(
                    self._normalize_regex_mapping_entry(pattern_spec, payload)
                )
        elif isinstance(config, Sequence) and not isinstance(config, (str, bytes)):
            for entry in config:
                entries.append(self._normalize_regex_sequence_entry(entry))
        else:
            raise TypeError(
                "highlight_regex must be a mapping or sequence of highlight definitions."
            )
        return entries

    def _normalize_regex_mapping_entry(
        self, pattern_spec: Any, payload: Any
    ) -> tuple[str | re.Pattern[str], StyleType, int]:
        pattern = self._normalize_pattern_spec(pattern_spec)
        if isinstance(payload, Mapping):
            if "style" not in payload:
                raise ValueError("highlight regex mapping payload must include 'style'.")
            style: StyleType = payload["style"]
            flags = int(payload.get("flags", 0))
        elif isinstance(payload, (list, tuple)):
            if not payload:
                raise ValueError("highlight regex tuple payload cannot be empty.")
            style = payload[0]
            flags = int(payload[1]) if len(payload) > 1 else 0
        else:
            style = payload
            flags = 0
        return pattern, style, flags

    def _normalize_regex_sequence_entry(
        self, entry: Any
    ) -> tuple[str | re.Pattern[str], StyleType, int]:
        if isinstance(entry, Mapping):
            if "pattern" not in entry or "style" not in entry:
                raise ValueError(
                    "Each highlight regex dict must include 'pattern' and 'style' keys."
                )
            pattern = self._normalize_pattern_spec(entry["pattern"])
            style: StyleType = entry["style"]
            flags = int(entry.get("flags", 0))
            return pattern, style, flags
        if isinstance(entry, (list, tuple)):
            if len(entry) < 2 or len(entry) > 3:
                raise ValueError(
                    "Each highlight regex tuple must be (pattern, style[, flags])."
                )
            pattern = self._normalize_pattern_spec(entry[0])
            style: StyleType = entry[1]
            flags = int(entry[2]) if len(entry) == 3 else 0
            return pattern, style, flags
        raise TypeError(
            "highlight_regex sequence entries must be dicts or tuples describing the highlight."
        )

    @staticmethod
    def _normalize_pattern_spec(pattern: Any) -> str | re.Pattern[str]:
        """Normalize a pattern specification to a raw pattern or compiled regex."""
        if isinstance(pattern, re.Pattern):
            return pattern
        if pattern is None:
            raise ValueError("Regex pattern cannot be None.")
        return str(pattern)

    def highlight_words(
        self,
        words: Sequence[str],
        style: StyleType,
        *,
        case_sensitive: bool = False,
    ) -> "Gradient":
        """
        Highlight occurrences of the provided words with an additional style \
            after gradients are applied.

        Args:
            words: Iterable of words to highlight.
            style: Style to overlay on matched words.
            case_sensitive: Whether matching is case-sensitive. Defaults to False.

        Returns:
            The gradient instance (for chaining).
        """
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
        self,
        pattern: str | re.Pattern[str],
        style: StyleType,
        *,
        flags: int = 0,
    ) -> "Gradient":
        """
        Highlight matches of a regex pattern with an additional style after gradients are applied.

        Args:
            pattern: Regex pattern (string or compiled).
            style: Style to overlay on matches.
            flags: Optional regex flags when pattern is a string.

        Returns:
            The gradient instance (for chaining).
        """
        highlight_style = self._coerce_highlight_style(style)
        compiled = pattern if isinstance(pattern, re.Pattern) else re.compile(pattern, flags)
        self._highlight_rules.append(
            _HighlightRule(
                kind="regex",
                style=highlight_style,
                pattern=compiled,
            )
        )
        return self

    def _coerce_highlight_style(self, style: StyleType) -> Style:
        """Normalize StyleType inputs to Style for highlight operations."""
        if isinstance(style, Style):
            return style
        if style is None:
            raise ValueError("Highlight style cannot be None.")
        return Style.parse(str(style))

    def _build_highlight_map(self, text: str) -> list[Optional[Style]]:
        """Compute per-character highlight styles for a line of text."""
        if not text or not self._highlight_rules:
            return []
        highlight_map: list[Optional[Style]] = [None] * len(text)
        for rule in self._highlight_rules:
            if rule.kind == "words":
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
                        self._apply_highlight_range(highlight_map, index, end, rule.style)
                        start = index + len(target)
            elif rule.kind == "regex" and rule.pattern is not None:
                for match in rule.pattern.finditer(text):
                    start, end = match.span()
                    if start == end:
                        continue
                    self._apply_highlight_range(highlight_map, start, end, rule.style)
        return highlight_map

    @staticmethod
    def _apply_highlight_range(
        highlight_map: list[Optional[Style]], start: int, end: int, style: Style
    ) -> None:
        """Apply style to a character range in the highlight map."""
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
        source = self.bg_colors if self.bg_colors else self.colors
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
        self, frac: float, stops: list, count: Optional[int] = None
    ):
        """Return the interpolated color at a fraction (for tests)."""
        return self._interpolate_color(frac, stops)


if __name__ == "__main__":
    # Example BaseGradient Usage
    _console=Console()
    _console.print(
        Gradient(
            renderables=Panel(
                RichText.from_markup(
                    "[b]BaseGradient[/b] can print any rich.console.ConsoleRenderable \
in [i]smooth[/i], [b]gradient[/b] color.\nIf no explicit colors are given, a spectrum of \
colors is generated based on hue.\n\n[b]BaseGradient[/b] can parse \
and render gradients from:\n\t- CSS3 named colors,\n\t- 3 and 6 digit hex \
codes,\n\t- RGB triplets (rich.color.ColorTriplet)",
                    justify="left"
                ),
                title="Color Parsing",
                expand=False
            ),
            highlight_words={
                "Color Parsing": "bold white",
                "hue": "bold white"
            },
            highlight_regex={r"\w+\.\w+": "bold white", r"\w+\.\w+\.\w+": "bold white"},
            justify='left'
        ),
        justify="center"
    )
# rich_gradient/gradient.py
