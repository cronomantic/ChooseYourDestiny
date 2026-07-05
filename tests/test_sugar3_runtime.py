"""Runtime verification of the Feature-3 syntax sugar on every target.

SWAP (direct and indirect), ENUM, character literals, ranges {a..b}, repetition
{v REPEAT n} and SELECT/CASE are pure front-end sugar (0 new runtime), but they
lower to real bytecode, so we run a program that exercises all of them in ZEsarUX
(headless) on the five targets and read FLAGS back.

The direct SWAP in particular is checked because the peephole optimizer fuses its
PUSH/POP pair (PUSH_I a, SET_I a<-b, POP_SET b); this proves that fusion still
swaps correctly on real hardware.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import run_cyd, emulator_available

PROGRAM = """[[
ENUM { RED, GREEN, BLUE }
DECLARE 0 AS a
DECLARE 1 AS b
DECLARE 2 AS sel
DECLARE 3 AS ch
DECLARE 4 AS r0
DECLARE 5 AS r1
DECLARE 6 AS x
DECLARE 7 AS y
DECLARE 8 AS px
DECLARE 9 AS py
DECLARE 10 AS rep0
DIM rng() = { 10..13 }
DIM rep() = { 9 REPEAT 4 }
SET a TO 7
SET b TO 99
SWAP a, b
LET ch = 'A'
SET x TO 3
SET y TO 8
SET px TO @@x
SET py TO @@y
SWAP [px], [py]
SET sel TO 0
SELECT @sel
  CASE 0    SET sel TO BLUE
  CASE 1    SET sel TO RED
  CASE ELSE SET sel TO 200
ENDSELECT
LET r0 = rng(0)
LET r1 = rng(3)
LET rep0 = rep(3)
LABEL spin
GOTO spin
]]"""

# a<->b swapped (99,7); sel: was 0 -> CASE 0 -> BLUE(=2); ch='A'(65); range rng(0)=10,
# rng(3)=13; x<->y swapped indirectly (8,3); px/py unchanged pointers (6,7);
# rep(3)=9 (repetition).
EXPECTED = [99, 7, 2, 65, 10, 13, 8, 3, 6, 7, 9]


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestSugar3Runtime(unittest.TestCase):
    def _check(self, model):
        flags = run_cyd(PROGRAM, model=model, n_bytes=16)
        self.assertEqual(list(flags)[:11], EXPECTED, f"feature-3 failed on {model}")

    def test_48k(self):
        self._check("48k")

    def test_128k(self):
        self._check("128k")

    def test_plus3(self):
        self._check("plus3")

    def test_mld(self):
        self._check("mld")

    def test_mld128(self):
        self._check("mld128")


if __name__ == "__main__":
    unittest.main()
