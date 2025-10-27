from rich.console import Console
from rich_gradient.text import Text
from rich_gradient.gradient import Gradient
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

console = Console(record=True, width=64, theme=GradientTheme())
console.line()
console.print(
    Gradient(
        Text(
            "rich-gradient is a package that extends the great rich library with \
gradient text, panels, rules, and spectrum utilities.",
            justify="center"
        ),
        highlight_words={
            "rich-gradient": "bold #ddd",
            "rich": "bold #ddd"
        }
    ),
    justify='center'
)
console.line()
console.save_svg(
    "docs/img/getting_started.svg",
    title="rich-gradient",
    theme=GRADIENT_TERMINAL_THEME,
)
