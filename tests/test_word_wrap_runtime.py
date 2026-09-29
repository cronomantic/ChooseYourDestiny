"""Word wrap with words wider than 255 pixels.

PRINT_STR adds up the width of the next word to decide whether it fits on the
line. The sum is 8-bit: a word of 300 pixels used to count as 44, so it looked
short and started in the middle of the line. It must go to a new line first,
like any other word that doesn't fit (the printer then breaks it at the edge).
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import emulator_available, run_cyd_ex

# "ab", then a 50-letter word (300 pixels in the 6-pixel font).
PROGRAM = "[[ CLEAR ]]ab " + "m" * 50 + "[[ SET 0 TO 42\nLABEL spin\nGOTO spin ]]"


def row_bytes(screen, char_row, first_col, last_col):
    """Bitmap bytes of a character row (8 pixel lines) between two columns."""
    out = []
    for line in range(8):
        y = char_row * 8 + line
        base = ((y & 0xC0) << 5) | ((y & 0x07) << 8) | ((y & 0x38) << 2)
        out += screen[base + first_col : base + last_col + 1]
    return out


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestLongWordWrap(unittest.TestCase):
    def test_word_wider_than_255_pixels_starts_a_new_line(self):
        flags, (screen,) = run_cyd_ex(PROGRAM, model="48k", reads=[(0x4000, 6144)])
        self.assertEqual(flags[0], 42, "program did not finish")
        self.assertTrue(any(row_bytes(screen, 0, 0, 1)), "'ab' was not printed")
        # Only "ab" on the first line: the long word starts on the next one.
        self.assertFalse(any(row_bytes(screen, 0, 3, 31)))
        self.assertTrue(any(row_bytes(screen, 1, 0, 1)))


if __name__ == "__main__":
    unittest.main()
