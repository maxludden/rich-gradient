from rich.console import Console
from rich.panel import Panel as RichPanel

from rich_gradient.animated_panel import AnimatedPanel


def test_animated_panel_wires_highlights() -> None:
    console = Console(record=True, width=60)
    animated_panel = AnimatedPanel(
        "Gradient Body",
        colors=["#ff0000", "#0000ff"],
        title="Header",
        title_style="bold yellow",
        subtitle="Footer",
        subtitle_style="dim italic",
        highlight_words={"Gradient": "bold magenta"},
        auto_refresh=False,
        refresh_per_second=10.0,
        console=console,
        disable=True,
    )

    assert isinstance(animated_panel.panel, RichPanel)

    regex_patterns = {
        rule.pattern.pattern
        for rule in animated_panel._highlight_rules
        if rule.kind == "regex" and rule.pattern is not None
    }
    expected_title_regex = AnimatedPanel._get_title_regex(animated_panel.panel.box)
    expected_subtitle_regex = AnimatedPanel._get_subtitle_regex(animated_panel.panel.box)
    assert expected_title_regex in regex_patterns
    assert expected_subtitle_regex in regex_patterns

    word_rules = [
        rule for rule in animated_panel._highlight_rules if rule.kind == "words"
    ]
    assert any("Gradient" in rule.words for rule in word_rules)
