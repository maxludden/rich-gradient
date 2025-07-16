import re
from typing import Any, Tuple

from rich.color import Color, ColorParseError
from rich.color_triplet import ColorTriplet
from rich.style import Style


def luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate the relative luminance of an RGB color."""

    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = rgb
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def contrast_ratio(fg: ColorTriplet, bg: ColorTriplet) -> float:
    """Calculate the contrast ratio between two RGB colors."""
    lum1 = luminance(fg)
    lum2 = luminance(bg)
    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)
    return (lighter + 0.05) / (darker + 0.05)


def has_sufficient_contrast(
    fg: Tuple[int, int, int], bg: Tuple[int, int, int], ratio: float = 6.0
) -> bool:
    """
    Return True if the contrast ratio between fg and bg is sufficient for legibility.
    Default ratio is 4.5 (WCAG AA for normal text).
    """

    def parse_color(color: Any) -> ColorTriplet:
        """Parse a color input into an RGB Tuple."""
        if isinstance(color, Color):
            return color.get_truecolor()
        try:
            color = Color.parse(color)
            return color.get_truecolor()
        except ColorParseError as cpe:
            raise ColorParseError(
                f"Attempted to parse color for contrast check but unable to parse color: {color!r}"
            ) from cpe

    fg_rgb = parse_color(fg)
    bg_rgb = parse_color(bg)
    return contrast_ratio(fg_rgb, bg_rgb) >= ratio


def is_valid_style(style: Style) -> bool:
    """Check if a style's foreground and background colors have sufficient contrast.

    Args:
        style (Style): The style to check.

    Returns:
        bool: True if the style has sufficient contrast, False otherwise.
    """
    if style.color:
        fg = style.color.get_truecolor()
    else:
        fg = Color.parse("default").get_truecolor()
    if style.bgcolor:
        bg = style.bgcolor.get_truecolor()
    else:
        bg = Color.parse("default").get_truecolor()
    return has_sufficient_contrast(fg, bg)


def adjust_style_for_contrast(style: Style, ratio: float = 4.5) -> Style:
    """Adjust a style's foreground or background color to ensure sufficient contrast."""
    fg = (
        style.color.get_truecolor()
        if style.color
        else Color.parse("default").get_truecolor()
    )
    bg = (
        style.bgcolor.get_truecolor()
        if style.bgcolor
        else Color.parse("default").get_truecolor()
    )

    def clamp(val, minval=0, maxval=255):
        return max(minval, min(maxval, int(val)))

    def adjust_color(fg, bg, ratio, lighten=True):
        # Try to lighten or darken fg until contrast is sufficient
        for step in range(1, 101):
            factor = step / 100.0
            if lighten:
                new_fg = tuple(clamp(c + (255 - c) * factor) for c in fg)
            else:
                new_fg = tuple(clamp(c * (1 - factor)) for c in fg)
            if contrast_ratio(ColorTriplet(*new_fg), ColorTriplet(*bg)) >= ratio:
                return new_fg
        return fg  # fallback

    if has_sufficient_contrast(fg, bg, ratio):
        return style

    # Try both lighten and darken, pick the one that achieves contrast with minimal change
    light_fg = adjust_color(fg, bg, ratio, lighten=True)
    dark_fg = adjust_color(fg, bg, ratio, lighten=False)

    def color_distance(c1, c2):
        return sum(abs(a - b) for a, b in zip(c1, c2))

    if (
        contrast_ratio(ColorTriplet(*light_fg), ColorTriplet(*bg)) >= ratio
        and contrast_ratio(ColorTriplet(*dark_fg), ColorTriplet(*bg)) >= ratio
    ):
        # Both work, pick the closest to original
        new_fg = (
            light_fg
            if color_distance(fg, light_fg) < color_distance(fg, dark_fg)
            else dark_fg
        )
    elif contrast_ratio(ColorTriplet(*light_fg), ColorTriplet(*bg)) >= ratio:
        new_fg = light_fg
    elif contrast_ratio(ColorTriplet(*dark_fg), ColorTriplet(*bg)) >= ratio:
        new_fg = dark_fg
    else:
        new_fg = fg  # fallback

    new_color = Color.from_triplet(ColorTriplet(*new_fg))
    return style + Style(color=new_color)
