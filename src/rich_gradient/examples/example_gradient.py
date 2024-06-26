from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from rich_gradient import Gradient
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

console = Console(width=64, record=True)


def gradient_example():
    console = Console(width=64, record=True)
    gradient = Gradient(
        "`rich_gradient` is a library built on top of the great `rich` library \
    that automates the printing of gradients in the terminal.",
        colors=["#5f00ff", "#aF00ff", "#ff00FF"],
        justify="center",
    )
    gradient.highlight_regex(r"`(\w+)`", style="bold #ffffff")
    console.print(Panel(gradient), justify="center")

    console.save_svg(
        "docs/img/gradient.svg", title="Rich Gradient", theme=GRADIENT_TERMINAL_THEME
    )


def hello_world(console: Console = console, file: str = "docs/img/hello_world.svg"):
    console.line()
    console.print(Gradient("Hello, World!"), justify="center")
    console.line()
    console.save_svg(file, title="Basic Gradient Result", theme=GRADIENT_TERMINAL_THEME)


def color_examples(
    console: Console = console, file: str = "docs/img/color_formats.svg"
):
    console.line()
    console.print(
        Panel(
            Text.assemble(
                *[
                    Text("Three or six digit hex colors:\n"),
                    Text("#0f0", style="#00ff00", end=""),
                    Text(" or "),
                    Text("#00ff00", style="#00ff00"),
                ],
                justify="center",
            ),
            expand=True,
            title="[b #99ff00]Hex Colors[/]",
            border_style="b #006600",
            width=64,
            padding=(1, 4),
        )
    )
    console.line()
    console.print(
        Panel(
            Text.assemble(
                *[
                    Text("rgb(", style="b #ffffff", end=""),
                    Text("0", style="#ff0000", end=""),
                    Text(", ", style="b #ffffff", end=""),
                    Text("255", style="b #00ff00", end=""),
                    Text(", ", style="b #ffffff", end=""),
                    Text("0", style="b #0099ff", end=""),
                    Text(") or rgba(", style="b #ffffff", end=""),
                    Text("0", style="#ff0000", end=""),
                    Text(", ", style="b #ffffff", end=""),
                    Text("255", style="b #00ff00", end=""),
                    Text(", ", style="b #ffffff", end=""),
                    Text("0", style="b #0099ff", end=""),
                    Text(",", style="b #ffffff", end=""),
                    Text(" 0.5", style="b dim", end=""),
                    Text(")", style="b #ffffff"),
                ],
                justify="center",
            ),
            expand=True,
            title="[b #99ff00]RGBA Colors[/]",
            border_style="b #006600",
            width=64,
            padding=(1, 4),
        )
    )
    console.line()
    console.print(
        Panel(
            Text.assemble(
                *[
                    Text("Lime", style="b #00ff00", end=""),
                    Text(" or ", style="b #ffffff", end=""),
                    Text("lime", style="b #00ff00"),
                ],
                justify="center",
            ),
            expand=True,
            title="[b #99ff00]CSS3 Named Colors[/]",
            border_style="b #006600",
            width=64,
            padding=(1, 4),
        ),
    )
    console.line()
    console.print(
        "[b #ffffff]You can also use any of the rich standard \
colors, or Color object from pydantic_extra_types or rich.color.Color.",
        justify="center",
    )
    console.line()
    console.save_svg(file, title="Color Formats", theme=GRADIENT_TERMINAL_THEME)


def specific_color_gradient_example(
    console: Console = console, file: str = "docs/img/specific_color_gradient.svg"
) -> None:
    console.line()
    console.print(
        Gradient(
            "This gradient uses specific colors.",
            colors=["red", "#ff9900", "#ff0", "Lime"],
            justify="center",
        ),
        justify="center",
    )
    console.line()
    console.print(
        "[i dim]*This gradient's colors: [dim red]red[/dim red], [dim #ff9900]#99ff00[/dim #ff9900], [dim yellow]#ff0[/dim yellow], [dim green]Lime[/dim green][/]",
        justify="center",
    )
    console.line(2)
    console.save_svg(
        file, title="Specific Color Gradient", theme=GRADIENT_TERMINAL_THEME
    )


def rainbow_gradient_example(
    console: Console = console, file: str = "docs/img/example_rainbow_gradient.svg"
) -> None:
    """Prints a rainbow gradient."""
    console.line()
    console.print(
        Gradient("This is a rainbow gradient.", rainbow=True), justify="center"
    )
    console.line()
    console.save_svg(file, title="Rainbow Gradient", theme=GRADIENT_TERMINAL_THEME)

def still_text(
        console:Console=console,
        file:str="docs/img/still_text.svg") -> None:
    console.line()
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
    console.save_svg(
        file, 
        title="Still Text", 
        theme=GRADIENT_TERMINAL_THEME
    )

if __name__ == "__main__":
    # hello_world()
    # color_examples()
    # specific_color_gradient_example()
    # rainbow_gradient_example()
    still_text()
