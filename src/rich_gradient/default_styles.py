"""A container for the default styles used by GradientConsole."""

from __future__ import annotations

from typing import Dict, Optional

from rich.console import Console
from rich.style import Style, StyleType
from rich.table import Table
from rich.text import Text
from rich.theme import Theme
from rich.traceback import install as tr_install
from rich.default_styles import DEFAULT_STYLES as RICH_DEFAULT_STYLES

global DEFAULT_STYLES
DEFAULT_STYLES: dict[str, StyleType] = {
    "none": Style.null(),
    "reset": Style(
        color="default",
        bgcolor="default",
        dim=False,
        bold=False,
        italic=False,
        underline=False,
        blink=False,
        blink2=False,
        reverse=False,
        conceal=False,
        strike=False,
    ),
    "dim": Style(dim=True),
    "bright": Style(dim=False),
    "bold": Style(bold=True),
    "strong": Style(bold=True),
    "code": Style(reverse=True, bold=True),
    "italic": Style(italic=True),
    "emphasize": Style(italic=True),
    "underline": Style(underline=True),
    "blink": Style(blink=True),
    "blink2": Style(blink2=True),
    "reverse": Style(reverse=True),
    "strike": Style(strike=True),
    "white": Style(color="#ffffff"),
    "bold.white": Style(color="#ffffff", bold=True),
    "repr.white": Style(color="#ffffff", bold=True),
    "cs.white": Style(color="#ffffff", bgcolor="#ffffff", bold=True),
    "style.white": Style(color="#ffffff", bgcolor="default", bold=True),
    "bg_style.white": Style(color="#FFFFFF", bgcolor="#ffffff", bold=True),
    "lightgrey": Style(color="#dddddd"),
    "bold.lightgrey": Style(color="#dddddd", bold=True),
    "repr.lightgrey": Style(color="#dddddd", bold=True),
    "cs.lightgrey": Style(color="#dddddd", bgcolor="#dddddd", bold=True),
    "style.lightgrey": Style(color="#dddddd", bgcolor="default", bold=True),
    "bg_style.lightgrey": Style(color="#FFFFFF", bgcolor="#dddddd", bold=True),
    "lightgray": Style(color="#dddddd"),
    "bold.lightgray": Style(color="#dddddd", bold=True),
    "repr.lightgray": Style(color="#dddddd", bold=True),
    "cs.lightgray": Style(color="#dddddd", bgcolor="#dddddd", bold=True),
    "style.lightgray": Style(color="#dddddd", bgcolor="default", bold=True),
    "bg_style.lightgray": Style(color="#FFFFFF", bgcolor="#dddddd", bold=True),
    "grey": Style(color="#888888"),
    "bold.grey": Style(color="#888888", bold=True),
    "repr.grey": Style(color="#888888", bold=True),
    "cs.grey": Style(color="#888888", bgcolor="#888888", bold=True),
    "style.grey": Style(color="#888888", bgcolor="default", bold=True),
    "bg_style.grey": Style(color="#FFFFFF", bgcolor="#888888", bold=True),
    "gray": Style(color="#888888"),
    "bold.gray": Style(color="#888888", bold=True),
    "repr.gray": Style(color="#888888", bold=True),
    "cs.gray": Style(color="#888888", bgcolor="#888888", bold=True),
    "style.gray": Style(color="#888888", bgcolor="default", bold=True),
    "bg_style.gray": Style(color="#FFFFFF", bgcolor="#888888", bold=True),
    "darkgrey": Style(color="#444444"),
    "bold.darkgrey": Style(color="#444444", bold=True),
    "repr.darkgrey": Style(color="#444444", bold=True),
    "cs.darkgrey": Style(color="#444444", bgcolor="#444444", bold=True),
    "style.darkgrey": Style(color="#444444", bgcolor="default", bold=True),
    "bg_style.darkgrey": Style(color="#ffffff", bgcolor="#444444", bold=True),
    "darkgray": Style(color="#444444"),
    "bold.darkgray": Style(color="#444444", bold=True),
    "repr.darkgray": Style(color="#444444", bold=True),
    "cs.darkgray": Style(color="#444444", bgcolor="#444444", bold=True),
    "style.darkgray": Style(color="#444444", bgcolor="default", bold=True),
    "bg_style.darkgray": Style(color="#ffffff", bgcolor="#444444", bold=True),
    "black": Style(color="#111111"),
    "bold.black": Style(color="#111111", bold=True),
    "repr.black": Style(color="#111111", bold=True),
    "cs.black": Style(color="#111111", bgcolor="default", bold=True),
    "style.black": Style(color="#111111", bgcolor="default", bold=True),
    "bg_style.black": Style(color="#ffffff", bgcolor="default", bold=True),
    "pink": Style(color="#ff00af", bold=True),
    "bold.pink": Style(color="#ff00af", bold=True),
    "repr.pink": Style(color="#ff00af", bold=True),
    "cs.pink": Style(color="#ff00af", bgcolor="default", bold=True),
    "style.pink": Style(color="#ff00af", bgcolor="default", bold=True),
    "bg_style.pink": Style(color="#FFFFFF", bgcolor="#ff00af", bold=True),
    "deeppink": Style(color="#ff1493"),
    "bold.deeppink": Style(color="#ff1493", bold=True),
    "repr.deeppink": Style(color="#ff1493", bold=True),
    "cs.deeppink": Style(color="#ff1493", bgcolor="default", bold=True),
    "style.deeppink": Style(color="#ff1493", bgcolor="default", bold=True),
    "bg_style.deeppink": Style(color="#FFFFFF", bgcolor="#ff1493", bold=True),
    "red": Style(color="#ff0000"),
    "bold.red": Style(color="#ff0000", bold=True),
    "repr.red": Style(color="#ff0000", bold=True),
    "cs.red": Style(color="#ff0000", bgcolor="default", bold=True),
    "style.red": Style(color="#ff0000", bgcolor="default", bold=True),
    "bg_style.red": Style(color="#FFFFFF", bgcolor="#ff0000", bold=True),
    "tomato": Style(color="#FF4B00"),
    "bold.tomato": Style(color="#FF4B00", bold=True),
    "repr.tomato": Style(color="#FF4B00", bold=True),
    "cs.tomato": Style(color="#FF4B00", bgcolor="default", bold=True),
    "style.tomato": Style(color="#FF4B00", bgcolor="default", bold=True),
    "bg_style.tomato": Style(color="#FFFFFF", bgcolor="#FF4B00", bold=True),
    "darkorange": Style(color="#FF8700"),
    "bold.darkorange": Style(color="#FF8700", bold=True),
    "repr.darkorange": Style(color="#FF8700", bold=True),
    "cs.darkorange": Style(color="#FF8700", bgcolor="default", bold=True),
    "style.darkorange": Style(color="#FF8700", bgcolor="default", bold=True),
    "bg_style.darkorange": Style(color="#FFFFFF", bgcolor="#FF8700", bold=True),
    "orange": Style(color="#FFAF00"),
    "bold.orange": Style(color="#FFAF00", bold=True),
    "repr.orange": Style(color="#FFAF00", bold=True),
    "cs.orange": Style(color="#FFAF00", bgcolor="default", bold=True),
    "style.orange": Style(color="#FFAF00", bgcolor="default", bold=True),
    "bg_style.orange": Style(color="#FFFFFF", bgcolor="#FFAF00", bold=True),
    "yellow": Style(color="#ffff00"),
    "bold.yellow": Style(color="#ffff00", bold=True),
    "repr.yellow": Style(color="#ffff00", bold=True),
    "cs.yellow": Style(color="#ffff00", bgcolor="default", bold=True),
    "style.yellow": Style(color="#ffff00", bgcolor="default", bold=True),
    "bg_style.yellow": Style(color="#FFFFFF", bgcolor="#ffff00", bold=True),
    "greenyellow": Style(color="#adff2f"),
    "bold.greenyellow": Style(color="#adff2f", bold=True),
    "repr.greenyellow": Style(color="#adff2f", bold=True),
    "cs.greenyellow": Style(color="#adff2f", bgcolor="default", bold=True),
    "style.greenyellow": Style(color="#adff2f", bgcolor="default", bold=True),
    "bg_style.greenyellow": Style(color="#FFFFFF", bgcolor="#adff2f", bold=True),
    "green": Style(color="#7CFF00"),
    "bold.green": Style(color="#7CFF00", bold=True),
    "repr.green": Style(color="#7CFF00", bold=True),
    "cs.green": Style(color="#7CFF00", bgcolor="default", bold=True),
    "style.green": Style(color="#7CFF00", bgcolor="default", bold=True),
    "bg_style.green": Style(color="#FFFFFF", bgcolor="#7CFF00", bold=True),
    "lime": Style(color="#00ff00"),
    "bold.lime": Style(color="#00ff00", bold=True),
    "repr.lime": Style(color="#00ff00", bold=True),
    "cs.lime": Style(color="#00ff00", bgcolor="default", bold=True),
    "style.lime": Style(color="#00ff00", bgcolor="default", bold=True),
    "bg_style.lime": Style(color="#FFFFFF", bgcolor="#00ff00", bold=True),
    "springgreen": Style(color="#00FFC3"),
    "bold.springgreen": Style(color="#00FFC3", bold=True),
    "repr.springgreen": Style(color="#00FFC3", bold=True),
    "cs.springgreen": Style(color="#00FFC3", bgcolor="default", bold=True),
    "style.springgreen": Style(color="#00FFC3", bgcolor="default", bold=True),
    "bg_style.springgreen": Style(color="#FFFFFF", bgcolor="#00FFC3", bold=True),
    "cyan": Style(color="#00ffff"),
    "bold.cyan": Style(color="#00ffff", bold=True),
    "repr.cyan": Style(color="#00ffff", bold=True),
    "cs.cyan": Style(color="#00ffff", bgcolor="default", bold=True),
    "style.cyan": Style(color="#00ffff", bgcolor="default", bold=True),
    "bg_style.cyan": Style(color="#FFFFFF", bgcolor="#00ffff", bold=True),
    "lightblue": Style(color="#00C3FF"),
    "bold.lightblue": Style(color="#00C3FF", bold=True),
    "repr.lightblue": Style(color="#00C3FF", bold=True),
    "cs.lightblue": Style(color="#00C3FF", bgcolor="default", bold=True),
    "style.lightblue": Style(color="#00C3FF", bgcolor="default", bold=True),
    "bg_style.lightblue": Style(color="#FFFFFF", bgcolor="#00C3FF", bold=True),
    "skyblue": Style(color="#0087FF"),
    "bold.skyblue": Style(color="#0087FF", bold=True),
    "repr.skyblue": Style(color="#0087FF", bold=True),
    "cs.skyblue": Style(color="#0087FF", bgcolor="default", bold=True),
    "style.skyblue": Style(color="#0087FF", bgcolor="default", bold=True),
    "bg_style.skyblue": Style(color="#FFFFFF", bgcolor="#0087FF", bold=True),
    "deepblue": Style(color="#0055FF"),
    "bold.deepblue": Style(color="#0055FF", bold=True),
    "repr.deepblue": Style(color="#0055FF", bold=True),
    "cs.deepblue": Style(color="#0055FF", bgcolor="default", bold=True),
    "style.deepblue": Style(color="#0055FF", bgcolor="default", bold=True),
    "bg_style.deepblue": Style(color="#FFFFFF", bgcolor="#0055FF", bold=True),
    "blue": Style(color="#0000ff"),
    "bold.blue": Style(color="#0000ff", bold=True),
    "repr.blue": Style(color="#0000ff", bold=True),
    "cs.blue": Style(color="#0000ff", bgcolor="default", bold=True),
    "style.blue": Style(color="#0000ff", bgcolor="default", bold=True),
    "bg_style.blue": Style(color="#FFFFFF", bgcolor="#0000ff", bold=True),
    "violet": Style(color="#5F00FF"),
    "bold.violet": Style(color="#5F00FF", bold=True),
    "repr.violet": Style(color="#5F00FF", bold=True),
    "cs.violet": Style(color="#5F00FF", bgcolor="default", bold=True),
    "style.violet": Style(color="#5F00FF", bgcolor="default", bold=True),
    "bg_style.violet": Style(color="#FFFFFF", bgcolor="#5F00FF", bold=True),
    "purple": Style(color="#AF00FF"),
    "bold.purple": Style(color="#AF00FF", bold=True),
    "repr.purple": Style(color="#AF00FF", bold=True),
    "cs.purple": Style(color="#AF00FF", bgcolor="default", bold=True),
    "style.purple": Style(color="#AF00FF", bgcolor="default", bold=True),
    "bg_style.purple": Style(color="#FFFFFF", bgcolor="#AF00FF", bold=True),
    "magenta": Style(color="#ff00ff"),
    "bold.magenta": Style(color="#ff00ff", bold=True),
    "repr.magenta": Style(color="#ff00ff", bold=True),
    "cs.magenta": Style(color="#ff00ff", bgcolor="default", bold=True),
    "style.magenta": Style(color="#ff00ff", bgcolor="default", bold=True),
    "bg_style.magenta": Style(color="#FFFFFF", bgcolor="#ff00ff", bold=True),
    "box.highlight": Style(color="#eeeeee"),
    "inspect.attr": Style(color="#ffff00", italic=True),
    "inspect.attr.dunder": Style(color="#ffff00", italic=True, dim=True),
    "inspect.callable": Style(color="#AF00FF", bold=True),
    "inspect.async_def": Style(color="#00ffff", italic=True),
    "inspect.def": Style(italic=True, color="#00ffff"),
    "inspect.class": Style(italic=True, color="#00ffff"),
    "inspect.error": Style(bold=True, color="#ff0000"),
    "inspect.equals": Style(),
    "inspect.help": Style(color="#00ffff"),
    "inspect.doc": Style(dim=True),
    "inspect.value.border": Style(color="#00ff00"),
    "live.ellipsis": Style(bold=True, color="#ff0000"),
    "layout.tree.row": Style(dim=False, color="#ff0000"),
    "layout.tree.column": Style(dim=False, color="#0000ff"),
    "logging.keyword": Style(bold=True, color="#ffff00"),
    "logging.level.notset": Style(dim=True),
    "logging.level.trace": Style(color="#cccccc"),
    "logging.level.debug": Style(color="#00ffff"),
    "logging.level.info": Style(color="#54d1ff"),
    "logging.level.success": Style(color="#afff00", bold=True),
    "logging.level.warning": Style(color="#ffff00", italic=True),
    "logging.level.error": Style(color="#ff3300", bold=True),
    "logging.level.critical": Style(color="#eeeeee",bgcolor="#990000", bold=True),
    "log.level": Style.null(),
    "log.time": Style(color="#00ffff", dim=True),
    "log.message": Style.null(),
    "log.path": Style(dim=True),
    "log.keyword": Style(color="#E3EC84", bold=True, italic=True),
    "log.index": Style(color="#7FD6E8", bold=True, italic=True),
    "log.separator": Style(color="#f0ffff", bold=True, italic=True),
    "syntax.class": Style(color="#7FD6E8", bold=True, italic=True),
    "repr.ellipsis": Style(color="#ffff00"),
    "repr.indent": Style(color="#00ff00", dim=True),
    "repr.error": Style(color="#ff0000", bold=True),
    "repr.str": Style(color="#99ff00", italic=False, bold=False),
    "repr.brace": Style(color="#DDDDDD", bold=True),
    "repr.comma": Style(color= "#555555", bold=True),
    "repr.ipv4": Style(bold=True, color="#00ff00"),
    "repr.ipv6": Style(bold=True, color="#00ff00"),
    "repr.eui48": Style(bold=True, color="#00ff00"),
    "repr.eui64": Style(bold=True, color="#00ff00"),
    "repr.tag_start": Style(bold=True),
    "repr.tag_name": Style(color="#99ff00", bold=True),
    "repr.tag_contents": Style(color="default"),
    "repr.tag_end": Style(bold=True),
    "repr.attrib_name": Style(color="#afaaff", italic=False),
    "repr.attrib_equal": Style(bold=True),
    "repr.attrib_value": Style(color="#5F00FF", italic=False),
    "repr.number": Style(
        color="#8BE8FC", bold=True, italic=False
    ),  # repr.number is identical to
    "repr.number_complex": Style(
        color="#00ffff", bold=True, italic=False
    ),  # repr.number_complex
    "repr.bool_true": Style(color="#00ff00", italic=True),
    "repr.bool_false": Style(color="#ff0000", italic=True),
    "repr.none": Style(color="#00ff00", italic=True),
    "repr.url": Style(underline=True, color="#0000ff", italic=False, bold=False),
    "repr.uuid": Style(color="#ffff00", bold=False),
    "repr.call": Style(color="#00ff00", bold=True),
    "repr.path": Style(color="#00ff00"),
    "repr.filename": Style(color="#99ff00"),
    "rule.line": Style(color="#ffffff", bold=True),
    "rule.text": Style(color="#af00ff", bold=True),
    "json.brace": Style(bold=True),
    "json.bool_true": Style(color="#00ff00", italic=True),
    "json.bool_false": Style(color="#ff0000", italic=True),
    "json.null": Style(color="#00ff00", italic=True),
    "json.number": Style(color="#8BE8FC", bold=True, italic=False),
    "json.str": Style(color="#00ff00", italic=False, bold=False),
    "json.key": Style(color="#0000ff", bold=True),
    "prompt": Style.null(),
    "prompt.choices": Style(color="#E0E0E0", bold=True),
    "prompt.default": Style(color="#C0FC8B", bold=True),
    "prompt.invalid": Style(color="#ff0000"),
    "prompt.invalid.choice": Style(color="#ff0000"),
    "pretty": Style.null(),
    "scope.border": Style(color="#0000ff"),
    "scope.key": Style(color="#ffffcc", italic=True),
    "scope.key.special": Style(color="#ffff00", italic=True, dim=True),
    "scope.equals": Style(color="#ff0000"),
    "table.header": Style(bold=True),
    "table.footer": Style(bold=True),
    "table.cell": Style.null(),
    "table.title": Style(italic=True),
    "table.caption": Style(italic=True, dim=True),
    "traceback.error": Style(color="#ff0000", italic=True),
    "traceback.border.syntax_error": Style(color="#ff0000"),
    "traceback.border": Style(color="#ff0000"),
    "traceback.text": Style.null(),
    "traceback.title": Style(color="#ff0000", bold=True),
    "traceback.exc_type": Style(color="#ff0000", bold=True),
    "traceback.exc_value": Style.null(),
    "traceback.offset": Style(color="#ff0000", bold=True),
    "bar.back": Style(color="grey23"),
    "bar.complete": Style(color="#646464"),
    "bar.finished": Style(color="#006a20"),
    "bar.pulse": Style(color="#00ffff"),
    "progress.description": Style.null(),
    "progress.filesize": Style(color="#00ff00"),
    "progress.filesize.total": Style(color="#00ff00"),
    "progress.download": Style(color="#00ff00"),
    "progress.elapsed": Style(color="#ffff00"),
    "progress.percentage": Style(color="#ff00ff"),
    "progress.remaining": Style(color="#00ffff"),
    "progress.data.speed": Style(color="#ff0000"),
    "progress.spinner": Style(color="#00ff00"),
    "status.spinner": Style(color="#00ff00"),
    "tree": Style(),
    "tree.line": Style(),
    "markdown.paragraph": Style(),
    "markdown.text": Style(),
    "markdown.em": Style(italic=True),
    "markdown.emph": Style(italic=True),  # For commonmark backwards compatibility
    "markdown.strong": Style(bold=True),
    "markdown.code": Style(bold=True, color="#00ffff", bgcolor="black"),
    "markdown.code_block": Style(color="#00ffff", bgcolor="black"),
    "markdown.block_quote": Style(color="#99ff00"),
    "markdown.list": Style(color="#00ffff"),
    "markdown.item": Style(),
    "markdown.item.bullet": Style(color="#ffff00", bold=True),
    "markdown.item.number": Style(color="#ffff00", bold=True),
    "markdown.hr": Style(color="#ffffff"),
    "markdown.h1.border": Style(),
    "markdown.h1": Style(bold=True),
    "markdown.h2": Style(bold=True, underline=True),
    "markdown.h3": Style(bold=True),
    "markdown.h4": Style(bold=True, dim=True),
    "markdown.h5": Style(underline=True),
    "markdown.h6": Style(italic=True),
    "markdown.h7": Style(italic=True, dim=True),
    "markdown.link": Style(color="#0000ff"),
    "markdown.link_url": Style(color="#0000ff", underline=True),
    "markdown.s": Style(strike=True),
    "iso8601.date": Style(color="#0000ff"),
    "iso8601.time": Style(color="#ff00ff"),
    "iso8601.timezone": Style(color="#ffff00"),
    "rgb.red": Style(color="#ff0000", bold=True, italic=True),
    "rgb.green": Style(color="#00ff00", bold=True, italic=True),
    "rgb.blue": Style(color="#0088ff", bold=True, italic=True),
    "repr.rgb_red": Style(color="#ff4444", bold=True, italic=True),
    "repr.rgb_green": Style(color="#44ff44", bold=True, italic=True),
    "repr.rgb_blue": Style(color="#44aaff", bold=True, italic=True),
    "repr.rgb_parentheses": Style(color="#ffffff", bold=True, italic=False),
    "mypy.error_path": Style(color="#5CECFF", italic=True),
    "mypy.error_line": Style(color="#00ff5f", bold=True),
    "mypy.error_msg": Style(color="#dfdfdf", bold=True),
    "mypy.error_border": Style(color="#ff0000", bold=True),
    "mypy.error": Style(color="#ff0000", bold=True),
    "mypy.numbers": Style(color="#8BE9FD", bold=True),
    "mypy.success": Style(color="#00ff00", bold=True),
    "mypy.colon": Style(color="#ffffff", bold=True),
    "mypy.quoted": Style(color="#00afff", bold=True),
    "mypy.message": Style(color="#ffffff", bold=True),
}


# Automatically generate EDITED_STYLES by comparing to rich's default styles
EDITED_STYLES: Dict[str, str] = {}
for key, style in DEFAULT_STYLES.items():
    if key not in RICH_DEFAULT_STYLES:
        EDITED_STYLES[key] = ":star: [bold #e1b400]New[/] :star:"
    elif str(style) != str(RICH_DEFAULT_STYLES[key]):
        EDITED_STYLES[key] = ":paintbrush: [bold #ffffff]Color Corrected[/]"
    else:
        EDITED_STYLES[key] = "[dim]Unchanged[/dim]"


def get_default_styles() -> Dict[str, StyleType]:
    """Retrieve the defaults styles from GRADIENT_STYLES."""
    return DEFAULT_STYLES


def formatted_title() -> Text:
    """Create a vibrant title for the styles table.

    Returns:
        Text: the colorful title
    """
    letters = (
        Text("Gr", style="bold #ff0000"),
        Text("ad", style="bold #ff8800"),
        Text("ie", style="bold #ffff00"),
        Text("nt", style="bold #00ff00"),
        Text("Th", style="bold #00ffff"),
        Text("e", style="bold #0088ff"),
        Text("m", style="bold #5f00ff"),
        Text("e", style="bold #af00ff"),
    )
    return Text.assemble(*letters)


def styles_table() -> Table:
    """Generate a table to display all styles, examples of how to call each,
    and if each style is new, or updated from rich, or unchanged."""
    table = Table(
        title=formatted_title(),
        border_style="bold #888888",
        caption="These styles are used when instantiating rich.console.Console",
        caption_style="dim",
        caption_justify="right",
        show_lines=False,
        row_styles=(["on #1f1f1f", "on #111111"]),
    )
    table.add_column("[bold.cyan]Styles[/]", justify="right", vertical="middle")
    table.add_column(
        "[bold.cyan]Description[/]",
        justify="left",
        width=40,
        vertical="middle",
    )
    table.add_column("[bold.cyan]Updated[/]", justify="center", vertical="middle")

    for style_name in DEFAULT_STYLES.keys():
        temp_style: Optional[StyleType] = DEFAULT_STYLES.get(style_name)
        assert temp_style is not None, "Style should not be None"
        style: Style = Style.parse(str(temp_style))
        style_string = str(style)
        if "grey" in style_name:
            style_string = f"{style_string} [dim]*Supports alternate spelling[/dim]"
        if "dark_grey" in style_name or "dark_gray" in style_name:
            continue
        if "gray" in style_name:
            continue
        edited = EDITED_STYLES.get(style_name)
        table.add_row(Text(style_name, style=style), style_string, edited)
        if style_name == "none" or style_name == "reset":
            table.add_section()

    return table


def example(record: bool = False) -> None:
    """Print the styles table to the console."""
    theme = Theme(DEFAULT_STYLES)
    console = Console(theme=theme, record=record)
    tr_install(console=console)

    console.print(styles_table(), justify="center")


if __name__ == "__main__":
    example()


# Ensure all keys in DEFAULT_STYLES are represented in EDITED_STYLES
for key in DEFAULT_STYLES:
    if key not in EDITED_STYLES:
        EDITED_STYLES[key] = "[dim]Unchanged[/dim]"
