# [![rich-gradient](https://raw.githubusercontent.com/maxludden/rich-gradient/main/docs/img/rich-gradient.svg)](https://maxludden.github.io/rich-gradient/)

<!-- markdownlint-disable MD033 MD013 -->
<p align="center">
  <a href="https://www.python.org/"><img
    src="https://img.shields.io/badge/Python-3.11%2C%203.12%2C%203.13%2C%203.14-blue" alt="Python versions"></a>
  <a href="https://pypi.org/project/rich_gradient/"><img
  src="https://img.shields.io/pypi/v/rich-gradient" alt="PyPI version"></a>
  <a href="https://pepy.tech/project/rich-gradient"><img
   src="https://img.shields.io/pepy/dt/rich-gradient" alt="PyPI downloads"></a>
  <a href="https://github.com/astral-sh/uv"><img
    src="https://raw.githubusercontent.com/maxludden/rich-gradient/refs/heads/main/docs/img/uv-badge.svg" alt="uv badge"></a>
</p>

![gradient example](https://raw.githubusercontent.com/maxludden/rich-gradient/main/docs/img/getting_started.svg)

## Purpose

`rich-gradient` layers smooth foreground and background gradients on top of
[Rich](https://github.com/Textualize/rich) renderables.
It includes a drop-in `Text` subclass, wrappers for `Panel` and `Rule`,
gradient-aware Markdown, convenience wrappers for common Rich renderables,
animated variants, and utilities for building palettes.

## Highlights

- Works anywhere Rich expects a `ConsoleRenderable`,
  including panels, tables, and live updates.
- Generates color stops automatically or from CSS color names,
  hex codes, RGB tuples, or `rich.color.Color` objects.
- Supports foreground and background gradients,
  rainbow palettes, and seedable color spectrums.
- Ships with ready-to-use renderables:
  - [`Text`](docs/text.md)
  - [`Gradient`](docs/gradient.md)
  - [`Panel`](docs/panel.md)
  - [`Rule`](docs/rule.md)
  - [`Spectrum`](docs/spectrum.md)
  - [`Markdown`](docs/gradient.md)
  - [`Table`, `Tree`, `Columns`, `Pretty`, and `Syntax`](docs/renderables.md)
  - Animated variants for `Gradient`, `Markdown`, `Panel`, `Rule`, and `Text`.
- `AnimatedText`, `AnimatedGradient`, `AnimatedPanel`, `AnimatedRule`, and
  `AnimatedMarkdown` for live gradient updates.
- Loads optional JSON configuration from `~/.rich-gradient/config.json`, where
  you can toggle animation globally and customize the default spectrum palette.
  Invalid settings are ignored with a logged warning rather than raising.
- Optional Rich traceback formatting via `rich_gradient.install_tracebacks()`.

### What's new in v0.4.0

- **Breaking** — importing `rich_gradient` no longer installs Rich's pretty
  traceback handler (it previously replaced `sys.excepthook` as an import side
  effect). Programs run identically; only uncaught-exception formatting is
  affected. To keep Rich tracebacks, call `rich_gradient.install_tracebacks()`
  once at startup, or set `RICH_GRADIENT_TRACEBACKS=1` for the old automatic
  behavior with no code changes.
- **Changed** — color strings are parsed with Rich's own parser first, falling
  back to `rich-color-ext` (CSS names and 3-digit hex). Names Rich defines keep
  Rich's meaning, so `"red"` is ANSI red (`#800000`); use `"#ff0000"` for pure
  red. Requires `rich-color-ext>=3.0.0`.
- **Changed** — `hues` has a minimum of 2 everywhere and raises `ValueError`
  below that (`Gradient` used to clamp silently).
- **Changed** — configuration loading is stricter and quieter: invalid values
  are ignored with a warning, `RICH_GRADIENT_ANIMATE` also accepts
  `0`/`false`/`no`/`off`, and the default `hotpink` palette entry is now `pink`.
- **Changed** — the docs moved from MkDocs to [Zensical](https://zensical.org)
  (`zensical.toml`), and CI now tests Python 3.11–3.14 and builds the docs.
- **Fixed** gradients now reach their first and last colors: `repeat_scale`
  defaults to `None` and is derived from the color stops (previously `Markdown`
  stopped at the second color and two-color gradients stopped halfway). Pass an
  explicit `repeat_scale` to keep the old spread.
- **Fixed** `Gradient` accepts a tuple or generator of renderables, as
  documented, and `Gradient("")` prints a blank line like `console.print("")`.
- **Fixed** `Rule` only reports "Invalid color for Rule" for real color errors;
  other errors (such as a bad `hues`) keep their own message.
- **Fixed** `Panel` crashing when `style` was passed as a `rich.style.Style`
  instance instead of a string.
- **Fixed** `Rule()` can now be constructed without a title, matching
  `AnimatedRule` and Rich's own `Rule`.
- **Fixed** `AnimatedRule` now uses its faster phase speed when animation is
  enabled via the global config, not only when `animate=True` is passed.
- **Removed** the unused `requests` runtime dependency for lighter installs.

See the [CHANGELOG](docs/CHANGELOG.md) for more details.

## Installation

`rich-gradient` requires Python 3.11 or newer.

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

### Contributor notes

Use [uv](https://github.com/astral-sh/uv) for everything:

- Install: `uv sync`
- Tests: `uv run pytest` works without an editable install because
  `tests/conftest.py` adds `src/` to `sys.path`.
- Type check: `uv run mypy`
- Docs: `uv run zensical serve` to preview and `uv run zensical build --clean`
  to build (the docs use [Zensical](https://zensical.org); there is no
  `mkdocs.yml`).

CI runs the tests on Python 3.11, 3.12, 3.13, and 3.14 and builds the docs, so
run `uv run pytest` and `uv run zensical build --clean` before committing.

## Usage

### Basic Gradient Text Example

Use `Text` when you want a drop-in `rich.text.Text` replacement with gradient
spans applied to the text itself.

```python
from rich.console import Console
from rich_gradient import Text

console = Console()
console.print(Text("[i]Hello[/i] [b u] World![/b u]"))
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

Colors are parsed with Rich's own parser first, falling back to
[`rich-color-ext`](https://github.com/maxludden/rich-color-ext) for CSS names
and 3-digit hex. Names Rich defines keep Rich's meaning, so `"red"` is ANSI red
(`#800000`) while `"#ff0000"` is pure red; CSS-only names like `"tomato"` work as
expected.

### Example Code

#### Specific Two-Color Gradient Example

```python
console.print(
    Text(
        "This a gradient with two colors.",
        colors=["#f00", "orange"],
    ),
    justify="center"
)
```

![Two Color Gradient](https://raw.githubusercontent.com/maxludden/rich-gradient/main/docs/img/two_color_gradient.svg)

---

#### Specific Four-Color Gradient Example

```python
console.print(
    Text(
        "This a gradient uses four specific colors.",
        colors=["#f00", "#ff9900", "#ff0", "Lime"],
        justify="center",
    ),
)
```

#### Specific Color Gradient Result

![multi-color specific colors](https://raw.githubusercontent.com/maxludden/rich-gradient/main/docs/img/v0.3.4/gradient_text_custom_colors.svg)

---

### Rainbow Gradient Example

If four colors aren't enough, you can use the 'rainbow' parameter to generate
a rainbow gradient that spans the full spectrum palette.

```python
console.print(
    Text(
        "This is a rainbow gradient.",
        rainbow=True,
        justify="center",
    ),
)
```

![Rainbow Gradient](https://raw.githubusercontent.com/maxludden/rich-gradient/refs/heads/main/docs/img/v0.3.4/text_rainbow_gradient_with_code.svg)

Use `Spectrum(hues=..., seed=...)` when you need reproducible color stops.

---

### Still inherits from `rich.text.Text`

Since `Text` is a subclass of `rich.text.Text`, you can still use all
the same methods and properties as you would with `Text`.

```python
console.print(
    Text(
        "This is an underlined rainbow gradient.",
        rainbow=True,
        style="underline",
    ),
    justify="center"
)
console.line()
console.print(
    Text(
        "This is a bold italic gradient.",
        style="bold italic",
    ),
    justify="center"
)
console.line()
```

![Still Text](https://github.com/maxludden/rich-gradient/raw/refs/heads/main/docs/img/v0.3.4/built_on_rich_text.svg)

## Wrap Any Rich Renderable

Use `Gradient` when you want to paint across an existing Rich renderable, such
as Markdown, a table, a layout, or a standard Rich panel.

```python
from rich.console import Console
from rich.markdown import Markdown
from rich_gradient import Gradient

console = Console()
console.print(
    Gradient(
        Markdown("## Renderables\n\n- Text\n- Panels\n- Markdown"),
        colors=["#38bdf8", "#a855f7", "#f97316"],
        bg_colors=["#0f172a", "#1f2937"],
        justify="center",
    )
)
```

Pass a list, tuple, or generator to wrap several renderables at once. See
[`examples/renderables_that_work.py`](examples/renderables_that_work.py) for a
script that renders every renderable and reports which ones work:

<p align="center">
  <img src="docs/img/renderables-that-work.svg" alt="Renderables that work" width="240">
</p>

## Background Gradients

Pass `bg_colors` to `Text`, `Gradient`, `Panel`, `Rule`, or `Markdown` to apply
background color stops. A single background color is treated as a solid fill;
multiple stops interpolate across the rendered output.

```python
from rich_gradient import Text

Text(
    "Foreground and background gradient",
    colors=["#f8fafc", "#a7f3d0"],
    bg_colors=["#0f172a", "#1e293b"],
)
```

## Markdown

Use `Markdown` for a Rich Markdown renderable with the same gradient controls
as `Gradient`.

```python
from rich.console import Console
from rich_gradient import Markdown

console = Console()
console.print(
    Markdown(
        "# Gradient Markdown\n\nSupports **Rich Markdown** content.",
        colors=["cyan", "magenta", "gold1"],
    )
)
```


## CLI

This package no longer ships a command-line interface. Install
[`rich-gradient-cli`](https://github.com/maxludden/rich-gradient-cli) for
terminal commands that build on the renderables provided here.

<div align="center">
  <a href="https://github.com/maxludden/maxludden" style="text-decoration:none; color:inherit;">
      <p>Designed by Max Ludden</p>
  </a>
  <br />
  <a href="https://github.com/maxludden/maxludden" style="text-decoration:none; color:inherit;">
    <img
      src="docs/img/maxlogo.svg"
      alt="Max Ludden's Logo"
      width="20%"
    />
  </a>
</div>
