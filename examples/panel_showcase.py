"""Show how `rich_gradient.Panel` enhances Rich panels with gradient styling."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel as RichPanel

from rich_gradient import Panel, Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "panel-overview.svg"


def main() -> None:
    console = Console(record=True, width=88)
    inner = RichPanel.fit(
        Text(
            "Gradient titles, custom borders, and highlighted keywords.",
            style="bold",
        ),
        title="[b]Features[/b]",
        border_style="white",
        padding=(1, 2),
    )

    gradient_panel = Panel(
        inner,
        colors=["#38bdf8", "#a855f7", "#f97316"],
        bg_colors=["#0f172a", "#2c1067"],
        title="rich_gradient.Panel",
        subtitle="powered by Rich",
        border_style="bold #22d3ee",
        highlight_words=[(["Gradient", "title"], "bold white on black", False)],
    )
    console.print(gradient_panel, justify="center")
    console.save_svg(str(OUTPUT), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)


if __name__ == "__main__":
    main()
