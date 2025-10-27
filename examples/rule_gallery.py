"""Gallery of gradient rules used in the user guide."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console, Group

from rich_gradient import Rule
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "rule-gallery.svg"


def main() -> None:
    console = Console(record=True, width=88)
    console.line()
    rules = Group(
        Rule("Default gradient rule", colors=["#38bdf8", "#a855f7", "#f97316"]),
        Rule("Left aligned", align="left", colors=["#14b8a6", "#6366f1"]),
        Rule("Right aligned", align="right", colors=["#f97316", "#facc15"]),
        Rule("Thin border", thickness=0, colors=["#22d3ee", "#6366f1"]),
        Rule("Double border", thickness=1, colors=["#f472b6", "#facc15"]),
        Rule("Thick block rule", thickness=3, colors=["#ef4444", "#f97316", "#facc15"]),
    )
    console.print(rules)
    console.line()
    console.save_svg(str(OUTPUT), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME)


if __name__ == "__main__":
    main()
