"""Color strings are parsed by Rich first, with rich-color-ext as the fallback."""

import pytest
from rich.color import Color, ColorParseError, ColorType
from rich.color_triplet import ColorTriplet

from rich_gradient import Gradient, Text
from rich_gradient._color_ext import parse_color


@pytest.mark.parametrize("name", ["red", "blue", "green", "yellow", "cyan", "magenta"])
def test_rich_names_keep_rich_meaning(name: str) -> None:
    """Names that Rich defines resolve to Rich's ANSI palette colors."""
    color = parse_color(name)
    assert color == Color.parse(name)
    assert color.type == ColorType.STANDARD


def test_red_is_ansi_red_not_css_red() -> None:
    """``red`` is ANSI red (#800000), not the CSS value #ff0000."""
    assert parse_color("red").get_truecolor() == ColorTriplet(128, 0, 0)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("tomato", ColorTriplet(255, 99, 71)),
        ("aliceblue", ColorTriplet(240, 248, 255)),
        ("  Tomato ", ColorTriplet(255, 99, 71)),
    ],
)
def test_css_names_fall_back_to_rich_color_ext(
    value: str, expected: ColorTriplet
) -> None:
    """Names Rich rejects are resolved through the CSS color map."""
    assert parse_color(value).get_truecolor() == expected


def test_three_digit_hex_is_expanded() -> None:
    """3-digit hex is expanded by the fallback."""
    assert parse_color("#f90").get_truecolor() == ColorTriplet(255, 153, 0)


def test_six_digit_hex_is_handled_by_rich() -> None:
    """6-digit hex goes straight through Rich's parser."""
    assert parse_color("#12ab34").get_truecolor() == ColorTriplet(0x12, 0xAB, 0x34)


@pytest.mark.parametrize("value", ["notacolor", "#12", "#GGG", "reddish", ""])
def test_unparseable_values_raise(value: str) -> None:
    """Strings neither parser understands raise ColorParseError."""
    with pytest.raises(ColorParseError):
        parse_color(value)


def test_gradient_uses_rich_first_then_fallback() -> None:
    """Gradient stops follow the same precedence as parse_color."""
    stops = Gradient._to_color_triplets(["red", "tomato", "#f90"])
    assert stops == [
        ColorTriplet(128, 0, 0),
        ColorTriplet(255, 99, 71),
        ColorTriplet(255, 153, 0),
    ]


def test_text_uses_rich_first_then_fallback() -> None:
    """Text normalizes colors with the same precedence as parse_color."""
    assert Text._normalize_color("red").get_truecolor() == ColorTriplet(128, 0, 0)
    assert Text._normalize_color("tomato").get_truecolor() == ColorTriplet(255, 99, 71)
    assert Text._normalize_color("#f90").get_truecolor() == ColorTriplet(255, 153, 0)
