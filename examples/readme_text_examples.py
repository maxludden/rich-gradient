"""Render the README's four-color, rainbow, and "still Text" snippets as SVGs.

Each image shows exactly what the matching README code block prints, so the
README screenshots stay in step with the code beside them.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from rich.console import Console

from rich_gradient import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

IMG_DIR = Path(__file__).resolve().parents[1] / "docs" / "img"


def _save(name: str, draw: Callable[[Console], None]) -> None:
    """Record ``draw`` on a 64-column console and save it as ``docs/img/<name>``."""
    console = Console(record=True, width=64)
    console.line()
    draw(console)
    console.line()
    console.save_svg(
        str(IMG_DIR / name), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME
    )


def four_colors(console: Console) -> None:
    """README: "Specific Four-Color Gradient Example"."""
    console.print(
        Text(
            "This a gradient uses four specific colors.",
            colors=["#f00", "#ff9900", "#ff0", "Lime"],
            justify="center",
        ),
    )


def rainbow(console: Console) -> None:
    """README: "Rainbow Gradient Example"."""
    console.print(
        Text(
            "This is a rainbow gradient.",
            rainbow=True,
            justify="center",
        ),
    )


def still_rich_text(console: Console) -> None:
    """README: "Still inherits from rich.text.Text"."""
    console.print(
        Text(
            "This is an underlined rainbow gradient.",
            rainbow=True,
            style="underline",
        ),
        justify="center",
    )
    console.line()
    console.print(
        Text(
            "This is a bold italic gradient.",
            style="bold italic",
        ),
        justify="center",
    )


def main() -> None:
    """Write every README text snippet image."""
    _save("text-four-colors.svg", four_colors)
    _save("text-rainbow.svg", rainbow)
    _save("text-still-rich-text.svg", still_rich_text)


if __name__ == "__main__":
    main()
