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

## Limitations

- Pulse mode (`pulse=True`) and indeterminate bars (`total=None`) render as Rich normally would, without a gradient.
- The half-cell character at the fill boundary keeps the track color.
- It is not yet available as a `rich.progress.Progress` column.

For the full signature see the [ProgressBar reference](progress_bar_ref.md).
