"""Benchmarks for rich-gradient rendering paths."""

from __future__ import annotations

from typing import Any

import pytest
from rich.console import Console, ConsoleRenderable
from rich.text import Text as RichText

from rich_gradient import AnimatedGradient, Gradient, Panel, Text


def _benchmark_console(width: int = 100) -> Console:
    """Create a console suitable for render-only benchmarks.

    Args:
        width: Console width in terminal cells.

    Returns:
        A Rich console configured for truecolor rendering.
    """
    return Console(width=width, force_terminal=True, color_system="truecolor")


def _render_segments(console: Console, renderable: ConsoleRenderable) -> None:
    """Fully render a Rich renderable to segments.

    Args:
        console: Console used to render the object.
        renderable: Rich-compatible renderable to benchmark.
    """
    list(console.render(renderable, console.options))


@pytest.mark.benchmark(group="gradient_static_render")
def test_benchmark_static_gradient_render(benchmark: Any) -> None:
    """Benchmark a standard Gradient render over moderate text."""
    console = _benchmark_console()
    renderable = Gradient(
        RichText("rich-gradient static render benchmark " * 20),
        colors=["cyan", "#99ff00", "magenta"],
    )

    benchmark(lambda: _render_segments(console, renderable))


@pytest.mark.benchmark(group="gradient_animated_frame_render")
def test_benchmark_animated_gradient_frame_render(benchmark: Any) -> None:
    """Benchmark one animated frame render without starting Live."""
    console = _benchmark_console()
    renderable = AnimatedGradient(
        renderables=RichText("animated gradient frame benchmark " * 20),
        colors=["#ff0000", "#00ff00", "#0000ff"],
        console=console,
        auto_refresh=False,
        animate=True,
    )

    def render_frame() -> None:
        """Advance phase and render one animated frame."""
        renderable.phase += 0.01
        _render_segments(console, renderable.get_renderable())

    benchmark(render_frame)


@pytest.mark.benchmark(group="gradient_long_text_render")
def test_benchmark_long_text_gradient_render(benchmark: Any) -> None:
    """Benchmark gradient rendering over long text content."""
    console = _benchmark_console(width=120)
    long_text = RichText("abcdefghijkl " * 5_000)
    renderable = Gradient(long_text, colors=["cyan", "#99ff00"])

    benchmark(lambda: _render_segments(console, renderable))


@pytest.mark.benchmark(group="gradient_panel_render")
def test_benchmark_panel_gradient_render(benchmark: Any) -> None:
    """Benchmark a gradient panel with title, subtitle, and highlighted text."""
    console = _benchmark_console(width=100)
    renderable = Panel(
        Text(
            "Panel benchmark body with highlighted content and multiple lines.\n" * 8,
            colors=["#ff9900", "#00ffff"],
        ),
        colors=["#ff0000", "#00ff00", "#0000ff"],
        title="Benchmark Panel",
        subtitle="rich-gradient",
        highlight_words={"benchmark": "bold white"},
    )

    benchmark(lambda: _render_segments(console, renderable))
