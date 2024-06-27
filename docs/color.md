# Color

`rich-gradient`'s Color class is a subclass of `pydantic_extra_types.color.Color` that extends the rich standard colors to include:

- 3 digit hex codes (e.g. `#f00`)
- 6 digit hex codes (e.g. `#ff0000`)
- RGB color codes (e.g. `rgb(255, 0, 0)`)
- RGB tuples (e.g. `(255, 0, 0)`)
- CSS3 Color Names (e.g. `red`)

![colors](img/colors.svg)