"""The default gradient runs from the first color to the last across the span."""

import pytest
from rich.color_triplet import ColorTriplet
from rich.text import Text as RichText

from rich_gradient import AnimatedGradient, Gradient, Markdown, Panel, Table
from rich_gradient.gradient import Gradient as _Gradient

SPAN = 88


def _rgb(style_color) -> tuple[int, int, int]:
    triplet = style_color.get_truecolor()
    return triplet.red, triplet.green, triplet.blue


def _ends(gradient: _Gradient, *, background: bool = False):
    """Return the (first, last) column colors the renderer would use."""
    ramp = gradient._get_gradient_ramp(SPAN)
    attr = "bgcolor" if background else "color"
    first = getattr(ramp.style_at(0, 1, 0.0), attr)
    last = getattr(ramp.style_at(SPAN - 1, 1, 0.0), attr)
    return _rgb(first), _rgb(last)


def _close(actual: tuple[int, int, int], expected: str, tol: int = 0x28) -> bool:
    exp = ColorTriplet(*(int(expected[i : i + 2], 16) for i in (1, 3, 5)))
    return all(abs(a - e) <= tol for a, e in zip(actual, exp))


@pytest.mark.parametrize(
    "colors",
    [
        ["#ff0000", "#0000ff"],
        ["#00ffff", "#ff00ff", "#ffff00"],
        ["#ff0000", "#00ff00", "#0000ff", "#ffff00"],
    ],
)
def test_default_reaches_first_and_last_color(colors: list[str]) -> None:
    """With no repeat_scale, both end colors appear across the span."""
    first, last = _ends(Gradient(RichText("x"), colors=colors))
    assert _close(first, colors[0])
    assert _close(last, colors[-1])


@pytest.mark.parametrize(
    "build",
    [
        lambda c: Markdown("# hi", colors=c),
        lambda c: Panel("hi", colors=c),
        lambda c: Table("a", colors=c),
    ],
)
def test_wrappers_reach_the_end_colors(build) -> None:
    """Markdown, Panel and Table share the same default."""
    colors = ["#00ffff", "#ff00ff", "#ffff00"]
    first, last = _ends(build(colors))
    assert _close(first, colors[0])
    assert _close(last, colors[-1])


def test_markdown_default_no_longer_stretches_four_times() -> None:
    """Markdown used to default to 4.0 and only reached the second color."""
    assert Markdown("x").repeat_scale is None


@pytest.mark.parametrize(("colors", "expected"), [(2, 1.0), (3, 2.0), (4, 2.0)])
def test_derived_scale_follows_stop_count(colors: int, expected: float) -> None:
    """Two colors need no repeat; three or more use the mirrored length."""
    palette = ["#ff0000", "#00ff00", "#0000ff", "#ffff00"][:colors]
    assert Gradient(RichText("x"), colors=palette)._effective_repeat_scale() == expected


def test_explicit_repeat_scale_is_respected() -> None:
    """An explicit value is used as given, with the stops untouched."""
    gradient = Gradient(RichText("x"), colors=["#ff0000", "#0000ff"], repeat_scale=3.0)
    assert gradient._effective_repeat_scale() == 3.0
    foreground, _, scale = gradient._ramp_stops()
    assert len(foreground) == 2
    assert scale == 3.0


def test_background_gradient_reaches_both_ends() -> None:
    """Background stops are mirrored with the foreground so they also reach the ends."""
    gradient = Gradient(
        RichText("x"),
        colors=["#ffffff", "#000000", "#ff0000"],
        bg_colors=["#112233", "#445566", "#778899"],
    )
    first, last = _ends(gradient, background=True)
    assert _close(first, "#112233")
    assert _close(last, "#778899")


def test_two_color_foreground_with_three_color_background() -> None:
    """Mismatched list lengths still share one period and reach every end."""
    gradient = Gradient(
        RichText("x"),
        colors=["#ff0000", "#0000ff"],
        bg_colors=["#112233", "#445566", "#778899"],
    )
    (fg_first, fg_last), (bg_first, bg_last) = (
        _ends(gradient),
        _ends(gradient, background=True),
    )
    assert _close(fg_first, "#ff0000") and _close(fg_last, "#0000ff")
    assert _close(bg_first, "#112233") and _close(bg_last, "#778899")


def test_solid_background_does_not_force_mirroring() -> None:
    """A single background color leaves a two-color foreground unmirrored."""
    gradient = Gradient(
        RichText("x"), colors=["#ff0000", "#0000ff"], bg_colors=["#000000"]
    )
    foreground, _, scale = gradient._ramp_stops()
    assert scale == 1.0
    assert len(foreground) == 2


def test_animated_default_is_unchanged() -> None:
    """Animated gradients keep their explicit default so loops stay seamless."""
    assert AnimatedGradient(["hi"]).repeat_scale == 4.0


def test_ramp_cache_updates_when_colors_change() -> None:
    """Changing the palette recomputes the derived scale."""
    gradient = Gradient(RichText("x"), colors=["#ff0000", "#0000ff"])
    assert gradient._effective_repeat_scale() == 1.0
    gradient.colors = ["#ff0000", "#00ff00", "#0000ff"]
    assert gradient._effective_repeat_scale() == 2.0
    first, last = _ends(gradient)
    assert _close(first, "#ff0000") and _close(last, "#0000ff")
