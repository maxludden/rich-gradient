import pytest
from rich.color import Color
from rich.style import Style
from rich.text import Text as RichText
from rich_gradient.text import Text

# Helper for color equality (Color.__eq__ is not always implemented)
def color_eq(c1, c2):
    return c1.get_truecolor() == c2.get_truecolor()

@pytest.mark.parametrize(
    "text,colors,rainbow,hues,style,justify,overflow,no_wrap,end,tab_size,markup,expected_plain,expected_colors_len",
    [
        # Simple text, 2 colors, no rainbow
        pytest.param(
            "Hello", ["#f00", "#0f0"], False, 5, "", "default", "fold", False, "\n", 4, True, "Hello", 2,
            id="simple-2colors"
        ),
        # Rainbow, hues ignored, colors ignored
        pytest.param(
            "World", None, True, 7, "", "center", "ellipsis", True, "", 2, False, "World", 18,
            id="rainbow"
        ),
        # No colors, hues=3
        pytest.param(
            "abc", None, False, 3, "bold", "right", "crop", False, "\n", 8, True, "abc", 3,
            id="no-colors-hues3"
        ),
        # One color only
        pytest.param(
            "X", ["#123456"], False, 5, "", "left", "fold", False, "\n", 4, True, "X", 1,
            id="one-color"
        ),
        # Empty text, colors provided
        pytest.param(
            "", ["#fff", "#000"], False, 5, "", "default", "fold", False, "\n", 4, True, "", 2,
            id="empty-text"
        ),
        # Empty text, no colors
        pytest.param(
            "", None, False, 2, "", "default", "fold", False, "\n", 4, True, "", 2,
            id="empty-text-no-colors"
        ),
        # Markup parsing
        pytest.param(
            "[bold]B[/bold]", ["#f00", "#00f"], False, 5, "", "default", "fold", False, "\n", 4, True, "B", 2,
            id="markup"
        ),
    ]
)
def test_text_init_and_properties(
    text, colors, rainbow, hues, style, justify, overflow, no_wrap, end, tab_size, markup,
    expected_plain, expected_colors_len
):
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
        (None, 18, True, 18, Color, "rainbow-18"),
        (["red", "blue"], 5, False, 2, Color, "css-names"),
        (["#f00"], 5, False, 1, Color, "single-color"),
    ]
)
def test_parse_colors(input_colors, hues, rainbow, expected_len, expected_type, case_id):
    # Act
    result = Text.parse_colors(colors=input_colors, hues=hues, rainbow=rainbow)

    # Assert
    assert isinstance(result, list)
    assert len(result) == expected_len
    for c in result:
        assert isinstance(c, expected_type)

@pytest.mark.parametrize(
    "plain,colors,expected,case_id",
    [
        # 2 colors, 5 chars
        ("abcde", [Color.parse("#f00"), Color.parse("#0f0")], 5, "2colors-5chars"),
        # 1 color, 3 chars
        ("xyz", [Color.parse("#123456")], 3, "1color-3chars"),
        # 3 colors, 4 chars
        ("test", [Color.parse("#f00"), Color.parse("#0f0"), Color.parse("#00f")], 4, "3colors-4chars"),
        # 0 chars, 2 colors
        ("", [Color.parse("#f00"), Color.parse("#0f0")], 0, "empty-2colors"),
    ]
)
def test_interpolate_colors(plain, colors, expected, case_id):
    # Arrange
    t = Text(plain, colors=colors)

    # Act
    if not plain:
        result = t.interpolate_colors()
        # Assert
        assert result == []
    else:
        result = t.interpolate_colors()
        # Assert
        assert isinstance(result, list)
        assert len(result) == expected
        for c in result:
            assert isinstance(c, Color)

def test_interpolate_colors_no_colors_raises():
    # Arrange
    t = Text("abc", colors=[])
    t.colors = []

    # Act & Assert
    with pytest.raises(ValueError, match="No colors to interpolate"):
        t.interpolate_colors()

@pytest.mark.parametrize(
    "plain,colors,case_id",
    [
        ("abc", [Color.parse("#f00"), Color.parse("#0f0")], "normal"),
        ("", [Color.parse("#f00"), Color.parse("#0f0")], "empty-plain"),
        ("xyz", [Color.parse("#123456")], "one-color"),
    ]
)
def test_apply_gradient(plain, colors, case_id):
    # Arrange
    t = Text(plain, colors=colors)

    # Act
    t.apply_gradient()

    # Assert
    # Check that spans are applied for each character
    if plain:
        assert len(t._spans) >= len(plain)
    else:
        assert len(t._spans) == 0

def test_colors_property_and_setter():
    # Arrange
    t = Text("hi", colors=["#f00", "#0f0"])
    # Act
    t.colors = [Color.parse("#fff")]
    # Assert
    assert isinstance(t.colors, list)
    assert len(t.colors) == 1
    assert color_eq(t.colors[0], Color.parse("#fff"))

def test_colors_setter_none():
    # Arrange
    t = Text("hi", colors=["#f00"])
    # Act
    t.colors = None
    # Assert
    assert t.colors == []

def test_repr_and_str():
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
    ]
)
def test_colors_setter_various(colors, expected):
    # Arrange
    t = Text("hi", colors=["#f00"])
    # Act
    t.colors = colors
    # Assert
    assert t.colors == (expected or [])

