"""
Parsers for color strings.
These parsers are used to convert color strings into RGB or HSL tuples.

Imports are lazy-loaded to avoid slowing down the import time of the main module.
The parsers are used in the following order:
1. Hex short
2. Hex long
3. RGB
4. HSL
5. RGB v4 style
6. HSL v4 style
"""

import math

__all__ = [
    "_r_255",
    "_r_comma",
    "_r_alpha",
    "_r_h",
    "_r_sl",
    "r_hex_short",
    "r_hex_long",
    "r_rgb",
    "r_hsl",
    "r_rgb_v4_style",
    "r_hsl_v4_style",
    "repeat_colors",
    "rads"
]

# Regex patterns for parsing colors
# these are not compiled here to avoid import slowdown, they'll be compiled the first time they're used, then cached
_r_255 = r"(\d{1,3}(?:\.\d+)?)"
_r_comma = r"\s*,\s*"
_r_alpha = r"(\d(?:\.\d+)?|\.\d+|\d{1,2}%)"
_r_h = r"(-?\d+(?:\.\d+)?|-?\.\d+)(deg|rad|turn)?"
_r_sl = r"(\d{1,3}(?:\.\d+)?)%"
r_hex_short = r"\s*(?:#|0x)?([0-9a-f])([0-9a-f])([0-9a-f])([0-9a-f])?\s*"
r_hex_long = r"\s*(?:#|0x)?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})?\s*"
# CSS3 RGB examples: rgb(0, 0, 0), rgba(0, 0, 0, 0.5), rgba(0, 0, 0, 50%)
r_rgb = rf"\s*rgba?\(\s*{_r_255}{_r_comma}{_r_255}{_r_comma}{_r_255}(?:{_r_comma}{_r_alpha})?\s*\)\s*"
# CSS3 HSL examples: hsl(270, 60%, 50%), hsla(270, 60%, 50%, 0.5), hsla(270, 60%, 50%, 50%)
r_hsl = rf"\s*hsla?\(\s*{_r_h}{_r_comma}{_r_sl}{_r_comma}{_r_sl}(?:{_r_comma}{_r_alpha})?\s*\)\s*"
# CSS4 RGB examples: rgb(0 0 0), rgb(0 0 0 / 0.5), rgb(0 0 0 / 50%), rgba(0 0 0 / 50%)
r_rgb_v4_style = (
    rf"\s*rgba?\(\s*{_r_255}\s+{_r_255}\s+{_r_255}(?:\s*/\s*{_r_alpha})?\s*\)\s*"
)
# CSS4 HSL examples: hsl(270 60% 50%), hsl(270 60% 50% / 0.5), hsl(270 60% 50% / 50%), hsla(270 60% 50% / 50%)
r_hsl_v4_style = (
    rf"\s*hsla?\(\s*{_r_h}\s+{_r_sl}\s+{_r_sl}(?:\s*/\s*{_r_alpha})?\s*\)\s*"
)

# colors where the two hex characters are the same, if all colors match this the short version of hex colors can be used
repeat_colors = {int(c * 2, 16) for c in "0123456789abcdef"}
rads = 2 * math.pi
