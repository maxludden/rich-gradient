"""Tests for the Gradient ``trailing_newline`` flag."""

from __future__ import annotations

from rich.console import Console

from rich_gradient import Gradient, Pretty

COLORS = ["red", "blue"]


def _printed(renderable: object) -> str:
    console = Console(width=12)
    with console.capture() as cap:
        console.print(renderable)
    return cap.get()


def test_trailing_newline_default() -> None:
    assert _printed(Gradient("hi", colors=COLORS)).endswith("\n")


def test_trailing_newline_disabled() -> None:
    assert not _printed(Gradient("hi", colors=COLORS, trailing_newline=False)).endswith("\n")


def test_wrapper_attribute_disables_newline() -> None:
    pretty = Pretty({"a": 1}, colors=COLORS)
    pretty.trailing_newline = False
    assert not _printed(pretty).endswith("\n")


def test_print_adds_exactly_one_newline() -> None:
    """Console.print adds no extra newline for a renderable, so no blank line."""
    out = _printed(Gradient("hi", colors=COLORS))
    assert out.count("\n") == 1
    assert _printed(Pretty({"a": 1}, colors=COLORS)).count("\n") == 1


def test_newline_terminated_content_gets_no_extra_blank_line() -> None:
    """Wrapped Panels and Rules already end in a newline; they must not gain a second."""
    from rich.panel import Panel as RichPanel

    from rich_gradient import Rule

    assert _printed(Gradient(RichPanel("hi", width=6), colors=COLORS)).count("\n") == 3
    assert _printed(Rule()).count("\n") == 1
