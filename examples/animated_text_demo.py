"""Small demo for AnimatedText."""

from __future__ import annotations

import time

from rich_gradient.animated_text import AnimatedText


def main() -> None:
    animated = AnimatedText(
        "Loading...",
        rainbow=True,
        refresh_per_second=30.0,
    )
    animated.start()
    try:
        time.sleep(1)
        animated.update_text("Almost there...")
        time.sleep(1)
        animated.update_text("Done!")
        time.sleep(1)
    finally:
        animated.stop()


if __name__ == "__main__":
    main()
