"""Gradient-enabled Rule built on Rich's Rule, powered by Gradient."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from rich.align import AlignMethod
from rich.cells import get_character_cell_size
from rich.color import ColorParseError
from rich.console import Console, ConsoleOptions, RenderResult
from rich.rule import Rule as RichRule
from rich.segment import Segment
from rich.style import Style, StyleType
from rich.text import Text as RichText
from rich.text import TextType

from rich_gradient.gradient import ColorType, Gradient
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

# Thickness-to-character mapping
CHARACTER_MAP = {0: "─", 1: "═", 2: "━", 3: "█"}


class Rule(Gradient):
    """A Rich Rule that supports gradients via the Gradient base class.

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
    """

    def __init__(
        self,
        title: Optional[str],
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
        console: Optional[Console] = None,
    ) -> None:
        self.title = title or ""
        self.title_style = title_style
        self.characters = CHARACTER_MAP.get(thickness, "━")

        # Build the underlying Rich Rule renderable
        base_rule = RichRule(
            title=self.title,
            characters=self.characters,
            style=style,
            end=end,
            align=align,
        )

        try:
            if self.title:
                highlight_words = {self.title: self.title_style}
            else:
                highlight_words = None

            super().__init__(
                base_rule,
                colors=list(colors) if colors is not None else None,
                bg_colors=list(bg_colors) if bg_colors is not None else None,
                console=console,
                hues=hues,
                rainbow=rainbow,
                vertical_justify="middle",
                highlight_words=highlight_words,
            )
        except ColorParseError as err:
            raise ValueError(f"Invalid color provided: {err}") from err

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Render the rule using the underlying RichRule at full width and
        apply gradient coloring using Gradient utilities.

        This overrides the base Gradient alignment wrapper to ensure the
        RichRule expands to the console width (so the line isn't collapsed
        to a single character when aligned/padded externally).
        """
        # Render underlying content directly (no Align wrapper)
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

    @property
    def title(self) -> Optional[TextType]:
        """Get the title of the Rule."""
        return self._title or None

    @title.setter
    def title(self, value: Optional[TextType]) -> None:
        """Set the title of the Rule."""
        if value is not None and not isinstance(value, (str, RichText, Text)):
            raise TypeError(
                f"title must be str, RichText, or Text, got {type(value).__name__}"
            )
        self._title = value

    @property
    def title_style(self) -> Optional[StyleType]:
        """Get the title style of the Rule's title."""
        return self._title_style or None

    @title_style.setter
    def title_style(self, value: Optional[StyleType]) -> None:
        """Set the title style of the Rule's title."""
        if value is not None and not isinstance(value, (str, Style)):
            raise TypeError(
                f"title_style must be str or Style, got {type(value).__name__}"
            )
        self._title_style = Style.parse(str(value)) if value is not None else None

    @property
    def characters(self) -> str:
        """Get the character used for the rule line."""
        return getattr(self, "_rule_char", CHARACTER_MAP[2])

    @characters.setter
    def characters(self, value: str | int) -> None:
        """Set the character used for the rule line."""
        # Allow specifying by thickness int or by the actual character.
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


def example() -> None:
    """Demonstrate the gradient Rule functionality."""
    console = Console(width=80, record=True)

    comment_style = Style.parse("dim italic")
    console.line()
    console.print(Rule(title="Centered Rule", rainbow=True, thickness=0))
    console.print(
        Text(
            "↑ This Rule is centered, with a thickness of 0. \
When no colors are provided, it defaults to a random gradient. ↑",
            style="dim italic",
        ),
        justify="center",
    )
    console.line()

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
                "↑ This Rule is left-aligned, with a thickness of 1. When colors \
are provided, the gradient is generated using the provided colors: ",
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
    console.line()

    GRADIENT_COLOR_PALETTE = [  # pylint: disable=C0103
        "deeppink",
        "purple",
        "violet",
        "blue",
        "dodgerblue",
    ]

    console.print(
        Rule(
            title="Right-aligned Rule",
            align="right",
            thickness=2,
            colors=list(GRADIENT_COLOR_PALETTE),
        )
    )
    purple_explanation = Text.assemble(*[
        Text(
            "↑  This Rule is right-aligned, with a thickness of 2. When colors are \
provided, the gradient is generated using the provided colors: ",
            colors=list(GRADIENT_COLOR_PALETTE),
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

    console.line()
    console.print(
        Rule(
            title="Centered Rule",
            rainbow=True,
            thickness=3,
            title_style="b u white",
        )
    )

    center_desc = Text(
        "↑ [i]This rule is[/i] [b]centered[/b][i], with a[/i] [b]thickness[/b] \
[i]of[/i] [b]3.[/b]\nWhen `rainbow=True`, a full-spectrum Rainbow gradient is generated. ",
        style="dim",
    )
    center_desc.highlight_words(
        ["centered", "thickness", "3", "rainbow"], style=Style.parse("not dim")
    )
    center_desc.highlight_words(["=", "`"], style=Style.parse("bold not dim orange"))
    center_desc.highlight_words(["True"], style=Style.parse("bold not dim white"))
    console.print(center_desc, justify="center")
    console.line()

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
        justify="left",
    )
    console.line()

    console.save_svg(
        "docs/img/rule.svg",
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME,
    )


if __name__ == "__main__":
    example()
