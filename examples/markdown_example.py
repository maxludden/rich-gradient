from pathlib import Path

from rich.console import Console
from rich_gradient import Markdown
from rich.panel import Panel
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT_PATH: Path = Path(__file__).parents[1] / "docs" / "img" / "gradient_markdown.svg"


def main(output_path: Path = OUTPUT_PATH):
    console = Console(record=True, width=88)
    console.print(
        Panel(
            Markdown(
                markdown="""# Gradient Markdown

Supports markdown just as rich does. However like other rich-gradient renderables, \
it allows for gradient coloring of text.

## Colors:
- #0ff
- #f0f
- #ff0
""",
                colors=["#0ff", "#f0f", "#ff0"],
            ),
            padding=(1, 2),
        )
    )

    console.save_svg(OUTPUT_PATH, theme=GRADIENT_TERMINAL_THEME, title="rich-gradient")


if __name__ == "__main__":
    main()
