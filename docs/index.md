# ![rich-gradient](img/rich-gradient.svg)

<div class="badges">
    <a href="https://github.com/astral-sh/uv"><img class="badge" src="https://camo.githubusercontent.com/4ab8b0cb96c66d58f1763826bbaa0002c7e4aea0c91721bdda3395b986fe30f2/68747470733a2f2f696d672e736869656c64732e696f2f656e64706f696e743f75726c3d68747470733a2f2f7261772e67697468756275736572636f6e74656e742e636f6d2f61737472616c2d73682f75762f6d61696e2f6173736574732f62616467652f76302e6a736f6e" alt=uv></a>
    <a href="https://GitHub.com/maxludden/rich-gradient"><img  class="badge" src="https://img.shields.io/badge/Python-3.10 | 3.11 | 3.12 | 3.13-blue?logo=python" alt="PyPI - rich-gradient"></a>
    <a href="https://GitHub.com/maxludden/rich-gradient"><img  class="badge" src="https://img.shields.io/badge/PyPI-rich_gradient-blue?" alt="PyPI - rich-gradient"></a>
    <a href="https://GitHub.com/maxludden/rich-gradient"><img  class="badge" src="https://img.shields.io/badge/Version-0.3.0-bbbbbb" alt="Version 0.3.0"></a>
    ![Rich Badge](https://img.shields.io/endpoint?url=https://your.domain/path/to/rich-badge.json)
</div>
<div id="spacer"></div>

![gradient example](img/gradient.svg)

This library is a wrapper of the great [rich](https://GitHub.com/textualize/rich) library that extends [rich.text.Text](https://github.com/Textualize/rich/blob/master/rich/text.py) to allow for the easy generation gradient text from either user entered colors or randomly if no colors are entered.

Borrowing from [rich-color-ext](https://github.com/maxludden/rich-color-ext) rich_gradient extends the rich standard colors to include:

- 3 or 6 digit hex code (e.g. `#f00` or `#ff0000`)
- RGB color codes (e.g. `rgb(255, 0, 0)`)
- RGB tuples   (e.g. `(255, 0, 0)`)
- CSS3 Color Names (e.g. `rebeccapurple`)

## Installation

### uv (Recommended)

```bash
uv add rich-gradient
```

### Pip

```bash
pip install rich-gradient
```

## Usage

### Basic Text Example

To print a simple gradient import the `Text` class from in the `rich_gradient` library:

![Hello, World!](img/hello_world.svg)


## Gradient

If just text is boring, `rich_gradient.gradient.Gradient` allows you to apply a gradient to any `rich.console.ConsoleRenderable`. Such as a `rich.panel.Panel` or `rich.table.Table`;
