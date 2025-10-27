"""Render gradients around arbitrary Rich renderables for the documentation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table

from rich_gradient import Gradient
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

PANEL_OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "gradient-panel.svg"
TABLE_OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "gradient-table.svg"


def render_panel_example() -> None:
    console = Console(record=True, width=80)
    markdown = Markdown(
        """
## Gradient panels

- Wrap any renderable: tables, markdown, syntax.
- Highlight sections with `highlight_words` or regex.
- Combine with Rich's layout primitives.
""".strip()
    )
    gradient_panel = Gradient(
        markdown,
        colors=["#38bdf8", "#a855f7", "#f97316"],
        bg_colors=["#0f172a", "#2c1067"],
        justify="center",
    )
    console.print(gradient_panel, justify="center")
    console.save_svg(
        str(PANEL_OUTPUT),
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME,
    )


def render_table_example() -> None:
    console = Console(record=True, width=88)
    table = Table(title="Renderables that work with Gradient", box=None, show_header=False)
    table.add_column("Renderable", style="bold")
    table.add_column("Supported", justify="center")
    for renderable in ("Text", "Panel", "Markdown", "Columns", "Layout", "Live updates"):
        table.add_row(renderable, "[bold green]✓[/]")
    gradient_table = Gradient(table, rainbow=True, repeat_scale=1.8, justify="center")
    console.print(gradient_table, justify="center")
    console.save_svg(
        str(TABLE_OUTPUT),
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME,
    )


def main() -> None:
    render_panel_example()
    render_table_example()


if __name__ == "__main__":
    main()
