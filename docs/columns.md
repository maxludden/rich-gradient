# Columns

`rich_gradient.Columns` wraps [`rich.columns.Columns`](https://rich.readthedocs.io/en/stable/columns.html) to lay a list of renderables out in neat columns, with a gradient across the result.

![Gradient columns](img/renderables-columns.svg)

## Basic usage

```python
from rich.console import Console
from rich_gradient import Columns

console = Console()
columns = Columns(
    ["Text", "Gradient", "Panel", "Rule", "Table", "Tree", "Syntax", "Pretty"],
    title="Gradient Columns",
    colors=["#34d399", "#60a5fa", "#f59e0b"],
    equal=True,
)
console.print(columns)
```

## Layout options

- `equal`: make every column the same width.
- `columns_expand`: let the columns expand to the full width.
- `column_first`: fill top-to-bottom before moving across.
- `right_to_left`: start from the right.
- `width`: a fixed column width.
- `padding`: padding around each cell.
- `align`: `"left"`, `"center"`, or `"right"` alignment of the cell contents.
- `title`: an optional title above the columns.

The items can be strings or any renderable, including other rich-gradient renderables. The underlying Rich columns are available as `columns.columns`.

## Highlighting items

```python
from rich_gradient import Columns

columns = Columns(
    ["Text", "Gradient", "Panel", "Rule"],
    colors=["#34d399", "#60a5fa", "#f59e0b"],
    columns_expand=True,
    highlight_words={"Gradient": "bold white"},
)
```

## Shared gradient options

Like every `Gradient`-based wrapper, `Columns` accepts:

- `colors` / `bg_colors`: foreground and background color stops (CSS names, hex, RGB tuples, or `rich.color.Color`).
- `rainbow` and `hues`: generate a palette automatically (`hues` is at least 2).
- `repeat_scale`: leave it unset and one pass across the output runs from the first color to the last. See [`Gradient`](gradient.md).
- `justify` / `vertical_justify` / `expand`: position the columns inside the gradient frame.
- `highlight_words` / `highlight_regex`: extra styles applied after the gradient pass.
- `console`: a specific Rich `Console` to render with.

For the full signature see the [Columns reference](columns_ref.md).
