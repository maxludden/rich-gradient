"""
Test suite for Text class covering initialization, color parsing, interpolation, gradient application, and property setters.
"""

import pytest
from rich.color import Color
from rich.style import Style
from rich.text import Text as RichText

from rich_gradient.text import Text


# Helper for color equality (Color.__eq__ is not always implemented)
def color_eq(c1, c2):
    """
    Helper to compare two Color objects by their truecolor value.
    """
    return c1.get_truecolor() == c2.get_truecolor()


@pytest.mark.parametrize(
    "text,colors,rainbow,hues,style,justify,overflow,no_wrap,end,tab_size,markup,expected_plain,expected_colors_len",
    [
        # Simple text, 2 colors, no rainbow
        pytest.param(
            "Hello",
            ["#f00", "#0f0"],
            False,
            5,
            "",
            "default",
            "fold",
            False,
            "\n",
            4,
            True,
            "Hello",
            2,
            id="simple-2colors",
        ),
        # Rainbow, hues ignored, colors ignored
        pytest.param(
            "World",
            None,
            True,
            7,
            "",
            "center",
            "ellipsis",
            True,
            "",
            2,
            False,
            "World",
            17,
            id="rainbow",
        ),
        # No colors, hues=3
        pytest.param(
            "abc",
            None,
            False,
            3,
            "bold",
            "right",
            "crop",
            False,
            "\n",
            8,
            True,
            "abc",
            3,
            id="no-colors-hues3",
        ),
        # One color only
        pytest.param(
            "X",
            ["#123456"],
            False,
            5,
            "",
            "left",
            "fold",
            False,
            "\n",
            4,
            True,
            "X",
            1,
            id="one-color",
        ),
        # Empty text, colors provided
        pytest.param(
            "",
            ["#fff", "#000"],
            False,
            5,
            "",
            "default",
            "fold",
            False,
            "\n",
            4,
            True,
            "",
            2,
            id="empty-text",
        ),
        # Empty text, no colors
        pytest.param(
            "",
            None,
            False,
            2,
            "",
            "default",
            "fold",
            False,
            "\n",
            4,
            True,
            "",
            2,
            id="empty-text-no-colors",
        ),
        # Markup parsing
        pytest.param(
            "[bold]B[/bold]",
            ["#f00", "#00f"],
            False,
            5,
            "",
            "default",
            "fold",
            False,
            "\n",
            4,
            True,
            "B",
            2,
            id="markup",
        ),
    ],
)
def test_text_init_and_properties(
    text,
    colors,
    rainbow,
    hues,
    style,
    justify,
    overflow,
    no_wrap,
    end,
    tab_size,
    markup,
    expected_plain,
    expected_colors_len,
):
    """
    Test Text initialization and property values for various input combinations.
    """
    # Act
    t = Text(
        text=text,
        colors=colors,
        rainbow=rainbow,
        hues=hues,
        style=style,
        justify=justify,
        overflow=overflow,
        no_wrap=no_wrap,
        end=end,
        tab_size=tab_size,
        markup=markup,
    )

    # Assert
    assert t.plain == expected_plain
    assert isinstance(t, RichText)
    assert isinstance(t.colors, list)
    assert len(t.colors) == expected_colors_len
    assert t.justify == justify
    assert t.overflow == overflow
    assert t.no_wrap == no_wrap
    assert t.end == end
    assert t.tab_size == tab_size


@pytest.mark.parametrize(
    "input_colors,hues,rainbow,expected_len,expected_type,case_id",
    [
        (["#f00", "#0f0"], 5, False, 2, Color, "hex-strings"),
        ([Color.parse("#f00"), Color.parse("#0f0")], 5, False, 2, Color, "color-objs"),
        ([], 4, False, 4, Color, "empty-list-hues4"),
        (None, 6, False, 6, Color, "none-hues6"),
        (None, 18, True, 17, Color, "rainbow-17"),
        (["red", "blue"], 5, False, 2, Color, "css-names"),
        (["#f00"], 5, False, 1, Color, "single-color"),
    ],
)
def test_parse_colors(
    input_colors, hues, rainbow, expected_len, expected_type, case_id
):
    """
    Test Text.parse_colors for various input color formats and rainbow mode.
    """
    # Act
    result = Text.parse_colors(colors=input_colors, hues=hues, rainbow=rainbow)

    # Assert
    assert isinstance(result, list)
    assert len(result) == expected_len
    assert all(isinstance(c, expected_type) for c in result)


@pytest.mark.parametrize(
    "plain,colors,expected,case_id",
    [
        # 2 colors, 5 chars
        ("abcde", [Color.parse("#f00"), Color.parse("#0f0")], 5, "2colors-5chars"),
        # 1 color, 3 chars
        ("xyz", [Color.parse("#123456")], 3, "1color-3chars"),
        # 3 colors, 4 chars
        (
            "test",
            [Color.parse("#f00"), Color.parse("#0f0"), Color.parse("#00f")],
            4,
            "3colors-4chars",
        ),
    ],
)
def test_interpolate_colors_non_empty(plain, colors, expected, case_id):
    """
    Test interpolate_colors returns correct number of colors for non-empty input.
    """
    # Arrange
    t = Text(plain, colors=colors)

    # Act
    result = t.interpolate_colors()
    # Assert
    assert isinstance(result, list)
    assert len(result) == expected
    assert all(isinstance(c, Color) for c in result)


@pytest.mark.parametrize(
    "plain,colors,expected,case_id",
    [
        # 0 chars, 2 colors
        ("", [Color.parse("#f00"), Color.parse("#0f0")], 0, "empty-2colors"),
    ],
)
def test_interpolate_colors_empty(plain, colors, expected, case_id):
    """
    Test interpolate_colors returns empty list for empty text input.
    """
    # Arrange
    t = Text(plain, colors=colors)

    # Act
    result = t.interpolate_colors()
    # Assert
    assert result == []


def test_interpolate_colors_no_colors_raises():
    """
    Test interpolate_colors raises ValueError when no colors are provided.
    """
    # Arrange
    t = Text("abc", colors=[])
    t.colors = []

    # Act & Assert
    with pytest.raises(ValueError, match="No colors to interpolate"):
        t.interpolate_colors()


@pytest.mark.parametrize(
    "plain,colors,expected_spans,case_id",
    [
        ("abc", [Color.parse("#f00"), Color.parse("#0f0")], 3, "normal"),
        ("", [Color.parse("#f00"), Color.parse("#0f0")], 0, "empty-plain"),
        ("xyz", [Color.parse("#123456")], 3, "one-color"),
    ],
)
def test_apply_gradient(plain, colors, expected_spans, case_id):
    """
    Test apply_gradient creates correct number of spans for each character in text.
    """
    # Arrange
    t = Text(plain, colors=colors)

    # Act
    t.apply_gradient()

    # Assert
    # Confirm span coverage matches character count (one per character)
    covered = {(s.start, s.end) for s in t._spans}
    expected = {(i, i + 1) for i in range(len(plain))}
    assert covered == expected, f"{covered=} != {expected=}"


def test_colors_property_and_setter():
    """
    Test colors property and setter for correct assignment and type.
    """
    # Arrange
    t = Text("hi", colors=["#f00", "#0f0"])
    # Act
    t.colors = [Color.parse("#fff")]
    # Assert
    assert isinstance(t.colors, list)
    assert len(t.colors) == 1
    assert color_eq(t.colors[0], Color.parse("#fff"))


def test_colors_setter_none():
    """
    Test colors setter with None resets colors to empty list.
    """
    # Arrange
    t = Text("hi", colors=["#f00"])
    # Act
    t.colors = None
    # Assert
    assert t.colors == []


def test_repr_and_str():
    """
    Test __repr__ and __str__ methods include text content.
    """
    # Arrange
    t = Text("hello", colors=["#f00", "#0f0"])
    # Act
    s = str(t)
    r = repr(t)
    # Assert
    assert isinstance(s, str)
    assert isinstance(r, str)
    assert "hello" in s


@pytest.mark.parametrize(
    "colors,expected",
    [
        (None, []),
        ([], []),
        ([Color.parse("#f00")], [Color.parse("#f00")]),
    ],
)
def test_colors_setter_various(colors, expected):
    """
    Test colors setter with None, empty, and single color values.
    """
    # Arrange
    t = Text("hi", colors=["#f00"])
    # Act
    t.colors = colors
    # Assert
    assert t.colors == (expected or [])

    assert t.colors == (expected or [])


def test_rich_method_returns_rich_text_and_preserves_styling():
    """Ensure Text.rich() returns a plain rich.text.Text with spans and style preserved."""
    # Create a gradient Text source
    gradient_text = Text("Hello", colors=["#f00", "#0f0"], style="bold")

    # Convert an existing Text instance to a plain RichText
    rich_text = gradient_text.as_rich()

    # Assert rich_text is rich.text.Text and not rich_gradient.text.Text
    assert isinstance(rich_text, RichText)
    assert not isinstance(rich_text, Text)

    # Plain content preserved
    assert rich_text.plain == gradient_text.plain

    # Spans copied across
    assert list(gradient_text._spans) == list(rich_text._spans)

    # Base style preserved (string or Style accepted)
    assert gradient_text.style == rich_text.style
