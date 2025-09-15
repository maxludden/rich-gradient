"""A container for style information, used by `gradient.Gradient'."""

from typing import Dict, Tuple

from rich.console import Console
from rich.style import Style, StyleType
from rich.table import Table
from rich.terminal_theme import TerminalTheme
from rich.theme import Theme

from rich_gradient.default_styles import DEFAULT_STYLES, styles_table

_ColorTuple = Tuple[int, int, int]

__all__ = ["GRADIENT_TERMINAL_THEME", "GradientTheme"]

class GradientTheme(Theme):
    """A container for style information used by ``rich.console.Console``.

    Args:
        styles (Dict[str, StyleType], optional): Mapping of style names to
            style definitions. Defaults to ``DEFAULT_STYLES``.

    Notes:
        The theme always inherits Rich's default styles (``inherit=True``).
    """

    # styles: Dict[str, Style] = {}

    def __init__(self, styles: Dict[str, StyleType] = DEFAULT_STYLES) -> None:
        """Initialize the theme with the given styles."""
        super().__init__(styles=styles, inherit=True)
        self._theme: Theme = Theme(DEFAULT_STYLES)
        self._styles: Dict[str, StyleType] = styles

    @property
    def theme(self) -> Theme:
        return self._theme

    @theme.setter
    def theme(self, theme: Theme = Theme(DEFAULT_STYLES)) -> None:
        self._theme = theme

    def __call__(self) -> Theme:
        return self.theme

    def __repr__(self) -> str:
        return f"GradientTheme({self._styles!r})"

    def __rich__(self) -> Table:
        return styles_table()

    def __getitem__(self, name: str) -> Style:
        return Style.parse(str(self._styles[name]))

    @classmethod
    def get_theme_table(cls) -> Table:
        """Get a table of all styles in the theme."""
        return styles_table()


GRADIENT_TERMINAL_THEME = TerminalTheme(
    background=(0, 0, 0),
    foreground=(255, 255, 255),
    normal=[
        (33, 34, 44),  # rgb(35 35 35),
        (255, 85, 85),  # rgb(254 109 109),
        (20, 200, 20),  # rgb(24 195 24),
        (241, 250, 140),  # rgb(211 208 31),
        (189, 147, 249),  # rgb(122 65 202),
        (255, 121, 198),  # rgb(255 139 205),
        (139, 233, 253),  # rgb(0 115 255),
        (248, 248, 242),  # rgb(245 245 245),
    ],
    bright=[
        (0, 0, 0),  #       rgb(0, 0, 0),
        (255, 0, 0),  #     rgb(255, 0, 0),
        (0, 255, 0),  #     rgb(0, 255, 0),
        (255, 255, 0),  #   rgb(255, 255, 0),
        (214, 172, 255),  # rgb(136, 0, 255),
        (255, 146, 223),  # rgb(255, 0, 255),
        (164, 255, 255),  # rgb(0, 0, 255),
        (255, 255, 255),  # rgb(255, 255, 255),
    ],
)

if __name__ == "__main__":  # pragma: no cover
    theme = GradientTheme()
    console = Console(theme=theme.theme)

    console.print(theme.get_theme_table(), justify="center")
