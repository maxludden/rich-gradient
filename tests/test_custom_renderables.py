"""Tests for gradient convenience wrappers around Rich renderables."""

from __future__ import annotations

from collections.abc import Iterable

from rich.columns import Columns as RichColumns
from rich.console import Console
from rich.pretty import Pretty as RichPretty
from rich.segment import Segment
from rich.syntax import Syntax as RichSyntax
from rich.table import Table as RichTable
from rich.tree import Tree as RichTree

from rich_gradient import Columns, Pretty, Syntax, Table, Tree


def _segments(renderable: object) -> list[Segment]:
    """Render a rich object and return only output segments."""
    console = Console(width=80)
    rendered = console.render(renderable, console.options)
    return [segment for segment in rendered if isinstance(segment, Segment)]


def _has_gradient_style(renderable: object) -> bool:
    """Return whether rendered output contains a gradient-applied style."""
    return any(
        segment.text.strip()
        and segment.style is not None
        and (segment.style.color is not None or segment.style.bgcolor is not None)
        for segment in _segments(renderable)
    )


def test_table_constructs_forwards_and_renders_gradient() -> None:
    """Table should wrap RichTable and forward row/column mutation methods."""
    table = Table("Name", title="Services", colors=["#ff0000", "#0000ff"])
    table.add_column("Status", justify="center")
    table.add_row("api", "ok")

    assert isinstance(table.table, RichTable)
    assert len(table.table.columns) == 2
    assert _has_gradient_style(table)


def test_tree_constructs_forwards_and_renders_gradient() -> None:
    """Tree should wrap RichTree and forward add() for nested nodes."""
    tree = Tree("Project", colors=["#ff0000", "#0000ff"])
    child = tree.add("src")
    child.add("rich_gradient")

    assert isinstance(tree.tree, RichTree)
    assert isinstance(child, RichTree)
    assert _has_gradient_style(tree)


def test_columns_constructs_and_renders_gradient() -> None:
    """Columns should wrap RichColumns from an iterable of renderables."""
    columns = Columns(
        ["alpha", "beta", "gamma"],
        colors=["#ff0000", "#0000ff"],
        equal=True,
    )

    assert isinstance(columns.columns, RichColumns)
    assert _has_gradient_style(columns)


def test_pretty_constructs_and_renders_gradient() -> None:
    """Pretty should wrap RichPretty for Python objects."""
    pretty = Pretty({"service": "api", "ok": True}, colors=["#ff0000", "#0000ff"])

    assert isinstance(pretty.pretty, RichPretty)
    assert _has_gradient_style(pretty)


def test_syntax_constructs_and_renders_gradient() -> None:
    """Syntax should wrap RichSyntax for highlighted code."""
    syntax = Syntax(
        "print('hello')",
        "python",
        colors=["#ff0000", "#0000ff"],
        line_numbers=True,
    )

    assert isinstance(syntax.syntax, RichSyntax)
    assert _has_gradient_style(syntax)


def test_package_exports_custom_renderables() -> None:
    """Package root should export the custom renderable wrappers."""
    exported: Iterable[type[object]] = (Table, Tree, Columns, Pretty, Syntax)
    assert all(wrapper.__module__.startswith("rich_gradient.") for wrapper in exported)
