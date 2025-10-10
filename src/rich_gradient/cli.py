"""
CLI for rich-gradient using Typer.

Provides a `text` command to print gradient-styled text.
"""

from __future__ import annotations

import sys
from io import StringIO
from pathlib import Path
from time import sleep
from typing import List, Optional, Union

import typer
from rich.align import Align
from rich.color import ColorParseError
from rich.console import Console, ConsoleRenderable, RichCast
from rich import box
from rich.live import Live
from rich.markdown import Markdown
from rich.markup import render as render_markup
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Prompt
from rich.rule import Rule as RichRule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text as RichText

from rich_gradient import Gradient, Rule as GradientRule, Text, __version__
from rich_gradient.theme import GRADIENT_TERMINAL_THEME


def parse_renderable(value: Union[str, RichCast, ConsoleRenderable]) -> ConsoleRenderable:
    """Cast any str, RichCast, or ConsoleRenderable into a valid console renderable.
    
    This function normalizes various input types into a ConsoleRenderable that can
    be displayed by Rich's Console.
    
    Args:
        value: The input to parse. Can be:
            - str: Converted to RichText with markup parsing enabled
            - RichCast: An object with a __rich__() method that returns a renderable
            - ConsoleRenderable: Already a valid renderable, returned as-is
    
    Returns:
        ConsoleRenderable: A valid renderable object for Rich's Console
        
    Raises:
        TypeError: If the value is not one of the accepted types
    
    Examples:
        >>> parse_renderable("Hello, [bold]World[/bold]!")
        Text('Hello, World!')
        
        >>> from rich.panel import Panel
        >>> parse_renderable(Panel("Content"))
        Panel(...)
        
        >>> class CustomRenderable:
        ...     def __rich__(self):
        ...         return Text("Custom")
        >>> parse_renderable(CustomRenderable())
        Text('Custom')
    """
    # If it's a string, convert to RichText with markup parsing
    if isinstance(value, str):
        return RichText.from_markup(value)
    
    # If it's a RichCast (has __rich__ method), call it to get the renderable
    if hasattr(value, "__rich__"):
        result = value.__rich__()
        # Recursively parse the result in case __rich__ returns a string or another RichCast
        if isinstance(result, str):
            return RichText.from_markup(result)
        return result
    
    # If it's already a ConsoleRenderable, return it as-is
    # This includes Text, Panel, Table, etc.
    return value


DEMO_COLORS: list[str] = ["#38bdf8", "#a855f7", "#f97316", "#fb7185"]


app = typer.Typer(
    help="rich-gradient CLI",
    no_args_is_help=True,
    context_settings={"help_option_names": []},
)


def _demo_text(message: str, *, style: str = "", end: str = "\n") -> Text:
    """Return gradient text using the shared demo color palette."""

    return Text(message, colors=DEMO_COLORS, style=style, end=end)


def parse_renderable(value: Union[str, RichCast, ConsoleRenderable]) -> ConsoleRenderable:
    """Cast a str, RichCast, or ConsoleRenderable into a valid ConsoleRenderable.
    
    Args:
        value: A string, RichCast object, or ConsoleRenderable to convert.
        
    Returns:
        ConsoleRenderable: A valid console renderable object.
        
    Raises:
        TypeError: If the value cannot be converted to a ConsoleRenderable.
    """
    # If it's already a ConsoleRenderable, return it as-is
    if isinstance(value, ConsoleRenderable):
        return value
    
    # If it's a string, convert to RichText with markup support
    if isinstance(value, str):
        return RichText.from_markup(value)
    
    # If it's a RichCast, call __rich__() to get the renderable
    if hasattr(value, "__rich__"):
        result = value.__rich__()
        # The result might be another RichCast, str, or ConsoleRenderable
        # Recursively parse it to ensure we get a ConsoleRenderable
        if isinstance(result, (str, ConsoleRenderable)) or hasattr(result, "__rich__"):
            return parse_renderable(result)
        else:
            raise TypeError(
                f"RichCast.__rich__() returned {type(result).__name__}, "
                "expected str, RichCast, or ConsoleRenderable"
            )
    
    # If none of the above, raise an error
    raise TypeError(
        f"Cannot parse {type(value).__name__} to ConsoleRenderable. "
        "Expected str, RichCast, or ConsoleRenderable."
    )


def _build_header() -> Text:
    """Return a gradient styled header for the CLI help screen."""

    return Text(
        text="Rich Gradient CLI",
        colors=["#38bdf8", "#a855f7", "#f97316", "#fb7185"],
        style="bold",
        justify="center",
    )


def _render_main_help(console: Console) -> None:
    """Render a custom help screen that mirrors the Rich CLI aesthetic."""

    console.print(Align.center(_build_header()))
    console.print(Align.center(RichText.from_markup(f"[dim]Version {__version__}[/dim]")))
    console.print()
    console.print(RichRule(style="#a855f7"))
    console.print(RichText.from_markup("[bold]Usage[/bold]"))
    console.print("  rich-gradient [OPTIONS] COMMAND [ARGS]...")
    console.print()

    options_table = Table.grid(padding=(0, 2))
    options_table.add_column(justify="right", style="cyan", no_wrap=True)
    options_table.add_column(style="magenta", no_wrap=True)
    options_table.add_column(style="white")
    options_table.add_row("--version", "-v", "Print version and exit.")
    options_table.add_row(
        "--install-completion",
        "",
        "Install completion for the current shell.",
    )
    options_table.add_row(
        "--show-completion",
        "",
        "Show completion for the current shell, to copy or customize the installation.",
    )
    options_table.add_row("--help", "-h", "Show this message and exit.")
    console.print(
        Panel.fit(
            options_table,
            title="Options",
            border_style="#38bdf8",
            box=box.SQUARE,
        )
    )
    console.print()

    commands_table = Table.grid(padding=(0, 2))
    commands_table.add_column(justify="right", style="cyan", no_wrap=True)
    commands_table.add_column(style="white")
    commands_table.add_row("text", "Print gradient-styled text to the console.")
    commands_table.add_row("gradient", "Display gradient banners using the Gradient renderable.")
    commands_table.add_row("rule", "Render a gradient-enhanced horizontal rule.")
    commands_table.add_row("panel", "Show a panel that wraps gradient text.")
    commands_table.add_row("table", "Render a table with gradient content.")
    commands_table.add_row("progress", "Run a short progress demonstration with gradients.")
    commands_table.add_row("syntax", "Highlight source code within a gradient frame.")
    commands_table.add_row("markdown", "Render Markdown content with gradient framing.")
    commands_table.add_row("markup", "Demonstrate Rich markup parsed into gradient text.")
    commands_table.add_row("box", "Preview a selection of Rich box styles in gradients.")
    commands_table.add_row("prompts", "Simulate prompts styled with gradient text.")
    commands_table.add_row("live", "Stream live updates with gradient styling.")
    console.print(
        Panel.fit(
            commands_table,
            title="Commands",
            border_style="#f97316",
            box=box.SQUARE,
        )
    )
    console.print()
    console.print(
        RichText.from_markup(
            "Tip: Run [bold cyan]rich-gradient text --help[/bold cyan] for gradient specific options."
        )
    )


def _help_callback(ctx: typer.Context, value: Optional[bool]) -> None:
    """Display the custom help screen when the global help flag is used."""

    if not value or ctx.resilient_parsing:
        return
    _render_main_help(Console())
    raise typer.Exit()


@app.command("text", context_settings={"help_option_names": ["-h", "--help"]})
def text_cmd(
    text: Optional[str] = typer.Argument(
        None,
        help="Text to print. If omitted, reads from stdin.",
        show_default=False,
    ),
    color: List[str] = typer.Option(
        [], "--color", "-c", help="Foreground color stop. Repeat for multiple."
    ),
    bgcolor: List[str] = typer.Option(
        [], "--bgcolor", "-b", help="Background color stop. Repeat for multiple."
    ),
    rainbow: bool = typer.Option(
        False, "--rainbow", help="Use a full-spectrum rainbow gradient."
    ),
    hues: int = typer.Option(
        5,
        "--hues",
        min=2,
        help="Number of hues when auto-generating colors (>=2).",
    ),
    style: str = typer.Option("", "--style", help="Rich style string (e.g. 'bold')."),
    justify: str = typer.Option(
        "default",
        "--justify",
        help="Text justification (default|left|right|center|full)",
    ),
    overflow: str = typer.Option(
        "fold",
        "--overflow",
        help="Overflow handling (fold|crop|ellipsis|ignore)",
    ),
    no_wrap: bool = typer.Option(
        False, "--no-wrap/--wrap", help="Disable/enable text wrapping."
    ),
    end: str = typer.Option("\n", "--end", help="String appended after the text."),
    tab_size: int = typer.Option(4, "--tab-size", min=1, help="Tab size in spaces."),
    markup: bool = typer.Option(
        True, "--markup/--no-markup", help="Enable/disable Rich markup parsing."
    ),
    width: Optional[int] = typer.Option(
        None, "--width", help="Console width. Defaults to terminal width."
    ),
    panel: bool = typer.Option(False, "--panel", help="Wrap output in a Panel."),
    title: Optional[str] = typer.Option(
        None, "--title", help="Optional Panel title when using --panel."
    ),
    record: bool = typer.Option(
        False,
        "--record",
        help="Enable Console(record=True). No files are saved by the CLI.",
    ),
    save_svg: Optional[Path] = typer.Option(
        None,
        "--save-svg",
        help="Save output to an SVG file at the given path.",
        show_default=False,
    ),
):
    """Print gradient-styled text to the console."""

    # Read from stdin if no positional text is provided
    if text is None:
        if not sys.stdin.isatty():
            text = sys.stdin.read()
        else:
            typer.echo("No text provided and stdin is empty.", err=True)
            raise typer.Exit(code=1)

    # Normalize color inputs: use None when not provided, otherwise lists
    colors_arg = color or None
    bgcolors_arg = bgcolor or None

    # Validate constrained string options for broad Typer/Click compatibility
    valid_justify = {"default", "left", "right", "center", "full"}
    if justify not in valid_justify:
        typer.echo(
            f"Error: invalid --justify '{justify}'. Choose from: "
            + ", ".join(sorted(valid_justify)),
            err=True,
        )
        raise typer.Exit(code=2)

    valid_overflow = {"fold", "crop", "ellipsis", "ignore"}
    if overflow not in valid_overflow:
        typer.echo(
            f"Error: invalid --overflow '{overflow}'. Choose from: "
            + ", ".join(sorted(valid_overflow)),
            err=True,
        )
        raise typer.Exit(code=2)

    # Build the gradient Text with friendly error handling
    try:
        assert text is not None, "text must be provided before building gradient Text"
        rg_text = Text(
            text=text,
            colors=colors_arg,
            rainbow=rainbow,
            hues=hues,
            style=style,
            justify=justify,  # type: ignore[arg-type]
            overflow=overflow,  # type: ignore[arg-type]
            no_wrap=no_wrap,
            end=end,
            tab_size=tab_size,
            bgcolors=bgcolors_arg,
            markup=markup,
        )
    except (ColorParseError, ValueError, TypeError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=2)
    except Exception as e:  # pragma: no cover - defensive
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(code=2)

    # If saving SVG, Console must be created with record=True
    effective_record = record or (save_svg is not None)
    console = (
        Console(width=width, record=effective_record)
        if width
        else Console(record=effective_record)
    )

    if title and not panel:
        typer.echo("Warning: --title has no effect without --panel", err=True)

    if panel:
        console.print(Panel(rg_text, title=title))
    else:
        console.print(rg_text)

    if save_svg is not None:
        # Ensure directory exists
        try:
            save_svg.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            # Non-fatal; Console will raise below if path invalid
            pass
        # Persist the recorded render to SVG using the project's terminal theme
        console.save_svg(
            str(save_svg),
            title="rich-gradient",
            unique_id="cli_text",
            theme=GRADIENT_TERMINAL_THEME,
        )


@app.command("gradient", context_settings={"help_option_names": ["-h", "--help"]})
def gradient_cmd() -> None:
    """Render sample banners using the Gradient renderable."""

    console = Console()
    banner = Gradient(
        [
            _demo_text("Gradient Showcase", style="bold"),
            Text(
                "Smoothly blend colors across multiple renderables.",
                colors=list(reversed(DEMO_COLORS)),
            ),
        ],
        colors=DEMO_COLORS,
        justify="center",
        expand=True,
    )
    console.print(banner)


@app.command("rule", context_settings={"help_option_names": ["-h", "--help"]})
def rule_cmd() -> None:
    """Showcase the gradient-enabled rule implementation."""

    console = Console()
    console.print(GradientRule("Gradient Rule", rainbow=True, thickness=1))
    console.print(
        _demo_text(
            "Gradient rules are perfect for separating sections.",
            style="italic",
        )
    )


@app.command("panel", context_settings={"help_option_names": ["-h", "--help"]})
def panel_cmd() -> None:
    """Display a panel filled with gradient text."""

    console = Console()
    panel = Panel(
        _demo_text(
            "Panels can frame gradient text for call-outs and highlights.",
        ),
        title=_demo_text("Gradient Panel", style="bold", end=""),
        border_style=DEMO_COLORS[0],
        box=box.ROUNDED,
    )
    console.print(panel)


@app.command("table", context_settings={"help_option_names": ["-h", "--help"]})
def table_cmd() -> None:
    """Render a table that includes gradient-enhanced cells."""

    console = Console()
    table = Table(
        title=_demo_text("Gradient Table", style="bold", end=""),
        box=box.SIMPLE_HEAD,
        expand=True,
    )
    table.add_column(_demo_text("Feature", style="bold", end=""))
    table.add_column(_demo_text("Description", style="bold", end=""))
    table.add_row(
        _demo_text("Color stops", end=""),
        Text(
            "Blend multiple colors across content.",
            colors=list(reversed(DEMO_COLORS)),
            end="",
        ),
    )
    table.add_row(
        _demo_text("Backgrounds", end=""),
        _demo_text("Add gradient backgrounds for extra depth.", end=""),
    )
    console.print(table)


@app.command("progress", context_settings={"help_option_names": ["-h", "--help"]})
def progress_cmd() -> None:
    """Run a short progress example accented with gradient text."""

    console = Console()
    intro = _demo_text("Starting gradient progress demo…")
    console.print(intro)
    with Progress(
        TextColumn("{task.description}", justify="left"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    ) as progress:
        task_id = progress.add_task("Applying colors", total=3)
        for step in range(3):
            progress.update(task_id, description=f"Applying colors step {step + 1}")
            sleep(0.05)
            progress.advance(task_id)
    console.print(_demo_text("Gradient progress complete!"))


@app.command("syntax", context_settings={"help_option_names": ["-h", "--help"]})
def syntax_cmd() -> None:
    """Render a Syntax block inside a gradient frame."""

    console = Console()
    code_sample = """def blend(colors):\n    return ' → '.join(colors)"""
    syntax = Syntax(code_sample, "python", line_numbers=True, word_wrap=True)
    console.print(
        Gradient(
            [
                _demo_text("Gradient Syntax", style="bold"),
                syntax,
            ],
            colors=DEMO_COLORS,
            expand=True,
        )
    )


@app.command("markdown", context_settings={"help_option_names": ["-h", "--help"]})
def markdown_cmd() -> None:
    """Render Markdown content with gradient styling."""

    console = Console()
    markdown = Markdown(
        """# Gradient Markdown\n\n- Smooth transitions\n- Vibrant palettes\n- Easy CLI demos"""
    )
    console.print(
        Gradient(
            [markdown],
            colors=list(reversed(DEMO_COLORS)),
            expand=True,
        )
    )


@app.command("markup", context_settings={"help_option_names": ["-h", "--help"]})
def markup_cmd() -> None:
    """Demonstrate Rich markup parsed into gradient text."""

    console = Console()
    markup_message = "[bold]Rich[/bold] [italic]markup[/italic] meets gradients!"
    parsed = render_markup(markup_message)
    gradient_text = Text(
        parsed.plain,
        colors=DEMO_COLORS,
        spans=list(parsed.spans),
        markup=False,
    )
    console.print(gradient_text)


@app.command("box", context_settings={"help_option_names": ["-h", "--help"]})
def box_cmd() -> None:
    """Preview several box styles with gradient text."""

    console = Console()
    samples = [
        ("ROUNDED", box.ROUNDED),
        ("HEAVY", box.HEAVY),
        ("DOUBLE", box.DOUBLE),
    ]
    for label, box_type in samples:
        console.print(
            Panel(
                _demo_text(f"{label.title()} borders pair nicely with gradients."),
                title=_demo_text(label, style="bold", end=""),
                border_style=DEMO_COLORS[1],
                box=box_type,
            )
        )


@app.command("prompts", context_settings={"help_option_names": ["-h", "--help"]})
def prompts_cmd() -> None:
    """Simulate prompt interaction using gradient-styled questions."""

    console = Console()
    prompt_text = _demo_text("What's your favorite gradient palette? ", end="")
    fake_input = StringIO("Aurora Borealis\n")
    response = Prompt.ask(
        prompt_text,
        console=console,
        stream=fake_input,
        default="Aurora Borealis",
        show_default=True,
    )
    console.print(_demo_text(f"Simulated response: {response}"))


@app.command("live", context_settings={"help_option_names": ["-h", "--help"]})
def live_cmd() -> None:
    """Update live content with gradient-rich messages."""

    console = Console()
    messages = [
        _demo_text("Preparing live gradient demo…", end=""),
        _demo_text("Streaming colorful updates…", end=""),
        _demo_text("Live rendering complete!", end=""),
    ]
    with Live(
        Panel(messages[0], border_style=DEMO_COLORS[0], box=box.ROUNDED),
        console=console,
        refresh_per_second=6,
    ) as live:
        for message in messages[1:]:
            sleep(0.05)
            live.update(Panel(message, border_style=DEMO_COLORS[2], box=box.ROUNDED))
    console.print(_demo_text("Exited live rendering session."))


def print_version(ctx: typer.Context, value: bool) -> None:
    """Display the version of rich-gradient and exit if requested.

    If the version flag is provided, prints the package version and exits the CLI. If the version cannot be determined, prints 'unknown' instead.

    Args:
        value: Boolean indicating whether the version flag was provided.
    """
    if not value or ctx.resilient_parsing:
        return
    typer.echo(f"rich-gradient, version: {__version__}")
    raise typer.Exit()


@app.callback(add_help_option=False)
def main(
    ctx: typer.Context,
    version: Optional[bool] = typer.Option(
        None,
        "-v",
        "--version",
        callback=print_version,
        is_eager=True,
        expose_value=False,
        help="Print version and exit.",
    ),
    help_option: Optional[bool] = typer.Option(
        None,
        "-h",
        "--help",
        callback=_help_callback,
        is_eager=True,
        expose_value=False,
        help="Show this message and exit.",
    ),
) -> None:
    """rich-gradient command line interface."""
    del ctx
    return


if __name__ == "__main__":
    app()
