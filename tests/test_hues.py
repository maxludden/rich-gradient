"""``hues`` has a minimum of 2 everywhere it is accepted."""

import pytest

from rich_gradient import (
    AnimatedGradient,
    AnimatedText,
    Columns,
    Gradient,
    Panel,
    Pretty,
    Rule,
    Spectrum,
    Syntax,
    Table,
    Text,
    Tree,
)
from rich_gradient.spectrum import MIN_HUES, validate_hues

BUILDERS = {
    "Spectrum": lambda h: Spectrum(h),
    "Text": lambda h: Text("hi", hues=h),
    "Gradient": lambda h: Gradient("hi", hues=h),
    "Panel": lambda h: Panel("hi", hues=h),
    "Rule": lambda h: Rule("hi", hues=h),
    "Table": lambda h: Table("a", hues=h),
    "Tree": lambda h: Tree("root", hues=h),
    "Columns": lambda h: Columns(["a"], hues=h),
    "Pretty": lambda h: Pretty({"a": 1}, hues=h),
    "Syntax": lambda h: Syntax("x = 1", "python", hues=h),
    "AnimatedGradient": lambda h: AnimatedGradient(["hi"], hues=h),
    "AnimatedText": lambda h: AnimatedText("hi", hues=h),
}


def test_min_hues_is_two() -> None:
    """The shared minimum is 2."""
    assert MIN_HUES == 2


@pytest.mark.parametrize("hues", [-1, 0, 1])
def test_validate_hues_rejects_below_minimum(hues: int) -> None:
    """Values below the minimum raise ValueError."""
    with pytest.raises(ValueError, match="at least 2"):
        validate_hues(hues)


def test_validate_hues_accepts_minimum() -> None:
    """The minimum itself is allowed and returned unchanged."""
    assert validate_hues(2) == 2


@pytest.mark.parametrize("name", BUILDERS)
@pytest.mark.parametrize("hues", [0, 1])
def test_every_renderable_rejects_hues_below_two(name: str, hues: int) -> None:
    """No renderable silently clamps or accepts fewer than two hues."""
    with pytest.raises(ValueError, match="at least 2"):
        BUILDERS[name](hues)


@pytest.mark.parametrize("name", BUILDERS)
def test_every_renderable_accepts_two_hues(name: str) -> None:
    """Two hues is valid for every renderable."""
    BUILDERS[name](2)
