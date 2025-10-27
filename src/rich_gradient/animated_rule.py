"""Animated gradient Rule rendered with Rich Live.

This module provides an AnimatedRule class that mirrors the behavior of
``rich_gradient.rule.Rule`` but animates the gradient over time using the
same Live/animation machinery as ``AnimatedGradient`` and ``AnimatedPanel``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional
from time import sleep

from rich.align import AlignMethod
from rich.cells import get_character_cell_size
from rich.color import ColorParseError
from rich.console import Console, ConsoleOptions, RenderResult
from rich.rule import Rule as RichRule
from rich.segment import Segment
from rich.style import Style, StyleType
from rich.text import Text as RichText
from rich.text import TextType

from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.gradient import ColorType
from rich_gradient.text import Text

__all__ = ["AnimatedRule"]


# Thickness-to-character mapping (kept in sync with rule.Rule)
CHARACTER_MAP = {0: "─", 1: "━", 2: "═", 3: "█"}


class AnimatedRule(AnimatedGradient):
    """A Rich Rule that animates a gradient across the line.

    Args:
            title: Optional title text placed within the rule.
            title_style: Style applied to the title text after gradients.
            colors: Foreground gradient color stops.
            bg_colors: Background gradient color stops.
            rainbow: If True, generate a rainbow regardless of colors.
            hues: Number of hues when generating default spectrum.
            thickness: 0..3 selects line character style.
            style: Base style for the rule line (merged with gradients).
            end: Trailing characters after the rule (default newline).
            align: Alignment for the rule within the available width.

            auto_refresh: Whether the Live context refreshes on its own.
            refresh_per_second: Target frames per second.
            console: Console to render to.
            transient: Keep Live transient (don’t clear on stop).
            redirect_stdout: Redirect stdout to Live.
            redirect_stderr: Redirect stderr to Live.
            disable: Disable rendering (useful for tests).
            phase_per_second: Phase advance per second (cycles per second).
            speed: Deprecated per-frame ms step; mapped to ``phase_per_second``.
            repeat_scale: Stretch factor for gradient color stops.
    """

    def __init__(
        self,
        title: Optional[str] = None,
        title_style: StyleType = "bold",
        colors: Optional[Sequence[ColorType]] = None,
        bg_colors: Optional[Sequence[ColorType]] = None,
        *,
        rainbow: bool = False,
        hues: int = 10,
        thickness: int = 2,
        style: StyleType = "",
        end: str = "\n",
        align: AlignMethod = "center",
        # Live / animation parameters (mirroring AnimatedGradient)
        auto_refresh: bool = True,
        refresh_per_second: float = 30.0,
        console: Optional[Console] = None,
        transient: bool = False,
        redirect_stdout: bool = False,
        redirect_stderr: bool = False,
        disable: bool = False,
        phase_per_second: Optional[float] = None,
        speed: Optional[int] = None,
        repeat_scale: float = 2.0,
    ) -> None:
        self.title = title or ""
        self.title_style = title_style
        self.characters = CHARACTER_MAP.get(thickness, "━")

        base_rule = RichRule(
            title=self.title,
            characters=self.characters,
            style=style,
            end=end,
            align=align,
        )

        try:
            highlight_words = {self.title: self.title_style} if self.title else None

            # Make animation more visible for rules by default: if caller didn't
            # specify a speed or explicit phase, bump the phase a bit.
            effective_phase = (
                phase_per_second
                if (phase_per_second is not None or speed is not None)
                else 0.25
            )

            super().__init__(
                renderables=base_rule,
                colors=list(colors) if colors is not None else None,  # type: ignore[arg-type]
                bg_colors=list(
                    bg_colors
                ) if bg_colors is not None else None,  # type: ignore[arg-type]
                auto_refresh=auto_refresh,
                refresh_per_second=refresh_per_second,
                console=console,
                transient=transient,
                redirect_stdout=redirect_stdout,
                redirect_stderr=redirect_stderr,
                disable=disable,
                expand=True,
                justify=align,
                vertical_justify="middle",
                hues=hues,
                rainbow=rainbow,
                phase_per_second=effective_phase,
                speed=speed,
                repeat_scale=repeat_scale,
                highlight_words=highlight_words,
            )
        except ColorParseError as err:
            raise ValueError(f"Invalid color provided: {err}") from err

    # underlying RichRule expands correctly across the console width,
    # while still applying animated gradient styles per character.
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        content = self.renderables[0] if self.renderables else ""
        width = options.max_width

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
        # Ensure a trailing newline after the rule so following content appears below
        yield Segment.line()

    # For Rules, let the underlying RichRule handle width/align. Avoid the
    # outer Align wrapper from AnimatedGradient to prevent the line from
    # collapsing under nested alignment contexts.
    def get_renderable(self):  # type: ignore[override]
        return self

    # -----------------
    # Properties (parity with Rule)
    # -----------------
    @property
    def title(self) -> Optional[TextType]:
        """The title text of the Rule."""
        return self._title or None

    @title.setter
    def title(self, value: Optional[TextType]) -> None:
        """Set the title text of the Rule."""
        if value is not None and not isinstance(value, (str, RichText, Text)):
            raise TypeError(
                f"title must be str, RichText, or Text, got {type(value).__name__}"
            )
        self._title = value

    @property
    def title_style(self) -> Optional[StyleType]:
        """The style applied to the title text of the Rule."""
        return self._title_style or None

    @title_style.setter
    def title_style(self, value: Optional[StyleType]) -> None:
        """Set the style applied to the title text of the Rule."""
        if value is not None and not isinstance(value, (str, Style)):
            raise TypeError(
                f"title_style must be str or Style, got {type(value).__name__}"
            )
        self._title_style = Style.parse(str(value)) if value is not None else None

    @property
    def characters(self) -> str:
        """The character used to draw the Rule line."""
        return getattr(self, "_rule_char", CHARACTER_MAP[2])

    @characters.setter
    def characters(self, value: str | int) -> None:
        """Set the character used to draw the Rule line."""
        if isinstance(value, int):
            if value not in CHARACTER_MAP:
                raise ValueError(
                    f"thickness must be between 0 and 3 (inclusive), got {value}"
                )
            self._rule_char = CHARACTER_MAP[value]
            return
        if not isinstance(value, str) or len(value) != 1:
            raise ValueError("rule_char must be a single character string")
        allowed = set(CHARACTER_MAP.values())
        if value not in allowed:
            raise ValueError(
                "The rule_char must be one of the following characters: "
                + ", ".join(CHARACTER_MAP.values())
            )
        self._rule_char = value


if __name__ == "__main__":  # pragma: no cover
    _console = Console(width=64)
    _console.line(2)
    animated_rule = AnimatedRule(
        title="Animated Gradient Rule",
        rainbow=True,
        title_style="bold white",
        refresh_per_second=20
    )
    animated_rule.start()
    sleep(5)
    animated_rule.stop()
