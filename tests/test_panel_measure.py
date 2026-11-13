"""Width measurement of expanding gradient panels inside and outside layouts."""

from rich.columns import Columns
from rich.console import Console
from rich.measure import Measurement
from rich.table import Table

from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.panel import Panel


def _console(width: int = 80) -> Console:
    """Return a non-terminal console with a fixed width for deterministic output."""
    return Console(width=width, force_terminal=True, color_system="truecolor", record=True)


def test_panel_measures_at_content_width() -> None:
    """An expanding Panel reports Rich's natural width, not the whole console."""
    console = _console()
    measurement = Measurement.get(console, console.options, Panel("hi"))
    # "hi" + 1-cell padding each side + 2 border cells
    assert measurement == Measurement(6, 6)


def test_expanding_panel_still_fills_width() -> None:
    """The border still spans the full console when rendered on its own."""
    console = _console(40)
    console.print(Panel("hi"))
    lines = console.export_text().splitlines()
    assert len(lines[0]) == 40
    assert lines[0].endswith("╮")


def test_expanding_panels_share_columns() -> None:
    """Several expanding Panels lay out side by side inside Columns."""
    console = _console(80)
    console.print(Columns([Panel("one"), Panel("two"), Panel("three")]))
    lines = console.export_text().splitlines()
    assert len(lines) == 3  # a single row of panels, not one per row
    assert lines[1].count("│") == 6


def test_expanding_panel_leaves_room_in_table() -> None:
    """A table column holding an expanding Panel does not starve its neighbour."""
    console = _console(60)
    table = Table(show_header=False)
    table.add_row(Panel("cell"), "neighbour text")
    console.print(table)
    text = console.export_text()
    assert "neighbour text" in text
    # The panel's column is sized to its content, not to the whole table.
    panel_top = next(line for line in text.splitlines() if "╭" in line)
    assert panel_top.index("╮") - panel_top.index("╭") + 1 < 20


def test_animated_panel_border_fills_width() -> None:
    """AnimatedPanel with expand=True draws its border across the full width."""
    console = _console(40)
    panel = AnimatedPanel("hi", console=console, animate=False)
    console.print(panel)
    lines = console.export_text().splitlines()
    assert len(lines[0]) == 40
    assert lines[0].endswith("╮")


def test_animated_panel_measures_at_content_width() -> None:
    """AnimatedPanel measures like a plain Rich Panel for parent layouts."""
    console = _console()
    panel = AnimatedPanel("hi", console=console, animate=False)
    assert Measurement.get(console, console.options, panel) == Measurement(6, 6)


def test_animated_panel_accepts_text_justify() -> None:
    """AnimatedPanel takes ``text_justify`` like Panel and centers string content."""
    console = _console(20)
    panel = AnimatedPanel("hi", console=console, animate=False, text_justify="center")
    console.print(panel)
    body = console.export_text().splitlines()[1]
    assert body.strip("│ ") == "hi"
    left, right = body.index("hi"), len(body) - body.index("hi") - 2
    assert abs(left - right) <= 1


def test_animated_panel_keeps_positional_console() -> None:
    """``text_justify`` is keyword-only, so ``console`` keeps its positional slot."""
    import inspect

    params = inspect.signature(AnimatedPanel.__init__).parameters
    assert params["text_justify"].kind is inspect.Parameter.KEYWORD_ONLY
    names = [n for n, p in params.items() if p.kind is p.POSITIONAL_OR_KEYWORD]
    assert names[names.index("safe_box") + 1] == "console"


def test_animated_panel_resolves_rich_cast_each_render() -> None:
    """A ``__rich__`` object is resolved per render, so animation frames update."""

    class Counter:
        def __init__(self) -> None:
            self.value = 0

        def __rich__(self) -> str:
            return f"count {self.value}"

    counter = Counter()
    console = _console(30)
    panel = AnimatedPanel(counter, console=console, animate=False)
    console.print(panel)
    counter.value = 7
    console.print(panel)
    text = console.export_text()
    assert "count 0" in text and "count 7" in text
