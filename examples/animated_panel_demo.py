"""Run an AnimatedPanel whose string content is centered with ``text_justify``."""

from __future__ import annotations

from rich_gradient.animated_panel import AnimatedPanel


def main() -> None:
    """Animate a rainbow panel with centered text for three seconds."""
    AnimatedPanel(
        "Centered [b]AnimatedPanel[/b] text",
        title="Centered",
        text_justify="center",
        rainbow=True,
        duration=3,
    ).run()


if __name__ == "__main__":
    main()
