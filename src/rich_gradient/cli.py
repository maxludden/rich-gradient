"""
CLI for rich-gradient using Typer.

Provides a `text` command to print gradient-styled text.
"""

from __future__ import annotations

import sys
from typing import List, Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel

from rich_gradient import Text
from rich.color import ColorParseError
from rich_gradient.theme import GRADIENT_TERMINAL_THEME


app = typer.Typer(help="rich-gradient CLI")


@app.command("text")
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
    console = Console(width=width, record=effective_record) if width else Console(record=effective_record)

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


def _version_callback(value: bool):
    """Display the version of rich-gradient and exit if requested.

    If the version flag is provided, prints the package version and exits the CLI. If the version cannot be determined, prints 'unknown' instead.

    Args:
        value: Boolean indicating whether the version flag was provided.
    """
    if not value:
        return
    try:
        from importlib.metadata import version

        typer.echo(version("rich-gradient"))
    except Exception:
        typer.echo("unknown")
    raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """rich-gradient command line interface."""
    return


if __name__ == "__main__":
    app()
