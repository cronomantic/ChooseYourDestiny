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


# Inline ASM blocks (ASM ... ENDASM): the body is written verbatim in the .cyd
# (no external file), assembled in isolation and placed by the build exactly like
# an IMPORTed routine. Same ABI (DE=FLAGS, RET), same OP_EXTERN handler.
INLINE_SINGLE = (
    "[[\n"
    "ASM nativo\n"
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
    "ENDASM\n"
    "CALL nativo\n"
    "SET 2 TO 123\n"
    "LABEL spin\n"
    "GOTO spin\n"
    "]]\n"
)

# Multi-export block: wr42 and wr99 are separate CALL targets that share a
# private helper (_store) via an intra-block CALL.
INLINE_MULTI = (
    "[[\n"
    "ASM mathlib EXPORTS wr42, wr99\n"
    "wr42:\n"
    "    ld a, 42\n"
    "    call _store     ; FLAGS+0 = 42\n"
    "    ret\n"
    "wr99:\n"
    "    inc de\n"
    "    ld a, 99\n"
    "    call _store     ; FLAGS+1 = 99\n"
    "    ret\n"
    "_store:\n"
    "    ld (de), a\n"
    "    ret\n"
    "ENDASM\n"
    "CALL wr42\n"
    "CALL wr99\n"
    "SET 2 TO 123\n"
    "LABEL spin\n"
    "GOTO spin\n"
    "]]\n"
)


# Injected ABI (cyd_abi.inc): the routine reaches the engine's resident image
# buffer and the FLAGS array by name (SCREEN_BUFFER_PXL / FLAGS EQUs injected by
# the compiler). Writing 170 into the buffer and reading it back proves the
# injected addresses are correct and reachable (also from a paged bank on 128k,
# since these live in the always-mapped low RAM).
INLINE_ABI = (
    "[[\n"
    "ASM bufio\n"
    "    ld hl, SCREEN_BUFFER_PXL   ; injected resident address\n"
    "    ld (hl), 170               ; write into the image buffer\n"
    "    ld a, (hl)                 ; read it back\n"
    "    ld (FLAGS), a              ; injected FLAGS symbol -> FLAGS+0\n"
    "    ret\n"
    "ENDASM\n"
    "CALL bufio\n"
    "SET 1 TO 200\n"
    "LABEL spin\n"
    "GOTO spin\n"
    "]]\n"
)


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not found under tools/")
class TestInlineAsm(unittest.TestCase):
    def _roundtrip(self, src, model, machine):
        with tempfile.TemporaryDirectory(prefix="cyd_inline_") as wd:
            tap, flags = compile_cyd(src, model, wd)
            f = run_in_zesarux(tap, flags, n_bytes=4, machine=machine, max_wait=35.0)
        self.assertEqual(f[0], 42, "inline routine did not write FLAGS+0 (DE=FLAGS)")
        self.assertEqual(f[1], 99, "inline routine did not write FLAGS+1")
        self.assertEqual(f[2], 123, "interpreter did not resume after CALL")

    def _abi_roundtrip(self, model, machine):
        with tempfile.TemporaryDirectory(prefix="cyd_abi_") as wd:
            tap, flags = compile_cyd(INLINE_ABI, model, wd)
            f = run_in_zesarux(tap, flags, n_bytes=4, machine=machine, max_wait=35.0)
        self.assertEqual(f[0], 170, "injected SCREEN_BUFFER_PXL/FLAGS not usable")
        self.assertEqual(f[1], 200, "interpreter did not resume after CALL")

    def test_inline_abi_symbols_48k(self):
        """Injected cyd_abi.inc: image buffer + FLAGS reachable by name (48k)."""
        self._abi_roundtrip("48k", "48k")

    def test_inline_abi_symbols_128k(self):
        """Injected ABI symbols reachable from a paged-bank routine (128k)."""
        self._abi_roundtrip("128k", "128k")

    def test_inline_single_48k(self):
        """48k: a verbatim inline block placed resident and called directly."""
        self._roundtrip(INLINE_SINGLE, "48k", "48k")

    def test_inline_single_128k(self):
        """128k: inline block placed in a paged bank; handler pages it in."""
        self._roundtrip(INLINE_SINGLE, "128k", "128k")

    def test_inline_multiexport_48k(self):
        """48k: two EXPORTS entry points sharing a private helper (intra-block call)."""
        self._roundtrip(INLINE_MULTI, "48k", "48k")

    def test_inline_multiexport_128k(self):
        """128k: multi-export block in a paged bank; both entries + helper reachable."""
        self._roundtrip(INLINE_MULTI, "128k", "128k")


if __name__ == "__main__":
    unittest.main()
