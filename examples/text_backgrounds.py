"""Demonstrate foreground and background gradients with `rich_gradient.Text`."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console, Group

from rich_gradient import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "text-backgrounds.svg"


def main() -> None:
    """Demonstrate foreground and background gradients with `rich_gradient.Text`."""
    console = Console(record=True, width=76)
    console.line()
    examples = Group(
        Text(
            "Matching foreground/background stops",
            colors=["#2563eb", "#ec4899"],
            bg_colors=["#0f172a", "#1f2937"],
            style="bold",
        ),
        Text(
            "Foreground rainbow with solid background",
            rainbow=True,
            bg_colors=["#111827"],
            style="bold italic",
        ),
        Text(
            "Background-only gradient",
            colors=["#f1f5f9"],
            bg_colors=["#22d3ee", "#a855f7", "#f97316"],
            style="bold black",
        ),
    )
    console.print(examples, justify="center")
    console.line()
    console.save_svg(str(OUTPUT), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)


if __name__ == "__main__":
    main()
