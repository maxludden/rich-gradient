# [![rich-gradient](https://maxludden.github.io/rich-gradient/img/rich-gradient.svg)](https://maxludden.github.io/rich-gradient/)

[![Python](https://img.shields.io/badge/Python-3.10%2C%203.11%2C%203.12-blue)](https://www.python.org/)
 [![PyPI](https://img.shields.io/pypi/v/rich-gradient)](https://pypi.org/project/rich_gradient/) [![PyPI - Downloads](https://img.shields.io/pypi/dm/rich-gradient)](https://pypi.org/project/rich-gradient/) [ ![uv](https://camo.githubusercontent.com/4ab8b0cb96c66d58f1763826bbaa0002c7e4aea0c91721bdda3395b986fe30f2/68747470733a2f2f696d672e736869656c64732e696f2f656e64706f696e743f75726c3d68747470733a2f2f7261772e67697468756275736572636f6e74656e742e636f6d2f61737472616c2d73682f75762f6d61696e2f6173736574732f62616467652f76302e6a736f6e)](https://github.com/astral-sh/uv)

![gradient example](https://maxludden.github.io/rich-gradient/img/gradient.svg)

This library is a wrapper of the great [rich](https://GitHub.com/textualize/rich) library that extends [rich.text.Text](https://github.com/Textualize/rich/blob/master/rich/text.py) to allow for the easy generation gradient text from either user entered colors or randomly if no colors are entered.

<del>Borrowing from [pydantic-extra-types](https://GitHub.com/pydantic/pydantic-extra-types)' [Color](https://github.com/pydantic/pydantic-extra-types/blob/main/pydantic_extra_types/color.py) class</del>
As of v0.2.0, rich-gradient internalized the Color class from [pydantic-extra-types](https://GitHub.com/pydantic/pydantic-extra-types) and extends it. `rich_gradient.color` extends the rich standard colors to include:

- 3 or 6 digit hex code (e.g. `#f00` or `#ff0000`)
- RGB color codes (e.g. `rgb(255, 0, 0)`)
- RGB tuples   (e.g. `(255, 0, 0)`)
- CSS3 Color Names (e.g. `red`)

---

Read the docs at [rich-gradient.readthedocs.io](https://maxludden.github.io/rich-gradient/)

## Installation

### [uv](https://github.com/astral-sh/uv) (Recommended)

```bash
uv add rich-gradient
```

### Pip

```bash
pip install rich-gradient
```

## Usage

### Basic Gradient Example

To print a simple gradient just substitue the `Gradient` class for the `Text` class in the rich library.

```python
from rich.console import Console
from rich_gradient import Gradient

console = Console()
console.print(Gradient("Hello, World!")
```

![Hello, World!](https://maxludden.github.io/rich-gradient/img/hello_world.svg)

---

### Gradient with Specific Colors

If you want a bit more control of the gradient, you can specify the colors you want to use in the gradient by passing them as a list of colors to the `colors` parameter.

#### Color Formats

Color can be parsed from a variety of formats including:

![3 or 6 digit hex colors, rgb/rgba colors, and CSS3 Named Colors](https://maxludden.github.io/rich-gradient/img/color_formats.svg)

#### Example Code

#### Specific Two-Color Gradient Example

```python
console.print(
    Gradient(
        "This a gradient with two colors.",
        colors=["red", "orange"]
    ),
    justify="center"
)
```

![Two Color Gradient](crun)

---

#### Specific Four-Color Gradient Example

```python
console.print(
    Gradient(
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
    Gradient(
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
