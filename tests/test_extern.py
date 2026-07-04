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
from emu_harness import (  # noqa: E402
    emulator_available,
    compile_cyd,
    run_in_zesarux,
    find_sjasmplus,
)

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


# Array broker (CYD_PEEK / CYD_POKE): a native routine reaches a CYD array by
# name through the injected ARR_<name> / _LEN / _BANK constants. The routine
# reads inv[2] (=33), overwrites inv[3] with 200 and reads it back, and reports
# the array's element count and physical bank. On banked targets the array may
# live in a paged RAM bank, so the broker pages it in at $C000, touches one byte,
# and pages the routine's own bank back -- all from resident code.
ARR_ROUTINE = (
    "ASM arrio\n"
    "    ld a, ARR_inv_BANK\n"
    "    ld hl, ARR_inv + 2\n"
    "    call CYD_PEEK        ; A = inv[2]\n"
    "    ld (FLAGS), a        ; FLAGS+0 = inv[2] = 33\n"
    "    ld a, ARR_inv_BANK\n"
    "    ld hl, ARR_inv + 3\n"
    "    ld e, 200\n"
    "    call CYD_POKE        ; inv[3] = 200\n"
    "    ld a, ARR_inv_BANK\n"
    "    ld hl, ARR_inv + 3\n"
    "    call CYD_PEEK        ; read it back\n"
    "    ld (FLAGS+1), a      ; FLAGS+1 = 200\n"
    "    ld a, ARR_inv_LEN\n"
    "    ld (FLAGS+2), a      ; FLAGS+2 = element count = 4\n"
    "    ld a, ARR_inv_BANK\n"
    "    ld (FLAGS+3), a      ; FLAGS+3 = physical bank ($FF if resident)\n"
    "    ret\n"
    "ENDASM\n"
    "CALL arrio\n"
    "SET 4 TO 123\n"
    "LABEL spin\n"
    "GOTO spin\n"
)

# Resident array: declared alone, it lives in the always-mapped chunk 0, so the
# broker sees ARR_inv_BANK = $FF and reads/writes it directly (no paging).
ARR_RESIDENT = "[[\nDIM inv(4) = {11, 22, 33, 44}\n" + ARR_ROUTINE + "]]\n"


# Block access (CYD_ARR_MAP / CYD_ARR_FLUSH): map the whole array to a directly
# addressable working copy, bump every element by 1, flush it back, then read two
# elements back with CYD_PEEK to prove the changes persisted. On banked targets
# MAP copies the array to the resident SAVE_FLAGS scratch and FLUSH copies it
# back; on a resident array both are no-ops (the routine works in place).
ARR_MAP_ROUTINE = (
    "ASM arrmap\n"
    "    ld a, ARR_inv_BANK\n"
    "    ld hl, ARR_inv\n"
    "    ld bc, ARR_inv_LEN\n"
    "    call CYD_ARR_MAP     ; HL -> working copy\n"
    "    ld b, ARR_inv_LEN\n"
    ".loop:\n"
    "    ld a, (hl)\n"
    "    inc a\n"
    "    ld (hl), a\n"
    "    inc hl\n"
    "    djnz .loop\n"
    "    ld a, ARR_inv_BANK\n"
    "    ld hl, ARR_inv\n"
    "    ld bc, ARR_inv_LEN\n"
    "    call CYD_ARR_FLUSH   ; write the working copy back\n"
    "    ld a, ARR_inv_BANK\n"
    "    ld hl, ARR_inv\n"
    "    call CYD_PEEK\n"
    "    ld (FLAGS), a        ; inv[0]: 11 -> 12\n"
    "    ld a, ARR_inv_BANK\n"
    "    ld hl, ARR_inv + 3\n"
    "    call CYD_PEEK\n"
    "    ld (FLAGS+1), a      ; inv[3]: 44 -> 45\n"
    "    ld a, ARR_inv_BANK\n"
    "    ld (FLAGS+3), a      ; FLAGS+3 = physical bank ($FF if resident)\n"
    "    ret\n"
    "ENDASM\n"
    "CALL arrmap\n"
    "SET 4 TO 123\n"
    "LABEL spin\n"
    "GOTO spin\n"
)

ARR_MAP_RESIDENT = "[[\nDIM inv(4) = {11, 22, 33, 44}\n" + ARR_MAP_ROUTINE + "]]\n"


def _bank0_filler():
    """~90 incompressible filler arrays (array data is stored raw, unlike text,
    which the compiler would shrink) to fill chunk 0 so a following array spills
    into a paged RAM bank and exercises the banked broker path."""
    s = ""
    for i in range(90):
        vals = ", ".join(str((i * 7 + j) & 255) for j in range(256))
        s += f"DIM fill{i}(256) = {{{vals}}}\n"
    return s


def _arr_banked_src():
    """`inv` forced into a paged RAM bank (banked CYD_PEEK/CYD_POKE path)."""
    return "[[\n" + _bank0_filler() + "DIM inv(4) = {11, 22, 33, 44}\n" + ARR_ROUTINE + "]]\n"


def _arr_map_banked_src():
    """`inv` forced into a paged RAM bank (banked CYD_ARR_MAP/CYD_ARR_FLUSH path)."""
    return "[[\n" + _bank0_filler() + "DIM inv(4) = {11, 22, 33, 44}\n" + ARR_MAP_ROUTINE + "]]\n"


# Cross-block native calls (CYD_CALL): a native routine calls another one that
# lives in a DIFFERENT block (and, on banked targets, a different RAM bank) via
# the resident trampoline. blockA declares `USES setb`, so the compiler injects
# RT_setb; `ld a, RT_setb : call CYD_CALL` dispatches to setb through the resident
# EXTERN_DISPATCH table. blockA writes 11, calls setb (writes 55), and the
# interpreter resumes (123).
def _cyd_call_src(filler=0):
    """CYD_CALL program. ``filler`` bytes bloat blockA so that on a banked target
    setb is pushed into a different physical RAM bank, exercising the cross-bank
    trampoline (page callee in, call, page caller back)."""
    pad = f"    DEFS {filler}, 0\n" if filler else ""
    return (
        "[[\n"
        "ASM blockB EXPORTS setb\n"
        "setb:\n"
        "    ld a, 55\n"
        "    ld (FLAGS+1), a\n"
        "    ret\n"
        "ENDASM\n"
        "ASM blockA USES setb\n"
        "    ld a, 11\n"
        "    ld (FLAGS), a\n"
        "    ld a, RT_setb\n"
        "    call CYD_CALL\n"
        "    ret\n"
        + pad +
        "ENDASM\n"
        "CALL blockA\n"
        "SET 2 TO 123\n"
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

    def _array_roundtrip(self, src, model, machine, resident):
        with tempfile.TemporaryDirectory(prefix="cyd_arr_") as wd:
            tap, flags = compile_cyd(src, model, wd)
            f = run_in_zesarux(tap, flags, n_bytes=6, machine=machine, max_wait=45.0)
        self.assertEqual(f[0], 33, "CYD_PEEK did not read inv[2] through ARR_inv")
        self.assertEqual(f[1], 200, "CYD_POKE/CYD_PEEK round-trip on inv[3] failed")
        self.assertEqual(f[2], 4, "ARR_inv_LEN (element count) is wrong")
        self.assertEqual(f[4], 123, "interpreter did not resume after CALL")
        if resident:
            self.assertEqual(f[3], 0xFF, "resident array should report bank $FF")
        else:
            self.assertNotEqual(
                f[3], 0xFF, "array was expected in a paged bank, not resident"
            )

    def test_inline_array_resident_48k(self):
        """48k: a resident array reached by name via CYD_PEEK/CYD_POKE (bank $FF)."""
        self._array_roundtrip(ARR_RESIDENT, "48k", "48k", resident=True)

    def test_inline_array_banked_128k(self):
        """128k: array forced into a paged bank; the broker pages it in/out."""
        self._array_roundtrip(_arr_banked_src(), "128k", "128k", resident=False)

    def _map_roundtrip(self, src, model, machine, resident):
        with tempfile.TemporaryDirectory(prefix="cyd_map_") as wd:
            tap, flags = compile_cyd(src, model, wd)
            f = run_in_zesarux(tap, flags, n_bytes=6, machine=machine, max_wait=45.0)
        self.assertEqual(f[0], 12, "CYD_ARR_MAP/FLUSH did not persist inv[0] (11->12)")
        self.assertEqual(f[1], 45, "CYD_ARR_MAP/FLUSH did not persist inv[3] (44->45)")
        self.assertEqual(f[4], 123, "interpreter did not resume after CALL")
        if resident:
            self.assertEqual(f[3], 0xFF, "resident array should report bank $FF")
        else:
            self.assertNotEqual(
                f[3], 0xFF, "array was expected in a paged bank, not resident"
            )

    def test_inline_array_map_resident_48k(self):
        """48k: CYD_ARR_MAP returns the array in place; FLUSH is a no-op."""
        self._map_roundtrip(ARR_MAP_RESIDENT, "48k", "48k", resident=True)

    def test_inline_array_map_banked_128k(self):
        """128k: CYD_ARR_MAP copies a paged array to the scratch; FLUSH writes back."""
        self._map_roundtrip(_arr_map_banked_src(), "128k", "128k", resident=False)

    def _cyd_call_roundtrip(self, src, model, machine):
        with tempfile.TemporaryDirectory(prefix="cyd_ccall_") as wd:
            tap, flags = compile_cyd(src, model, wd)
            f = run_in_zesarux(tap, flags, n_bytes=4, machine=machine, max_wait=45.0)
        self.assertEqual(f[0], 11, "caller block did not run before CYD_CALL")
        self.assertEqual(f[1], 55, "CYD_CALL did not reach the callee in the other block")
        self.assertEqual(f[2], 123, "interpreter did not resume after the CALL")

    def test_inline_cyd_call_48k(self):
        """48k: cross-block native call through the resident dispatch table."""
        self._cyd_call_roundtrip(_cyd_call_src(), "48k", "48k")

    def test_inline_cyd_call_128k(self):
        """128k: CYD_CALL between two blocks (banked callee and caller)."""
        self._cyd_call_roundtrip(_cyd_call_src(), "128k", "128k")

    def test_inline_cyd_call_crossbank_128k(self):
        """128k: caller and callee forced into different RAM banks; CYD_CALL pages
        the callee in and the caller back."""
        self._cyd_call_roundtrip(_cyd_call_src(filler=15000), "128k", "128k")


# Broker extirpation (UNUSED_ARR_BROKER): the resident CYD_PEEK/POKE/ARR_MAP/
# ARR_FLUSH services must be stripped from the build when no native routine
# references them. This is a compile-time check (reads the engine symbol dump),
# so it only needs sjasmplus, not the full emulator.
EXTERN_NO_ARRAY = (
    "[[\n"
    "ASM nativo\n"
    "    ld a, 42\n"
    "    ld (de), a\n"
    "    ret\n"
    "ENDASM\n"
    "CALL nativo\n"
    "SET 2 TO 123\n"
    "LABEL spin\n"
    "GOTO spin\n"
    "]]\n"
)

EXTERN_WITH_ARRAY = (
    "[[\n"
    "DIM inv(4) = {11, 22, 33, 44}\n"
    "ASM nativo\n"
    "    ld a, ARR_inv_BANK\n"
    "    ld hl, ARR_inv\n"
    "    call CYD_PEEK\n"
    "    ld (FLAGS), a\n"
    "    ret\n"
    "ENDASM\n"
    "CALL nativo\n"
    "SET 2 TO 123\n"
    "LABEL spin\n"
    "GOTO spin\n"
    "]]\n"
)


@unittest.skipUnless(find_sjasmplus(), "sjasmplus not found under tools/")
class TestBrokerExtirpation(unittest.TestCase):
    def _sym_has(self, src, symbol, model="48k"):
        with tempfile.TemporaryDirectory(prefix="cyd_strip_") as wd:
            compile_cyd(src, model, wd)  # writes cyd.sym in wd
            sym = Path(wd) / "cyd.sym"
            text = sym.read_text(encoding="utf-8", errors="ignore") if sym.is_file() else ""
        return symbol in text

    def test_broker_stripped_when_unused(self):
        """A native routine that never touches an array drops the whole broker."""
        self.assertFalse(
            self._sym_has(EXTERN_NO_ARRAY, "CYD_PEEK"),
            "broker should be extirpated when no routine references it",
        )

    def test_broker_kept_when_used(self):
        """A native routine that reaches an array keeps the broker resident."""
        self.assertTrue(
            self._sym_has(EXTERN_WITH_ARRAY, "CYD_PEEK"),
            "broker must be present when a routine references it",
        )

    def test_cyd_call_stripped_when_unused(self):
        """No CYD_CALL anywhere -> the trampoline is extirpated (UNUSED_CYD_CALL)."""
        self.assertFalse(
            self._sym_has(EXTERN_NO_ARRAY, "CYD_CALL"),
            "CYD_CALL should be stripped when no routine references it",
        )

    def test_cyd_call_kept_when_used(self):
        """A cross-block CYD_CALL keeps the trampoline resident."""
        self.assertTrue(
            self._sym_has(_cyd_call_src(), "CYD_CALL"),
            "CYD_CALL must be present when a routine references it",
        )


if __name__ == "__main__":
    unittest.main()
