from rich.console import Console
from rich_gradient.text import Text
from rich_gradient.gradient import Gradient
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

console = Console(record=True, width=64, theme=GradientTheme())

def description():
    """Description of rich-gradient."""
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

def quick_example_gradient_text():
    """Quick example gradient text result."""

    console.line()
    console.print(
        Text(
            "    Hello, [b]world[/b]!",
            colors=["#f00", "#f90", "#FF0"]
        )
    )
    console.line()
    console.save_svg(
        "docs/img/quick_example_gradient_text.svg",
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME
    )

def quick_start_rainbow_text():
    """Quick example rainbow text result."""

    console.line()
    console.print(
        Text(
            "    All the colors of the rainbow!",
            rainbow=True
        )
    )
    console.line()
    console.save_svg(
        "docs/img/quick_example_rainbow_text.svg",
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME
    )

def quick_start_gradient_panel():
    """rich-gradient panel -t 'Panel Title' "Gradient Panel content..."""

    from rich.panel import Panel

    console.line()
    console.print(
        Panel(
            "Gradient Panel content...",
            title="Panel Title"
        )
    )
    console.line()
    console.save_svg(
        "docs/img/quick_start_gradient_panel.svg",
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME
    )

if __name__=="__main__":
    # quick_example_gradient_text()
    # quick_start_rainbow_text()
    quick_start_gradient_panel()
