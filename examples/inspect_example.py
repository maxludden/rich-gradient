"""Render the docs screenshot for the gradient ``inspect``."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

from rich_gradient import Inspect
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "inspect.svg"


@dataclass
class Point:
    """A 2D point."""

    x: int = 1
    y: float = 2.5
    label: str = "origin"


def main() -> None:
    """Print a gradient inspection of a dataclass and save it as an SVG."""
    console = Console(record=True, width=64)
    console.print(Inspect(Point(), colors=["#38bdf8", "#a855f7", "#f97316"]))
    console.save_svg(str(OUTPUT), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)
    print(f"-> saved {OUTPUT.name}")


if __name__ == "__main__":
    main()
