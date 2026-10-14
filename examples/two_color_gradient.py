"""Render the two-color gradient snippet from the README as an SVG."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from rich_gradient import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "two_color_gradient.svg"


def main() -> None:
    """Render the two-color gradient snippet from the README as an SVG."""
    console = Console(record=True, width=64)
    console.line()
    console.print(
        Text(
            "This a gradient with two colors.",
            colors=["#f00", "orange"],
        ),
        justify="center",
    )
    console.line()
    console.save_svg(str(OUTPUT), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)


if __name__ == "__main__":
    main()
