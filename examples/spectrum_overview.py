"""Render the Spectrum table for documentation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from rich_gradient.spectrum import Spectrum
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "spectrum.svg"


def main() -> None:
    console = Console(record=True, width=88)
    console.print(Spectrum(hues=8, seed=42), justify="center")
    console.save_svg(str(OUTPUT), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)


if __name__ == "__main__":
    main()
