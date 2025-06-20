import pytest
from rich.style import Style
from rich.color import Color
from rich.table import Table
from rich_gradient.spectrum import Spectrum, SPECTRUM_COLORS

def test_spectrum_default_length():
    spectrum = Spectrum()
    assert len(spectrum.colors) == 18
    assert all(isinstance(c, Color) for c in spectrum.colors)

def test_spectrum_invert_flag():
    spectrum_normal = Spectrum(hues=5, invert=False).colors
    spectrum_inverted = list(reversed(spectrum_normal))
    assert spectrum_normal != spectrum_inverted
    assert spectrum_normal == list(reversed(spectrum_inverted))

def test_spectrum_styles_match_colors():
    spectrum = Spectrum(hues=10)
    assert len(spectrum.styles) == 10
    for style, color in zip(spectrum.styles, spectrum.colors):
        assert isinstance(style, Style)
        assert style.color is not None
        assert str(style.color.get_truecolor().hex).lower() == color.get_truecolor().hex.lower(), f"{style.color=} != {color.get_truecolor().hex}"

def test_spectrum_hex_matches_color():
    spectrum = Spectrum(hues=8)
    assert len(spectrum.hex) == 8
    assert [h.lower() for h in spectrum.hex] == [c.get_truecolor().hex.lower() for c in spectrum.colors]
