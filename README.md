# [![rich-gradient](https://raw.githubusercontent.com/maxludden/rich-gradient/main/docs/img/rich-gradient.svg)](https://maxludden.github.io/rich-gradient/)

<!-- markdownlint-disable MD033 -->
<!-- markdownlint-disable MD013 -->
<p align="center">
  <a href="https://www.python.org/"><img
    src="https://img.shields.io/badge/Python-3.10%2C%203.11%2C%203.12%2C%203.13-blue" alt="Python versions"></a>
  <a href="https://pypi.org/project/rich_gradient/"><img
  src="https://img.shields.io/pypi/v/rich-gradient" alt="PyPI version"></a>
  <a href="https://pypi.org/project/rich_gradient/"><img
   src="https://img.shields.io/pypi/dm/rich-gradient" alt="PyPI downloads"></a>
  <a href="https://github.com/astral-sh/uv"><img
    src="https://raw.githubusercontent.com/maxludden/rich-gradient/refs/heads/main/docs/img/uv-badge.svg" alt="uv badge"></a>
</p>

![gradient example](https://raw.githubusercontent.com/maxludden/rich-gradient/main/docs/img/getting_started.svg)

## Purpose

`rich-gradient` layers smooth foreground and background gradients on top of
[Rich](https://github.com/Textualize/rich) renderables.
It includes a drop-in `Text` subclass, wrappers for `Panel` and `Rule`,
utilities for building palettes, and
a rich-click (Click) CLI for trying gradients from the terminal.

## Highlights

- Works anywhere Rich expects a `ConsoleRenderable`,
  including panels, tables, and live updates.
- Generates color stops automatically or from CSS color names,
  hex codes, RGB tuples, or `rich.color.Color` objects.
- Supports foreground and background gradients,
  rainbow palettes, and deterministic color spectrums.
- Ships with ready-to-use renderables:
  - [`Text`](text.md)
  - [`Gradient`](gradient.md)
  - [`Panel`](panel.md)
- [`Rule`](rule.md)
- [`Spectrum`](spectrum.md)
- And their animated counterparts.
- Includes a CLI for quick experiments
  and SVG export for documentation or asset generation.
- Auto-bootstraps a configuration file (`~/.rich-gradient`) where you can toggle
  animation globally and customise the default spectrum palette.

### What's new in v0.3.9

- CLI docs now reflect the Click + rich-click commands
  (`print`, `panel`, `rule`, `markdown`) with up-to-date options and examples.
- Help text across CLI options uses the rich markup styling
  from `text_command.py` for consistency.
- Tests run without an editable install because `tests/conftest.py`
  prepends `src/` to `sys.path`.
- Docs CSS forces the page background to the theme color
  to eliminate the black/transparent flash at the top of pages.

## Installation

`rich-gradient` targets Python 3.10+.

### [uv](https://github.com/astral-sh/uv)

```shell
# Recommended: use uv
uv add rich-gradient

# or via `uv pip`
uv pip install rich-gradient
```

### [Pip](https://pip.pypa.io/en/stable/)

Or with pip:

```shell
# via pip
pip install rich-gradient
```

[📘 Read the Docs](https://maxludden.github.io/rich-gradient/)

## CLI Usage

The CLI is built with Click + rich-click. Subcommands:

- `print`: gradient text. Options: `--colors/-c`, `--bgcolors`, `--rainbow`,
  `--hues`, `--style`, `--justify`, `--overflow`, `--no-wrap`, `--end`.
- `rule`: gradient rule. Options: `--title`, `--title-style`, `--colors`,
  `--bgcolors`, `--rainbow`, `--hues`, `--thickness`, `--align`, `--end`.
- `panel`: gradient panel. Options: `--colors`, `--bgcolors`, `--rainbow`,
  `--hues`, `--title`, `--title-style`, `--title-align`, `--subtitle`,
  `--subtitle-style`, `--subtitle-align`, `--style`, `--border-style`,
  `--padding`, `--vertical-justify`, `--text-justify`, `--justify`,
  `--expand/--no-expand`, `--width`, `--height`, `--box`,
  `--end`, `--animate`, `--duration`.
- `markdown`: gradient markdown. Options: `--colors`, `--bgcolors`,
  `--rainbow`, `--hues`, `--style`, `--justify`, `--vertical-justify`,
  `--overflow`, `--no-wrap`, `--end`, `--animate`, `--duration`.

Quick examples:

- Gradient text: `rich-gradient print "Hello [b]world[/b]!" -c magenta,cyan`
- Rainbow text: `rich-gradient print "Rainbow!" --rainbow`
- Panel with title: `rich-gradient panel "Panel content"
-c red,blue --title "Gradient Panel"`
- Rule with title: `rich-gradient rule --title "Section" -c "#f00,#0ff"`
- Gradient markdown: `rich-gradient markdown
"# Title" --colors "#ff0,#0ff" --justify center`

### Contributor notes

- Tests: `pytest` works without an editable install because
  `tests/conftest.py` adds `src/` to `sys.path`. No extra
  env tweaks needed; just install deps and run `pytest`.

## Usage

### Basic Gradient Text Example

To print a simple gradient just substitute the `Gradient` class
for the `Text` class in the rich-gradient library.

```python
from rich.console import Console
from rich_gradient import Gradient

console = Console()
console.print(Gradient("Hello, World!"))
```

![Hello, World!](https://raw.githubusercontent.com/maxludden/rich-gradient/main/docs/img/hello_world.svg)

---

## Gradient Text with Specific Colors

If you want a bit more control of the gradient,
you can specify the colors you want to use in the gradient
by passing them as a list of colors to the `colors` parameter.

### Color Formats

Color can be parsed from a variety of formats including:

![3 or 6 digit hex colors, rgb/rgba colors, and CSS3 Named Colors](https://raw.githubusercontent.com/maxludden/rich-gradient/main/docs/img/v0.3.4/gradient_text_custom_colors.svg)

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

![Two Color Gradient](https://raw.githubusercontent.com/maxludden/rich-gradient/main/docs/img/v0.3.3/two_color_gradient.svg)

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

![multi-color specific colors](https://raw.githubusercontent.com/maxludden/rich-gradient/main/docs/img/v0.3.4/gradient_text_custom_colors.svg)

---

### Rainbow Gradient Example

If four colors isn't enough, you can use the 'rainbow' parameter to generate
 a rainbow gradient that spans the entire spectrum of colors randomly.

```python
console.print(
    Text(
        "This is a rainbow gradient.",
        rainbow=True,
        justify="center"
    )
)
```

![Rainbow Gradient](https://raw.githubusercontent.com/maxludden/rich-gradient/refs/heads/main/docs/img/v0.3.4/text_rainbow_gradient_with_code.svg)

_The rainbow gradient is generated randomly each time the code is run._

---

### Still inherits from `rich.text.Text`

Since `Gradient` is a subclass of `Text`, you can still use all
the same methods and properties as you would with `Text`.

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

![Still Text](https://github.com/maxludden/rich-gradient/raw/refs/heads/main/docs/img/v0.3.4/built_on_rich_text.svg)
