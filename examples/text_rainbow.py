"""Generate rainbow gradient text examples."""
from rich.console import Console

from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

def gen_text_rainbow(save: bool=True) -> None:
    """Generate rainbow gradient text examples."""
    console = Console(record=save)
    console.line()
    rainbow_text = Text(
        # "Use rainbow colors for the gradient.",
        "🌈 https://maxludden.github.io/rich-gradient",
        rainbow=True
    )
    console.print(rainbow_text)
    console.line(2)
    console.print(rainbow_text.spans)
    console.line()

    if save:
        console.save_svg(
            "docs/img/text_rainbow.svg",
            title="rich-gradient",
            theme=GRADIENT_TERMINAL_THEME,)

if __name__ == "__main__":
    gen_text_rainbow()
