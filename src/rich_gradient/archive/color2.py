# rich_gradient/colors.py

import json
import re
from typing import Optional
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

# Regular expressions for hex and rgb parsing
_HEX3_RE = re.compile(r'^#?([0-9A-Fa-f])([0-9A-Fa-f])([0-9A-Fa-f])$')
_HEX6_RE = re.compile(r'^#?([0-9A-Fa-f]{6})$')
_RGB_RE = re.compile(
	r'^rgb\(\s*(?P<R>\d{1,3})\s*,\s*(?P<G>\d{1,3})\s*,\s*(?P<B>\d{1,3})\s*\)$'
)

# ──────────────────────────────────────────────────────────────────────────────
# 1) Define Color
# ──────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Color:
	"""Represents a color with a name, hex code, and ANSI code.
	Attributes:
		name (str): The name of the color (lowercase).
		hex (str): The hex code of the color (always stored as "#RRGGBB").
		ansi_code (int): The ANSI code of the color.
	"""

	name: str
	hex: str  # always stored as "#RRGGBB"
	ansi_code: int


	@cached_property
	def rgb_tuple(self) -> tuple[int, int, int]:
		h = self.hex.lstrip("#").upper()
		r = int(h[:2], 16)
		g = int(h[2:4], 16)
		b = int(h[4:6], 16)
		return (r, g, b)

	@cached_property
	def rgb_string(self) -> str:
		r, g, b = self.rgb_tuple
		return f"rgb({r}, {g}, {b})"

	@classmethod
	def parse(cls, raw: str | int) -> Optional["Color"]:
		"""Parse a raw input (name, hex, rgb(...) or ANSI code) into a Color or return None."""
		# delegate to the module‐level parser
		return parse(raw)




# ──────────────────────────────────────────────────────────────────────────────
# 2) Lazy-loaded reverse maps
# ──────────────────────────────────────────────────────────────────────────────
_name_map: dict[str, Color] | None = None
_hex_map: dict[str, Color] | None = None
_rgb_map: dict[tuple[int, int, int], Color] | None = None
_ansi_map: dict[int, Color] | None = None

class ColorMaps:
	"""Lazy‐loaded color maps and parsing logic."""
	def __init__(self):
		self._name_map: dict[str, Color] | None = None
		self._hex_map: dict[str, Color] | None = None
		self._rgb_map: dict[tuple[int, int, int], Color] | None = None
		self._ansi_map: dict[int, Color] | None = None

	def _load(self):
		here = Path(__file__).parent.parent.parent / "css_color.json"
		with open(here, "r", encoding="utf-8") as f:
			raw_data = json.load(f)
		hex_dict = raw_data["hex"]
		rgb_dict = raw_data["rgb"]

		nm_map: dict[str, Color] = {}
		hx_map: dict[str, Color] = {}
		rg_map: dict[tuple[int, int, int], Color] = {}
		an_map: dict[int, Color] = {}

		for name, hex_str in hex_dict.items():
			nm = name.lower()
			hx = hex_str.upper().rjust(7, "#") if not hex_str.startswith("#") else hex_str.upper()
			r, g, b = map(int, rgb_dict[nm].split())
			rgb = (r, g, b)
			# Placeholder ANSI mapping (can be improved with nearest-color match later)
			ac = hash(rgb) % 256
			color_obj = Color(name=nm, hex=hx, ansi_code=ac)
			nm_map[nm] = color_obj
			hx_map[hx] = color_obj
			rg_map[rgb] = color_obj
			an_map[ac] = color_obj

		self._name_map = nm_map
		self._hex_map = hx_map
		self._rgb_map = rg_map
		self._ansi_map = an_map

	def get_maps(self) -> tuple[
		dict[str, Color],
		dict[str, Color],
		dict[tuple[int, int, int], Color],
		dict[int, Color]
	]:
		if self._name_map is None:
			self._load()
		return self._name_map, self._hex_map, self._rgb_map, self._ansi_map  # type: ignore

	def parse(self, raw: str | int) -> Color | None:
		name_map, hex_map, rgb_map, ansi_map = self.get_maps()

		# 1) ANSI code as int or digit-string
		if isinstance(raw, int):
			return ansi_map.get(raw)
		raw_s = str(raw).strip()
		if raw_s.isdigit():
			return ansi_map.get(int(raw_s))

		# 2) 3-digit hex
		if m := _HEX3_RE.match(raw_s):
			r2, g2, b2 = m.group(1) * 2, m.group(2) * 2, m.group(3) * 2
			normalized = f"#{r2.upper()}{g2.upper()}{b2.upper()}"
			return hex_map.get(normalized)

		# 3) 6-digit hex
		if m := _HEX6_RE.match(raw_s):
			normalized = f"#{m.group(1).upper()}"
			return hex_map.get(normalized)

		# 4) rgb(R, G, B)
		if m := _RGB_RE.match(raw_s):
			r, g, b = int(m.group("R")), int(m.group("G")), int(m.group("B"))
			if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
				return rgb_map.get((r, g, b))
			return None

		# 5) name
		return name_map.get(raw_s.lower())

# module‐level singleton
_color_maps = ColorMaps()

def get_color_maps():
	"""Return (name_map, hex_map, rgb_map, ansi_map)."""
	return _color_maps.get_maps()

def parse(raw: str | int) -> Color | None:
	"""Delegate to ColorMaps.parse."""
	return _color_maps.parse(raw)

def example():
	"""Generate a rich table with all of the colors with a sample of the color, name, hex code, and RGB code printed in their own color."""
	from rich.console import Console
	from rich.table import Table
	from rich.text import Text
	from rich.columns import Columns
	from rich.color import Color as RichColor
	console = Console()
	rich_table: Table = Table(title=Text("Rich Color Samples", style="bold white"))
	css_table: Table = Table(title=Text("CSS Color Samples", style="bold white"))
	for table in (rich_table, css_table):
		table.add_column(Text("Sample", style="bold white"), justify="center")
		table.add_column(Text("Name", style="bold white", justify="center"), justify="right")
		table.add_column(Text("Hex Code", style="bold white", justify="center"), justify="right")
		table.add_column(Text("RGB Code", style="bold white", justify="center"), justify="left")

	name_map, hex_map, rgb_map, ansi_map = get_color_maps()

	for index, color in enumerate(name_map.values()):
		# Name, hex, and rgb printed in their actual color via hex tag
		sample = f"[bold {color.hex}]██████████[/]"
		name_col = f"[bold {color.hex}]{color.name}[/]"
		hex_col = Text(f" {color.hex} ", style=f"bold on {color.hex}",justify="full", no_wrap=True)
		# hex_col = f"[bold  on {color.hex}] {color.hex} [/]"
		rgb_col =Text(f" {color.rgb_string} ", style=f"bold {color.hex}",no_wrap=True)
		if index < 148:
			css_table.add_row(sample, name_col, hex_col, rgb_col)
		else:
			rich_table.add_row(sample, name_col, hex_col, rgb_col)

	console.print(Columns([css_table, rich_table], expand=True, equal=True))

if __name__ == "__main__":
	example()
