from __future__ import annotations

import re
from typing import Any, List, Tuple, Dict, Optional

from rich_gradient._colors_dict import COLOR_DATA_DICT

COLORS_BY_NAME: Dict[str, Dict[str, str | Tuple[int, int, int] | int]] = COLOR_DATA_DICT

def colors_by_rgb() -> Dict[Tuple[int, int, int], Dict[str, str | int]]:
    """Get a dictionary of colors by their RGB values."""
    COLORS_BY_RGB: Dict[Tuple[int, int, int], Dict[str, str | int]] = {}
    for name, color in COLORS_BY_NAME.items():
        assert isinstance(color["rgb"], tuple), (
            f"Expected rgb to be a tuple, got {type(color['rgb'])}"
        )
        rgb: Tuple[int, int, int] = color["rgb"][0], color["rgb"][1], color["rgb"][2]
        assert isinstance(color["hex"], str), (
            f"Expected hex to be a string, got {type(color['hex'])}"
        )
        hex_code: str = color["hex"]
        _ansi = color["ansi"]
        assert _ansi is None or isinstance(_ansi, int), (
            f"Expected ansi to be an int or None, got {type(_ansi)}"
        )
        ansi: Optional[int] = _ansi
        new_color: Dict[str, str | int] = {"name": name, "hex": hex_code, "ansi": ansi}
        COLORS_BY_RGB[rgb] = new_color
    return COLORS_BY_RGB

COLORS_BY_RGB: Dict[Tuple[int, int, int], Dict[str, str | int]] = colors_by_rgb()

def colors_by_hex() -> Dict[str, Dict[str, str | Tuple[int, int, int] | int]]:
    """Get a dictionary of colors by their hex values."""
    COLORS_BY_HEX: Dict[str, Dict[str, str | Tuple[int, int, int] | int]] = {}
    for name, color in COLORS_BY_NAME.items():
        assert isinstance(color["rgb"], tuple), (
            f"Expected rgb to be a tuple, got {type(color['rgb'])}"
        )
        rgb: Tuple[int, int, int] = color["rgb"]
        assert isinstance(color["hex"], str), (
            f"Expected hex to be a string, got {type(color['hex'])}"
        )
        hex_code: str = color["hex"]
        _ansi = color["ansi"]
        assert isinstance(_ansi, int), f"Expected ansi to be an int, got {type(_ansi)}"
        ansi: int = _ansi
        new_color = {"name": name, "rgb": rgb, "ansi": ansi}
        COLORS_BY_HEX[hex_code] = new_color
    return COLORS_BY_HEX

COLORS_BY_HEX: Dict[str, Dict[str, str | Tuple[int, int, int] | int]] = colors_by_hex()

def colors_by_ansi() -> Dict[int, Dict[str, Tuple[int, int, int] | str]]:
    """Get a dictionary of colors by their ANSI values."""
    COLORS_BY_ANSI: Dict[int, Dict[str, Tuple[int, int, int] | str]] = {}
    for name, color in COLORS_BY_NAME.items():
        if color["ansi"] != -1:
            assert isinstance(color["rgb"], tuple), (
                f"Expected rgb to be a tuple, got {type(color['rgb'])}"
            )
            rgb: Tuple[int, int, int] = color["rgb"]
            assert isinstance(color["hex"], str), (
                f"Expected hex to be a string, got {type(color['hex'])}"
            )
            hex_code: str = color["hex"]
            _ansi = color["ansi"]
            assert isinstance(_ansi, int), (
                f"Expected ansi to be an int, got {type(_ansi)}"
            )
            ansi: int = _ansi
            new_color: Dict[str, str | Tuple[int, int, int]] = {
                "name": name,
                "rgb": rgb,
                "hex": hex_code,
            }
            COLORS_BY_ANSI[ansi] = new_color
        continue
    return COLORS_BY_ANSI

COLORS_BY_ANSI: Dict[int, Dict[str, Tuple[int, int, int] | str]] = colors_by_ansi()

def get_spectrum_colors() -> List[str]:
        """Get a list of all color names in the spectrum."""
        SPECTRUM_COLORS: List[str] = []
        for index, (name, color) in enumerate(COLOR_DATA_DICT.items()):
            if index < 18:
                assert isinstance(color["hex"], str), f"Unexpected type for hex: {type(color['hex'])}"
                SPECTRUM_COLORS.append(color["hex"])
                continue
            if index == 18:
                break
        return SPECTRUM_COLORS

SPECTRUM_COLOR_STRS: List[str] = list(get_spectrum_colors())
