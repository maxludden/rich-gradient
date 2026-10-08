"""Render gradients around arbitrary Rich renderables for the documentation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown

from rich_gradient.panel import Panel
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

PANEL_OUTPUT = (
    Path(__file__).resolve().parents[1] / "docs" / "img" / "gradient-panel.svg"
)


def render_panel_example() -> None:
    """Render a panel example with gradient text and background."""
    console = Console(record=True, width=80)
    markdown = Markdown(
        """
# Gradient Panels

- **Wrap any renderable**: tables, markdown, syntax.
- **Highlight** sections with *highlight_words* or regex.
- Combine with **Rich's layout** primitives.
""".strip()
    )
    gradient_panel = Panel(
            markdown,
            colors=["#38bdf8", "#a855f7", "#f97316"],
            bg_colors=['#000000'],
            justify="center",
            highlight_words={"Gradient Panels": "#ffffff"},
    )
    console.print(gradient_panel, justify="center")
    console.save_svg(
        str(PANEL_OUTPUT),
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME,
    )


def main() -> None:
    """Render gradient examples for the documentation."""
    render_panel_example()


if __name__ == "__main__":
    main()
