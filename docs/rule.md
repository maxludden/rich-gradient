# Rule

`rich_gradient.Rule` subclasses `rich.rule.Rule` and applies gradient color stops (foreground and optional background) across the rule glyphs. All alignment, justify, and text options from the Rich base class are preserved.

![Rule gallery](img/rule-gallery.svg)

```python
from rich.console import Console
from rich_gradient import Rule

console = Console()
console.print(Rule("Default gradient rule", colors=["#38bdf8", "#a855f7", "#f97316"]))
console.print(Rule("Left aligned", align="left", colors=["#14b8a6", "#6366f1"]))
console.print(Rule("Right aligned", align="right", colors=["#f97316", "#facc15"]))
console.print(Rule("Thin border", thickness=0, colors=["#22d3ee", "#6366f1"]))
console.print(Rule("Double border", thickness=1, colors=["#f472b6", "#facc15"]))
console.print(Rule("Thick block rule", thickness=3, colors=["#ef4444", "#facc15"]))
```

## Thickness and alignment

- `align`: `"left"`, `"center"` (default), or `"right"`.
- `thickness`: integer 0–3 controlling the glyph (`─`, `═`, `━`, `█` respectively).
- `characters`: provide your own glyph when you need full control.

The gradient is distributed across the rendered width after padding and indentation are applied.

## Titles and colors

Rules support `title`, `title_align`, and `title_style` exactly like Rich. Styles can reference any color supported by `rich.color.Color`, including CSS names and hex codes provided by `rich-color-ext`. Pass `bg_colors` to paint the rule background.

The example script that generates the gallery is saved as `examples/rule_gallery.py`.
