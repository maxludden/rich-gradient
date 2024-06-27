"""Rule class for rich-gradient package."""

from pathlib import Path
from typing import List, Literal, Optional, Union

from rich.align import AlignMethod
from rich.cells import cell_len, set_cell_size
from rich.console import Console, ConsoleOptions, RenderResult
from rich.jupyter import JupyterMixin
from rich.measure import Measurement
from rich.text import Text

from rich_gradient.color import Color
from rich_gradient.spectrum import Spectrum
from rich_gradient.gradient import Gradient

# # from rich-gradient.log import log
Thickness = Literal["thin", "medium", "thick"]

console = Console()


class GradientRule(JupyterMixin):
    """A console renderable to draw a horizontal rule (line).

    Args:
        title (Union[str, Text], optional): Text to render in the rule. Defaults to "".
        gradient (bool, optional): Whether to use gradient colors. Defaults to True.
        thickness (Thickness, optional): Thickness of the rule. Defaults to "medium".
        end (str, optional): Character at end of Rule. defaults to "\\\\n"
        align (str, optional): How to align the title, one of "left",
            "center", or "right". Defaults to "center".
    """

    def __init__(
        self,
        title: Union[str, Text] = "",
        *,
        gradient: bool = True,
        thickness: Thickness = "medium",
        end: str = "\n",
        align: AlignMethod = "center",
    ) -> None:
        """Initialize the GradientRule Class.
        
        Args:
            title (Union[str, Text]): Text to render in the rule. Defaults to "".
            gradient (bool, optional): Whether to use gradient colors. Defaults to True.
            thickness (Thickness, optional): Thickness of the rule. Valid thicknesses are \
thin (`─`), medium (`━`), and thick (`█`). Defaults to "medium".
            end (str, optional): Character at end of Rule. Defaults to "\\n"
            align (AlignMethod, optional): How to align the title, one of "left", "center", or "right". Defaults to "center".
        """
        self.gradient: bool = gradient
        assert thickness in ["thin", "medium", "thick"], "Invalid thickness"
        assert thickness is not None, "Invalid thickness"
        self.thickness = thickness  # type: ignore
        if self.thickness == "thin":
            self.characters = "─"
        elif self.thickness == "medium":
            self.characters = "━"
        elif self.thickness == "thick":
            self.characters = "█"

        if cell_len(self.characters) < 1:
            raise ValueError(
                "'characters' argument must have a cell width of at least 1"
            )
        assert align in ("left", "center", "right"), "Invalid align"

        if isinstance(title, str):
            self.title: Text = Text(title, style="b #ffffff")
        elif isinstance(title, Text):
            self.title = title
        self.end = end
        self.align = align

        rule_color_list: Spectrum = Spectrum(10)
        self.left_colors: List[Color] = [
            rule_color_list[0],
            rule_color_list[1],
            rule_color_list[2],
            rule_color_list[3],
            rule_color_list[4],
        ]
        self.right_colors: List[Color] = [
            rule_color_list[4],
            rule_color_list[5],
            rule_color_list[6],
            rule_color_list[7],
            rule_color_list[8],
        ]

    def __repr__(self) -> str:
        """The string representation of the GradientRule class.
        
        Returns:
            str: The string representation of the GradientRule"""
        return f"Rule<{self.title!r}, {self.characters!r}>"

    # @spy
    def __rich_console__(
        self, console: Console, options: ConsoleOptions) -> RenderResult:
        """The rich renderable method for the GradientRule class.
        
        Args:
            console (Console): The console instance.
            options (ConsoleOptions): The console options.
            
        Returns:
            RenderResult: The renderable result of the GradientRule class.
        """
        width = options.max_width

        characters = (
            "-"
            if (options.ascii_only and not self.characters.isascii())
            else self.characters
        )

        chars_len = cell_len(characters)
        if not self.title:
            color_list = Spectrum(5)
            yield Gradient(
                self._rule_line(chars_len, width),
                colors=[
                    color_list[0],
                    color_list[1],
                    color_list[2],
                    color_list[3],
                    color_list[4],
                ],
            )
            return

        if isinstance(self.title, Text):
            self.title_text: Text = self.title
        else:
            self.title_text = console.render_str(self.title, style="rule.text")

        self.title_text.plain = self.title_text.plain.replace("\n", " ")
        self.title_text.expand_tabs()

        required_space = 4 if self.align == "center" else 2
        truncate_width = max(0, width - required_space)

        # / No Title
        if not truncate_width:
            yield self._rule_line(chars_len, width)
            return

        rule_text = Text(end=self.end)
        if self.align == "center":
            rule_text = self.center_rule(rule_text, truncate_width, chars_len, width)
        elif self.align == "left":
            self.title_text.truncate(truncate_width, overflow="ellipsis")
            rule_text.append(self.title_text)
            rule_text.append(" ")
            if self.gradient:
                rule_text.append(
                    Gradient(
                        characters * (width - self.title_text.cell_len - 1),
                        colors=self.right_colors,  # type: ignore
                    )
                )
            else:
                rule_text.append(characters * (width - rule_text.cell_len))
        elif self.align == "right":
            self.title_text.truncate(truncate_width, overflow="ellipsis")
            rule_text.append(
                Gradient(
                    characters * (width - self.title_text.cell_len - 1),
                    colors=self.left_colors,  # type: ignore
                )
            )
            rule_text.append(" ")
            rule_text.append(self.title_text)

        rule_text.plain = set_cell_size(rule_text.plain, width)
        yield rule_text

    def _rule_line(self, chars_len: int, width: int) -> Text:
        """Generate a rule line.

        Args:
            chars_len (int): Width of the rule characters.
            width (int): Width of the rule.
        
        Returns:
            Text: The rule line.
        """
        rule_text = Gradient(
            self.characters * ((width // chars_len) + 1),
            colors=self.left_colors,  # type: ignore
        )
        rule_text.truncate(width)
        rule_text.plain = set_cell_size(rule_text.plain, width)
        return rule_text

    def center_rule(
        self,
        rule_text: Text,
        truncate_width: int,
        chars_len: int,
        width: int) -> Text:
        """Generate a centered rule.

        Args:
            rule_text (Text): Text of the rule.
            truncate_width (int): Width of the truncated rule.
            chars_len (int): Width of the rule characters.
            width (int): Width of the rule.

        Returns:
            Text: The centered rule
        """
        if rule_text is None:
            rule_text = Text()
        self.title_text.truncate(truncate_width, overflow="ellipsis")
        self.side_width: int = (width - cell_len(self.title_text.plain)) // 2
        if self.gradient:
            rule_text.append(
                Gradient(
                    self.characters * (self.side_width // chars_len + 1),
                    colors=self.left_colors,  # type: ignore
                    end="",
                )
            )
        else:
            rule_text.append(
                Text(self.characters * (self.side_width // chars_len + 1), end="")
            )
        rule_text.append(" ")
        rule_text.append(self.title_text)
        rule_text.append(" ")
        if self.gradient:
            rule_text.append(
                Gradient(
                    self.characters * (self.side_width // chars_len + 1),
                    colors=self.right_colors,  # type: ignore
                    end=" ",
                )
            )
        else:
            rule_text.append(
                Text(self.characters * (self.side_width // chars_len + 1), end=" ")
            )
        rule_text.truncate(width)
        return rule_text

    def __rich_measure__(
        self, console: Console, options: ConsoleOptions) -> Measurement:
        """The rich measure method for the GradientRule class.
        
        Args:
            console (Console): The console instance.
            options (ConsoleOptions): The console options.
        
        Returns:
            Measurement: The measurement of the GradientRule class."""
        return Measurement(1, 1)

    @property
    def thickness(self) -> str:
        """Thickness of the rule line.
        
        Returns:
            str: The thickness of the rule line."""
        return self._thickness

    # @spy
    @thickness.setter
    def thickness(self, thickness: Thickness) -> None:
        """Set the thickness of the rule line.

        Args:
            thickness (Thickness): The thickness of the rule line.
        
        Raises:
            AssertionError: If the thickness is not one of "thin", "medium", or "thick".
        """
        assert thickness in ("thin", "medium", "thick"), "Invalid thickness"
        self._thickness = thickness

    @property
    def characters(self) -> str:
        """Characters used to draw the rule.
        
        Returns:
            str: The characters used to draw the rule."""
        return self._characters

    @characters.setter
    def characters(self, characters: Optional[str]) -> None:
        """Set or generate the characters to draw the rule.
        
        Args:
            characters (Optional[str]): The characters to draw the rule.
        """
        # If being set by the user, use the value they provided
        if characters is not None:
            self._characters = characters
            return

        # If no characters are set, generate them based on the thickness
        else:
            if self.thickness == "thin":
                self.characters = "─"
            elif self.thickness == "medium":
                self.characters = "━"
            elif self.thickness == "thick":
                self.characters = "█"

    @classmethod
    def rule_example(cls, save: bool = False) -> None:
        """Create a console with examples of Rule.
        
        Args:
            save (bool, optional): Save the console output to an SVG file. Defaults to False."""
        import sys

        from rich_gradient.theme import GRADIENT_TERMINAL_THEME
        from rich.console import Console

        try:
            title: str = sys.argv[1]
        except IndexError:
            title = "Rule Example"

        console = Console(width=60, record=True)

        console.line(2)
        console.print("[u b #ffffff]Rule Examples[/]", justify="center")
        console.line()
        # console.print("[dim]Gradient Rule without a title ⬇︎[/]", justify="center")
        console.print(GradientRule(title=f"{title}", thickness="thin", align="left"))
        console.line()
        console.print(
            GradientRule(
                title="Thin Gradient Rule",
                gradient=True,
                thickness="thin",
                align="center",
            )
        )
        console.line()
        console.print(
            GradientRule(title="Medium Gradient Rule", gradient=True, align="right")
        )
        console.line()
        console.print(
            GradientRule(
                title="Medium Left-aligned Non-gradient Rule",
                gradient=False,
                thickness="medium",
                align="left",
            )
        )
        console.line()
        console.print(
            GradientRule(title="Medium Right-aligned Gradient Rule", align="right")
        )
        console.line()
        console.print(GradientRule("Thick Gradient Rule", thickness="thick"))
        console.line(2)
        console.save_svg(
            path="docs/img/rule_example.svg",
            title="rich-gradient",
            theme=GRADIENT_TERMINAL_THEME
        )


if __name__ == "__main__":
    GradientRule.rule_example(True)
