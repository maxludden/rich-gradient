"""Tests for the gradient-enabled Markdown renderables."""

import pytest
from rich.markdown import Markdown as RichMarkdown

from rich_gradient.markdown import AnimatedMarkdown, Markdown


def test_markdown_initializes_with_string_content():
    """Ensure Markdown strings are converted to Rich Markdown renderables."""
    content = "# Gradient Heading\nSome *emphasis*."
    markdown = Markdown(content, colors=["#ff0000", "#0000ff"])
    rich_md = markdown.rich_markdown
    assert isinstance(rich_md, RichMarkdown)
    assert rich_md.markdown == content


def test_markdown_preserves_kwargs_on_update():
    """Verify markdown_kwargs persist when updating string content."""
    markdown = Markdown(
        "**bold**",
        colors=["#ff0000", "#00ff00"],
        markdown_kwargs={"style": "markdown.bold"},
    )
    assert markdown.rich_markdown.style == "markdown.bold"
    markdown.update_markdown("_italic_")
    assert markdown.rich_markdown.style == "markdown.bold"
    assert markdown.rich_markdown.markdown == "_italic_"


def test_markdown_rejects_kwargs_with_renderable():
    """Providing kwargs alongside an existing Rich Markdown renderable should fail."""
    rich_md = RichMarkdown("content")
    with pytest.raises(ValueError):
        Markdown(rich_md, markdown_kwargs={"style": "markdown.custom"})


def test_animated_markdown_allows_updates():
    """AnimatedMarkdown should expose the underlying Rich Markdown and support updates."""
    animated = AnimatedMarkdown("Initial", colors=["#abcdef", "#123456"])
    assert isinstance(animated.rich_markdown, RichMarkdown)
    assert animated.rich_markdown.markdown == "Initial"
    animated.update_markdown("Updated")
    assert animated.rich_markdown.markdown == "Updated"
