"""PRINT shows a number without leading zeroes, whatever ran before it.

The number routine (PRINT_HL_WORD) keeps the leading zeroes when the carry is
set on entry, and PRINT_A_BYTE relies on it being clear. EXEC_LOOP used to
clear it for every opcode (its SLA E did, as opcodes are below 128); when the
opcodes started being stored x2 that went away, and a PRINT after a sum that
overflows or a RANDOM showed "00100" instead of "100". Each program here prints
100 after one of those and its screen must match printing the text "100".
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import run_cyd_ex, emulator_available

SCREEN = (0x4000, 6912)
START = "[[ DECLARE 1 AS vida : DECLARE 2 AS x : CLEAR : "
END = "\nSET 0 TO 42\nLABEL spin\nGOTO spin ]]"
TEXT = START + "SET vida TO 100 ]]100[[" + END
AFTER = {
    "a sum that overflows": "SET x TO 200 : SET x TO @x + 100",
    "RANDOM": "SET x TO RANDOM(10)",
}


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestPrintNumbers(unittest.TestCase):
    def _screen(self, source, model):
        flags, (screen,) = run_cyd_ex(source, model=model, reads=[SCREEN])
        self.assertEqual(flags[0], 42, "the program did not finish")
        return screen

    def test_no_leading_zeroes(self):
        for model in ("48k", "128k"):
            expected = self._screen(TEXT, model)
            self.assertTrue(any(expected), "nothing was printed")
            for what, code in AFTER.items():
                with self.subTest(model=model, after=what):
                    source = START + code + " : SET vida TO 100 : PRINT @vida" + END
                    self.assertEqual(self._screen(source, model), expected)


if __name__ == "__main__":
    unittest.main()
