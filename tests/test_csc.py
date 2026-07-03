"""Test suite for ScreenCompress — the .scr -> .csc image compressor.

ScreenCompress owns two things: the CSC *container* (header + planes) and the
left-right *mirror detection*. Neither depends on the actual ZX0 byte output, and
pyZX0's optimal parser is very slow on non-trivial data (~10-30s per screen), so
most tests stub ``compress_data`` to isolate ScreenCompress's own logic and stay
fast. One separate test keeps the real compressor (on a blank screen, which ZX0
handles instantly) to confirm end-to-end size reduction.

CSC layout (from ``convert_to_CSC``):
  byte 0-1 : filesize (little-endian) = len(csc) - 2
  byte 2   : num_lines_scr
  byte 3   : num_lines_att, bit 7 = mirror flag
  then     : ZX0-compressed pixel plane, then ZX0-compressed attribute plane
"""

import sys
import unittest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

import cydc_csc
from cydc_csc import ScreenCompress

FULL_SCREEN = 6912

# A blank screen is left-right symmetric; the ramp is not. Mirror detection reads
# the raw input (no ZX0), so the ramp is fine as a fixture once compress is stubbed.
BLANK = bytes(FULL_SCREEN)
RAMP = bytes([(i * 37) & 0xFF for i in range(FULL_SCREEN)])


def mirror_flag(csc):
    return (csc[3] >> 7) & 1


def filesize_field(csc):
    return csc[0] | (csc[1] << 8)


def _fast_compress(data, *args, **kwargs):
    """Stand-in for pyZX0 compress_data: predictable, instant, returns (bytes, delta)."""
    return (bytes(max(1, len(data) // 8)), 0)


class TestCscContainerAndMirror(unittest.TestCase):
    """Container assembly + mirror detection, with ZX0 stubbed for speed."""

    def setUp(self):
        self._real_compress = cydc_csc.compress_data
        cydc_csc.compress_data = _fast_compress

    def tearDown(self):
        cydc_csc.compress_data = self._real_compress

    def test_filesize_field_matches_length(self):
        csc, _ = ScreenCompress(RAMP).convert_to_CSC(num_lines=192)
        self.assertEqual(filesize_field(csc), len(csc) - 2)

    def test_num_lines_scr_recorded(self):
        csc, _ = ScreenCompress(RAMP).convert_to_CSC(num_lines=192)
        self.assertEqual(csc[2], 192)
        csc2, _ = ScreenCompress(RAMP).convert_to_CSC(num_lines=96)
        self.assertEqual(csc2[2], 96)

    def test_all_bytes_in_range(self):
        csc, _ = ScreenCompress(RAMP).convert_to_CSC(num_lines=192)
        for b in csc:
            self.assertTrue(0 <= b <= 255)

    def test_deterministic(self):
        a, _ = ScreenCompress(RAMP).convert_to_CSC(num_lines=192)
        b, _ = ScreenCompress(RAMP).convert_to_CSC(num_lines=192)
        self.assertEqual(a, b)

    def test_symmetric_image_enables_mirror(self):
        csc, _ = ScreenCompress(BLANK).convert_to_CSC(num_lines=192)
        self.assertEqual(mirror_flag(csc), 1)

    def test_asymmetric_image_does_not_enable_mirror(self):
        csc, _ = ScreenCompress(RAMP).convert_to_CSC(num_lines=192)
        self.assertEqual(mirror_flag(csc), 0)

    def test_force_mirror_overrides_detection(self):
        csc, _ = ScreenCompress(RAMP).convert_to_CSC(num_lines=192, force_mirror=True)
        self.assertEqual(mirror_flag(csc), 1)


class TestCscRealCompression(unittest.TestCase):
    """Real pyZX0 compression (blank screen only -> instant)."""

    def test_blank_screen_compresses_massively(self):
        csc, _ = ScreenCompress(BLANK).convert_to_CSC(num_lines=192)
        self.assertLess(len(csc), FULL_SCREEN // 10)


if __name__ == "__main__":
    unittest.main()
