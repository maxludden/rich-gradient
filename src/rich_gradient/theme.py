"""A container for style information, used by `gradient.Gradient'."""

from rich.console import Console
from rich.style import Style, StyleType
from rich.table import Table as RichTable
from rich.terminal_theme import TerminalTheme
from rich.theme import Theme

from rich_gradient.default_styles import DEFAULT_STYLES, styles_table

_ColorTuple = tuple[int, int, int]

__all__: list[str] = ["GRADIENT_TERMINAL_THEME", "GradientTheme"]


class GradientTheme(Theme):
    """A container for style information used by ``rich.console.Console``.

    Args:
        styles (Optional[dict[str, StyleType]]): Mapping of style names to styles, e.g.
            ``{"warning": "b u"}``. Defaults to None, which uses
            ``DEFAULT_STYLES``.

    Notes:
        The theme always inherits Rich's default styles (``inherit=True``).
    """

    # styles: Dict[str, Style] = {}

    def __init__(self, styles: dict[str, StyleType] | None = None) -> None:
        """Initialize the theme; see the class docstring for arguments."""
        if styles is None:
            styles = dict(DEFAULT_STYLES)
        super().__init__(styles=styles, inherit=True)
        self._theme: Theme = Theme(styles, inherit=True)
        self._styles: dict[str, StyleType] = styles

    @property
    def theme(self) -> Theme:
        """The ``rich.theme.Theme`` built from this instance's styles."""
        return self._theme

    @theme.setter
    def theme(self, theme: Theme = Theme(DEFAULT_STYLES)) -> None:
        """Replace the theme used for styling.

        Args:
            theme: The new Rich theme. Defaults to a theme of ``DEFAULT_STYLES``.
        """
        self._theme = theme

    def __call__(self) -> Theme:
        """Return the theme, so the instance can be used as a theme factory.

        Returns:
            The ``rich.theme.Theme`` for this instance.
        """
        return self.theme

    def __repr__(self) -> str:
        """Return a developer-friendly representation.

        Returns:
            ``GradientTheme({...styles...})``.
        """
        return f"GradientTheme({self._styles!r})"

    def __rich__(self) -> RichTable:
        """Render the theme as a table of its styles.

        Returns:
            The styles table from ``default_styles.styles_table()``.
        """
        return styles_table()

    def __getitem__(self, name: str) -> Style:
        """Look up a style by name, e.g. ``theme["warning"]``.

        Args:
            name: The style name.

        Returns:
            The parsed ``Style``.

        Raises:
            KeyError: If no style has that name.
        """
        return Style.parse(str(self._styles[name]))

    @classmethod
    def get_theme_table(cls) -> RichTable:
        """Get a table of all default styles.

        Returns:
            The styles table from ``default_styles.styles_table()``.
        """
        return styles_table()


GRADIENT_TERMINAL_THEME = TerminalTheme(
    background=(0, 0, 0),
    foreground=(255, 255, 255),
    normal=[
        (33, 34, 44),  # rgb(20 20 20),
        (255, 85, 85),  # rgb(254 109 109),
        (20, 200, 20),  # rgb(0 160 0),
        (241, 250, 140),  # rgb(177 174 0),
        (189, 147, 249),  # rgb(83 0 198),
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
    themes = GradientTheme()
    console = Console(theme=themes.theme)

    console.print(themes.get_theme_table(), justify="center")
