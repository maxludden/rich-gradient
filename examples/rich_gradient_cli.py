"""Generate the gradient title for the CLI help text."""

from turtle import title
from rich.console import Console
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

def generate_cli_footer() -> Text:
    """Generate the gradient footer for the CLI help text."""
    console = Console()
    title_text = Text(
        "🌈 https://maxludden.github.io/rich-gradient",
        rainbow=True
    )
    console.print(title_text)
    return title_text

def generate_cli_title(save: bool = False) -> None:
    """Generate the gradient title for the CLI help text."""
    console = Console(record=save)
    console.line()
    title_text = Text(
        "rich-gradient ",
        style="bold"
    ).rich
    title_text.append("CLI", style="bold #fff")
    console.print(title_text, justify="center")
    console.line()
    console.print(title_text.spans)

    if save:
        console.save_svg(
            "docs/img/cli_title.svg",
            title="rich-gradient",
            theme=GRADIENT_TERMINAL_THEME,
        )

if __name__ == "__main__":
    generate_cli_title(save=True)
