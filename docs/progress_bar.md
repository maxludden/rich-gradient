# ProgressBar

`rich_gradient.ProgressBar` is a drop-in for [`rich.progress_bar.ProgressBar`](https://rich.readthedocs.io/en/stable/progress.html) that paints only the **filled** portion of the bar with a gradient. The unfilled track keeps its normal style.

![Gradient progress bars](img/renderables-progress-bar.svg)

## Basic usage

```python
from rich.console import Console
from rich_gradient import ProgressBar

console = Console()
console.print(ProgressBar(total=100, completed=60, width=40, colors=["#38bdf8", "#a855f7", "#f97316"]))
```

The gradient spans the whole bar width, so each position keeps its color and new colors are revealed as the bar fills. Call `update(completed, total=None)` to change progress.

## In progress, complete, and pulsing

The bar is painted with a gradient in all three states, and each state can have its own colors:

| State | When | Colors |
|---|---|---|
| In progress | `completed < total` | `colors` |
| Complete | `completed >= total` | `finished_colors`, or `colors` |
| Pulsing | `pulse=True` or `total=None` | `pulse_colors`, or `colors` |

```python
from rich_gradient import ProgressBar

ProgressBar(total=100, completed=100, finished_colors=["#22c55e", "#a3e635"])
ProgressBar(total=None, pulse_colors=["#f43f5e", "#f59e0b"])
```

A pulsing bar keeps Rich's sliding wave, but the bright part of the wave takes its color from the gradient, so it changes color as it moves and fades into the track's color (`style`). Pass `animation_time` to freeze or drive the wave yourself; by default it follows the clock.

When no colors are given, a palette is picked once (from the spectrum, or the full rainbow with `rainbow=True`) and reused for every render, so a live display doesn't flicker.

## In a `rich.progress.Progress` display

Use `GradientBarColumn` in place of Rich's `BarColumn`. Running tasks show the in-progress gradient, finished tasks the finished gradient, and tasks that haven't started (or have no total) the gradient pulse:

```python
import time

from rich.progress import Progress, TextColumn
from rich_gradient import GradientBarColumn

with Progress(
    TextColumn("{task.description}"),
    GradientBarColumn(
        colors=["#38bdf8", "#a855f7", "#f97316"],
        finished_colors=["#22c55e", "#a3e635"],
    ),
) as progress:
    task = progress.add_task("Downloading", total=100)
    while not progress.finished:
        progress.update(task, advance=5)
        time.sleep(0.05)
```

## Limitations

- The half-cell character at the fill boundary keeps the track color.
- On terminals without color blending (no color, or a 16-color legacy console), the pulse is Rich's plain two-tone pulse.

For the full signature see the [ProgressBar reference](progress_bar_ref.md).
