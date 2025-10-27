"""Example usage of rich-gradient to print "Hello World!" with a gradient."""
from rich.console import Console, Group
from rich.syntax import Syntax
from rich_gradient import Text
from rich_gradient.theme import GradientTheme, GRADIENT_TERMINAL_THEME

console = Console(record=True, width=64, theme=GradientTheme())
console.line()
CODE = '''>>> from rich.console import Console
>>> from rich_gradient import Text

>>> console = Console()
>>> console.print(Text("[i]Hello[/i] [b u]World[/b u]!"))

'''
syntax = Syntax(
    CODE,
    "python",
    background_color="#000",
)
console.print(
    Group(
        syntax,
        Text("[i]Hello[/i] [b u]World[/b u]!"),
    )
)
console.line()
console.save_svg(
    "docs/img/hello_world.svg",
    title="rich-gradient",
    theme=GRADIENT_TERMINAL_THEME
)
