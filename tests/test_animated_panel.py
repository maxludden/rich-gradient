from rich.console import Console
from rich.panel import Panel as RichPanel

from rich_gradient.animated_panel import AnimatedPanel
from rich_gradient.panel import Panel


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
    expected_subtitle_regex = AnimatedPanel._get_subtitle_regex(
        animated_panel.panel.box
    )
    assert expected_title_regex in regex_patterns
    assert expected_subtitle_regex in regex_patterns

    word_rules = [
        rule for rule in animated_panel._highlight_rules if rule.kind == "words"
    ]
    assert any("Gradient" in rule.words for rule in word_rules)


def test_expand_propagates_to_panel() -> None:
    console = Console(record=True, width=60)
    animated_panel = AnimatedPanel(
        "Body",
        console=console,
        expand=False,
        auto_refresh=False,
        refresh_per_second=10.0,
        disable=True,
    )
    # initial state is respected on both wrapper and inner Rich Panel
    assert animated_panel.expand is False
    assert animated_panel.panel.expand is False

    # updating expand on the wrapper should propagate to the inner panel
    animated_panel.expand = True
    assert animated_panel.panel.expand is True


def test_panel_expand_propagates() -> None:
    panel = Panel("Body", expand=False)
    assert panel.expand is False
    # Panel should track its underlying RichPanel and reflect the expand flag
    assert hasattr(panel, "panel")
    assert panel.panel.expand is False
    panel.expand = True
    assert panel.panel.expand is True
