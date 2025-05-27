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

# Regex fragment for an RGB channel (0-255)
_r_255: str = r"(\d{1,3}(?:\.\d+)?)"
# Comma with optional surrounding spaces
_r_comma: str = r"\s*,\s*"
# Alpha channel: float (0.0–1.0) or percentage
_r_alpha: str = r"(\d(?:\.\d+)?|\.\d+|\d{1,2}%)"
# Hue value with optional unit: deg, rad, or turn
_r_h: str = r"(-?\d+(?:\.\d+)?|-?\.\d+)(deg|rad|turn)?"
# Saturation/lightness percentage
_r_sl: str = r"(\d{1,3}(?:\.\d+)?)%"

# Short and long hexadecimal notation
r_hex_short: str = r"\s*(?:#|0x)?([0-9a-f])([0-9a-f])([0-9a-f])([0-9a-f])?\s*"
r_hex_long: str = r"\s*(?:#|0x)?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})?\s*"

# CSS3-compatible rgba() and hsla()
r_rgb: str = rf"\s*rgba?\(\s*{_r_255}{_r_comma}{_r_255}{_r_comma}{_r_255}(?:{_r_comma}{_r_alpha})?\s*\)\s*"
r_hsl: str = rf"\s*hsla?\(\s*{_r_h}{_r_comma}{_r_sl}{_r_comma}{_r_sl}(?:{_r_comma}{_r_alpha})?\s*\)\s*"

# CSS4 color syntax with spaces and optional slash
r_rgb_v4_style: str = (
    rf"\s*rgba?\(\s*{_r_255}\s+{_r_255}\s+{_r_255}(?:\s*/\s*{_r_alpha})?\s*\)\s*"
)
r_hsl_v4_style: str = (
    rf"\s*hsla?\(\s*{_r_h}\s+{_r_sl}\s+{_r_sl}(?:\s*/\s*{_r_alpha})?\s*\)\s*"
)

# Precomputed integer values where both hex characters are the same (used for short hex matching)
repeat_colors: set[int] = {int(c * 2, 16) for c in "0123456789abcdef"}

# Constant for 2π (used in radian conversion)
rads: float = 2 * math.pi
