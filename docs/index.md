# rich-gradient



`rich-gradient` layers smooth foreground and background gradients on top of [Rich](https://github.com/Textualize/rich) renderables. It includes a drop-in `Text` subclass, wrappers for `Panel` and `Rule`, utilities for building palettes, and a Typer-powered CLI for trying gradients from the terminal.

## Highlights

- Works anywhere Rich expects a `ConsoleRenderable`, including panels, tables, and live updates.
- Generates color stops automatically or from CSS color names, hex codes, RGB tuples, or `rich.color.Color` objects.
- Supports foreground and background gradients, rainbow palettes, and deterministic color spectrums.
- Ships with ready-to-use renderables (`Gradient`, `Panel`, `Rule`, `Spectrum`) plus animated variants.
- Includes a CLI for quick experiments and SVG export for documentation or asset generation.

## Installation

`rich-gradient` targets Python 3.10+.

```bash
# Recommended: use uv
uv add rich-gradient

# Or with pip
pip install rich-gradient
```

## Quick start

```python
from rich.console import Console
from rich_gradient import Text

console = Console()
console.print(
    Text(
        "Rich gradients with almost no setup.",
        colors=["#38bdf8", "#a855f7", "#f97316"],
        style="bold",
        justify="center",
    )
)
```

The example above is bundled in `examples/text_quickstart.py` and renders:

<a href="#" class="copy-install" data-copy="uv add rich-gradient" title="Click to copy: <code>uv add rich-gradient</code>" aria-label="Copy install command">
    <img src="img/text-quickstart.svg" alt="Text quickstart">

</a>

## Explore the user guide

- [Text](text.md) – gradient-aware drop-in replacement for `rich.text.Text`.
- [Gradient](gradient.md) – wrap any renderable with foreground/background gradients.
- [Panel](panel.md) – gradient panels with highlighted titles and subtitles.
- [Rule](rule.md) – gradient horizontal rules with adjustable thickness.
- [Spectrum](spectrum.md) – generate and preview deterministic palettes.
- [CLI](cli.md) – scriptable demos and helpers built with Typer.
- [Animation](animation.md) – create animated gradients with `Live`.

Prefer API-level details? See the [reference section](animated_gradient_ref.md) generated with `mkdocstrings`.
