"""A container for style information, used by `gradient.Gradient'."""

from typing import Dict, Tuple

from rich.console import Console
from rich.style import Style, StyleType
from rich.table import Table
from rich.terminal_theme import TerminalTheme
from rich.theme import Theme

from rich_gradient.default_styles import DEFAULT_STYLES, styles_table

_ColorTuple = Tuple[int, int, int]


class GradientTheme:
    """A container for style information used by 'rich.console.Console'.
    
    Args:
        styles (Dict[str, Style], optional): A mapping of style names on to \
            styles. Defaults to None for a theme with no styles.
        inherit (bool, optional): Inherit default styles. Defaults to True.
    """

    # styles: Dict[str, Style] = {}

    def __init__(self) -> None:
        self.theme = Theme(DEFAULT_STYLES)
        self.styles = DEFAULT_STYLES

    @property
    def theme(self) -> Theme:
        return self._theme

    @theme.setter
    def theme(self, theme: Theme = Theme(DEFAULT_STYLES)) -> None:
        self._theme = theme

    @property
    def styles(self) -> Dict[str, StyleType]:
        """The styles of the the theme."""
        if self._styles is None:
            self._styles: Dict[str, StyleType] = DEFAULT_STYLES
        return self._styles

    @styles.setter
    def styles(self, styles: Dict[str, StyleType] = DEFAULT_STYLES) -> None:
        """Set the style of the theme.

        Args:
            style(Dict[str, StyleType]): The styles of the theme."""
        assert styles, "Cannot set styles to None."
        self._style: Dict[str, StyleType] = styles

    def __call__(self) -> Theme:
        return self.theme

    def __repr__(self) -> str:
        return f"GradientTheme({self.styles!r})"

    def __rich__(self) -> Table:
        return styles_table()

    def __getitem__(self, name: str) -> Style:
        return Style.parse(str(self.styles[name]))

    @classmethod
    def get_theme_table(cls) -> Table:
        """Get a table of all styles in the theme."""
        return styles_table()


GRADIENT_TERMINAL_THEME = TerminalTheme(
    background=(0, 0, 0),
    foreground=(255, 255, 255),
    normal=[
        (33, 34, 44),
        (255, 85, 85),
        (20, 200, 20),
        (241, 250, 140),
        (189, 147, 249),
        (255, 121, 198),
        (139, 233, 253),
        (248, 248, 242),
    ],
    bright=[
        (0, 0, 0),
        (255, 0, 0),
        (0, 255, 0),
        (255, 255, 0),
        (214, 172, 255),
        (255, 146, 223),
        (164, 255, 255),
        (255, 255, 255),
    ],
)

if __name__ == "__main__":  # pragma: no cover
    theme = GradientTheme()
    console = Console(theme=theme.theme)

    console.print(theme.get_theme_table(), justify="center")
