"""Tests for GradientTheme behavior."""

from rich.style import Style

from rich_gradient.theme import GradientTheme


def test_gradient_theme_uses_custom_styles() -> None:
    """GradientTheme should expose a Theme that includes provided styles."""
    styles = {"custom.style": "bold red"}
    theme = GradientTheme(styles=styles)
    resolved = theme.theme.styles.get("custom.style")
    assert isinstance(resolved, Style)
    assert resolved.bold
    assert resolved.color is not None
    assert resolved.color.get_truecolor().hex.lower() == "#ff0000"
