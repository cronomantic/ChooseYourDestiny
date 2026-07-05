"""Runtime verification of the syntax-sugar features on every target.

FOR ... NEXT and wide constants (WORD/DWORD/string) are pure front-end sugar (0
new runtime), but they lower to real bytecode, so we prove the lowered code runs
correctly by executing a program in ZEsarUX (headless) on all five targets — tape
(48k/128k), disk (+3) and Dandanator (mld/mld128) — and reading FLAGS back.

The program exercises the semantics that matter at runtime:
  - an ascending FOR that accumulates 1..5  -> 15
  - a descending FOR that counts down TO 0 STEP -2 (the byte-underflow case that a
    naive lowering would turn into an infinite loop) -> 6 iterations; that the
    program reaches the later assignments at all proves this loop terminates
  - a WORD wide store split into two little-endian bytes
  - a wide value living in an array (WORD in DIM init) read back byte by byte
    (also exercises the MLD flash->RAM array relocation)
  - a string wide store lowered to glyph bytes

Gated on the emulator being available (skips otherwise).
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import run_cyd, emulator_available

PROGRAM = """[[
DECLARE 10 AS i
DECLARE 11 AS j
DECLARE 0 AS sum
DECLARE 1 AS cnt
DECLARE 2 AS w
DECLARE 4 AS a0
DECLARE 5 AS a1
DECLARE 6 AS s
DIM arr() = { WORD 1000 }
SET sum TO 0
FOR i = 1 TO 5
  LET sum += @i
NEXT
SET cnt TO 0
FOR j = 10 TO 0 STEP -2
  LET cnt += 1
NEXT
LET w = WORD 1000
LET a0 = arr(0)
LET a1 = arr(1)
LET s = "AB"
LABEL spin
GOTO spin
]]"""

# 1000 = 0x03E8 -> low 0xE8 = 232, high 0x03 = 3. 'A' = 65, 'B' = 66.
EXPECTED = [15, 6, 232, 3, 232, 3, 65, 66]


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestSugarRuntime(unittest.TestCase):
    def _check(self, model):
        flags = run_cyd(PROGRAM, model=model, n_bytes=16)
        self.assertEqual(list(flags)[:8], EXPECTED, f"sugar failed on {model}")

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

    def test_esxdos(self):
        self._check("esxdos")


if __name__ == "__main__":
    unittest.main()
