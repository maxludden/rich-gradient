"""
Test suite for Spectrum class covering color generation, inversion, style matching, and hex code consistency.
"""

import pytest
from rich.color import Color
from rich.style import Style

from rich_gradient.spectrum import Spectrum


def test_spectrum_default_length():
    """
    Test that Spectrum generates the default number of colors and all are Color instances.
    """
    spectrum = Spectrum()
    assert len(spectrum.colors) == 17
    assert all(isinstance(c, Color) for c in spectrum.colors)


def test_spectrum_invert_flag():
    """
    Test that the invert flag reverses the color order in Spectrum.
    """
    spectrum_normal = Spectrum(hues=5, invert=False).colors
    spectrum_inverted = list(reversed(spectrum_normal))
    assert spectrum_normal != spectrum_inverted
    assert spectrum_normal == list(reversed(spectrum_inverted))


def test_spectrum_styles_match_colors():
    """
    Test that each style in Spectrum matches its corresponding color's hex code.
    """
    spectrum = Spectrum(hues=10)
    # all styles should be Style instances and have a color
    assert all(isinstance(s, Style) for s in spectrum.styles)
    assert all(s.color is not None for s in spectrum.styles)
    # compare lists of hex strings (lowercase) to ensure exact correspondence
    style_hexes = [str(s.color.get_truecolor().hex).lower() for s in spectrum.styles if s.color is not None]
    color_hexes = [c.get_truecolor().hex.lower() for c in spectrum.colors]
    assert style_hexes == color_hexes


def test_spectrum_hex_matches_color():
    """
    Test that the hex property matches the hex codes of the colors in Spectrum.
    """
    spectrum = Spectrum(hues=8)
    assert len(spectrum.hex) == 8
    assert [h.lower() for h in spectrum.hex] == [
        c.get_truecolor().hex.lower() for c in spectrum.colors
    ]
