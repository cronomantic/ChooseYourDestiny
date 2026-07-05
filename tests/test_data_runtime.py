"""Runtime verification of the immutable DATA feature on every target.

DATA / READ / RESTORE / RESTORE-label / DATAEND() are runtime behaviour, so they
are checked by actually running a program in ZEsarUX (headless) on all five
targets — tape (48k/128k), disk (+3) and Dandanator (mld/mld128) — and reading the
result back from FLAGS. This is what proves the uniform DATA path (TYPE_DATA chunk
+ LOAD_DATA_CHUNK) works on the banked/disk/flash targets, not just that it
compiles. Gated on the emulator being available (skips otherwise).
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import run_cyd, emulator_available

# Reads across the two DATA blocks, then RESTORE (offset 0), RESTORE label
# (offset 3 = first byte after 'second'), and DATAEND() at end / mid-stream.
# End in an infinite loop so the interpreter stays live while FLAGS is read.
DATA_PROGRAM = """[[
DATA 11, 22, 33
LABEL second
DATA 44, 55
RESTORE
READ 0
READ 1
READ 2
READ 3
READ 4
SET 5 TO DATAEND()
RESTORE second
READ 6
SET 7 TO DATAEND()
LABEL spin
GOTO spin
]]"""

# READ 0..4 -> the 5 DATA bytes; [5] DATAEND at end -> 1; RESTORE second + READ 6
# -> 44; [7] DATAEND mid-stream -> 0.
EXPECTED = [11, 22, 33, 44, 55, 1, 44, 0]

# Wrap-around ("endless tape"): 3 values read 7 times must repeat from the start.
WRAP_PROGRAM = """[[
DECLARE 0 AS v
DECLARE 1 AS i
DATA 10, 20, 30
SET i TO 3
WHILE (@i < 10)
  READ v
  SET [i] TO @v
  LET i += 1
WEND
LABEL spin
GOTO spin
]]"""
WRAP_EXPECTED = [10, 20, 30, 10, 20, 30, 10]  # FLAGS[3..9]


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestDataRuntime(unittest.TestCase):
    def _check(self, model):
        flags = run_cyd(DATA_PROGRAM, model=model, n_bytes=16)
        self.assertEqual(list(flags)[:8], EXPECTED, f"DATA failed on {model}")

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

    def test_wrap_around_48k(self):
        flags = run_cyd(WRAP_PROGRAM, model="48k", n_bytes=16)
        self.assertEqual(list(flags)[3:10], WRAP_EXPECTED)


if __name__ == "__main__":
    unittest.main()
