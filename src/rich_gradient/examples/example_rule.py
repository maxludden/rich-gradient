from rich.console import Console
from rich.text import Text
from rich_gradient.rule import GradientRule
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

console: Console = Console(record=True, width=64)

def rule_example1(
    console: Console = console,
    path: str = "docs/img/rule_example1.svg") -> None:
    """Generate a gradient rule with default settings."""
    console.line()
    console.print(
        GradientRule(
            title="Hello, world!"
        )
    )
    console.line()
    console.save_svg(path, title="Basic GradientRule Usage", theme=GRADIENT_TERMINAL_THEME)  


def rule_example2(
    console: Console = console,
    path: str = "docs/img/rule_example2.svg") -> None:
    """Generate a gradient rule with alignment set to left."""
    console.line()
    console.print(
        GradientRule(
            title="Hello, world! on the left.",
            align="left"
        )
    )
    console.line()
    console.save_svg(
        path,
        title="Alignment",
        theme=GRADIENT_TERMINAL_THEME
    )

def rule_example3(
    console: Console = console,
    path: str = "docs/img/rule_example3.svg") -> None:
    """Generate a gradient rule with alignment set to right."""
    console.line()
    console.print(
        GradientRule(
            title="Thick GradientRule on the right.",
            align="right",
            thickness="thick"
        )
    )
    console.line()
    console.save_svg(
        path,
        title="Thick GradientRule",
        theme=GRADIENT_TERMINAL_THEME
    )   

if __name__ == '__main__':
    # rule_example1(console)
    # rule_example2()
    rule_example3()