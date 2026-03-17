import importlib
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

cyd = importlib.import_module("cyd")


class _DummyResult:
    returncode = 0
    stderr = ""


class TestMldIndexMapping(unittest.TestCase):
    def _build_and_capture(self, mld_is_128: bool):
        captured = {"interpreter_asm": "", "loader_asm": ""}

        def fake_run_assembler(asm_path, asm, filename, listing=True, capture_output=False):
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

        # Two aggregated payload banks to force deterministic slot mapping:
        # bank 0 -> slot 2, bank 3 -> slot 3.
        test_index = [
            (0, 0, 0, 0x9000),  # TXT in bank 0 -> must become slot 2
            (1, 0, 3, 0xC000),  # SCR in bank 3 -> must become slot 3
            (2, 0, 0, 0xC123),  # TRK in bank 0 -> keep RAM-bank semantics on mld128
        ]
        test_blocks = [bytes([1] * 32), bytes([2] * 32)]
        test_banks = [0, 3]

        with tempfile.TemporaryDirectory() as tmp:
            with patch("cyd.run_assembler", side_effect=fake_run_assembler):
                cyd.do_asm_mld(
                    sjasmplus_path="tools/sjasmplus.exe",
                    output_path=tmp,
                    verbose=False,
                    mld_name="test",
                    index=test_index,
                    blocks=test_blocks,
                    banks=test_banks,
                    size_interpreter=0,
                    bank0_offset=0x8000,
                    tokens=[],
                    chars=[],
                    charw=[],
                    sfx_asm=None,
                    loading_scr=None,
                    has_tracks=True,
                    mld_type="$88" if mld_is_128 else "$83",
                    mld_is_128=mld_is_128,
                    name="TEST",
                )

        return captured

    def test_mld_remaps_txt_scr_to_dandanator_slots(self):
        captured = self._build_and_capture(mld_is_128=False)
        asm = captured["interpreter_asm"]
        loader = captured["loader_asm"]

        # TXT/SCR entries must carry Dandanator slot IDs (2 and 3 here).
        self.assertIn("DEFB $0, $0, $2", asm)
        self.assertIn("DEFB $1, $0, $3", asm)

        # Strict mld should preload only interpreter to RAM (slot 1 entry only).
        block_section = loader.split("BLOCK_TABLE:", 1)[1].split("PREVIEW_SCREEN:", 1)[0]
        self.assertIn("DEFB $01", block_section)
        self.assertNotIn("DEFB $02", block_section)
        self.assertNotIn("DEFB $03", block_section)

    def test_mld128_keeps_music_ram_semantics(self):
        captured = self._build_and_capture(mld_is_128=True)
        asm = captured["interpreter_asm"]
        loader = captured["loader_asm"]

        # TXT/SCR still remapped to Dandanator slots.
        self.assertIn("DEFB $0, $0, $2", asm)
        self.assertIn("DEFB $1, $0, $3", asm)

        # TRK keeps RAM-bank semantic in index for mld128.
        self.assertIn("DEFB $2, $0, $0", asm)

        # mld128 preloads data blocks to RAM as well.
        block_section = loader.split("BLOCK_TABLE:", 1)[1].split("PREVIEW_SCREEN:", 1)[0]
        self.assertIn("DEFB $01", block_section)
        self.assertIn("DEFB $02", block_section)


if __name__ == "__main__":
    unittest.main()
