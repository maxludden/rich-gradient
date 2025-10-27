"""Quickstart example that prints gradient text and saves an SVG for the docs."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console, Group
from rich.panel import Panel

from rich_gradient import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "text-quickstart.svg"


def main() -> None:
    console = Console(record=True, width=72)
    console.line()
    message = Text(
        "Rich gradients with almost no setup.",
        colors=["#38bdf8", "#a855f7", "#f97316"],
        style="bold",
        justify="center",
    )
    console.print(
        Group(
            Panel(
                Text("uv add rich-gradient", style="bold green"),
                title=Text("Install", colors=["#22d3ee", "#a855f7"], style="bold"),
                padding=(1, 2),
                width=44,
            ),
            message,
        ),
        justify="center",
    )
    console.line()
    console.save_svg(str(OUTPUT), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)


if __name__ == "__main__":
    main()
