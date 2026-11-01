"""Render SVG examples for gradient convenience renderables."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console, Group

from rich_gradient import JSON, Columns, Pretty, ProgressBar, Syntax, Table, Tree
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "img"


def _save(renderable: object, filename: str, width: int = 88) -> None:
    """Render a gradient object and save it as an SVG.

    Args:
        renderable: Rich-compatible object to render.
        filename: Output SVG filename under ``docs/img``.
        width: Console width in terminal cells.
    """
    console = Console(record=True, width=width)
    console.print(renderable)
    console.save_svg(
        str(OUTPUT_DIR / filename),
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME,
    )


def table_example() -> Table:
    """Build a gradient table example."""
    table = Table(
        "Service",
        "Status",
        "Latency",
        title="Gradient Table",
        colors=["#38bdf8", "#a855f7", "#f97316"],
        border_style="white",
        show_lines=True,
        highlight_words={"ok": "bold green", "degraded": "bold yellow"},
    )
    table.add_row("api", "ok", "42 ms")
    table.add_row("worker", "degraded", "180 ms")
    table.add_row("database", "ok", "19 ms")
    return table


def tree_example() -> Tree:
    """Build a gradient tree example."""
    tree = Tree(
        "rich-gradient",
        colors=["#22d3ee", "#a78bfa", "#f472b6"],
        guide_style="dim",
        highlight_words={"docs": "bold cyan", "tests": "bold magenta"},
    )
    tree.add("src").add("rich_gradient")
    tree.add("docs").add("gradient.md")
    tree.add("tests").add("test_custom_renderables.py")
    return tree


def columns_example() -> Columns:
    """Build a gradient columns example."""
    return Columns(
        ["Text", "Gradient", "Panel", "Rule", "Table", "Tree", "Syntax", "Pretty"],
        title="Gradient Columns",
        colors=["#34d399", "#60a5fa", "#f59e0b"],
        equal=True,
        columns_expand=True,
        highlight_words={"Gradient": "bold white", "Syntax": "bold cyan"},
    )


def pretty_example() -> Pretty:
    """Build a gradient pretty-printer example."""
    payload = {
        "project": "rich-gradient",
        "renderables": ["Table", "Tree", "Columns", "Pretty", "Syntax"],
        "status": {"tests": "passing", "docs": "updated"},
    }
    return Pretty(
        payload,
        colors=["#f43f5e", "#f59e0b", "#22c55e"],
        indent_guides=True,
        expand_all=True,
        highlight_words={"passing": "bold green", "updated": "bold cyan"},
    )


def syntax_example() -> Syntax:
    """Build a gradient syntax example."""
    code = """\
from rich.console import Console, Group
from rich_gradient import Syntax

console = Console()
console.print(Syntax("print('hello')", "python"))
"""
    return Syntax(
        code,
        "python",
        colors=["#38bdf8", "#a855f7", "#f97316"],
        line_numbers=True,
        dedent=True,
        padding=(1, 2),
        highlight_words={"Syntax": "bold white"},
    )


def json_example() -> JSON:
    """Build a gradient JSON example."""
    return JSON.from_data(
        {"project": "rich-gradient", "renderables": ["JSON", "ProgressBar"], "stable": True},
        colors=["#38bdf8", "#a855f7", "#f97316"],
    )


def progress_bar_example() -> Group:
    """Build a stack of gradient progress bars."""
    colors = ["#38bdf8", "#a855f7", "#f97316"]
    return Group(
        *(ProgressBar(total=100, completed=done, width=60, colors=colors) for done in (15, 50, 85, 100))
    )


def main() -> None:
    """Render all gradient convenience renderable examples."""
    _save(table_example(), "renderables-table.svg")
    _save(tree_example(), "renderables-tree.svg")
    _save(columns_example(), "renderables-columns.svg")
    _save(pretty_example(), "renderables-pretty.svg")
    _save(syntax_example(), "renderables-syntax.svg")
    _save(json_example(), "renderables-json.svg")
    _save(progress_bar_example(), "renderables-progress-bar.svg")


if __name__ == "__main__":
    main()
