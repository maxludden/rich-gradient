# Monkey-patch rich.console.Console._collect_renderables to special-case empty rich_gradient.Text
from typing import List, cast

import rich.console as _rc
from rich.text import Text as RichText
from rich_color_ext import install

from rich_gradient._logger import get_logger
from rich_gradient.gradient import Gradient
from rich_gradient.rule import Rule
from rich_gradient.spectrum import Spectrum
from rich_gradient.text import Text
from rich_gradient.theme import GRADIENT_TERMINAL_THEME, GradientTheme

__all__ = [
    "Text",
    "Gradient",
    "Rule",
    "GradientTheme",
    "GRADIENT_TERMINAL_THEME",
    "Spectrum"
]

# Install rich_color_ext
install()

# Set up logging
logger = get_logger(False)
logger.disable("rich_gradient")


# Patch rich.console.Console._collect_renderables
if not getattr(_rc.Console, "_rich_gradient_patched", False):
    _original_collect = _rc.Console._collect_renderables

    def _collect_renderables_patched(
        self,
        objects,
        sep: str,
        end: str,
        *,
        justify=None,
        emoji=None,
        markup=None,
        highlight=None,
    ):
        # If all provided objects are rich_gradient.Text with empty plain, replace with a single
        #   standard Rich Text that has empty end so rendering produces no trailing newline.
        all_empty_gtexts = True
        processed_objects = []
        for obj in objects:
            try:
                from rich_gradient.text import Text as GradientText

                if isinstance(obj, GradientText) and getattr(obj, "plain", "") == "":
                    processed_objects.append(obj)
                    continue
            except Exception:
                # If we can't import or something unexpected, bail to original implementation
                all_empty_gtexts = False
                break
            all_empty_gtexts = False
            break

        if all_empty_gtexts and processed_objects:
            # Return a single Rich Text with empty end so capture returns empty string
            return cast(List[_rc.ConsoleRenderable], [RichText("", end="")])

        # Fallback to original implementation
        return _original_collect(
            self,
            objects,
            sep,
            end,
            justify=justify,
            emoji=emoji,
            markup=markup,
            highlight=highlight,
        )

    setattr(_rc.Console, "_collect_renderables", _collect_renderables_patched)
    setattr(_rc.Console, "_rich_gradient_patched", True)
