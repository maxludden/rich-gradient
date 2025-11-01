<a href="https://maxludden.github.io/rich-gradient/" alt="rich-gradient">
  <h1>
    <img src="docs/img/rich-gradient.svg" alt="rich-gradient" class="banner"/>
  </h1>
</a>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2C%203.11%2C%203.12%2C%203.13-blue" alt="Python versions"></a>
  <a href="https://pypi.org/project/rich_gradient/"><img src="https://img.shields.io/pypi/v/rich-gradient" alt="PyPI version"></a>
  <a href="https://github.com/astral-sh/uv"><img src="docs/img/uv-badge.svg" alt="uv badge"></a>
</p>

![gradient example](docs/img/getting_started.svg)

## Purpose

`rich-gradient` layers smooth foreground and background gradients on top of [Rich](https://github.com/Textualize/rich) renderables.
It includes a drop-in `Text` subclass, wrappers for `Panel` and `Rule`, utilities for building palettes, and
a Typer-powered CLI for trying gradients from the terminal.

## Highlights

- Works anywhere Rich expects a `ConsoleRenderable`, including panels, tables, and live updates.
- Generates color stops automatically or from CSS color names, hex codes, RGB tuples, or `rich.color.Color` objects.
- Supports foreground and background gradients, rainbow palettes, and deterministic color spectrums.
- Ships with ready-to-use renderables:
  - [`Text`](text.md)
  - [`Gradient`](gradient.md)
  - [`Panel`](panel.md)
  - [`Rule`](rule.md)
  - [`Spectrum`](spectrum.md)
  - And their animated counterparts.
- Includes a CLI for quick experiments and SVG export for documentation or asset generation.

## Installation

`rich-gradient` targets Python 3.10+.

### [uv](https://github.com/astral-sh/uv

```shell
# Recommended: use uv
uv add rich-gradient

# or via `uv pip`
uv pip install rich-gradient
```

### [Pip](https://pip.pypa.io/en/stable/

Or with pip:

```shell
# via pip
pip install rich-gradient
```

<a href="https://maxludden.github.io/rich-gradient/" alt="Read the Docs" class="btn">
  <span>📘 Read the Docs</span>
</a>

## CLI Usage

The package ships with a Typer-based CLI. The first command is `text`, which prints gradient-styled text. More commands may be added over time.

### Quick examples

- Print gradient text with two color stops:

  `rich-gradient text "Hello [b]world[/b]!" -c magenta -c cyan`

- Rainbow gradient (auto-generated colors):

  `rich-gradient text "Rainbow!" --rainbow`

- Read from stdin:

  `echo "From stdin" | rich-gradient text`

- Wrap in a panel with a title:

  `rich-gradient text "Panel content" --panel --title "Gradient Panel"`

- Save to SVG (uses the project terminal theme):

  `rich-gradient text "Save me" --save-svg out/example.svg`

### Common options

- `-c/--color`: Repeat to add multiple foreground color stops.
- `-b/--bgcolor`: Repeat for background color stops.
- `--rainbow`, `--hues`: Auto-generate a palette if colors aren’t provided.
- `--style`, `--justify`, `--overflow`, `--no-wrap/--wrap`, `--end`, `--tab-size`, `--markup/--no-markup`.
- `--panel`, `--title`: Wrap output in a panel with optional title.
- `--width`: Console width. `--record`: enable recording.
- `--save-svg PATH`: Save the current render as SVG.

## Usage

### Basic Gradient Text Example

To print a simple gradient just substitute the `Gradient` class for the `Text` class in the rich-gradient library.

```python
from rich.console import Console
from rich_gradient import Gradient

console = Console()
console.print(Gradient("Hello, World!"))
```

![Hello, World!](https://maxludden.github.io/rich-gradient/img/hello_world.svg)

---

## Gradient Text with Specific Colors

If you want a bit more control of the gradient, you can specify the colors you want to use in the gradient by passing them as a list of colors to the `colors` parameter.

### Color Formats

Color can be parsed from a variety of formats including:

![3 or 6 digit hex colors, rgb/rgba colors, and CSS3 Named Colors](/docs/img/v0.3.4/gradient_text_custom_colors.svg)

### Example Code

#### Specific Two-Color Gradient Example

```python
console.print(
    Text(
        "This a gradient with two colors.",
        colors=["red", "orange"]
    ),
    justify="center"
)
```

![Two Color Gradient](docs/img/v0.3.3/two_color_gradient.svg)

---

#### Specific Four-Color Gradient Example

```python
console.print(
    Text(
        "This a gradient uses four specific colors.",
        colors=["red", "#ff9900", "#ff0", "Lime"],
        justify="center"
    )
)
```

#### Specific Color Gradient Result

![multi-color specific colors](https://raw.githubusercontent.com/maxludden/rich-gradient/2a42b1b61ef1bb163f3b6e37412e669bffd6504b/docs/img/specific_multi_color_gradient.svg)

---

### Rainbow Gradient Example

If four colors isn't enough, you can use the 'rainbow' parameter to generate a rainbow gradient that spans the entire spectrum of colors randomly.

```python
console.print(
    Text(
        "This is a rainbow gradient.",
        rainbow=True,
        justify="center"
    )
)
```

![Rainbow Gradient](https://maxludden.github.io/rich-gradient/img/example_rainbow_gradient.svg)
<p style="text-align:right;">*The rainbow gradient is generated randomly each time the code is run.</p>

---

### Still inherits from `rich.text.Text`

Since `Gradient` is a subclass of `Text`, you can still use all the same methods and properties as you would with `Text`.

```python
console.print(
    Gradient(
        "This is an underlined rainbow gradient.",
        rainbow=True,
        style="underline"
    ),
    justify="center"
)
console.line()
console.print(
    Gradient(
        "This is a bold italic gradient.",
        style="bold italic"
    ),
    justify="center"
)
console.line()
```

![Still Text](https://maxludden.github.io/rich-gradient/img/still_text.svg)
