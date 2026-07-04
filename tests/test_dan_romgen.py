"""Regression tests for dan_romgen (the pure-Python Dandanator ROM assembler).

The expected SHA-256 hashes below were captured from output that is byte-for-byte
identical to the reference tool (grelobites/dandanator-mini v10.4.3), whose ROMs
are confirmed to boot on real hardware and on EsPectrum. These tests therefore
guard the Dandanator ROM generation without needing Java or any manual check.
"""
import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import dan_romgen  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _game(path: Path, name: str) -> dict:
    data = path.read_bytes()
    return {
        "data": data,
        "num_slots": len(data) // 0x4000,
        "mld_type": data[16363],
        "header_slot": 0,
        "display_name": name,
    }


class TestDanRomgen(unittest.TestCase):
    # SHA-256 of ROMs byte-identical to dandanator-mini v10.4.3 (default es locale).
    EXPECTED = {
        "mini48": "50ee0d96f8429bda8431f3db50d6e0f39d27dba2488a5c2ec540629787dd953a",
        "test128": "269ed3a805c27f93d86ef3a7186288d93ca09b5f2f1e5f3a11bd969eccc13a22",
        "two": "509dfde7031fde0953e0f0842d39059a70c1804b3299102b17907039f2bb7302",
    }

    def _sha(self, rom: bytes) -> str:
        return hashlib.sha256(rom).hexdigest()

    def test_mld48_single(self):
        rom = dan_romgen.build_dandanator_rom([_game(FIXTURES / "mini48.mld", "MINI48")])
        self.assertEqual(len(rom), 0x80000)
        self.assertEqual(self._sha(rom), self.EXPECTED["mini48"])

    def test_mld128_single(self):
        rom = dan_romgen.build_dandanator_rom([_game(FIXTURES / "test128.mld", "TEST")])
        self.assertEqual(len(rom), 0x80000)
        self.assertEqual(self._sha(rom), self.EXPECTED["test128"])

    def test_two_games(self):
        rom = dan_romgen.build_dandanator_rom([
            _game(FIXTURES / "mini48.mld", "MINI48"),
            _game(FIXTURES / "test128.mld", "TEST"),
        ])
        self.assertEqual(self._sha(rom), self.EXPECTED["two"])

    def test_menu_infrastructure_present(self):
        # The bug that motivated this work: an empty menu zone (CBlocks table and
        # slot 1) makes the firmware hang. Guard against a regression.
        rom = dan_romgen.build_dandanator_rom([_game(FIXTURES / "test128.mld", "TEST")])
        self.assertNotEqual(rom[16360:16380], bytes(20), "CBlocks table must not be empty")
        self.assertNotEqual(rom[16384:16384 + 300], bytes(300), "slot 1 must not be empty")

    def test_autoboot_flag(self):
        rom = dan_romgen.build_dandanator_rom(
            [_game(FIXTURES / "test128.mld", "TEST")], autoboot=True)
        self.assertEqual(rom[16381], 1)

    # ---- optional overrides (standalone GUI) --------------------------------
    def test_disable_border_flag(self):
        g = _game(FIXTURES / "test128.mld", "TEST")
        self.assertEqual(dan_romgen.build_dandanator_rom([g])[16380], 0)
        self.assertEqual(dan_romgen.build_dandanator_rom([g], disable_border=True)[16380], 1)

    def test_text_override_is_deterministic_and_changes_output(self):
        g = _game(FIXTURES / "test128.mld", "TEST")
        base = self._sha(dan_romgen.build_dandanator_rom([g]))
        a = self._sha(dan_romgen.build_dandanator_rom([g], text_launchgame="Play"))
        b = self._sha(dan_romgen.build_dandanator_rom([g], text_launchgame="Play"))
        self.assertNotEqual(a, base)
        self.assertEqual(a, b, "text override must be deterministic")

    def test_charset_override(self):
        g = _game(FIXTURES / "test128.mld", "TEST")
        base = self._sha(dan_romgen.build_dandanator_rom([g]))
        rom = dan_romgen.build_dandanator_rom([g], charset=bytes(range(256)) * 3)  # 768 B
        self.assertEqual(len(rom), 0x80000)
        self.assertNotEqual(self._sha(rom), base)
        with self.assertRaises(ValueError):
            dan_romgen.build_dandanator_rom([g], charset=b"\x00" * 100)

    def test_background_override_changes_output(self):
        g = _game(FIXTURES / "test128.mld", "TEST")
        base = self._sha(dan_romgen.build_dandanator_rom([g]))
        rom = dan_romgen.build_dandanator_rom([g], background_scr=bytes(6912))
        self.assertEqual(len(rom), 0x80000)
        self.assertNotEqual(self._sha(rom), base)


if __name__ == "__main__":
    unittest.main()
