from __future__ import annotations
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from rich_gradient._colors import COLOR_DATA_DICT
from rich_gradient._colors_by_ import (
    COLORS_BY_RGB,
    COLORS_BY_HEX,
    COLORS_BY_NAME,
    COLORS_BY_ANSI,
    SPECTRUM_COLOR_STRS
)

class ColorData:
    """Class to handle color data.

    This class provides methods to retrieve color information by name, RGB value,
    hex code, or ANSI value. It also includes a method to convert color data to a
    dictionary format.

    Attributes:
        color_dict (Dict[str, Dict[str, str | Tuple[int, int, int] | int]]):
            A dictionary containing color data, where the keys are color names and
            the values are dictionaries with RGB, hex, and ANSI values.

    Methods:
        by_name(name: str) -> Optional[Dict[str, str | Tuple[int, int, int] | int]]:
            Retrieves color data by name.
        by_rgb(rgb: Tuple[int, int, int] | str) -> Optional[Dict[str, str | int]]:
            Retrieves color data by RGB value.
        by_hex(hex_code: str) -> Optional[Dict[str, str | Tuple[int, int, int] | int]]:
            Retrieves color data by hex code.
        by_ansi(ansi: int) -> Optional[Dict[str, Any]]:
            Retrieves color data by ANSI value.
        to_dict(name: str) -> Tuple[str, Dict[str, Any]]:
            Converts color data to a dictionary format.
        find(value: Union[str, Tuple[int, int, int], int]) -> Optional[Dict[str, Any]]:
            Auto-detects the lookup method based on the type of the input value.
    """


    def __init__(self) -> None:
        self.color_dict: Dict[str, Dict[str, str | Tuple[int, int, int] | int]] = (
            COLOR_DATA_DICT
        )

    def by_name(
        self, name: str
    ) -> Optional[Dict[str, str | Tuple[int, int, int] | int]]:
        colors: Optional[Dict[str, str | Tuple[int, int, int] | int]] = (
            self.color_dict.get(name)
        )
        if colors is not None:
            return {
                "hex": colors["hex"],
                "rgb": colors["rgb"],
                "ansi": colors["ansi"],
            }
        raise KeyError(
            f"Color with name {name} not found in color data.",
            {
                "input": {"name": name},
                "function_name": "ColorData.by_name",
            },
        )

    def by_rgb(self, rgb: Tuple[int, int, int] | str) -> Optional[Dict[str, str | int]]:
        if isinstance(rgb, str):
            match = re.match(r"^\((\d+),\s*(\d+),\s*(\d+)\)$", rgb)
            if match:
                r = int(match.group(1))
                g = int(match.group(2))
                b = int(match.group(3))
                if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
                    raise ValueError(
                        f"RGB values must be between 0 and 255. Got: {rgb}"
                    )
                rgb = (r, g, b)
            else:
                raise ValueError(
                    f"Invalid RGB string format: {rgb}. Expected format: '(R, G, B)'"
                )
        color: Optional[Dict[str, str | int]] = COLORS_BY_RGB.get(rgb)
        if color is not None:
            return {
                "name": color["name"],
                "hex": color["hex"],
                "ansi": color["ansi"],
            }
        raise KeyError(
            f"Color with RGB value {rgb} not found in color data.",
            {
                "input": {"rgb": rgb},
                "function_name": "ColorData.by_rgb",
            },
        )

    def by_hex(
        self, hex_code: str
    ) -> Optional[Dict[str, str | Tuple[int, int, int] | int]]:
        if not hex_code.startswith("#"):
            raise ValueError("Hex code must start with '#'")
        length = len(hex_code)
        if length not in [4, 7]:
            raise ValueError(
                f"Hex code `{hex_code}` must be 4 or 7 characters long. Length: {len(hex_code)}"
            )
        else:
            if length == 4:
                hex_code = f"#{hex_code[1:]}{hex_code[1:]}"
            if hex_code not in COLORS_BY_HEX:
                raise KeyError(
                    f"Color with hex code {hex_code} not found in color data.",
                    {
                        "input": {"hex": hex_code},
                        "function_name": "ColorData.by_hex",
                    },
                )
        color: Optional[Dict[str, str | Tuple[int, int, int] | int]] = (
            COLORS_BY_HEX.get(hex_code)
        )
        if color is not None:
            return {
                "name": color["name"],
                "rgb": color["rgb"],
                "ansi": color["ansi"],
            }
        raise KeyError(
            f"Color with hex code {hex_code} not found in color data.",
            {
                "input": {"hex": hex_code},
                "function_name": "ColorData.by_hex",
            },
        )

    def by_ansi(self, ansi: int) -> Optional[Dict[str, Any]]:
        if ansi not in COLORS_BY_ANSI:
            raise KeyError(
                f"Color with ANSI value {ansi} not found in color data.",
                {
                    "input": {"ansi": ansi},
                    "function_name": "ColorData.by_ansi",
                },
            )
        color: Optional[Dict[str, Tuple[int, int, int] | str]] = COLORS_BY_ANSI.get(
            ansi
        )
        if color is not None:
            return {
                "name": color["name"],
                "hex": color["hex"],
                "rgb": color["rgb"],
            }
        raise KeyError(
            f"Color with ANSI value {ansi} not found in color data.",
            {
                "input": {"ansi": ansi},
                "function_name": "ColorData.by_ansi",
            },
        )



    @staticmethod
    def to_dict(name: str) -> Tuple[str, Dict[str, Any]]:
        """Convert color data to a dictionary."""
        return name, {
            "hex": COLOR_DATA_DICT[name]["hex"],
            "rgb": COLOR_DATA_DICT[name]["rgb"],
            "ansi": COLOR_DATA_DICT[name]["ansi"],
        }

    def find(
        self, value: Union[str, Tuple[int, int, int], int]
    ) -> Optional[Dict[str, Any]]:
        """Auto-detect lookup based on value type."""
        if isinstance(value, tuple) and len(value) == 3:
            return self.by_rgb(value)
        elif isinstance(value, str):
            if value.startswith("#"):
                return self.by_hex(value)
            else:
                return self.by_name(value)
        elif isinstance(value, int):
            return self.by_ansi(value)
        return None

    @property
    def COLORS_BY_NAME(self) -> Dict[str, Dict[str, str | Tuple[int, int, int] | int]]:
        """Get a list of all color names."""
        return COLORS_BY_NAME

    @property
    def COLORS_BY_RGB(self) -> Dict[Tuple[int, int, int], Dict[str, str | int]]:
        """Get a list of all color values."""
        return COLORS_BY_RGB

    @property
    def COLOR_BY_HEX(self) -> Dict[str, Dict[str, str | Tuple[int, int, int] | int]]:
        """Get a list of all color names."""
        return COLORS_BY_HEX

    @property
    def COLOR_BY_ANSI(self) -> Dict[int, Dict[str, Tuple[int, int, int] | str]]:
        """Get a list of all color names."""
        return COLORS_BY_ANSI

    @property
    def SPECTRUM_COLOR_STRS(self) -> List[str]:
        """Get a list of all color names in the spectrum."""
        return SPECTRUM_COLOR_STRS

    @classmethod
    def example(cls) -> None:
        """Example usage of the ColorData class."""
        console: Console = Console()
        console.print(COLOR_DATA.by_name("red1"))
        console.print(COLOR_DATA.by_rgb((255, 0, 0)))
        console.print(COLOR_DATA.by_hex("#FF0000"))
        console.print(COLOR_DATA.by_ansi(196))
        console.print(COLOR_DATA.find("red1"))
        console.print(COLOR_DATA.find((255, 0, 0)))
        console.print(COLOR_DATA.find("#FF0000"))


COLOR_DATA = ColorData()

if __name__ == "__main__":
    from typing import Any, Dict, List, Optional, Tuple, Union

    from rich.console import Console
    from rich.style import Style

    # Example usage
    console: Console = Console()
    for color in SPECTRUM_COLOR_STRS:
        console.print(
            f"[{color}] {color} - {COLORS_BY_HEX[color]['name']}",
            style=Style(color=color),
        )
