# ![rich-gradient](img/rich-gradient.svg)

<div class="badges">
    <a href="https://GitHub.com/maxludden/maxgradient"><img  class="badge" src="https://img.shields.io/badge/Python-3.10 | 3.11 | 3.12 -blue?logo=python" alt="PyPI - MaxGradient"></a>
    <a href="https://GitHub.com/maxludden/rich-gradient"><img  class="badge" src="https://img.shields.io/badge/PyPI-rich_gradient-blue?" alt="PyPI - rich_radient"></a>
    <a href="https://GitHub.com/maxludden/rich-gradient"><img  class="badge" src="https://img.shields.io/badge/Version-0.3.1-bbbbbb" alt="Version 0.3.1"></a>
</div>
<div id="spacer"></div>

![gradient example](img/gradient.svg)

This library is a wrapper of the great [rich](https://GitHub.com/textualize/rich) library that extends [rich.text.Text](https://github.com/Textualize/rich/blob/master/rich/text.py) to allow for the easy generation gradient text from the user inputed colors or randomly if not colors are presented.

Borrowing from [pydantic-Looextra-types](https://GitHub.com/pydantic/pydantic-extra-types)' [Color](https://github.com/pydantic/pydantic-extra-types/blob/main/pydantic_extra_types/color.py) class, rich_gradient extends the rich standard colors to include:
- 3 or 6 digit hex code (e.g. `#f00` or `#ff0000`)
- RGB color codes (e.g. `rgb(255, 0, 0)`)
- RGB tuples   (e.g. `(255, 0, 0)`)
- CSS3 Color Names (e.g. `red`)



## Installation

### Rye (Recommended)
```bash
rye add rich-gradient
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
![Hello, World!](img/hello_world.svg)

---

### Gradient with Specific Colors

If you want a bit more control of the gradient, you can specify the colors you want to use in the gradient by passing them as a list of colors to the `colors` parameter.

#### Color Formats

Color can be parsed from a variety of formats including:

![3 or 6 digit hex colors, rgb/rgba colors, and CSS3 Named Colors](img/color_formats.svg)

#### Example Code

```python
console.print(
    Gradient(
        "This a gradient with specific colors.",
        colors=["red", "#ff9900", "#ff0", "Lime"],
        justify="center"
    )
)
```

#### Specific Color Gradient Result:

![specific colors](img/specific_color_gradient.svg)

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


![Rainbow Gradient](img/example_rainbow_gradient.svg)
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

![Still Text](img/still_text.svg)

