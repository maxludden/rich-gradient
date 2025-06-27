# tests/benchmark_perf.py
import pytest
from rich_gradient import Gradient
from rich.text import Text

large = "abcdefghijkl" * 10_000
txt = Text(large)
grad = Gradient(txt, ["cyan", "#99ff00"])

@pytest.mark.benchmark(group="gradient_render")
def test_benchmark_gradient(benchmark):
    benchmark(grad, txt)
