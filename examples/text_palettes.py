"""Showcase different ways to configure colors for `rich_gradient.Text`."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console, Group

from rich_gradient import Text
from rich_gradient.spectrum import Spectrum
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "text-palettes.svg"


def main() -> None:
    console = Console(record=True, width=76)
    console.line()
    examples = Group(
        Text(
            "Explicit color stops",
            colors=["#0ea5e9", "#a855f7", "#f97316"],
            style="bold",
        ),
        Text(
            "Auto-generated hues (hues=6)",
            colors=None,
            hues=6,
            style="italic",
        ),
        Text(
            "Palette via Spectrum(seed=7)",
            colors=Spectrum(hues=5, seed=7).triplets,
            style="underline",
        ),
    )
    console.print(examples, justify="center")
    console.line()
    console.save_svg(str(OUTPUT), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)


if __name__ == "__main__":
    main()
