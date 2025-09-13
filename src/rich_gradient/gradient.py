"""Public Gradient facade.

This module re-exports the `Gradient` factory which returns either a
static `BaseGradient` or an `AnimatedGradient` depending on constructor
parameters. Keeping the public import stable avoids duplication.
"""

from ._animated_gradient import Gradient  # noqa: F401
