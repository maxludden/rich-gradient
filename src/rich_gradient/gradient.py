# rich_gradient/gradient.py

"""Gradient module for rich-gradient.

This module defines the Gradient class, which provides the core logic for
rendering color gradients in the terminal using the Rich library. It supports
foreground and background gradients, color interpolation with gamma
correction, and flexible alignment options.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import TypeAlias, cast

from rich import get_console
from rich.align import Align, AlignMethod, VerticalAlignMethod
from rich.cells import get_character_cell_size
from rich.color import Color, ColorParseError
from rich.color_triplet import ColorTriplet
from rich.console import (Console, ConsoleOptions, ConsoleRenderable, Group,
                          RenderableType, RenderResult)
from rich.jupyter import JupyterMixin
from rich.measure import Measurement
from rich.panel import Panel
from rich.segment import Segment
from rich.style import Style, StyleType
from rich.text import Text as RichText

from rich_gradient._color_ext import parse_color
from rich_gradient._gradient_ramp import GradientRamp
from rich_gradient._highlight import (HighlightRegex, HighlightRegexType,
                                      HighlightWords, HighlightWordsType)
from rich_gradient.spectrum import Spectrum, validate_hues

ColorType: TypeAlias = str | Color | ColorTriplet | tuple[int, int, int]
_GradientRampKey: TypeAlias = tuple[
    tuple[ColorTriplet, ...],
    tuple[ColorTriplet, ...],
    int,
    float,
    float,
]


@dataclass(frozen=True)
class _HighlightRule:
    """Instruction describing how to highlight content in the rendered output."""

    kind: str  # "words" or "regex"
    style: Style
    words: tuple[str, ...] = ()
    case_sensitive: bool = True
    pattern: re.Pattern[str] | None = None


class Gradient(JupyterMixin):
    """Apply a smooth color gradient to any Rich renderable.

    The renderable is rendered normally, then each character is recolored by
    its horizontal position along a gamma-corrected ramp between the color
    stops. Styles already on the renderable (bold, italic, ...) are kept.

    Args:
        renderables (RenderableType | Iterable[RenderableType]): A renderable, or an
            iterable of renderables to stack vertically. Strings are parsed as console
            markup, e.g. ``"[bold]Hi[/bold]"`` or ``[Panel("a"), Panel("b")]``.
        colors (Optional[list[ColorType]]): Foreground color stops. Each stop may be a
            color name (Rich/ANSI names such as ``"red"`` keep Rich's meaning; CSS names
            such as ``"tomato"`` also work), a hex string (``"#f00"``, ``"#ff0000"``),
            an ``"rgb(255, 0, 0)"`` string, an ``(r, g, b)`` tuple, or a
            ``rich.color.Color``, e.g. ``["#f00", "orange", (0, 128, 255)]``. If omitted
            and ``rainbow`` is False, ``hues`` colors are taken from the spectrum
            palette. Defaults to None.
        bg_colors (Optional[list[ColorType]]): Background color stops, in the same
            formats as ``colors``, e.g. ``["#000033", "#330033"]``. If omitted, no
            background gradient is applied. Defaults to None.
        console (Optional[Console]): Console used for rendering and measurement.
            Defaults to ``rich.get_console()``.
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted (a run of consecutive hues with a random starting point). Valid
            values are 2 to 17. Defaults to 5.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues``. Defaults to False.
        expand (bool): Expand the output to the full console width. Defaults to True.
        justify (AlignMethod): Horizontal alignment of the content: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"left"``.
        vertical_justify (VerticalAlignMethod): Vertical alignment of the content:
            ``"top"``, ``"middle"``, or ``"bottom"``. Defaults to ``"middle"``.
        repeat_scale (Optional[float]): Width of one full color cycle as a multiple of
            the rendered width; larger values give a more gradual gradient, e.g.
            ``1.5``. ``None`` derives it from the stops so one pass runs from the first
            color to the last (1.0 for two colors, 2.0 for three or more). Defaults to
            None.
        highlight_words (HighlightWordsType | HighlightWords | Sequence[HighlightWords] | None):
            Words to restyle on top of the gradient. Accepts a mapping of a word (or a
            tuple of words) to a style, e.g.
            ``{"error": "bold red", ("warn", "caution"): "yellow"}``; a sequence of
            ``(words, style[, case_sensitive])`` tuples, e.g.
            ``[("error", "bold red"), (("warn", "caution"), "yellow", False)]``; or
            ``HighlightWords`` instances, e.g.
            ``[HighlightWords(words=("error",), style=Style.parse("bold red"))]``.
            Matching is case-sensitive unless ``case_sensitive`` is False. Defaults to
            None.
        highlight_regex (HighlightRegexType | HighlightRegex | Sequence[HighlightRegex] | None):
            Regular expressions whose matches are restyled on top of the gradient.
            Accepts a mapping of a pattern to a style, e.g.
            ``{r"[0-9]+": "bold cyan"}``; a sequence of ``(pattern, style[, flags])``
            tuples, e.g. ``[(r"error|fail", "red", re.IGNORECASE)]``; or
            ``HighlightRegex`` instances, e.g.
            ``[HighlightRegex(pattern=re.compile(r"[0-9]+"), style=Style.parse("cyan"))]``.
            Defaults to None.
        animated (bool): Record that the caller wants animation. Static gradients do not
            animate; use ``AnimatedGradient`` for that. Defaults to False.
        trailing_newline (bool): End the output with a newline, like other Rich
            renderables. Pass False to print a gradient inline with other text. Defaults
            to True.

    Raises:
        ValueError: If ``renderables`` is ``None``, ``hues`` is less than 2 (or more
            than 17 when colors come from the spectrum), or a justify value is invalid.
        ColorParseError: If a color cannot be parsed, an RGB tuple is outside
            0-255, or a color stop has an unsupported type.

    Examples:
        >>> from rich.console import Console
        >>> from rich.panel import Panel
        >>> console = Console()
        >>> console.print(Gradient("Hello, gradient!", colors=["#f00", "#00f"]))
        >>> console.print(Gradient(Panel("Boxed"), rainbow=True, expand=False))
        >>> console.print(
        ...     Gradient(
        ...         "error: disk full",
        ...         colors=["cyan", "magenta"],
        ...         highlight_words={"error": "bold red"},
        ...     )
        ... )
    """

    # Gamma correction exponent for linear interpolation
    _GAMMA_CORRECTION: float = 2.2

    def __init__(
        self,
        renderables: RenderableType | Iterable[RenderableType],
        colors: list[ColorType] | None = None,
        bg_colors: list[ColorType] | None = None,
        *,
        console: Console | None = None,
        hues: int = 5,
        rainbow: bool = False,
        expand: bool = True,
        justify: AlignMethod = "left",
        vertical_justify: VerticalAlignMethod = "middle",
        repeat_scale: float | None = None,
        highlight_words: HighlightWordsType | HighlightWords | \
            Sequence[HighlightWords] | None = None,
        highlight_regex: HighlightRegexType | HighlightRegex | \
            Sequence[HighlightRegex] | None = None,
        animated: bool = False,
        trailing_newline: bool = True,
    ) -> None:
        """Initialize the gradient; see the class docstring for arguments.

        Raises:
            ValueError: If ``renderables`` is ``None``, ``hues`` is out of range, or a
                justify value is invalid.
            ColorParseError: If a color cannot be parsed, an RGB tuple is outside
                0-255, or a color stop has an unsupported type.
        """
        self.trailing_newline: bool = trailing_newline
        self.console: Console = console or get_console()
        self.hues: int = validate_hues(hues)
        self.rainbow: bool = rainbow
        self.repeat_scale: float | None = repeat_scale
        self.phase: float = 0.0
        self._gradient_ramp: GradientRamp | None = None
        self._gradient_ramp_key: _GradientRampKey | None = None
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
        self._set_renderables(renderables)

        # Parse and store color stops
        foreground_colors: list[ColorType] = list(colors or [])
        background_colors: list[ColorType] = list(bg_colors or [])
        self.colors = foreground_colors  # type: ignore[assignment]
        # Help type-checkers understand the setter accepts ColorType values
        self.bg_colors = cast(list[ColorType] | None, background_colors)  # type: ignore[assignment]
        self._active_stops = self._initialize_color_stops()
        self._highlight_rules: list[_HighlightRule] = []
        self._highlight_map_cache: dict[str, list[Style | None]] = {}
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
        """Set ``expand`` and propagate it to a wrapped panel, table, or rule.

        Args:
            value: Whether to expand to the available width.
        """
        self._expand = bool(value)
        # If we have a tracked underlying Panel-like renderable, try to
        # propagate the expand flag to it so Rich rendering honors the
        # intended expansion behavior.
        # Propagate to any well-known stored renderable attributes.
        for attr in ("_panel", "_table", "_rule"):
            obj = getattr(self, attr, None)
            if obj is not None and hasattr(obj, "expand"):
                try:
                    obj.expand = self._expand
                except (AttributeError, TypeError):
                    # Don't propagate failures to avoid breaking rendering.
                    pass

        # Also attempt best-effort propagation to any renderables we've been
        # given (e.g., Table, Panel objects inside self._renderables).
        try:
            for r in getattr(self, "_renderables", []) or []:
                if hasattr(r, "expand"):
                    try:
                        r.expand = self._expand
                    except (AttributeError, TypeError):
                        # Ignore failures when an individual renderable disallows setting expand.
                        pass
        except (AttributeError, TypeError):
            # Defensive: if internal structures are not yet set, ignore.
            pass

    @property
    def renderables(self) -> list[ConsoleRenderable]:
        """List of renderable objects to which the gradient is applied."""
        return self._renderables

    @renderables.setter
    def renderables(
        self, value: RenderableType | Iterable[RenderableType]
    ) -> None:
        """Set and normalize the list of renderables.

        Args:
            value: A renderable, or an iterable of renderables. Strings are
                parsed as console markup, e.g. ``"[bold]Hi[/bold]"``.
        """
        self._set_renderables(value)

    def _set_renderables(
        self, value: RenderableType | Iterable[RenderableType]
    ) -> None:
        """Normalize and store renderables without going through the descriptor.

        Any iterable (list, tuple, set, generator, custom container, ...) is
        expanded into several renderables; iterators are consumed once.
        Strings and objects that render themselves (``rich.text.Text``, panels,
        ...) are iterable or look iterable but must stay whole, so they are
        checked first.

        Args:
            value: A renderable, or an iterable of renderables.
        """
        is_whole = (
            isinstance(value, str)
            or hasattr(value, "__rich_console__")
            or hasattr(value, "__rich__")
        )
        if not is_whole and isinstance(value, Iterable):
            render_list: list[RenderableType] = list(value)
        else:
            render_list = [cast(ConsoleRenderable, value)]
        normalized: list[ConsoleRenderable] = []
        for item in render_list:
            if isinstance(item, str):
                normalized.append(cast(ConsoleRenderable, RichText.from_markup(item)))
            else:
                normalized.append(cast(ConsoleRenderable, item))  # RichCast renders via Group
        self._renderables = normalized

    @property
    def colors(self) -> list[ColorTriplet]:
        """List of parsed ColorTriplet objects for gradient foreground."""
        return self._foreground_colors

    @colors.setter
    def colors(self, colors: list[ColorType]) -> None:
        """Parse and set the foreground color stops.

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
        self._invalidate_gradient_ramp()

    @property
    def bg_colors(self) -> list[ColorTriplet]:
        """List of parsed ColorTriplet objects for gradient background."""
        return self._background_colors

    @bg_colors.setter
    def bg_colors(self, colors: list[ColorType] | None) -> None:
        """Parse and set the background color stops.

        Args:
            colors: Optional list of color strings, Color, or ColorTriplet.
        """
        if not colors:
            self._background_colors = []
            # Recompute active stops after change
            self._active_stops = self._initialize_color_stops()
            self._invalidate_gradient_ramp()
            return

        if len(colors) == 1:
            triplet = self._to_color_triplets([colors[0]])[0]
            # repeat single color across hues
            self._background_colors = [triplet] * self.hues
        else:
            triplets = self._to_color_triplets(colors)
            self._background_colors = triplets
        # Recompute active stops after change
        self._active_stops = self._initialize_color_stops()
        self._invalidate_gradient_ramp()

    @property
    def justify(self) -> AlignMethod:
        """Horizontal alignment method."""
        return self._justify  # type: ignore

    @justify.setter
    def justify(self, method: AlignMethod) -> None:
        """Validate and set horizontal alignment.

        Args:
            method: 'left', 'center', or 'right'.

        Raises:
            ValueError: If method is invalid.
        """
        if isinstance(method, str) and method.lower() in {"left", "center", "right"}:
            self._justify = method.lower()
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
            method(VerticalAlignMethod): 'top', 'middle', or 'bottom'.

        Raises:
            ValueError: If method is invalid.
        """
        if isinstance(method, str) and method.lower() in {"top", "middle", "bottom"}:
            self._vertical_justify = method.lower()
        else:
            raise ValueError(f"Invalid vertical justify method: {method}")

    @staticmethod
    def _to_color_triplets(colors: list[ColorType]) -> list[ColorTriplet]:
        """Convert a list of color specifications to ColorTriplet instances.

        Args:
            colors: Color stops as strings, ``Color``, ``ColorTriplet``, or
                ``(r, g, b)`` tuples, e.g. ``["#f00", (0, 128, 255)]``.

        Returns:
            One ``ColorTriplet`` per input color, in order.

        Raises:
            ColorParseError: If a string fails to parse, an RGB tuple is outside
                0-255, or a color has an unsupported type.
        """
        triplets: list[ColorTriplet] = []
        for c in colors:
            if isinstance(c, ColorTriplet):
                triplets.append(c)
            elif isinstance(c, Color):
                triplets.append(c.get_truecolor())
            elif isinstance(c, tuple) and len(c) == 3:
                red, green, blue = (int(channel) for channel in c)
                if not all(0 <= channel <= 255 for channel in (red, green, blue)):
                    raise ColorParseError(
                        f"RGB tuple values must be between 0 and 255: {c}"
                    )
                triplets.append(ColorTriplet(red, green, blue))
            elif isinstance(c, str):
                triplets.append(parse_color(c).get_truecolor())
            else:
                raise ColorParseError(
                    f"Unsupported color type: {type(c)}\n\tCould not parse color: {c}"
                )
        return triplets

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions
    ) -> Measurement:
        """Measure the minimum and maximum width for the gradient content.

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
        """Render the gradient by applying interpolated colors to each segment.

        Args:
            console: Console to render to.
            options: Rendering options.

        Yields:
            Segment: Colored text segments for gradient effect.
        """
        width = options.max_width
        if self.renderables and all(
            isinstance(r, RichText) and not r.plain for r in self.renderables
        ):
            # Rich prints each empty text as a single newline, whatever its ``end``,
            # but rendering it as lines yields nothing, so emit it directly.
            for _ in self.renderables:
                yield Segment.line()
            return
        group = Group(*self.renderables)
        content = Align(
            group,
            align=self.justify,
            vertical=self.vertical_justify,
            width=width,
            pad=self.expand,
        )

        span, offset = width, 0
        if not self.expand:
            # Spread the ramp over the content, not the whole line, so a narrow
            # block still runs from the first color to the last. The offset
            # mirrors where ``Align`` places the block for center/right.
            span = max(1, min(Measurement.get(console, options, group).maximum, width))
            excess = width - span
            offset = {"center": excess // 2, "right": excess}.get(self.justify, 0)

        yield from self._render_styled_lines(
            console,
            options,
            content,
            trailing_newline=self.trailing_newline and bool(self.renderables),
            span=span,
            offset=offset,
        )

    def _render_styled_lines(
        self,
        console: Console,
        options: ConsoleOptions,
        content: ConsoleRenderable,
        *,
        trailing_newline: bool = False,
        span: int | None = None,
        offset: int = 0,
    ) -> RenderResult:
        """Render content line-by-line and apply gradient styles to cell clusters.

        Args:
            console: The console being rendered to.
            options: The console options for the current render.
            content: The renderable to render and recolor.
            trailing_newline: Emit a final newline after the last line.
                Defaults to False.
            span: Cells the gradient ramp covers. Defaults to None, meaning the
                full line width (``options.max_width``).
            offset: Column where the ramp starts. Cells outside
                ``[offset, offset + span)`` take the nearest end color.
                Defaults to 0.

        Yields:
            Styled segments, with a line break between rendered lines.
        """
        lines = console.render_lines(content, options, pad=True, new_lines=False)
        ramp_span = options.max_width if span is None else span
        for line_index, segments in enumerate(lines):
            highlight_map = self._get_highlight_map_for_segments(segments)
            yield from self._render_styled_segments(
                segments, ramp_span, highlight_map, offset=offset
            )
            if line_index < len(lines) - 1:
                yield Segment.line()
        if trailing_newline:
            yield Segment.line()

    def _get_highlight_map_for_segments(
        self, segments: Sequence[Segment]
    ) -> list[Style | None] | None:
        """Return a cached highlight map for a rendered line when possible.

        Args:
            segments: The segments of one rendered line.

        Returns:
            Per-character highlight styles for the line, or ``None`` when no
            highlight rules are configured.
        """
        if not self._highlight_rules:
            return None
        line_text = "".join(segment.text for segment in segments)
        if self.animated:
            return self._build_highlight_map(line_text)

        cached = self._highlight_map_cache.get(line_text)
        if cached is None:
            cached = self._build_highlight_map(line_text)
            self._highlight_map_cache[line_text] = cached
        return cached

    def _render_styled_segments(
        self,
        segments: Sequence[Segment],
        span: int,
        highlight_map: list[Style | None] | None,
        *,
        offset: int = 0,
    ) -> RenderResult:
        """Apply gradient and highlight styles to rendered Rich segments.

        Args:
            segments: The segments of one rendered line.
            span: Cells the gradient ramp covers.
            highlight_map: Per-character highlight styles for the line, if any.
            offset: Column where the ramp starts; shifts the ramp right.
                Defaults to 0.

        Yields:
            One styled segment per display-cell cluster; control segments
            pass through unchanged.
        """
        column = -offset
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
                    yield self._styled_cluster(
                        cluster,
                        column - cluster_width,
                        cluster_width,
                        span,
                        base_style,
                        highlight_map,
                        cluster_indices,
                    )
                    cluster = ""
                    cluster_width = 0
                    cluster_indices = []
                cluster = character
                cluster_width = character_width
                cluster_indices = [current_index]
                column += character_width
            if cluster:
                yield self._styled_cluster(
                    cluster,
                    column - cluster_width,
                    cluster_width,
                    span,
                    base_style,
                    highlight_map,
                    cluster_indices,
                )

    def _styled_cluster(
        self,
        text: str,
        position: int,
        width: int,
        span: int,
        base_style: Style,
        highlight_map: list[Style | None] | None,
        indices: Sequence[int],
    ) -> Segment:
        """Build a styled segment for one display-cell cluster.

        Args:
            text: The cluster's characters.
            position: Column of the cluster relative to the ramp start.
            width: Display width of the cluster in cells.
            span: Cells the gradient ramp covers.
            base_style: The segment's original style.
            highlight_map: Per-character highlight styles for the line, if any.
            indices: Character indices of the cluster within the line.

        Returns:
            A segment combining the base, gradient, and highlight styles.
        """
        # Clamp padding cells outside the ramp (only possible with an offset or
        # a span narrower than the line) to the nearest end of the ramp.
        position = max(0, min(position, span - width))
        gradient_style = self._get_style_at_position(position, width, span)
        merged_style = self._merge_styles(base_style, gradient_style)
        merged_style = self._apply_highlight_style(merged_style, highlight_map, indices)
        return Segment(text, merged_style)

    def _get_style_at_position(self, position: int, width: int, span: int) -> Style:
        """Compute the Rich Style for a character cluster at a given position.

        Args:
            position(int): Starting cell index of the cluster.
            width(int): Cell width of the cluster.
            span(int): Total available width for gradient calculation.

        Returns:
            Style: rich.style.Style with appropriate foreground and/or background colors.
        """
        return self._get_gradient_ramp(span).style_at(position, width, self.phase)

    def _get_gradient_ramp(self, span: int) -> GradientRamp:
        """Return a cached gradient ramp for the current color configuration.

        Args:
            span: Render span in terminal cells.

        Returns:
            A precomputed gradient ramp for style lookups.
        """
        key = self._build_gradient_ramp_key(span)
        if self._gradient_ramp is None or self._gradient_ramp_key != key:
            foreground_stops, background_stops, ramp_span, repeat_scale, gamma = key
            self._gradient_ramp = GradientRamp(
                foreground_stops=foreground_stops,
                background_stops=background_stops,
                span=ramp_span,
                repeat_scale=repeat_scale,
                gamma=gamma,
            )
            self._gradient_ramp_key = key
        return self._gradient_ramp

    def _build_gradient_ramp_key(self, span: int) -> _GradientRampKey:
        """Build a hashable cache key for the active gradient ramp.

        Args:
            span: Cells the gradient ramp covers.

        Returns:
            A tuple of the foreground stops, background stops, span, repeat
            scale, and gamma.
        """
        foreground, background, scale = self._ramp_stops()
        return (
            tuple(foreground),
            tuple(background),
            int(span or 0),
            float(scale),
            float(self._GAMMA_CORRECTION),
        )

    def _effective_repeat_scale(self) -> float:
        """Return ``repeat_scale``, or the value derived from the color stops."""
        return self._ramp_stops()[2]

    def _ramp_stops(
        self,
    ) -> tuple[list[ColorTriplet], list[ColorTriplet], float]:
        """Return the foreground stops, background stops, and scale for the ramp.

        An explicit ``repeat_scale`` is used as given, with the stops untouched.
        When it is None the scale is derived so one pass across the span runs
        from the first color to the last:

        - Two colors, or a solid background, need no repeat: scale 1.0.
        - Three or more colors are stored as a palindrome (``a, b, c, b, a``),
          so scale 2.0 shows exactly ``a, b, c``. Any other list in play (a
          two-color foreground, or a varying background) is mirrored the same
          way so both share one period.
        """
        foreground = list(self.colors)
        background = list(self.bg_colors)
        if self.repeat_scale:
            return foreground, background, float(self.repeat_scale)

        background_varies = len(set(background)) > 1
        needs_mirror = len(foreground) > 2 or (background_varies and len(background) > 2)
        if not needs_mirror:
            return foreground, background, 1.0
        if len(foreground) == 2:
            foreground = foreground + foreground[-2::-1]
        if background_varies:
            background = background + background[-2::-1]
        return foreground, background, 2.0

    def _invalidate_gradient_ramp(self) -> None:
        """Clear cached gradient ramp state after color changes."""
        if hasattr(self, "_gradient_ramp"):
            self._gradient_ramp = None
            self._gradient_ramp_key = None

    def _compute_fraction(self, position: int, width: int, span: float) -> float:
        """Compute fractional position for gradient interpolation, including phase.

        Args:
            position(int): Starting cell index.
            width(int): Cell width.
            span(float): Total span for gradient.

        Returns:
            float: Fraction between 0.0 and 1.0.
        """
        total_width = (span or 0) * self._effective_repeat_scale()
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
            """Convert an sRGB channel to linear light.

            Args:
                c: Channel value, 0-255.

            Returns:
                Linear-light value, 0-1.
            """
            return (c / 255.0) ** self._GAMMA_CORRECTION

        def to_srgb(x: float) -> float:
            """Convert a linear-light value back to an sRGB channel.

            Args:
                x: Linear-light value, 0-1.

            Returns:
                Channel value, 0-255.
            """
            return (x ** (1.0 / self._GAMMA_CORRECTION)) * 255.0

        lr0, lg0, lb0 = to_linear(r0), to_linear(g0), to_linear(b0)
        lr1, lg1, lb1 = to_linear(r1), to_linear(g1), to_linear(b1)

        lr = lr0 + (lr1 - lr0) * t
        lg = lg0 + (lg1 - lg0) * t
        lb = lb0 + (lb1 - lb0) * t

        return to_srgb(lr), to_srgb(lg), to_srgb(lb)

    def _merge_styles(self, original: Style, gradient_style: Style) -> Style:
        """Merge original Style with gradient Style, preserving original attributes.

        Args:
            original: The existing Rich Style.
            gradient_style: Style with gradient colors.

        Returns:
            Combined Style.
        """
        return original + gradient_style if original else gradient_style

    @staticmethod
    def _coerce_highlight_style(style: StyleType) -> Style:
        """Parse a highlight style.

        Args:
            style: A ``Style`` (returned unchanged) or a style string such as
                ``"bold red"``.

        Returns:
            The parsed ``Style``.
        """
        if isinstance(style, Style):
            return style
        return Style.parse(str(style))

    def highlight_words(
        self,
        words: Sequence[str],
        style: StyleType,
        *,
        case_sensitive: bool = True,
    ) -> Gradient:
        """Highlight words with an extra style applied after the gradient.

        Args:
            words (Sequence[str]): Words to highlight, e.g. ``["error", "fail"]``.
                Empty strings are ignored.
            style (StyleType): Style to overlay on matches, e.g. ``"bold red"``.
            case_sensitive (bool): Whether matching is case-sensitive. Defaults to True.

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
    ) -> Gradient:
        """Highlight matches of a regex pattern with an additional style after gradients are applied.

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

    def _build_highlight_map(self, text: str) -> list[Style | None]:
        """Compute per-character highlight styles for a line of text.

        Args:
            text: The plain text of one rendered line.

        Returns:
            One entry per character: the merged highlight style, or ``None``.
            Empty if there is no text or no highlight rules.
        """
        if not text or not self._highlight_rules:
            return []
        highlight_map: list[Style | None] = [None] * len(text)
        apply_range = self._apply_highlight_range

        def apply_word_rule() -> None:
            """Mark every occurrence of the current rule's words."""
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
            """Mark the current rule's regex matches (or their capture groups)."""
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
        highlight_map: list[Style | None], start: int, end: int, style: Style
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
        highlight_map: list[Style | None] | None,
        indices: Sequence[int],
    ) -> Style:
        """Merge highlight styles for character indices into the base style.

        Args:
            base_style: The style to merge onto.
            highlight_map: Per-character highlight styles for the line, if any.
            indices: Character indices whose highlights apply.

        Returns:
            ``base_style`` combined with the highlight styles found.
        """
        if not highlight_map or not indices:
            return base_style
        highlight_style: Style | None = None
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
    def _initialize_color_stops(self) -> list[ColorTriplet]:
        """Initialize the active color stops based on mode and provided stops.

        If only one stop is provided, duplicate it to create a smooth segment pair.

        Returns:
            The foreground stops, or the background stops when there are none,
            with a single stop doubled. Empty if neither is set.
        """
        # Prefer foreground color stops; fall back to background stops if set
        source: list[ColorTriplet] = self.colors if self.colors else self.bg_colors
        if not source:
            return []
        return [source[0], source[0]] if len(source) == 1 else source

    def _color_at(self, pos: int, width: int, span: int) -> str:
        """Return the hex color at a given position (for tests).

        Args:
            pos: Column of the cluster.
            width: Display width of the cluster in cells.
            span: Cells the gradient covers.

        Returns:
            A ``#rrggbb`` string, or ``"#000000"`` when there are no stops.
        """
        stops = self._active_stops
        if not stops:
            return "#000000"
        frac = self._compute_fraction(pos, width, span)
        r, g, b = self._interpolate_color(frac, stops)
        return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

    def _styled(self, original: Style, color: str) -> Style:
        """Return a Style with the given color or bgcolor, preserving original (for tests).

        Args:
            original: The style to extend.
            color: The color to apply, e.g. ``"#ff0000"``.

        Returns:
            ``original`` plus ``color`` as the background when background stops
            are set, otherwise as the foreground.
        """
        return (
            original + Style(bgcolor=color)
            if self.bg_colors
            else original + Style(color=color)
        )

    def _interpolated_color(
        self, frac: float, stops: list, _count: int | None = None
    ):
        """Return the interpolated color at a fraction (for tests).

        Args:
            frac: Position along the ramp, 0-1.
            stops: Color stops to interpolate.
            _count: Ignored; kept for backward compatibility. Defaults to None.

        Returns:
            The ``(r, g, b)`` color at ``frac``.
        """
        return self._interpolate_color(frac, stops)


if __name__ == "__main__":  # pragma: no cover
    # Example Gradient Usage
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
