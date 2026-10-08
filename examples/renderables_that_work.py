"""Render every rich-gradient renderable and report which ones work.

Each renderable is built and printed inside a guard, so one failure does not
stop the rest. A summary table at the end shows the status of every renderable.
A compact SVG of the summary table is saved to ``docs/img``; the console is
sized to the table so the image has no wasted horizontal space.
"""

from __future__ import annotations

import io
from collections.abc import Callable
from pathlib import Path

from rich import box
from rich.console import Console, RenderableType

from rich_gradient import (
    Columns,
    Gradient,
    Markdown,
    Panel,
    Pretty,
    Rule,
    Syntax,
    Table,
    Text,
    Tree,
)
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

COLORS = ["#38bdf8", "#a855f7", "#f97316"]
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "docs" / "img" / "renderables-that-work.svg"

CODE = '''\
from rich_gradient import Text

print(Text("Hello, gradient!", colors=["#38bdf8", "#f97316"]))
'''


def text_example() -> RenderableType:
    """Build a gradient ``Text``."""
    return Text("Gradient text with zero fuss.", colors=COLORS, style="bold")


def gradient_example() -> RenderableType:
    """Build a ``Gradient`` wrapping plain text."""
    return Gradient("Any Rich renderable can be wrapped.", colors=COLORS)


def panel_example() -> RenderableType:
    """Build a gradient ``Panel``."""
    return Panel("Gradient borders and content.", colors=COLORS, title="Panel")


def rule_example() -> RenderableType:
    """Build a gradient ``Rule``."""
    return Rule("Rule", colors=COLORS)


def markdown_example() -> RenderableType:
    """Build a gradient ``Markdown``."""
    return Markdown("# Markdown\n\n- gradient\n- renderables", colors=COLORS)


def table_example() -> RenderableType:
    """Build a gradient ``Table``."""
    table = Table("Service", "Status", title="Table", colors=COLORS, show_lines=True)
    table.add_row("api", "ok")
    table.add_row("worker", "degraded")
    return table


def tree_example() -> RenderableType:
    """Build a gradient ``Tree``."""
    tree = Tree("rich-gradient", colors=COLORS)
    tree.add("src").add("rich_gradient")
    tree.add("docs").add("gradient.md")
    return tree


def columns_example() -> RenderableType:
    """Build a gradient ``Columns``."""
    return Columns(
        ["Text", "Gradient", "Panel", "Rule", "Table", "Tree"],
        colors=COLORS,
        equal=True,
    )


def pretty_example() -> RenderableType:
    """Build a gradient ``Pretty``."""
    return Pretty({"project": "rich-gradient", "tests": "passing"}, colors=COLORS)


def syntax_example() -> RenderableType:
    """Build a gradient ``Syntax``."""
    return Syntax(CODE, "python", colors=COLORS, line_numbers=True)


EXAMPLES: dict[str, Callable[[], RenderableType]] = {
    "Text": text_example,
    "Gradient": gradient_example,
    "Panel": panel_example,
    "Rule": rule_example,
    "Markdown": markdown_example,
    "Table": table_example,
    "Tree": tree_example,
    "Columns": columns_example,
    "Pretty": pretty_example,
    "Syntax": syntax_example,
}


def save_svg(table: Table) -> None:
    """Save ``table`` as an SVG whose width matches the table.

    Args:
        table: The summary table to render.
    """
    width = Console().measure(table).maximum
    svg_console = Console(record=True, width=width, file=io.StringIO())
    svg_console.print(table)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    svg_console.save_svg(
        str(OUTPUT_PATH), title="rich-gradient", theme=GRADIENT_TERMINAL_THEME
    )


def main() -> int:
    """Render each renderable, print a summary, and return the failure count."""
    console = Console()
    results: dict[str, str | None] = {}

    for name, build in EXAMPLES.items():
        console.print(Rule(name, colors=COLORS))
        try:
            console.print(build())
            results[name] = None
        except Exception as exc:  # noqa: BLE001 - report every failure
            results[name] = f"{type(exc).__name__}: {exc}"
            console.print(f"[bold red]failed:[/] {results[name]}")

    summary = Table(
        "Renderable",
        "Works",
        title="Renderables that work",
        rainbow=True,
        box=box.ROUNDED,
        padding=(0, 2),
    )
    for name, error in results.items():
        summary.add_row(name, "✓" if error is None else "✗")
    console.print(summary)
    save_svg(summary)

    return sum(error is not None for error in results.values())


if __name__ == "__main__":
    raise SystemExit(main())
