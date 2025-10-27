"""Capture the custom CLI help screen for the documentation."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console

from rich_gradient.cli import _render_main_help
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "cli-help.svg"


def main() -> None:
    console = Console(record=True, width=88)
    _render_main_help(console)
    console.save_svg(str(OUTPUT), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)


if __name__ == "__main__":
    main()
