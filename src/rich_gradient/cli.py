"""Command line interface for ``rich-gradient``.

This module exposes a Typer based command line application that mirrors the
capabilities of the library. The CLI focuses on ergonomic defaults while also
providing fine-grained control over gradient generation, alignment, panel
styling, syntax highlighting, and animation playback. The options are inspired
by the popular ``rich-cli`` utility so that existing Rich users feel right at
home when using ``rich-gradient`` from the terminal.
"""

from __future__ import annotations

import json
import sys
from io import StringIO
from enum import Enum
from pathlib import Path
from time import sleep
from typing import Iterable, List, Optional

import typer
from rich import box
from rich.color import ColorParseError
from rich.console import Console, ConsoleRenderable, RichCast
from rich.json import JSON as RichJSON
from rich.markdown import Markdown
from rich.markup import render as render_markup
from rich.panel import Panel as RichPanel
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Prompt
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text as RichText
from rich.live import Live

from rich_gradient import Gradient, Rule as GradientRule, Text, __version__
from rich_gradient.animated_gradient import AnimatedGradient
from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.panel import Panel
from rich_gradient.spectrum import Spectrum
from rich_gradient.theme import GRADIENT_TERMINAL_THEME


class JustifyOption(str, Enum):
    """Enumeration mapping CLI choices to ``JustifyMethod`` values."""

    DEFAULT = "default"
    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"
    FULL = "full"


class OverflowOption(str, Enum):
    """Enumeration covering the overflow behaviours supported by ``Text``."""

    FOLD = "fold"
    CROP = "crop"
    ELLIPSIS = "ellipsis"
    IGNORE = "ignore"


class AlignOption(str, Enum):
    """Enumeration for horizontal alignment options used by several commands."""

    LEFT = "left"
    RIGHT = "right"
    CENTER = "center"


class VerticalAlignOption(str, Enum):
    """Enumeration for vertical alignment choices used by gradient renderers."""

    TOP = "top"
    MIDDLE = "middle"
    BOTTOM = "bottom"


class BoxOption(str, Enum):
    """Available Rich box styles exposed to the CLI."""

    ROUNDED = "rounded"
    HEAVY = "heavy"
    DOUBLE = "double"
    SQUARE = "square"
    ASCII = "ascii"
    ASCII2 = "ascii2"
    SIMPLE = "simple"
    SIMPLE_HEAD = "simple_head"


BOX_STYLE_MAP: dict[BoxOption, box.Box] = {
    BoxOption.ROUNDED: box.ROUNDED,
    BoxOption.HEAVY: box.HEAVY,
    BoxOption.DOUBLE: box.DOUBLE,
    BoxOption.SQUARE: box.SQUARE,
    BoxOption.ASCII: box.ASCII,
    BoxOption.ASCII2: box.ASCII2,
    BoxOption.SIMPLE: box.SIMPLE,
    BoxOption.SIMPLE_HEAD: box.SIMPLE_HEAD,
}


app = typer.Typer(help="Render gradients and export colourful output from the terminal.")


def _read_text_source(source: Optional[str]) -> str:
    """Read textual content from an argument, stdin, or a file path.

    The behaviour mirrors ``rich-cli``:

    * ``None`` – fall back to stdin when data is piped in, otherwise raise an
      error so the user knows they need to supply content.
    * ``-`` – always read from stdin, even if stdin is attached to a TTY.
    * Existing path – load the file as UTF-8 encoded text.
    * Everything else – treat the argument as the literal text to render.

    Args:
        source: Value provided by the CLI.  May be ``None`` when omitted.

    Returns:
        The textual content to render.

    Raises:
        typer.BadParameter: Raised when no data can be resolved.
    """

    if source == "-":
        data = sys.stdin.read()
        if not data:
            raise typer.BadParameter("stdin did not provide any data")
        return data

    if source is None:
        if sys.stdin.isatty():
            raise typer.BadParameter("provide text or pipe content to stdin")
        return sys.stdin.read()

    candidate_path = Path(source)
    if candidate_path.exists() and candidate_path.is_file():
        try:
            return candidate_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as error:  # pragma: no cover - defensive
            raise typer.BadParameter("file is not valid UTF-8 text") from error

    return source


def _parse_padding(value: Optional[str]) -> tuple[int, int, int, int]:
    """Parse padding strings (``"1"``, ``"2,4"``, ``"1,2,3,4"``) into a 4-tuple."""

    if value is None:
        return (0, 0, 0, 0)
    parts = [element.strip() for element in value.split(",") if element.strip()]
    if not parts:
        return (0, 0, 0, 0)
    try:
        values = [int(part) for part in parts]
    except ValueError as error:
        raise typer.BadParameter("padding must contain integers") from error
    if len(values) == 1:
        top = right = bottom = left = values[0]
    elif len(values) == 2:
        top, right = values
        bottom, left = top, right
    elif len(values) == 4:
        top, right, bottom, left = values
    else:
        raise typer.BadParameter("padding requires 1, 2 or 4 integers")
    return (top, right, bottom, left)


def _create_console(
    width: Optional[int],
    max_width: Optional[int],
    record: bool,
    force_terminal: bool,
) -> Console:
    """Create a ``Console`` configured from CLI flags."""

    kwargs: dict[str, object] = {"record": record, "force_terminal": force_terminal}
    if width is not None:
        kwargs["width"] = width
    if max_width is not None:
        kwargs["max_width"] = max_width
    return Console(**kwargs)


def _save_svg(console: Console, destination: Optional[Path]) -> None:
    """Persist the console buffer to an SVG file when requested."""

    if destination is None:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    console.save_svg(
        str(destination),
        title="rich-gradient",
        theme=GRADIENT_TERMINAL_THEME,
        unique_id="rich-gradient-cli",
    )


def _resolve_renderables(lines: Iterable[str], markup: bool) -> list[ConsoleRenderable]:
    """Convert a sequence of strings into Rich renderables."""

    renderables: list[ConsoleRenderable] = []
    for line in lines:
        if markup:
            renderables.append(RichText.from_markup(line.rstrip("\n")))
        else:
            renderables.append(RichText(line.rstrip("\n")))
    return renderables


def _maybe_warn_panel_title(panel_requested: bool, title: Optional[str]) -> None:
    """Emit a friendly warning when panel specific options are ignored."""

    if title and not panel_requested:
        typer.echo("Warning: --title has no effect without --panel")


def parse_renderable(value: str | RichCast | ConsoleRenderable) -> ConsoleRenderable:
    """Coerce input into a Rich ``ConsoleRenderable`` instance.

    Args:
        value: A string, object implementing ``__rich__``, or an existing
            ``ConsoleRenderable``.

    Returns:
        A ``ConsoleRenderable`` suitable for printing to a ``Console``.

    Raises:
        TypeError: Raised when the value cannot be converted into a renderable.
    """

    if isinstance(value, ConsoleRenderable):
        return value
    if isinstance(value, str):
        return RichText.from_markup(value)
    if hasattr(value, "__rich__"):
        result = value.__rich__()
        if isinstance(result, (str, ConsoleRenderable)) or hasattr(result, "__rich__"):
            return parse_renderable(result)  # type: ignore[arg-type]
        raise TypeError(
            f"RichCast.__rich__() returned {type(result).__name__}, expected "
            "str, RichCast, or ConsoleRenderable."
        )
    raise TypeError(
        f"Cannot parse {type(value).__name__} to ConsoleRenderable. "
        "Expected str, RichCast, or ConsoleRenderable."
    )


DEMO_COLORS: list[str] = ["#38bdf8", "#a855f7", "#f97316", "#fb7185"]


def _demo_text(message: str, *, style: str = "", end: str = "\n") -> Text:
    """Generate gradient text using the shared demo palette."""

    return Text(message, colors=DEMO_COLORS, style=style, end=end)


@app.command(name="text")
def text_command(
    source: Optional[str] = typer.Argument(
        None,
        help="Text, file path, or '-' to read from stdin.",
    ),
    color: List[str] = typer.Option(
        [],
        "-c",
        "--color",
        help="Foreground gradient color stop. Repeat for multiple stops.",
    ),
    bgcolor: List[str] = typer.Option(
        [],
        "-b",
        "--bgcolor",
        help="Background gradient color stop. Repeat for multiple stops.",
    ),
    rainbow: bool = typer.Option(False, "--rainbow", help="Generate a rainbow palette."),
    hues: int = typer.Option(5, "--hues", min=2, help="Auto-generated hues when no stops provided."),
    style: str = typer.Option("", "-s", "--style", help="Base style applied before gradients."),
    justify: JustifyOption = typer.Option(
        JustifyOption.DEFAULT,
        "--justify",
        help="Text justification passed to rich Text.",
    ),
    overflow: OverflowOption = typer.Option(
        OverflowOption.FOLD,
        "--overflow",
        help="Overflow strategy (fold, crop, ellipsis, ignore).",
    ),
    no_wrap: bool = typer.Option(False, "--no-wrap", help="Disable word wrapping."),
    end: str = typer.Option("\n", "--end", help="Trailing text appended after rendering."),
    tab_size: int = typer.Option(4, "--tab-size", min=1, help="Tab size used by Rich Text."),
    markup: bool = typer.Option(True, "--markup/--no-markup", help="Enable Rich markup parsing."),
    markdown_mode: bool = typer.Option(
        False,
        "-m",
        "--markdown",
        help="Render the input as Markdown with gradient framing.",
    ),
    json_mode: bool = typer.Option(
        False,
        "-J",
        "--json",
        help="Render the input as JSON with gradient framing.",
    ),
    syntax: bool = typer.Option(False, "--syntax", help="Syntax highlight the input."),
    lexer: Optional[str] = typer.Option(
        None,
        "-x",
        "--lexer",
        help="Lexer to use with --syntax. Defaults to python when omitted.",
    ),
    theme: str = typer.Option(
        "monokai",
        "--theme",
        help="Syntax highlighting theme when --syntax is used.",
    ),
    line_numbers: bool = typer.Option(
        False,
        "-n",
        "--line-numbers",
        help="Show line numbers for --syntax output.",
    ),
    guides: bool = typer.Option(
        False,
        "-g",
        "--guides",
        help="Show indentation guides for --syntax output.",
    ),
    syntax_no_wrap: bool = typer.Option(
        False,
        "--syntax-no-wrap",
        help="Disable word wrapping for --syntax output.",
    ),
    head: Optional[int] = typer.Option(
        None,
        "--head",
        min=1,
        help="Only render the first N lines (requires --syntax).",
    ),
    tail: Optional[int] = typer.Option(
        None,
        "--tail",
        min=1,
        help="Only render the last N lines (requires --syntax).",
    ),
    width: Optional[int] = typer.Option(None, "-w", "--width", help="Explicit console width."),
    max_width: Optional[int] = typer.Option(
        None, "-W", "--max-width", help="Maximum console width for wrapping."
    ),
    panel: bool = typer.Option(False, "-a", "--panel", help="Wrap the output in a panel."),
    panel_title: Optional[str] = typer.Option(None, "--title", help="Panel title when --panel is used."),
    panel_caption: Optional[str] = typer.Option(
        None, "--caption", help="Panel caption when --panel is used."
    ),
    panel_style: str = typer.Option("", "--panel-style", help="Style applied to the panel body."),
    panel_box: BoxOption = typer.Option(
        BoxOption.ROUNDED,
        "--panel-box",
        help="Panel border box style.",
    ),
    padding: Optional[str] = typer.Option(
        None,
        "-d",
        "--padding",
        help="Padding around panel content (1, 2 or 4 comma separated integers).",
    ),
    expand_panel: bool = typer.Option(
        True, "--expand/--no-expand", help="Expand the panel to available width.", show_default=True
    ),
    record: bool = typer.Option(False, "--record", help="Enable console recording (required for SVG export)."),
    save_svg: Optional[Path] = typer.Option(
        None,
        "--save-svg",
        "--export-svg",
        help="Write the render to an SVG file.",
        show_default=False,
    ),
    force_terminal: bool = typer.Option(
        False,
        "--force-terminal",
        help="Force terminal rendering even when stdout is redirected.",
    ),
) -> None:
    """Render gradient text similar to ``rich-cli --print``."""

    if sum((markdown_mode, json_mode, syntax)) > 1:
        raise typer.BadParameter("Choose at most one of --markdown, --json, or --syntax")
    if (head is not None or tail is not None) and not syntax:
        raise typer.BadParameter("--head/--tail require --syntax")
    if head is not None and tail is not None:
        raise typer.BadParameter("--head and --tail cannot be combined")

    content = _read_text_source(source)
    try:
        renderable: ConsoleRenderable
        if json_mode:
            try:
                data = json.loads(content)
            except json.JSONDecodeError as error:  # pragma: no cover - user input validation
                raise typer.BadParameter(f"invalid JSON: {error}") from error
            renderable = Gradient(
                RichJSON.from_data(data, indent=2),
                colors=color or None,
                bg_colors=bgcolor or None,
                hues=hues,
                rainbow=rainbow,
                justify=justify.value,
            )
        elif markdown_mode:
            renderable = Gradient(
                Markdown(content),
                colors=color or None,
                bg_colors=bgcolor or None,
                hues=hues,
                rainbow=rainbow,
                justify=justify.value,
            )
        elif syntax:
            snippet = content
            lines = content.splitlines()
            if head is not None:
                snippet = "\n".join(lines[:head])
            elif tail is not None:
                snippet = "\n".join(lines[-tail:])
            renderable = Gradient(
                Syntax(
                    snippet,
                    lexer or "python",
                    theme=theme,
                    line_numbers=line_numbers,
                    indent_guides=guides,
                    word_wrap=not syntax_no_wrap,
                ),
                colors=color or None,
                bg_colors=bgcolor or None,
                hues=hues,
                rainbow=rainbow,
                justify=justify.value,
            )
        else:
            renderable = Text(
                text=content,
                colors=color or None,
                bgcolors=bgcolor or None,
                rainbow=rainbow,
                hues=hues,
                style=style,
                justify=justify.value,
                overflow=overflow.value,
                no_wrap=no_wrap,
                end=end,
                tab_size=tab_size,
                markup=markup,
            )
    except (ColorParseError, ValueError, TypeError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(1) from error
    _maybe_warn_panel_title(panel, panel_title)
    console = _create_console(width, max_width, record or save_svg is not None, force_terminal)
    if panel:
        panel_renderable = RichPanel(
            renderable,
            title=panel_title,
            subtitle=panel_caption,
            expand=expand_panel,
            box=BOX_STYLE_MAP[panel_box],
            padding=_parse_padding(padding),
            style=panel_style,
        )
        console.print(panel_renderable)
    else:
        console.print(renderable)
    _save_svg(console, save_svg)


@app.command(name="gradient")
def gradient_command(
    line: Optional[List[str]] = typer.Argument(
        None,
        help="Individual lines to include in the gradient. When omitted, read from stdin.",
    ),
    color: List[str] = typer.Option(
        [], "-c", "--color", help="Foreground color stops. Repeat for multiple values."
    ),
    bgcolor: List[str] = typer.Option(
        [], "-b", "--bgcolor", help="Background color stops. Repeat for multiple values."
    ),
    rainbow: bool = typer.Option(False, "--rainbow", help="Generate a rainbow gradient."),
    hues: int = typer.Option(5, "--hues", min=2, help="Auto-generated hues when color stops missing."),
    justify: AlignOption = typer.Option(
        AlignOption.LEFT,
        "--justify",
        help="Horizontal alignment applied to the gradient output.",
    ),
    vertical_justify: VerticalAlignOption = typer.Option(
        VerticalAlignOption.MIDDLE,
        "--vertical",
        help="Vertical alignment applied when expand is enabled.",
    ),
    markup: bool = typer.Option(True, "--markup/--no-markup", help="Treat input as Rich markup."),
    expand: bool = typer.Option(True, "--expand/--no-expand", help="Expand to available width."),
    record: bool = typer.Option(False, "--record", help="Record console output for export."),
    width: Optional[int] = typer.Option(None, "-w", "--width", help="Explicit console width."),
    max_width: Optional[int] = typer.Option(
        None, "-W", "--max-width", help="Maximum width when wrapping output."
    ),
    force_terminal: bool = typer.Option(
        False, "--force-terminal", help="Force terminal output when piping."
    ),
    save_svg: Optional[Path] = typer.Option(
        None,
        "--save-svg",
        "--export-svg",
        help="Write the gradient render to SVG.",
        show_default=False,
    ),
) -> None:
    """Apply gradients across multiple renderables."""

    console = _create_console(width, max_width, record or save_svg is not None, force_terminal)
    if not line:
        stdin_payload = ""
        if not sys.stdin.isatty():
            stdin_payload = sys.stdin.read()
            if stdin_payload:
                line = stdin_payload.splitlines()
        if not line:
            banner = Gradient(
                [
                    _demo_text("Gradient Showcase", style="bold"),
                    Text(
                        "Smoothly blend colors across multiple renderables.",
                        colors=list(reversed(DEMO_COLORS)),
                        end="",
                    ),
                ],
                colors=DEMO_COLORS,
                justify="center",
                expand=True,
            )
            console.print(banner)
            typer.echo("Gradient Showcase")
            _save_svg(console, save_svg)
            return

    renderables = _resolve_renderables(line, markup)
    gradient = Gradient(
        renderables,
        colors=color or None,
        bg_colors=bgcolor or None,
        hues=hues,
        rainbow=rainbow,
        expand=expand,
        justify=justify.value,
        vertical_justify=vertical_justify.value,
    )
    console.print(gradient)
    _save_svg(console, save_svg)


@app.command(name="rule")
def rule_command(
    title: Optional[str] = typer.Argument(None, help="Optional title rendered inside the rule."),
    color: List[str] = typer.Option(
        [], "-c", "--color", help="Foreground color stops for the rule line."
    ),
    bgcolor: List[str] = typer.Option(
        [], "-b", "--bgcolor", help="Background color stops for the rule line."
    ),
    rainbow: bool = typer.Option(False, "--rainbow", help="Use a rainbow palette regardless of color stops."),
    hues: int = typer.Option(10, "--hues", min=2, help="Number of hues when auto-generating colors."),
    thickness: int = typer.Option(2, "--thickness", min=0, max=3, help="Rule thickness (0-3)."),
    title_style: str = typer.Option("bold", "--title-style", help="Style applied to the rule title."),
    style: str = typer.Option("", "--style", help="Base style applied to the rule characters."),
    align: AlignOption = typer.Option(
        AlignOption.CENTER, "--align", help="Align the rule within the console width."
    ),
    end: str = typer.Option("\n", "--end", help="Characters appended after the rule."),
    width: Optional[int] = typer.Option(None, "-w", "--width", help="Explicit console width."),
    max_width: Optional[int] = typer.Option(
        None, "-W", "--max-width", help="Maximum console width."
    ),
    force_terminal: bool = typer.Option(
        False, "--force-terminal", help="Force terminal output when stdout is redirected."
    ),
    record: bool = typer.Option(False, "--record", help="Enable console recording."),
    save_svg: Optional[Path] = typer.Option(
        None,
        "--save-svg",
        "--export-svg",
        help="Write the rendered rule to an SVG.",
        show_default=False,
    ),
) -> None:
    """Render a gradient powered rule."""

    console = _create_console(width, max_width, record or save_svg is not None, force_terminal)
    demo_mode = (
        title is None
        and not color
        and not bgcolor
        and not rainbow
        and hues == 10
        and thickness == 2
        and style == ""
        and title_style == "bold"
        and align == AlignOption.CENTER
        and end == "\n"
    )
    if demo_mode:
        console.print(GradientRule("Gradient Rule", rainbow=True, thickness=1))
        console.print(
            _demo_text(
                "Gradient rules are perfect for separating sections.",
                style="italic",
            )
        )
        _save_svg(console, save_svg)
        return

    rule = GradientRule(
        title=title,
        title_style=title_style,
        colors=color or None,
        bg_colors=bgcolor or None,
        rainbow=rainbow,
        hues=hues,
        thickness=thickness,
        style=style,
        end=end,
        align=align.value,
    )
    console.print(rule)
    _save_svg(console, save_svg)


@app.command(name="panel")
def panel_command(
    source: Optional[str] = typer.Argument(None, help="Content text, file path, or '-' for stdin."),
    color: List[str] = typer.Option([], "-c", "--color", help="Foreground gradient stops."),
    bgcolor: List[str] = typer.Option([], "-b", "--bgcolor", help="Background gradient stops."),
    rainbow: bool = typer.Option(False, "--rainbow", help="Use a rainbow gradient."),
    hues: int = typer.Option(5, "--hues", min=2, help="Auto-generated hues when no colors provided."),
    title: Optional[str] = typer.Option(None, "--title", help="Panel title."),
    title_align: AlignOption = typer.Option(
        AlignOption.CENTER, "--title-align", help="Alignment for the panel title."
    ),
    title_style: str = typer.Option("bold", "--title-style", help="Style applied to the title."),
    subtitle: Optional[str] = typer.Option(None, "--subtitle", help="Panel subtitle."),
    subtitle_align: AlignOption = typer.Option(
        AlignOption.RIGHT, "--subtitle-align", help="Alignment for the panel subtitle."
    ),
    subtitle_style: str = typer.Option("", "--subtitle-style", help="Style applied to the subtitle."),
    border_style: str = typer.Option("", "--border-style", help="Border style for the panel."),
    box_style: BoxOption = typer.Option(
        BoxOption.ROUNDED, "--box", help="Border box type used for the panel."
    ),
    padding: Optional[str] = typer.Option(
        None,
        "-d",
        "--padding",
        help="Padding inside the panel (1, 2 or 4 comma separated integers).",
    ),
    justify: AlignOption = typer.Option(
        AlignOption.LEFT, "--justify", help="Horizontal alignment for gradient application."
    ),
    vertical: VerticalAlignOption = typer.Option(
        VerticalAlignOption.MIDDLE,
        "--vertical",
        help="Vertical alignment for gradient application.",
    ),
    expand: bool = typer.Option(True, "--expand/--no-expand", help="Expand panel to available width."),
    style: str = typer.Option("", "--style", help="Style applied to the panel content."),
    width: Optional[int] = typer.Option(None, "-w", "--width", help="Explicit console width."),
    height: Optional[int] = typer.Option(None, "--height", help="Fixed panel height."),
    safe_box: bool = typer.Option(False, "--safe-box", help="Use ASCII safe box drawing characters."),
    markup: bool = typer.Option(True, "--markup/--no-markup", help="Interpret content as Rich markup."),
    record: bool = typer.Option(False, "--record", help="Enable console recording."),
    save_svg: Optional[Path] = typer.Option(
        None,
        "--save-svg",
        "--export-svg",
        help="Write the rendered panel to SVG.",
        show_default=False,
    ),
    force_terminal: bool = typer.Option(
        False, "--force-terminal", help="Force terminal rendering when stdout is redirected."
    ),
) -> None:
    """Render a gradient panel with fine grained styling controls."""

    console = _create_console(width, None, record or save_svg is not None, force_terminal)
    if source is None:
        payload = ""
        if not sys.stdin.isatty():
            payload = sys.stdin.read()
        if sys.stdin.isatty() or not payload:
            demo_panel = RichPanel(
                _demo_text("Panels can frame gradient text for call-outs and highlights."),
                title=_demo_text("Gradient Panel", style="bold", end=""),
                border_style=DEMO_COLORS[0],
                box=box.ROUNDED,
            )
            console.print(demo_panel)
            typer.echo("Panels can frame gradient text for call-outs and highlights.")
            _save_svg(console, save_svg)
            return
        content = payload
    else:
        content = _read_text_source(source)
    inner = Text(
        content,
        colors=color or None,
        bgcolors=bgcolor or None,
        rainbow=rainbow,
        hues=hues,
        markup=markup,
    )
    panel = Panel(
        inner,
        colors=color or None,
        bg_colors=bgcolor or None,
        rainbow=rainbow,
        hues=hues,
        title=title,
        title_align=title_align.value,
        title_style=title_style,
        subtitle=subtitle,
        subtitle_align=subtitle_align.value,
        subtitle_style=subtitle_style,
        border_style=border_style,
        box=BOX_STYLE_MAP[box_style],
        padding=_parse_padding(padding),
        expand=expand,
        style=style,
        width=width,
        height=height,
        safe_box=safe_box,
        justify=justify.value,
        vertical_justify=vertical.value,
    )
    console.print(panel)
    _save_svg(console, save_svg)


@app.command(name="spectrum")
def spectrum_command(
    hues: int = typer.Option(17, "--hues", min=2, help="Number of colors to display."),
    invert: bool = typer.Option(False, "--invert", help="Reverse the generated palette."),
    seed: Optional[int] = typer.Option(None, "--seed", help="Seed for deterministic ordering."),
    width: Optional[int] = typer.Option(None, "-w", "--width", help="Console width."),
    max_width: Optional[int] = typer.Option(
        None, "-W", "--max-width", help="Maximum console width."
    ),
    record: bool = typer.Option(False, "--record", help="Enable console recording."),
    save_svg: Optional[Path] = typer.Option(
        None,
        "--save-svg",
        "--export-svg",
        help="Write the spectrum table to SVG.",
        show_default=False,
    ),
    force_terminal: bool = typer.Option(False, "--force-terminal", help="Force terminal rendering."),
) -> None:
    """Display the built-in color spectrum."""

    spectrum = Spectrum(hues=hues, invert=invert, seed=seed)
    console = _create_console(width, max_width, record or save_svg is not None, force_terminal)
    console.print(spectrum)
    _save_svg(console, save_svg)


@app.command(name="table")
def table_command() -> None:
    """Render a gradient-enhanced table demo."""

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


@app.command(name="progress")
def progress_command() -> None:
    """Run a short gradient accented progress demo."""

    console = Console()
    console.print(_demo_text("Starting gradient progress demo…"))
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


@app.command(name="syntax")
def syntax_command() -> None:
    """Render a syntax-highlighted snippet with gradient framing."""

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


@app.command(name="markdown")
def markdown_command() -> None:
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


@app.command(name="markup")
def markup_command() -> None:
    """Demonstrate Rich markup parsed into gradient text."""

    console = Console()
    parsed = render_markup("[bold]Rich[/bold] [italic]markup[/italic] meets gradients!")
    gradient_text = Text(
        parsed.plain,
        colors=DEMO_COLORS,
        spans=list(parsed.spans),
        markup=False,
    )
    console.print(gradient_text)


@app.command(name="box")
def box_command() -> None:
    """Preview several box styles with gradient text."""

    console = Console()
    samples = [
        ("ROUNDED", box.ROUNDED),
        ("HEAVY", box.HEAVY),
        ("DOUBLE", box.DOUBLE),
    ]
    for label, box_type in samples:
        console.print(
            RichPanel(
                _demo_text(f"{label.title()} borders pair nicely with gradients."),
                title=_demo_text(label, style="bold", end=""),
                border_style=DEMO_COLORS[1],
                box=box_type,
            )
        )


@app.command(name="prompts")
def prompts_command() -> None:
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


@app.command(name="live")
def live_command() -> None:
    """Stream live updates with gradient styling."""

    console = Console()
    messages = [
        _demo_text("Preparing live gradient demo…", end=""),
        _demo_text("Streaming colorful updates…", end=""),
        _demo_text("Live rendering complete!", end=""),
    ]
    with Live(
        RichPanel(messages[0], border_style=DEMO_COLORS[0], box=box.ROUNDED),
        console=console,
        refresh_per_second=6,
    ) as live:
        for message in messages[1:]:
            sleep(0.05)
            live.update(RichPanel(message, border_style=DEMO_COLORS[2], box=box.ROUNDED))
    console.print(_demo_text("Exited live rendering session."))


animate_app = typer.Typer(help="Animated gradient demonstrations.")


@animate_app.command(name="gradient")
def animated_gradient_command(
    source: Optional[List[str]] = typer.Argument(
        None,
        help="Textual content for the animated gradient. Reads stdin when omitted.",
    ),
    color: List[str] = typer.Option([], "-c", "--color", help="Foreground gradient stops."),
    bgcolor: List[str] = typer.Option([], "-b", "--bgcolor", help="Background gradient stops."),
    rainbow: bool = typer.Option(False, "--rainbow", help="Animate using a rainbow gradient."),
    hues: int = typer.Option(5, "--hues", min=2, help="Auto-generated color stops when none provided."),
    expand: bool = typer.Option(False, "--expand/--no-expand", help="Expand renderables to fill the terminal."),
    justify: AlignOption = typer.Option(
        AlignOption.LEFT, "--justify", help="Horizontal alignment for the animation."
    ),
    vertical: VerticalAlignOption = typer.Option(
        VerticalAlignOption.TOP,
        "--vertical",
        help="Vertical alignment for the animation.",
    ),
    refresh_per_second: float = typer.Option(
        30.0, "--refresh", min=1.0, help="Refresh rate for the animation."
    ),
    phase_per_second: Optional[float] = typer.Option(
        None,
        "--phase",
        help="Phase advance per second (cycles/s). Defaults to 0.12 for 30 FPS.",
    ),
    duration: Optional[float] = typer.Option(
        None,
        "--duration",
        help="Automatically stop the animation after the given number of seconds.",
    ),
) -> None:
    """Play an animated gradient using ``AnimatedGradient``."""

    if not source:
        if sys.stdin.isatty():
            raise typer.BadParameter("provide content or pipe data for the animation")
        source = sys.stdin.read().splitlines()

    renderables = _resolve_renderables(source, markup=True)
    animation = AnimatedGradient(
        renderables=renderables,
        colors=color or None,
        bg_colors=bgcolor or None,
        rainbow=rainbow,
        hues=hues,
        expand=expand,
        justify=justify.value,
        vertical_justify=vertical.value,
        refresh_per_second=refresh_per_second,
        phase_per_second=phase_per_second,
    )
    if duration is None:
        typer.echo("Press CTRL+C to stop the animation.")
        try:
            animation.run()
        except KeyboardInterrupt:
            pass
        return
    animation.start()
    try:
        sleep(duration)
    except KeyboardInterrupt:
        pass
    finally:
        animation.stop()


@animate_app.command(name="panel")
def animated_panel_command(
    source: Optional[str] = typer.Argument(
        None,
        help="Content text, file path, or '-' for stdin to animate within a panel.",
    ),
    color: List[str] = typer.Option([], "-c", "--color", help="Foreground gradient stops."),
    bgcolor: List[str] = typer.Option([], "-b", "--bgcolor", help="Background gradient stops."),
    rainbow: bool = typer.Option(False, "--rainbow", help="Use rainbow gradients."),
    hues: int = typer.Option(5, "--hues", min=2, help="Auto-generated hues when colors missing."),
    title: Optional[str] = typer.Option(None, "--title", help="Panel title."),
    subtitle: Optional[str] = typer.Option(None, "--subtitle", help="Panel subtitle."),
    border_style: str = typer.Option("", "--border-style", help="Panel border style."),
    box_style: BoxOption = typer.Option(
        BoxOption.ROUNDED, "--box", help="Box style used by the panel border."
    ),
    padding: Optional[str] = typer.Option(
        None,
        "-d",
        "--padding",
        help="Padding inside the panel (1, 2 or 4 comma separated integers).",
    ),
    expand: bool = typer.Option(True, "--expand/--no-expand", help="Expand panel to available width."),
    refresh_per_second: float = typer.Option(
        30.0, "--refresh", min=1.0, help="Refresh rate for the animation."
    ),
    phase_per_second: Optional[float] = typer.Option(
        None,
        "--phase",
        help="Phase advance per second (cycles/s). Defaults to 0.12 at 30 FPS.",
    ),
    duration: Optional[float] = typer.Option(
        None,
        "--duration",
        help="Automatically stop the animation after the given number of seconds.",
    ),
) -> None:
    """Animate a gradient panel."""

    content = _read_text_source(source)
    inner = RichText.from_markup(content)
    panel = Panel(
        inner,
        colors=color or None,
        bg_colors=bgcolor or None,
        rainbow=rainbow,
        hues=hues,
        title=title,
        subtitle=subtitle,
        border_style=border_style,
        box=BOX_STYLE_MAP[box_style],
        padding=_parse_padding(padding),
        expand=expand,
    )
    animation = AnimatedPanel(
        panel,
        colors=color or None,
        bg_colors=bgcolor or None,
        rainbow=rainbow,
        hues=hues,
        refresh_per_second=refresh_per_second,
        phase_per_second=phase_per_second,
    )
    if duration is None:
        typer.echo("Press CTRL+C to stop the animation.")
        try:
            animation.run()
        except KeyboardInterrupt:
            pass
        return
    animation.start()
    try:
        sleep(duration)
    except KeyboardInterrupt:
        pass
    finally:
        animation.stop()


app.add_typer(animate_app, name="animate")


@app.callback()
def main_callback(
    version: Optional[bool] = typer.Option(
        None,
        "-v",
        "--version",
        help="Print the rich-gradient version and exit.",
        callback=lambda value: _show_version(value),
        is_eager=True,
    )
) -> None:
    """Entry point for Typer application."""

    del version  # ``version`` is handled by the eager callback


def _show_version(value: Optional[bool]) -> None:
    """Display the package version when the --version flag is used."""

    if value:
        typer.echo(f"rich-gradient {__version__}")
        raise typer.Exit()


def run() -> None:
    """Execute the Typer application."""

    app()


if __name__ == "__main__":
    run()
