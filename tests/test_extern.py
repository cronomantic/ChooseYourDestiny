"""Emulator regression tests for native routines (IMPORT / CALL -> OP_EXTERN).

Exercises the whole OP_EXTERN pipeline on the 48k target: a native Z80 routine
is assembled in isolation, placed resident by the build, and invoked with CALL.
The routine is entered with DE=FLAGS, writes known values into the FLAGS array,
and clobbers IX/IY on purpose to prove the handler preserves the interpreter's
state. Results are read back from FLAGS over ZRCP. Gated on the emulator.

Run: python tests/run_tests.py   (or: python -m unittest tests.test_extern)
"""

import os
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import emulator_available, compile_cyd, run_in_zesarux  # noqa: E402

# Native routine body. The author writes only the body; CYD frames it with the
# ORG/SAVEBIN. Entered with DE=FLAGS, ends with RET. Clobbers IX/IY and uses the
# stack to verify the handler saves/restores them.
NATIVE = (
    "    ld ix, 0\n"
    "    ld iy, 0\n"
    "    push bc\n"
    "    ld a, 42\n"
    "    ld (de), a      ; FLAGS+0 = 42\n"
    "    inc de\n"
    "    ld a, 99\n"
    "    ld (de), a      ; FLAGS+1 = 99\n"
    "    pop bc\n"
    "    ret\n"
)


SRC = (
    "[[\n"
    'IMPORT nativo FROM "nativo.asm"\n'
    "CALL nativo\n"
    "SET 2 TO 123\n"          # interpreter must resume after the call
    "LABEL spin\n"
    "GOTO spin\n"
    "]]\n"
)


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not found under tools/")
class TestExtern(unittest.TestCase):
    def _roundtrip(self, model, machine):
        with tempfile.TemporaryDirectory(prefix="cyd_extern_") as wd:
            (Path(wd) / "nativo.asm").write_text(NATIVE, encoding="utf-8")
            tap, flags = compile_cyd(SRC, model, wd)
            f = run_in_zesarux(tap, flags, n_bytes=4, machine=machine, max_wait=35.0)
        self.assertEqual(f[0], 42, "native routine did not write FLAGS+0 (DE=FLAGS)")
        self.assertEqual(f[1], 99, "native routine did not write FLAGS+1")
        self.assertEqual(f[2], 123, "interpreter did not resume after CALL")

    def test_import_call_48k(self):
        """48k: routine placed resident, called directly."""
        self._roundtrip("48k", "48k")

    def test_import_call_128k(self):
        """128k: routine placed in a paged bank; handler pages it in and restores."""
        self._roundtrip("128k", "128k")

    def test_import_call_plus3(self):
        """+3: same $7FFD-banked path as 128k, loaded from disk (DSK)."""
        self._roundtrip("plus3", "P341")


if __name__ == "__main__":
    unittest.main()
