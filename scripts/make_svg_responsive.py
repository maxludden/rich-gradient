# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "loguru>=0.7.3",
#     "rich>=13.0.0",
#     "typer>=0.12.0",
# ]
# ///
"""Make SVG images respond to the viewer's light/dark color scheme.

The script rewrites near-white and near-black colors in an SVG so the image
stays legible on both light and dark pages. Original colors are left in place;
the swapped colors are applied through ``@media (prefers-color-scheme: ...)``
rules in a ``<style>`` element appended to the document, so the browser picks
the right palette at render time.

How colors are swapped depends on whether the SVG paints its own background
(a "canvas": the root ``<svg>`` ``background`` style or a ``<rect>`` covering
nearly the whole viewBox, like the window frame in Rich's ``save_svg`` output):

* ``split`` (no canvas, i.e. a transparent image): in light mode near-white
  becomes the dark color (``#111``); in dark mode near-black becomes the light
  color (``#eee``). Each color only changes when it would vanish.
* ``light`` (dark canvas): the whole image flips in light mode. Near-white
  becomes ``#111`` and near-black, canvas included, becomes ``#eee``.
* ``dark`` (light canvas): the whole image flips in dark mode, canvas included.

``auto`` (the default) picks one of these per file from the canvas color.
A near-white *canvas* is never darkened in ``split`` or ``light`` mode.

Output is written next to each input as ``<name>-responsive.svg`` (or into
``--output-dir``). The rest of the file is preserved byte for byte.

Usage::

    uv run scripts/make_svg_responsive.py docs/img/getting_started.svg
    uv run scripts/make_svg_responsive.py docs/img --output-dir build/svg
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

console = Console()
app = typer.Typer(add_completion=False, help=__doc__.split("\n\n")[0] if __doc__ else None)

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #

#: Presentation attributes / CSS properties whose value is a single color.
COLOR_PROPERTIES: tuple[str, ...] = (
    "fill",
    "stroke",
    "stop-color",
    "flood-color",
    "lighting-color",
    "color",
    "background-color",
    "background",
)

#: Properties that paint a background (only these can be "the canvas").
BACKGROUND_PROPERTIES: frozenset[str] = frozenset({"fill", "background", "background-color"})

#: Named colors close enough to white/black to be worth handling.
NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "white": (255, 255, 255),
    "snow": (255, 250, 250),
    "ivory": (255, 255, 240),
    "ghostwhite": (248, 248, 255),
    "floralwhite": (255, 250, 240),
    "whitesmoke": (245, 245, 245),
    "black": (0, 0, 0),
}

#: Prefix for the classes this script adds to elements.
CLASS_PREFIX = "rsvg"

#: Marker comment so re-running on an output file is a no-op.
MARKER = "<!-- made light/dark responsive by make_svg_responsive.py -->"

# Regions the tag rewriter must not touch, and <style> blocks to analyse.
_PROTECTED_RE = re.compile(
    r"<!--.*?-->|<!\[CDATA\[.*?\]\]>|<script\b.*?</script\s*>"
    r"|(?P<style><style\b[^>]*>)(?P<css>.*?)</style\s*>",
    re.DOTALL | re.IGNORECASE,
)
_TAG_RE = re.compile(r"<(?P<name>[A-Za-z][\w:.-]*)(?P<attrs>(?:\s[^<>]*?)?)(?P<close>/?)>")
_ATTR_RE = re.compile(r"(?P<name>[\w:.-]+)\s*=\s*(?P<q>[\"'])(?P<value>.*?)(?P=q)", re.DOTALL)
_HEX_RE = re.compile(r"^#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$", re.IGNORECASE)
_RGB_RE = re.compile(r"^rgba?\(\s*([^)]*)\)$", re.IGNORECASE)
_NUMBER_RE = re.compile(r"^\s*(-?[\d.]+)\s*(%?)\s*$")


# --------------------------------------------------------------------------- #
# Data types
# --------------------------------------------------------------------------- #


class Scheme(str, Enum):
    """How a file's colors are swapped (see the module docstring)."""

    AUTO = "auto"
    SPLIT = "split"
    LIGHT = "light"
    DARK = "dark"


@dataclass(frozen=True)
class RGBA:
    """A parsed color with 0-255 channels and a 0-1 alpha.

    Attributes:
        r: Red channel.
        g: Green channel.
        b: Blue channel.
        a: Alpha, 1.0 when the source color had none.
        has_alpha: Whether the source spelled out an alpha component, so the
            replacement keeps the same form.
    """

    r: int
    g: int
    b: int
    a: float = 1.0
    has_alpha: bool = False

    @property
    def luminance(self) -> float:
        """Return the WCAG relative luminance in the range 0-1."""

        def channel(value: int) -> float:
            c = value / 255
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

        return 0.2126 * channel(self.r) + 0.7152 * channel(self.g) + 0.0722 * channel(self.b)


@dataclass(frozen=True)
class Thresholds:
    """Limits that decide whether a color counts as near-white or near-black.

    Attributes:
        white_min: Every channel must be at least this for near-white.
        black_max: Every channel must be at most this for near-black.
        max_chroma: Max spread between channels, so tinted colors are skipped.
    """

    white_min: int = 224
    black_max: int = 48
    max_chroma: int = 32

    def classify(self, color: RGBA) -> str | None:
        """Return ``"white"``, ``"black"`` or ``None`` for ``color``.

        Args:
            color: The color to test.

        Returns:
            The extreme the color is close to, or ``None`` if it is neither.
        """
        channels = (color.r, color.g, color.b)
        if max(channels) - min(channels) > self.max_chroma:
            return None
        if min(channels) >= self.white_min:
            return "white"
        if max(channels) <= self.black_max:
            return "black"
        return None


@dataclass
class Overrides:
    """CSS override rules collected while scanning one SVG.

    Attributes:
        rules: Media query -> list of ``selector { declaration }`` strings.
        swapped: Count of colors scheduled for swapping, for reporting.
    """

    rules: dict[str, list[str]] = field(default_factory=dict)
    swapped: int = 0

    def add(self, media: str, rule: str) -> None:
        """Record ``rule`` under ``media`` once, keeping insertion order.

        Args:
            media: The media query, e.g. ``(prefers-color-scheme: light)``.
            rule: A complete CSS rule.
        """
        bucket = self.rules.setdefault(media, [])
        if rule not in bucket:
            bucket.append(rule)


@dataclass(frozen=True)
class Plan:
    """What to swap, in which color scheme, for one file.

    Attributes:
        scheme: The resolved (non-auto) scheme.
        light_color: Replacement for near-white colors.
        dark_color: Replacement for near-black colors.
        thresholds: Near-white / near-black limits.
    """

    scheme: Scheme
    light_color: RGBA
    dark_color: RGBA
    thresholds: Thresholds

    def target(self, kind: str, is_background: bool) -> tuple[str, RGBA] | None:
        """Return the media query and replacement for a matched color.

        Args:
            kind: ``"white"`` or ``"black"`` as returned by ``Thresholds.classify``.
            is_background: Whether the color paints the canvas.

        Returns:
            ``(media_query, replacement)`` or ``None`` to leave the color alone.
        """
        light_query = "(prefers-color-scheme: light)"
        dark_query = "(prefers-color-scheme: dark)"
        if kind == "white":
            # A white canvas only flips when the whole image flips to dark.
            if self.scheme is Scheme.DARK:
                return dark_query, self.dark_color
            if is_background:
                return None
            return light_query, self.dark_color
        # kind == "black"
        if self.scheme is Scheme.LIGHT:
            return light_query, self.light_color
        # Black content becomes light in dark mode, both when the whole image
        # flips (``dark``) and when it is transparent (``split``).
        return dark_query, self.light_color


# --------------------------------------------------------------------------- #
# Color helpers
# --------------------------------------------------------------------------- #


def parse_color(value: str) -> RGBA | None:
    """Parse a CSS/SVG color string.

    Supports ``#rgb``, ``#rgba``, ``#rrggbb``, ``#rrggbbaa``, ``rgb()``/``rgba()``
    (comma or space separated, numbers or percentages) and a few named colors.

    Args:
        value: The raw color, optionally followed by ``!important``.

    Returns:
        The parsed color, or ``None`` for anything else (gradients, ``url()``,
        ``none``, ``currentColor``...).
    """
    text = value.replace("!important", "").strip().lower()
    if text in NAMED_COLORS:
        return RGBA(*NAMED_COLORS[text])
    if hex_match := _HEX_RE.match(text):
        digits = hex_match.group(1)
        if len(digits) in (3, 4):
            digits = "".join(ch * 2 for ch in digits)
        r, g, b = (int(digits[i : i + 2], 16) for i in (0, 2, 4))
        if len(digits) == 8:
            return RGBA(r, g, b, round(int(digits[6:8], 16) / 255, 3), True)
        return RGBA(r, g, b)
    if rgb_match := _RGB_RE.match(text):
        parts = [p for p in re.split(r"[\s,/]+", rgb_match.group(1)) if p]
        if len(parts) not in (3, 4):
            return None
        values: list[float] = []
        for index, part in enumerate(parts):
            number = _NUMBER_RE.match(part)
            if not number:
                return None
            amount, percent = float(number.group(1)), number.group(2)
            if index < 3:
                values.append(amount * 2.55 if percent else amount)
            else:
                values.append(amount / 100 if percent else amount)
        r, g, b = (max(0, min(255, round(v))) for v in values[:3])
        if len(values) == 4:
            return RGBA(r, g, b, max(0.0, min(1.0, values[3])), True)
        return RGBA(r, g, b)
    return None


def format_color(color: RGBA, alpha_from: RGBA) -> str:
    """Render ``color`` as CSS, carrying over the alpha of the color it replaces.

    Args:
        color: The replacement color (its own alpha is ignored).
        alpha_from: The original color whose alpha should be kept.

    Returns:
        ``#rrggbb`` when the original had no alpha, otherwise ``rgba(...)``.
    """
    if alpha_from.has_alpha and alpha_from.a < 1:
        return f"rgba({color.r},{color.g},{color.b},{alpha_from.a:g})"
    return f"#{color.r:02x}{color.g:02x}{color.b:02x}"


# --------------------------------------------------------------------------- #
# SVG scanning helpers
# --------------------------------------------------------------------------- #


def parse_attrs(attr_text: str) -> dict[str, str]:
    """Parse the attributes of a start tag.

    Args:
        attr_text: Everything between the tag name and ``>``.

    Returns:
        Attribute names (lower-cased) mapped to their values.
    """
    return {m.group("name").lower(): m.group("value") for m in _ATTR_RE.finditer(attr_text)}


def parse_style(style: str) -> list[tuple[str, str]]:
    """Split a CSS declaration block into ``(property, value)`` pairs.

    Args:
        style: Declarations such as ``"fill: #fff; stroke: none"``.

    Returns:
        Lower-cased property names with stripped values, in source order.
    """
    pairs: list[tuple[str, str]] = []
    for declaration in style.split(";"):
        if ":" in declaration:
            prop, value = declaration.split(":", 1)
            pairs.append((prop.strip().lower(), value.strip()))
    return pairs


def _length(value: str | None, reference: float) -> float | None:
    """Convert an SVG length (number, ``px`` or ``%``) into user units.

    Args:
        value: The attribute value, or ``None`` if absent.
        reference: The length that ``100%`` corresponds to.

    Returns:
        The length, or ``None`` if it cannot be interpreted.
    """
    if value is None:
        return None
    text = value.strip().lower().removesuffix("px")
    try:
        if text.endswith("%"):
            return float(text[:-1]) / 100 * reference
        return float(text)
    except ValueError:
        return None


def viewport_size(root_attrs: dict[str, str]) -> tuple[float, float] | None:
    """Return the drawing area size from the root ``viewBox`` or width/height.

    Args:
        root_attrs: Attributes of the root ``<svg>`` element.

    Returns:
        ``(width, height)``, or ``None`` if the size is unknown.
    """
    if view_box := root_attrs.get("viewbox"):
        parts = re.split(r"[\s,]+", view_box.strip())
        if len(parts) == 4:
            try:
                return float(parts[2]), float(parts[3])
            except ValueError:
                pass
    width = _length(root_attrs.get("width"), 0)
    height = _length(root_attrs.get("height"), 0)
    if width and height:
        return width, height
    return None


def is_canvas_rect(attrs: dict[str, str], size: tuple[float, float] | None) -> bool:
    """Decide whether a ``<rect>`` paints (nearly) the whole image.

    Args:
        attrs: The rect's attributes.
        size: The viewport size from :func:`viewport_size`.

    Returns:
        ``True`` if the rect covers at least 90% of the viewport area.
    """
    if attrs.get("width", "").strip() == "100%" and attrs.get("height", "").strip() == "100%":
        return True
    if size is None:
        return False
    width = _length(attrs.get("width"), size[0])
    height = _length(attrs.get("height"), size[1])
    if not width or not height:
        return False
    return width * height >= 0.9 * size[0] * size[1]


def element_fill(attrs: dict[str, str]) -> str | None:
    """Return the fill/background color an element sets for itself.

    Args:
        attrs: The element's attributes.

    Returns:
        The raw color string from ``style`` or the ``fill`` attribute, if any.
    """
    for prop, value in reversed(parse_style(attrs.get("style", ""))):
        if prop in BACKGROUND_PROPERTIES:
            return value
    return attrs.get("fill")


def find_canvas(svg: str) -> RGBA | None:
    """Find the color the SVG paints behind everything else.

    Looks at the root ``<svg>`` style and then at the first full-size ``<rect>``.

    Args:
        svg: The SVG document text.

    Returns:
        The canvas color, or ``None`` for a transparent image.
    """
    masked = _PROTECTED_RE.sub(lambda m: " " * len(m.group(0)), svg)
    root_match = re.search(r"<svg\b([^>]*)>", masked, re.IGNORECASE)
    if not root_match:
        return None
    root_attrs = parse_attrs(root_match.group(1))
    for prop, value in parse_style(root_attrs.get("style", "")):
        if prop in ("background", "background-color") and (color := parse_color(value)):
            return color
    size = viewport_size(root_attrs)
    for tag in _TAG_RE.finditer(masked, root_match.end()):
        if tag.group("name").lower() != "rect":
            continue
        attrs = parse_attrs(tag.group("attrs"))
        if is_canvas_rect(attrs, size) and (fill := element_fill(attrs)):
            if color := parse_color(fill):
                return color
    return None


def resolve_scheme(requested: Scheme, canvas: RGBA | None) -> Scheme:
    """Turn ``auto`` into a concrete scheme based on the canvas color.

    Args:
        requested: The scheme from the command line.
        canvas: The canvas color, or ``None`` for a transparent image.

    Returns:
        ``requested`` unless it is ``auto``; then ``split`` without a canvas,
        ``light`` for a dark canvas and ``dark`` for a light one.
    """
    if requested is not Scheme.AUTO:
        return requested
    if canvas is None:
        return Scheme.SPLIT
    return Scheme.DARK if canvas.luminance > 0.5 else Scheme.LIGHT


# --------------------------------------------------------------------------- #
# Rewriting
# --------------------------------------------------------------------------- #


def class_name(prop: str, kind: str, color: RGBA, important: bool) -> str:
    """Build the class added to an element for one swapped color.

    Args:
        prop: The color property, e.g. ``fill``.
        kind: ``"white"`` or ``"black"``.
        color: The original color (its alpha is part of the name).
        important: Whether the override must use ``!important``.

    Returns:
        A class name such as ``rsvg-fill-white`` or ``rsvg-stroke-white-a35-i``.
    """
    name = f"{CLASS_PREFIX}-{prop}-{kind}"
    if color.has_alpha and color.a < 1:
        name += f"-a{round(color.a * 100)}"
    return name + ("-i" if important else "")


def collect_css_overrides(css: str, plan: Plan, overrides: Overrides) -> None:
    """Add overrides for color declarations in a ``<style>`` block.

    Only plain top-level rules are considered; ``@font-face``, ``@media`` and
    other at-rules are skipped. Overrides reuse the original selector with
    ``!important`` so they win regardless of specificity.

    Args:
        css: The contents of the ``<style>`` element.
        plan: The swap plan for this file.
        overrides: Collector the new rules are added to.
    """
    text = re.sub(r"/\*.*?\*/", " ", css, flags=re.DOTALL)
    text = text.replace("<![CDATA[", " ").replace("]]>", " ")
    position = 0
    while (open_brace := text.find("{", position)) != -1:
        selector = text[position:open_brace].strip()
        # Find the matching closing brace, allowing nested blocks.
        depth, cursor = 1, open_brace + 1
        while cursor < len(text) and depth:
            depth += {"{": 1, "}": -1}.get(text[cursor], 0)
            cursor += 1
        body = text[open_brace + 1 : cursor - 1]
        position = cursor
        if not selector or selector.startswith("@"):
            continue
        for prop, value in parse_style(body):
            if prop not in COLOR_PROPERTIES or not (color := parse_color(value)):
                continue
            if not (kind := plan.thresholds.classify(color)):
                continue
            is_background = prop in ("background", "background-color")
            if not (target := plan.target(kind, is_background)):
                continue
            media, replacement = target
            overrides.add(media, f"{selector} {{ {prop}: {format_color(replacement, color)} !important; }}")
            overrides.swapped += 1


def rewrite_tag(
    tag: re.Match[str], plan: Plan, canvas_seen: list[bool], size: tuple[float, float] | None, overrides: Overrides
) -> str:
    """Add swap classes to one start tag and record the matching overrides.

    Args:
        tag: A match of ``_TAG_RE``.
        plan: The swap plan for this file.
        canvas_seen: One-item list flagging whether the canvas rect was found,
            so only the first full-size rect is treated as background.
        size: The viewport size.
        overrides: Collector the new rules are added to.

    Returns:
        The tag text, with a ``class`` attribute added or extended if needed.
    """
    name = tag.group("name").lower()
    attr_text = tag.group("attrs")
    attrs = parse_attrs(attr_text)

    is_canvas = False
    if name == "svg":
        is_canvas = True  # Root background style is the canvas.
    elif name == "rect" and not canvas_seen[0] and is_canvas_rect(attrs, size):
        is_canvas = canvas_seen[0] = True

    # (property, raw value, from inline style?) for every color on the element.
    candidates: list[tuple[str, str, bool]] = [(p, attrs[p], False) for p in COLOR_PROPERTIES if p in attrs]
    candidates += [(p, v, True) for p, v in parse_style(attrs.get("style", "")) if p in COLOR_PROPERTIES]

    new_classes: list[str] = []
    for prop, value, inline in candidates:
        if not (color := parse_color(value)) or not (kind := plan.thresholds.classify(color)):
            continue
        is_background = is_canvas and prop in BACKGROUND_PROPERTIES
        if not (target := plan.target(kind, is_background)):
            continue
        media, replacement = target
        cls = class_name(prop, kind, color, inline)
        flag = " !important" if inline else ""
        overrides.add(media, f".{cls} {{ {prop}: {format_color(replacement, color)}{flag}; }}")
        overrides.swapped += 1
        if cls not in new_classes:
            new_classes.append(cls)

    if not new_classes:
        return tag.group(0)
    class_match = re.search(r"(\sclass\s*=\s*)([\"'])(.*?)\2", attr_text, re.DOTALL)
    if class_match:
        merged = " ".join([class_match.group(3).strip(), *new_classes]).strip()
        attr_text = (
            attr_text[: class_match.start()]
            + f"{class_match.group(1)}{class_match.group(2)}{merged}{class_match.group(2)}"
            + attr_text[class_match.end() :]
        )
    else:
        trailing = attr_text[len(attr_text.rstrip()) :]  # Keep e.g. the space before "/>".
        attr_text = attr_text.rstrip() + f' class="{" ".join(new_classes)}"' + trailing
    return f"<{tag.group('name')}{attr_text}{tag.group('close')}>"


def build_style(overrides: Overrides) -> str:
    """Render collected overrides as a ``<style>`` element.

    Args:
        overrides: The rules gathered for one file.

    Returns:
        The style element text (with a leading newline), or ``""`` if empty.
    """
    if not overrides.rules:
        return ""
    blocks = []
    for media, rules in overrides.rules.items():
        body = "\n".join(f"        {rule}" for rule in rules)
        blocks.append(f"    @media {media} {{\n{body}\n    }}")
    return f"\n{MARKER}\n<style>\n" + "\n".join(blocks) + "\n</style>\n"


def make_responsive(
    svg: str, requested: Scheme, light_color: RGBA, dark_color: RGBA, thresholds: Thresholds
) -> tuple[str, Scheme, int]:
    """Return a light/dark responsive version of an SVG document.

    Args:
        svg: The SVG document text.
        requested: The scheme to use, or ``auto`` to detect it.
        light_color: Replacement for near-black colors.
        dark_color: Replacement for near-white colors.
        thresholds: Near-white / near-black limits.

    Returns:
        ``(new_svg, resolved_scheme, swapped_count)``. ``new_svg`` equals the
        input when nothing needed swapping.

    Raises:
        ValueError: If the text has no ``<svg>`` root or was already processed.
    """
    if MARKER in svg:
        raise ValueError("already processed by this script")
    if not re.search(r"<svg\b", svg, re.IGNORECASE):
        raise ValueError("no <svg> element found")

    canvas = find_canvas(svg)
    plan = Plan(resolve_scheme(requested, canvas), light_color, dark_color, thresholds)
    overrides = Overrides()

    masked = _PROTECTED_RE.sub(lambda m: " " * len(m.group(0)), svg)
    root = re.search(r"<svg\b([^>]*)>", masked, re.IGNORECASE)
    size = viewport_size(parse_attrs(root.group(1))) if root else None
    canvas_seen = [False]

    # Rewrite tags outside protected regions; analyse <style> contents.
    pieces: list[str] = []
    cursor = 0
    for region in _PROTECTED_RE.finditer(svg):
        pieces.append(
            _TAG_RE.sub(lambda t: rewrite_tag(t, plan, canvas_seen, size, overrides), svg[cursor : region.start()])
        )
        if region.group("css") is not None:
            collect_css_overrides(region.group("css"), plan, overrides)
        pieces.append(region.group(0))
        cursor = region.end()
    pieces.append(_TAG_RE.sub(lambda t: rewrite_tag(t, plan, canvas_seen, size, overrides), svg[cursor:]))
    result = "".join(pieces)

    style = build_style(overrides)
    if style:
        close = result.lower().rfind("</svg")
        result = result[:close] + style + result[close:]
    return result, plan.scheme, overrides.swapped


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def gather_inputs(paths: list[Path], suffix: str) -> list[Path]:
    """Expand directories into their ``*.svg`` files and drop previous outputs.

    Args:
        paths: Files and/or directories from the command line.
        suffix: The output suffix; files already ending in it are skipped.

    Returns:
        Sorted, de-duplicated SVG files to convert.
    """
    found: set[Path] = set()
    for path in paths:
        if path.is_dir():
            found.update(path.glob("*.svg"))
        elif path.suffix.lower() == ".svg":
            found.add(path)
        else:
            logger.warning("Skipping {} (not an .svg file or directory)", path)
    outputs = {p for p in found if p.stem.endswith(suffix)}
    for path in sorted(outputs):
        logger.warning("Skipping {} (already ends with {!r})", path, suffix)
    return sorted(found - outputs)


def _color_option(value: str) -> RGBA:
    """Parse a color passed on the command line.

    Args:
        value: The color string.

    Returns:
        The parsed color.

    Raises:
        typer.BadParameter: If the color cannot be parsed.
    """
    color = parse_color(value)
    if color is None:
        raise typer.BadParameter(f"not a color: {value!r}")
    return color


@app.command()
def main(
    paths: Annotated[list[Path], typer.Argument(exists=True, help="SVG files or directories of SVGs.")],
    output_dir: Annotated[
        Path | None, typer.Option("--output-dir", "-o", help="Write outputs here instead of next to each input.")
    ] = None,
    suffix: Annotated[str, typer.Option(help="Appended to each output file name.")] = "-responsive",
    scheme: Annotated[
        Scheme, typer.Option(help="Swap strategy; 'auto' picks one from the canvas color.")
    ] = Scheme.AUTO,
    dark: Annotated[str, typer.Option(help="Color that replaces near-white.")] = "#111111",
    light: Annotated[str, typer.Option(help="Color that replaces near-black.")] = "#eeeeee",
    white_min: Annotated[int, typer.Option(min=0, max=255, help="Min channel value counted as near-white.")] = 224,
    black_max: Annotated[int, typer.Option(min=0, max=255, help="Max channel value counted as near-black.")] = 48,
    max_chroma: Annotated[
        int, typer.Option(min=0, max=255, help="Max channel spread; more saturated colors are left alone.")
    ] = 32,
) -> None:
    """Write a ``<name><suffix>.svg`` light/dark responsive copy of each SVG.

    Args:
        paths: SVG files or directories containing SVGs.
        output_dir: Optional directory for outputs (created if missing).
        suffix: Text appended to each output file's stem.
        scheme: Swap strategy, see the module docstring.
        dark: Replacement for near-white colors.
        light: Replacement for near-black colors.
        white_min: Minimum channel value for near-white.
        black_max: Maximum channel value for near-black.
        max_chroma: Maximum channel spread for either extreme.
    """
    thresholds = Thresholds(white_min=white_min, black_max=black_max, max_chroma=max_chroma)
    dark_color, light_color = _color_option(dark), _color_option(light)
    inputs = gather_inputs(paths, suffix)
    if not inputs:
        logger.error("No SVG files to convert.")
        raise typer.Exit(1)
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)

    table = Table("Input", "Output", "Scheme", "Swaps", title="make_svg_responsive")
    table.columns[0].overflow = table.columns[1].overflow = "fold"
    failures = 0
    for source in inputs:
        target = (output_dir or source.parent) / f"{source.stem}{suffix}{source.suffix}"
        try:
            text = source.read_text(encoding="utf-8")
            result, resolved, swapped = make_responsive(text, scheme, light_color, dark_color, thresholds)
        except (OSError, UnicodeDecodeError, ValueError) as error:
            logger.error("{}: {}", source, error)
            failures += 1
            continue
        target.write_text(result, encoding="utf-8")
        table.add_row(str(source), str(target), resolved.value, str(swapped))
    console.print(table)
    if failures:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
