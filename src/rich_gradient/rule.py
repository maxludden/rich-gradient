"""Gradient-enabled Rule built on Rich's Rule, powered by Gradient."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from rich.align import AlignMethod
from rich.color import ColorParseError
from rich.console import Console, ConsoleOptions, RenderResult
from rich.rule import Rule as RichRule
from rich.style import Style, StyleType
from rich.text import Text as RichText
from rich.text import TextType

from rich_gradient.gradient import ColorType, Gradient
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

# Thickness-to-character mapping
CHARACTER_MAP = {0: "─", 1: "━", 2: "═", 3: "█"}


class Rule(Gradient):
    """A Rich Rule that supports gradients via the Gradient base class.

    Args:
        title (Optional[str]): Text shown in the middle of the rule, e.g.
            ``"Section 2"``. Defaults to None.
        title_style (StyleType): Style layered over the gradient on the title. A style
            string or ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to
            ``"bold"``.
        colors (Optional[Sequence[ColorType]]): Foreground color stops. Each stop may be
            a color name (Rich/ANSI names such as ``"red"`` keep Rich's meaning; CSS
            names such as ``"tomato"`` also work), a hex string (``"#f00"``,
            ``"#ff0000"``), an ``"rgb(255, 0, 0)"`` string, an ``(r, g, b)`` tuple, or a
            ``rich.color.Color``, e.g. ``["#f00", "orange", (0, 128, 255)]``. If omitted
            and ``rainbow`` is False, ``hues`` colors are taken from the spectrum
            palette. Defaults to None.
        bg_colors (Optional[Sequence[ColorType]]): Background color stops, in the same
            formats as ``colors``, e.g. ``["#000033", "#330033"]``. If omitted, no
            background gradient is applied. Defaults to None.
        rainbow (bool): Use the full 17-color spectrum palette, ignoring ``colors`` and
            ``hues``. Defaults to False.
        hues (int): Number of colors to take from the spectrum palette when ``colors``
            is omitted (a run of consecutive hues with a random starting point). Valid
            values are 2 to 17. Defaults to 17.
        thickness (int): Line weight: ``0`` (``─``), ``1`` (``━``), ``2`` (``═``), or
            ``3`` (``█``). Ignored when ``characters`` is given. Defaults to 1.
        characters (Optional[str]): A single line character, e.g. ``"─"``, ``"━"``,
            ``"═"``, ``"█"``, or ``"*"``. ``None`` picks it from ``thickness``.
            Defaults to None.
        style (StyleType): Base style of the line, under the gradient. A style string or
            ``rich.style.Style``, e.g. ``"bold #ff8800"``. Defaults to ``""``.
        end (str): String printed after the rule. Defaults to a newline.
        align (AlignMethod): Alignment of the title within the rule: ``"left"``,
            ``"center"``, or ``"right"``. Defaults to ``"center"``.
        console (Optional[Console]): Console used for rendering and measurement.
            Defaults to ``rich.get_console()``.
        animate (bool): Mark the content as changing between renders, so highlight
            matches are recomputed every frame instead of cached. Static renderables
            never animate on their own; use the ``Animated*`` classes for live
            animation. Defaults to False.
    """

    def __init__(
        self,
        title: str | None = None,
        title_style: StyleType = "bold",
        colors: Sequence[ColorType] | None = None,
        bg_colors: Sequence[ColorType] | None = None,
        *,
        rainbow: bool = False,
        hues: int = 17,
        thickness: int = 1,
        characters: str | None = None,
        style: StyleType = "",
        end: str = "\n",
        align: AlignMethod = "center",
        console: Console | None = None,
        animate: bool = False,
    ) -> None:
        """Initialize the gradient rule; see the class docstring for arguments.

        Raises:
            ValueError: If a color is invalid, ``thickness``/``characters`` is not
                supported, or ``hues`` is out of range.
        """
        self.title = title or ""
        self.title_style = title_style
        self.thickness = thickness
        self.characters = characters or CHARACTER_MAP.get(thickness, CHARACTER_MAP[2])

        # Build the underlying Rich Rule renderable
        base_rule = RichRule(
            title=title or "",
            characters=self.characters,
            style=style,
            end=end,
            align=align,
        )

        try:
            if self.title:
                highlight_words = {title or "": title_style or "bold"}
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
                animate=animate,
            )
        except (ColorParseError, TypeError) as err:
            # Bad color inputs raise ColorParseError (unparseable strings) or
            # TypeError (unsupported types). Normalize those into ValueError so
            # Rule callers get one exception type for invalid colors. Other
            # errors, such as an invalid ``hues``, propagate unchanged.
            raise ValueError(f"Invalid color for Rule: {err}") from err

    @property
    def thickness(self) -> int:
        """The line weight, 0-3 (``─``, ``━``, ``═``, ``█``)."""
        if hasattr(self, "_thickness"):
            return self._thickness
        for thickness, char in CHARACTER_MAP.items():
            if char == getattr(self, "_characters", CHARACTER_MAP[2]):
                return thickness
        return 2  # Default

    @thickness.setter
    def thickness(self, value: int) -> None:
        """Set the thickness of the Rule.

        Args:
            value: Thickness as an integer between 0 and 3 (inclusive).

        Raises:
            ValueError: If the value is not an integer between 0 and 3.
        """
        if isinstance(value, int) and 0 <= value <= 3:
            self._thickness = value
            self._characters = CHARACTER_MAP[value]
            return
        raise ValueError(
            f"thickness must be an integer between 0 and 3 (inclusive), got {value!r}"
        )

    @property
    def characters(self) -> str:
        """The character used to draw the rule line.

        Raises:
            ValueError: If no character is set and ``thickness`` is invalid.
            TypeError: If no character is set and ``thickness`` is not an int.
        """
        if self._characters:
            return self._characters

        # Validate thickness
        if not isinstance(self.thickness, int):
            raise TypeError(
                f"thickness must be an integer, received {type(self.thickness).__name__}"
            )
        if not 0 <= self.thickness <= 3:
            raise ValueError("thickness must be an integer between 0 and 3 (inclusive)")

        return CHARACTER_MAP.get(self.thickness, CHARACTER_MAP[2])

    @characters.setter
    def characters(self, value: str) -> None:
        """Set the character used to draw the rule line.

        Args:
            value: A single character, e.g. ``"─"`` or ``"*"``.

        Raises:
            ValueError: If ``value`` is not a one-character string.
        """
        if not isinstance(value, str) or len(value) != 1:
            raise ValueError("characters must be a single character string")
        self._characters = value

    @property
    def title(self) -> TextType | None:
        """The title text of the rule, or ``None``."""
        return self._title or None

    @title.setter
    def title(self, value: TextType | None) -> None:
        """Set the title of the rule.

        Args:
            value: The new title, or ``None`` to clear it.

        Raises:
            TypeError: If ``value`` is not a ``str``, Rich ``Text``, or ``Text``.
        """
        if value is not None and not isinstance(value, (str, RichText, Text)):
            raise TypeError(
                f"title must be str, RichText, or Text, got {type(value).__name__}"
            )
        self._title = value

    @property
    def title_style(self) -> StyleType | None:
        """The style applied to the title, or ``None``."""
        return self._title_style or None

    @title_style.setter
    def title_style(self, value: StyleType | None) -> None:
        """Set the style applied to the title.

        Args:
            value: A style string such as ``"bold"``, a ``Style``, or ``None``.

        Raises:
            TypeError: If ``value`` is not a ``str`` or ``Style``.
        """
        if value is not None and not isinstance(value, (str, Style)):
            raise TypeError(
                f"title_style must be str or Style, got {type(value).__name__}"
            )
        self._title_style = Style.parse(str(value)) if value is not None else None

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        """Render the rule at full width with gradient coloring.

        This overrides the base Gradient alignment wrapper to ensure the
        RichRule expands to the console width (so the line isn't collapsed
        to a single character when aligned/padded externally).

        Args:
            console: The console being rendered to.
            options: The console options for the current render.

        Yields:
            Styled segments for the rule line.
        """
        # Render underlying content directly (no Align wrapper)
        content = self.renderables[0] if self.renderables else RichText("")

        yield from self._render_styled_lines(
            console,
            options,
            content,
            trailing_newline=self.trailing_newline,
        )


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
        RichText.assemble(
            *[
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
            ]
        ),
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
    purple_explanation = Text.assemble(
        *[
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
        ]
    )
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
