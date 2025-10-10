"""
CLI for rich-gradient using Typer.

Provides a `text` command to print gradient-styled text.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional
from typing_extensions import Annotated

import typer
from rich.align import Align
from rich.color import ColorParseError
from rich.console import Console, ConsoleRenderable, RenderableType
from rich import box
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text as RichText

from rich_gradient import Text, __version__
from rich_gradient.theme import GRADIENT_TERMINAL_THEME

app = typer.Typer(
    help="rich-gradient CLI",
    no_args_is_help=True,
    context_settings={"help_option_names": []},
    rich_markup_mode="rich"
)


def _build_header() -> RichText:
    """Return a gradient styled header for the CLI help screen."""

    header_parts = [
            Text(
                text="Rich Gradient ",
                colors=[
                    "#38bdf8",
                    "#a855f7",
                    "#f97316",
                    "#fb7185"
                ],
                style="bold"
            ),
            Text(
                'CLI v',
                style='bold white'
            ),
            Text(
                f"{__version__}",
                colors=[
                    "#0f0",
                    "#0ff",
                    "#09f",
                ],
                style="italic"
            )
        ]
    header = RichText.assemble(*header_parts)
    return header



def _render_main_help(console: Console) -> None:
    """Render a custom help screen that mirrors the Rich CLI aesthetic."""

    console.print(Align.center(_build_header()))
    console.print(Align.center(RichText.from_markup(f"[dim]Version {__version__}[/dim]")))
    console.print()
    console.print(Rule(style="#a855f7"))
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
            "Tip: Run [bold cyan]rich-gradient text --help[/bold cyan] for gradient \
specific options."
        )
    )


def _help_callback(ctx: typer.Context, value: Optional[bool]) -> None:
    """Display the custom help screen when the global help flag is used."""

    if not value or ctx.resilient_parsing:
        return
    _render_main_help(Console())
    raise typer.Exit()

def parse_renderable(value: RenderableType) -> ConsoleRenderable:
    """Parse a str, rich renderable, rich_gradient.text.Text, or rich_gradient.\
    gradient.Gradient into a valid RichRenderable."""
    


@app.command(
        "print",
        context_settings={
            "help_option_names": [
                "-h",
                "--help"
            ]
        }
    )
def print_cmd(
    renderable: Annotated[
        ConsoleRenderable,
        typer.Argument(
            parser=parse_renderable)]
            help="The renderable to print. If not provided, will print help screen.",
            show_default=False,

        ),
    ],
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
    if renderable is None:

        # if not sys.stdin.isatty():
        #     renderable = sys.stdin.read()
        # else:
        #     typer.echo("No text provided and stdin is empty.", err=True)
        #     raise typer.Exit(code=1)

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
        except OSError:
            # Non-fatal; Console will raise below if path invalid
            pass
        # Persist the recorded render to SVG using the project's terminal theme
        console.save_svg(
            str(save_svg),
            title="rich-gradient",
            unique_id="cli_text",
            theme=GRADIENT_TERMINAL_THEME,
        )


def print_version(ctx: typer.Context, value: bool) -> None:
    """Display the version of rich-gradient and exit if requested.

    If the version flag is provided, prints the package version and exits the CLI.
        If the version cannot be determined, prints 'unknown' instead.

    Args:
        value: Boolean indicating whether the version flag was provided.
    """
    if not value or ctx.resilient_parsing:
        return
    console = Console()
    rich_gradient_text: Text = Text(
        'rich-gradient ',
        colors=[
            '#f00',
            '#f90',
            '#ff0',
            '#9f0'
        ],
        style='bold'
    )
    version: Text = Text(
        f'{__version__}',
        colors=[
            '#0f0',
            '#0ff',
            '#09f'
        ],
        style='italic'
    )
    console.print(
        RichText.assemble(
            rich_gradient_text,
            RichText(' v', style='bold white'),
            version
        )
    )
    raise typer.Exit()


@app.callback(no_args_is_help=True)
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
