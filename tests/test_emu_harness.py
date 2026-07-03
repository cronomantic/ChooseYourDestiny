"""Self-test for the headless emulator harness (emu_harness.py).

Verifies the whole automated loop end-to-end: compile a tiny .cyd that stores a
known marker + value in the engine variables, run it in ZEsarUX headless, and
read those variables back over ZRCP. Skipped when sjasmplus/ZEsarUX are absent.

If this passes, runtime behaviour can be asserted automatically in other tests.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from emu_harness import run_cyd, emulator_available

# Store a distinctive marker in variables 0..3 and a value in variable 4.
MARKER_PROGRAM = """[[
SET 0 TO 222
SET 1 TO 173
SET 2 TO 190
SET 3 TO 239
SET 4 TO 42
LABEL spin
GOTO spin
]]
"""


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestEmuHarness(unittest.TestCase):
    def test_variables_read_back_from_emulator(self):
        flags = run_cyd(MARKER_PROGRAM, model="48k", n_bytes=8)
        self.assertEqual(list(flags[:5]), [222, 173, 190, 239, 42])


if __name__ == "__main__":
    unittest.main()
