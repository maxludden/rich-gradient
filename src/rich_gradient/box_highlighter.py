from typing import Optional, Tuple
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.style import Style
from rich.highlighter import RegexHighlighter
from rich.markup import escape
from rich.box import Box, DOUBLE
from colorsys import hls_to_rgb


# BoxHighlighter: highlights Unicode box-drawing characters with a distinct style.
class BoxHighlighter(RegexHighlighter):
    highlights = [
        r"(?P<box>[─━│┃┌┍┎┏┐┑┒┓└┕┖┗┘┙┚┛├┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬])"
    ]


def _hsl_to_rgb_hex(h: float, s: float = 1.0, l: float = 0.5) -> str:
    r, g, b = hls_to_rgb(h, l, s)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def gradient_box_characters(text: str) -> Text:
    """
    Returns a Text object where each box character is colored with a smooth gradient.
    Non-box characters are left unstyled.
    """
    box_chars = "─━│┃┌┍┎┏┐┑┒┓└┕┖┗┘┙┚┛├┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬"
    output = Text()
    count = sum(1 for char in text if char in box_chars)
    index = 0

    for i, char in enumerate(text):
        if char in box_chars:
            hue = (index / max(count - 1, 1)) % 1.0
            color = _hsl_to_rgb_hex(hue)
            style = Style(color=color)
            output.append(char, style)
            index += 1
        else:
            output.append(char)

    return output
