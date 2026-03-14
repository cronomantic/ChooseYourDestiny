import re
import unittest
import sys
import tempfile
import importlib
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

cyd = importlib.import_module("cyd")


class _DummyResult:
    returncode = 0
    stderr = ""


class TestMldFooter(unittest.TestCase):
    def _build_with_fake_assembler(self, loading_scr, mld_type):
        captured = {"loader_asm": ""}

        def fake_run_assembler(asm_path, asm, filename, listing=True, capture_output=False):
            filename_str = str(filename)
            if filename_str.endswith("cyd.asm"):
                out_dir = Path(filename_str).parent
                interp_path = out_dir / "__INTERP.BIN"
                interp_path.write_bytes(bytes([1, 2, 3, 4]))
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
                    mld_name="test_mld",
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
                    mld_type=mld_type,
                    mld_is_128=False,
                    name="TEST",
                )

        return captured["loader_asm"]

    def test_footer_contains_type_and_preview_when_scr_is_present(self):
        asm = self._build_with_fake_assembler(loading_scr=bytes([0] * 6912), mld_type="$83")
        self.assertIn("DEFB $83", asm)
        self.assertIn("DEFW PREVIEW_SCREEN", asm)
        self.assertIn("DEFW PREVIEW_SCREEN_END-PREVIEW_SCREEN", asm)
        self.assertRegex(asm, r"PREVIEW_SCREEN:\n\s*DEFB\s+\$")

    def test_footer_has_zero_preview_fields_without_scr(self):
        asm = self._build_with_fake_assembler(loading_scr=None, mld_type="$88")
        self.assertIn("DEFB $88", asm)
        self.assertIn("DEFW 0 ; Preview screen addr", asm)
        self.assertIn("DEFW 0 ; Preview screen size", asm)


if __name__ == "__main__":
    unittest.main()
