import pytest

# from rich.table import Table
from rich.console import Console

from rich_gradient.color import Color
from rich_gradient.spectrum import Spectrum


def test_spectrum_initialization():
    # Test default initialization
    spectrum = Spectrum()
    assert len(spectrum) == 18

    # Test initialization with specific length
    length = 10
    spectrum = Spectrum(length=length)
    assert len(spectrum) == length


def test_spectrum_color_creation():
    # Test if all colors are created correctly
    spectrum = Spectrum()
    assert all(isinstance(color, Color) for color in spectrum)


def test_console_output():
    # Test the console output for visual inspection
    console = Console()
    spectrum = Spectrum()
    console.print(spectrum)
    # This test is more for manual/visual inspection

def test_spectrum_sequence():
    # Test the sequence of colors
    spectrum = Spectrum()
    colors = spectrum.COLORS
    for i in range(1, len(colors)):
        assert colors[i - 1].triplet.hex != colors[i].triplet.hex

if __name__ == "__main__":
    pytest.main()
