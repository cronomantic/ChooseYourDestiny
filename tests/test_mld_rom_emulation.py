"""
Tests for the MLD ROM emulation fixes:
  1. inkey.asm wraps ROM calls with RESTORE_DAN_ROM / SET_DAN_BANK when
     IS_MLD_DAN is defined, so KEY_SCAN/K_TEST/K_DECODE are reachable.
  2. cyd_mld.asm decompresses and displays the loading/intro screen at
     startup when MLD_HAS_INTRO_SCR is defined.
  3. get_asm_mld / get_asm_mld128 accept loading_scr and forward it to
     the assembled interpreter binary.
  4. Makefile BASE_ROM path no longer has a stray trailing quote.
"""

import importlib
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

cyd = importlib.import_module("cyd")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _DummyResult:
    returncode = 0
    stderr = ""


def _capture_mld_asms(mld_is_128=False, loading_scr=None):
    """Run do_asm_mld with a fake assembler and return the captured ASM texts."""
    captured = {"interpreter_asm": "", "loader_asm": ""}

    def fake_run_assembler(asm_path, asm, filename, listing=True, capture_output=False):  # noqa: ARG001
        filename_str = str(filename)
        if filename_str.endswith("cyd.asm"):
            captured["interpreter_asm"] = asm
            out_dir = Path(filename_str).parent
            (out_dir / "__INTERP.BIN").write_bytes(bytes([0xAA]) * 64)
        elif filename_str.endswith("cyd_loader_mld.asm"):
            captured["loader_asm"] = asm
            m = re.search(r'SAVEBIN\s+"([^"]+)"', asm)
            if m:
                Path(m.group(1)).write_bytes(bytes([0xFF]) * 0x4000)
        return _DummyResult()

    with tempfile.TemporaryDirectory() as tmp:
        with patch("cyd.run_assembler", side_effect=fake_run_assembler):
            cyd.do_asm_mld(
                sjasmplus_path="tools/sjasmplus.exe",
                output_path=tmp,
                verbose=False,
                mld_name="test",
                index=[],
                blocks=[],
                banks=[],
                size_interpreter=0,
                bank0_offset=0x8000,
                tokens=[],
                chars=[],
                charw=[],
                sfx_asm=None,
                loading_scr=loading_scr,
                has_tracks=False,
                mld_type="$88" if mld_is_128 else "$83",
                mld_is_128=mld_is_128,
                name="TEST",
            )

    return captured


# ---------------------------------------------------------------------------
# Test: INKEY ROM call guard (IS_MLD_DAN)
# ---------------------------------------------------------------------------

class TestInkeyMldDanGuard(unittest.TestCase):
    def _get_interpreter_asm(self, mld_is_128=False):
        captured = _capture_mld_asms(mld_is_128=mld_is_128)
        return captured["interpreter_asm"]

    def test_restore_dan_rom_called_before_key_scan_in_mld(self):
        asm = self._get_interpreter_asm(mld_is_128=False)
        # RESTORE_DAN_ROM must appear before the first KEY_SCAN call inside INKEY
        restore_pos = asm.find("call RESTORE_DAN_ROM")
        key_scan_pos = asm.find("call KEY_SCAN")
        self.assertGreater(restore_pos, -1, "RESTORE_DAN_ROM should be present")
        self.assertGreater(key_scan_pos, -1, "KEY_SCAN should be present")
        self.assertLess(
            restore_pos,
            key_scan_pos,
            "RESTORE_DAN_ROM must come before KEY_SCAN in the INKEY function",
        )

    def test_set_dan_bank_called_after_key_decode(self):
        asm = self._get_interpreter_asm(mld_is_128=False)
        # SET_DAN_BANK must appear after K_DECODE (to re-map the script slot)
        k_decode_pos = asm.find("call K_DECODE")
        set_dan_pos = asm.find("call SET_DAN_BANK", k_decode_pos)
        self.assertGreater(k_decode_pos, -1, "K_DECODE should be present")
        self.assertGreater(
            set_dan_pos,
            k_decode_pos,
            "SET_DAN_BANK must be called after K_DECODE in the success path",
        )

    def test_set_dan_bank_on_empty_inkey(self):
        asm = self._get_interpreter_asm(mld_is_128=False)
        # There must be a SET_DAN_BANK call in the empty_inkey path too
        empty_pos = asm.find(".empty_inkey:")
        self.assertGreater(empty_pos, -1, ".empty_inkey label should be present")
        set_dan_pos = asm.find("call SET_DAN_BANK", empty_pos)
        self.assertGreater(
            set_dan_pos,
            empty_pos,
            "SET_DAN_BANK must be called in the .empty_inkey path",
        )

    def test_mld128_also_has_restore_and_remap(self):
        asm = self._get_interpreter_asm(mld_is_128=True)
        self.assertIn("call RESTORE_DAN_ROM", asm)
        self.assertIn("call SET_DAN_BANK", asm)

    def test_script_bank_used_for_remap(self):
        asm = self._get_interpreter_asm(mld_is_128=False)
        # The remap should use SCRIPT_BANK (not a hard-coded slot number)
        self.assertIn("ld a, (SCRIPT_BANK)", asm)


# ---------------------------------------------------------------------------
# Test: Intro screen display at MLD startup
# ---------------------------------------------------------------------------

class TestMldIntroScreen(unittest.TestCase):
    FAKE_SCR = bytes(6912)  # 6144 pixels + 768 attrs, all zeros

    def test_no_intro_screen_without_loading_scr(self):
        captured = _capture_mld_asms(loading_scr=None)
        asm = captured["interpreter_asm"]
        # The DEFINE directive must be absent when no loading_scr is given.
        # The IFDEF guard lines are always in the source but are never activated
        # because the DEFINE is not emitted, so MLD_INTRO_SCR_BYTES is empty.
        self.assertNotIn("DEFINE MLD_HAS_INTRO_SCR", asm)
        # Compressed data bytes must not appear (the DEFB block should be empty)
        # Confirm the data section has no actual DEFB content under the label
        ifdef_block = ""
        in_block = False
        for line in asm.splitlines():
            if "IFDEF MLD_HAS_INTRO_SCR" in line:
                in_block = True
            elif in_block and "ENDIF" in line:
                in_block = False
            elif in_block:
                ifdef_block += line + "\n"
        # Inside the IFDEF block there must be no DEFB data
        self.assertNotIn("DEFB", ifdef_block)

    def test_intro_screen_define_present_with_loading_scr(self):
        with patch("cyd.zx7_compress_data", return_value=bytes([0x01, 0x02, 0x03])):
            captured = _capture_mld_asms(loading_scr=self.FAKE_SCR)
        asm = captured["interpreter_asm"]
        self.assertIn("DEFINE MLD_HAS_INTRO_SCR", asm)

    def test_intro_screen_data_bytes_present(self):
        compressed = bytes([0xDE, 0xAD, 0xBE, 0xEF])
        with patch("cyd.zx7_compress_data", return_value=compressed):
            captured = _capture_mld_asms(loading_scr=self.FAKE_SCR)
        asm = captured["interpreter_asm"]
        self.assertIn("MLD_INTRO_SCR_DATA:", asm)
        # All compressed bytes must appear as DEFB entries
        for b in compressed:
            self.assertIn(f"${b:02X}", asm)

    def test_intro_screen_decompression_code_present(self):
        with patch("cyd.zx7_compress_data", return_value=bytes([0xAB])):
            captured = _capture_mld_asms(loading_scr=self.FAKE_SCR)
        asm = captured["interpreter_asm"]
        self.assertIn("MLD_INTRO_SCR_DATA", asm)
        self.assertIn("SCR_PXL", asm)
        # dzx0_turbo is the ZX Spectrum decompressor used throughout the project
        # for data compressed with pyZX7 (ZX7/ZX0 compatible format).
        self.assertIn("dzx0_turbo", asm)

    def test_mld128_also_emits_intro_screen(self):
        compressed = bytes([0x11, 0x22])
        with patch("cyd.zx7_compress_data", return_value=compressed):
            captured = _capture_mld_asms(mld_is_128=True, loading_scr=self.FAKE_SCR)
        asm = captured["interpreter_asm"]
        self.assertIn("DEFINE MLD_HAS_INTRO_SCR", asm)
        self.assertIn("MLD_INTRO_SCR_DATA:", asm)


# ---------------------------------------------------------------------------
# Test: Makefile BASE_ROM path correctness
# ---------------------------------------------------------------------------

class TestMakefileBaseRom(unittest.TestCase):
    def test_base_rom_no_trailing_quote(self):
        makefile = Path(__file__).parent.parent / "Makefile"
        content = makefile.read_text(encoding="utf-8")
        for line in content.splitlines():
            if "BASE_ROM" in line and ":=" in line:
                value = line.split(":=", 1)[1].strip()
                self.assertFalse(
                    value.endswith('"'),
                    f"BASE_ROM value has a trailing quote: {line!r}",
                )

    def test_base_rom_points_to_correct_file(self):
        makefile = Path(__file__).parent.parent / "Makefile"
        content = makefile.read_text(encoding="utf-8")
        for line in content.splitlines():
            if line.strip().startswith("BASE_ROM") and ":=" in line:
                value = line.split(":=", 1)[1].strip()
                self.assertIn(
                    "dandanator-mini.rom",
                    value,
                    "BASE_ROM should reference dandanator-mini.rom",
                )


if __name__ == "__main__":
    unittest.main()
