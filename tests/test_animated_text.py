"""Tests for AnimatedText."""

from rich.text import Text as RichText

from rich_gradient.animated_text import AnimatedText


def test_animated_text_rich_text_property():
    animated = AnimatedText("Hello", colors=["#f00", "#0f0"])
    rich_text = animated.rich_text
    assert isinstance(rich_text, RichText)
    assert rich_text.plain == "Hello"


def test_animated_text_update_text_with_string():
    animated = AnimatedText("First", colors=["#f00", "#0f0"])
    animated.update_text("Second")
    assert animated.rich_text.plain == "Second"


def test_animated_text_preserves_markup_setting():
    animated = AnimatedText("**Bold**", colors=["#f00", "#0f0"], markup=False)
    assert animated.rich_text.plain == "**Bold**"
    animated.update_text("**Still literal**")
    assert animated.rich_text.plain == "**Still literal**"
