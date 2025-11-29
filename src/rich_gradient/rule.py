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

from rich_gradient.config import config
from rich_gradient.gradient import ColorType, Gradient
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

# Thickness-to-character mapping
CHARACTER_MAP = {0: "─", 1: "━", 2: "═", 3: "█"}


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
        hues: int = 17,
        thickness: int = 1,
        characters: Optional[str] = None,
        style: StyleType = "",
        end: str = "\n",
        align: AlignMethod = "center",
        console: Optional[Console] = None,
    ) -> None:
        self.title = title or ""
        self.title_style = title_style
        self.thickness = thickness
        self.characters = characters or CHARACTER_MAP.get(thickness, CHARACTER_MAP[2])

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

            # Validate provided color names against runtime config to ensure
            # clearly invalid names (e.g., 'bad') are rejected. We accept
            # hex values and rgb(...) forms, and for plain names consult the
            # runtime config color keys (case-insensitive) as accepted names.
            if colors is not None:
                known_names = {
                    k.lower() for k in dict(getattr(config, "colors", {}) or {}).keys()
                }
                for c in colors:
                    if isinstance(c, str):
                        s = c.strip()
                        if s.startswith("#") or s.lower().startswith(("rgb(", "rgba(")):
                            # hex or rgb forms are allowed; parsing will validate further
                            continue
                        # Plain name: must exist in runtime config (case-insensitive)
                        if s.lower() not in known_names:
                            raise ValueError(f"Invalid color name: {s}")

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
        except Exception as err:
            # Normalize any parsing/validation error into ValueError for the
            # public Rule API so callers receive a consistent exception type
            # for invalid color inputs.
            raise ValueError(f"Invalid color provided: {err}") from err

    @property
    def thickness(self) -> int:
        """Get the thickness of the Rule."""
        for thickness, char in CHARACTER_MAP.items():
            if char == getattr(self, "_rule_char", CHARACTER_MAP[2]):
                return thickness
        return 2  # Default

    @thickness.setter
    def thickness(self, value: int) -> None:
        """Set the thickness of the Rule.
        Args:
            value: Thickness as an integer (0-3) or the corresponding character.
        Raises:
            ValueError: If the value is not a valid thickness or character."""
        if isinstance(value, int) and 0 <= value <= 3:
            self._thickness = value
            self._characters = CHARACTER_MAP[value]
            return
        raise ValueError(
            "thickness string must be one of the following characters: "
            + ", ".join(CHARACTER_MAP.values())
        )

    @property
    def characters(self) -> str:
        """Get the character used for the rule line."""
        if self._characters:
            return self._characters

        # Validate thickness
        if not isinstance(self.thickness, int):
            raise TypeError(
                f"thickness must be an integer, recieved {type(self.thickness).__name__}"
            )
        if 0 <= self.thickness <= 3:
            raise ValueError("thickness must be an integer between 0 and 3 (inclusive)")

        return CHARACTER_MAP.get(self.thickness, CHARACTER_MAP[2])

    @characters.setter
    def characters(self, value: str) -> None:
        """Set the character used for the rule line."""
        if not isinstance(value, str) or len(value) != 1:
            raise ValueError("characters must be a single character string")
        self._characters = value

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


def example() -> None:
    """Demonstrate the gradient Rule functionality."""
    console = Console(width=80, record=True)

    comment_style = Style.parse("italic")
    console.line()
    console.print(Rule(title="Centered Rule", rainbow=True, thickness=0))
    console.print(
        RichText(
            "↑ This Rule is centered, with a thickness of 0. \
When no colors are provided, it defaults to a random gradient. ↑",
            style="italic",
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
        RichText.assemble(*[
            RichText(
                "↑ This Rule is left-aligned, with a thickness of 1. When colors \
are provided, the gradient is generated using the provided colors: ",
                style="italic",
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
            title_style="bold #9f0",
            align="right",
            thickness=2,
            colors=list(GRADIENT_COLOR_PALETTE),
        )
    )
    purple_explanation = Text.assemble(*[
        RichText(
            "↑  This Rule is right-aligned, with a thickness of 2. When colors are \
provided, the gradient is generated using the provided colors: ",
            style="italic",
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

    center_desc = RichText.from_markup(
        "↑ [i]This rule is[/i] [b]centered[/b][i], with a[/i] [b]thickness[/b] \
[i]of[/i] [b]3.[/b]\nWhen `rainbow=True`, a full-spectrum Rainbow gradient is generated. ",
        style="",
    )
    center_desc.highlight_words(
        ["centered", "thickness", "3", "rainbow"], style=Style.parse("")
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
        RichText(
            "↑ This Rule has no title, but still has a gradient rule. ↑",
            style="italic",
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
