"""Tests for mld2rom.py — empirical validation of MLD → ROM packaging.

These tests exercise the public functions of mld2rom.py with synthetic MLD
binaries built in-memory, so they run without sjasmplus and without any real
MLD file from a CYD compilation. The goal is to detect regressions in the
packaging logic (slot allocation, footer patching, game-struct emission,
validation severity classification).
"""

import importlib.util
import struct
import sys
import tempfile
import unittest
from pathlib import Path

# Dandanator/MLD aparcado: el soporte MLD no arranca y se ha ocultado de las
# superficies de usuario. Estos tests quedan aquí (decorados con @unittest.skip)
# para retomarlos en el futuro.
_MLD_PARKED = "Soporte Dandanator/MLD aparcado"


REPO_ROOT = Path(__file__).parent.parent
MLD2ROM_PATH = REPO_ROOT / "mld2rom.py"

_spec = importlib.util.spec_from_file_location("mld2rom", MLD2ROM_PATH)
mld2rom = importlib.util.module_from_spec(_spec)
sys.modules["mld2rom"] = mld2rom
_spec.loader.exec_module(mld2rom)


SLOT = mld2rom.SLOT_SIZE
ROM_SIZE = mld2rom.ROM_SIZE
HDR = mld2rom.MLD_HEADER_OFFSET
SIG_OFF = mld2rom.MLD_SIGNATURE_OFFSET


def make_mld(
    num_slots: int = 2,
    mld_type: int = mld2rom.MLD_TYPE_48K,
    base_slot: int = 0,
    req_sectors: int = 4,
    sector_ids=(0, 0, 0, 0),
    table_offset: int = 0,
    table_row_size: int = 0,
    table_rows: int = 0,
    row_slot_off: int = 0,
    screen_offset: int = 0,
    screen_size: int = 0,
    signature: bytes = b"MLD",
    null_term: int = 0,
    header_slot: int = 0,
    fill_byte: int = 0x00,
) -> bytearray:
    """Build a synthetic MLD binary with a controllable footer.

    Defaults produce a footer that passes validation with zero CRITICAL/ERROR
    issues (it may still emit INFO/WARNING about specific fields).
    """
    data = bytearray([fill_byte]) * (num_slots * SLOT)
    base = header_slot * SLOT + HDR
    data[base + 0] = base_slot & 0xFF
    data[base + 1] = mld_type & 0xFF
    data[base + 2] = req_sectors & 0xFF
    for i, b in enumerate(sector_ids):
        data[base + 3 + i] = b & 0xFF
    struct.pack_into("<H", data, base + 7, table_offset)
    struct.pack_into("<H", data, base + 9, table_row_size)
    struct.pack_into("<H", data, base + 11, table_rows)
    data[base + 13] = row_slot_off & 0xFF
    struct.pack_into("<H", data, base + 14, screen_offset)
    struct.pack_into("<H", data, base + 16, screen_size)
    data[base + 18 : base + 21] = signature
    data[base + 21] = null_term & 0xFF
    return data


def make_base_rom_firmware_only() -> bytes:
    """Minimal 3584-byte 'firmware-only' base ROM (auto-padded by mld2rom)."""
    return bytes(mld2rom.BASEROM_SIZE)


def make_base_rom_empty_full() -> bytearray:
    """Full 524288-byte empty base ROM (zero games)."""
    rom = bytearray(ROM_SIZE)
    return rom


def severities(issues):
    return [sev for sev, _ in issues]


@unittest.skip(_MLD_PARKED)
class ValidateMldFileTests(unittest.TestCase):
    """Test 1 + Test 2: validate_mld_file() behaviour on clean and defective MLDs."""

    def test_clean_mld_has_no_critical_or_error(self):
        data = make_mld()
        issues = mld2rom.validate_mld_file(data, "synthetic")
        sevs = severities(issues)
        self.assertNotIn(mld2rom.SEV_CRITICAL, sevs)
        self.assertNotIn(mld2rom.SEV_ERROR, sevs)

    def test_empty_file_is_critical(self):
        issues = mld2rom.validate_mld_file(b"", "empty")
        self.assertEqual(severities(issues), [mld2rom.SEV_CRITICAL])

    def test_truncated_size_is_critical(self):
        data = make_mld()[: SLOT + 100]
        issues = mld2rom.validate_mld_file(data, "trunc")
        self.assertIn(mld2rom.SEV_CRITICAL, severities(issues))

    def test_missing_signature_is_critical(self):
        data = make_mld(signature=b"XXX")
        issues = mld2rom.validate_mld_file(data, "no_sig")
        self.assertIn(mld2rom.SEV_CRITICAL, severities(issues))

    def test_unknown_type_is_error(self):
        data = make_mld(mld_type=0x77)
        issues = mld2rom.validate_mld_file(data, "bad_type")
        sevs = severities(issues)
        self.assertIn(mld2rom.SEV_ERROR, sevs)
        self.assertNotIn(mld2rom.SEV_CRITICAL, sevs)

    def test_nonzero_null_terminator_is_error(self):
        data = make_mld(null_term=0xAB)
        issues = mld2rom.validate_mld_file(data, "bad_null")
        self.assertIn(mld2rom.SEV_ERROR, severities(issues))

    def test_screen_outside_slot_is_error(self):
        data = make_mld(screen_offset=0x3F00, screen_size=0x0200)
        issues = mld2rom.validate_mld_file(data, "bad_scr")
        self.assertIn(mld2rom.SEV_ERROR, severities(issues))

    def test_nsectors_too_large_is_error(self):
        data = make_mld(num_slots=2, req_sectors=100)
        issues = mld2rom.validate_mld_file(data, "nsec")
        self.assertIn(mld2rom.SEV_ERROR, severities(issues))

    def test_nonzero_base_slot_is_warning_only(self):
        data = make_mld(base_slot=5)
        issues = mld2rom.validate_mld_file(data, "warn_base")
        sevs = severities(issues)
        self.assertIn(mld2rom.SEV_WARNING, sevs)
        self.assertNotIn(mld2rom.SEV_CRITICAL, sevs)
        self.assertNotIn(mld2rom.SEV_ERROR, sevs)


@unittest.skip(_MLD_PARKED)
class ParseMldTests(unittest.TestCase):
    """Test 3: parse_mld() returns consistent metadata."""

    def test_parse_extracts_expected_metadata(self):
        data = make_mld(num_slots=3, mld_type=mld2rom.MLD_TYPE_128K)
        info = mld2rom.parse_mld(data, "synthetic")
        self.assertEqual(info["num_slots"], 3)
        self.assertEqual(info["mld_type"], mld2rom.MLD_TYPE_128K)
        self.assertEqual(info["header_slot"], 0)
        self.assertEqual(info["screen_offset"], 0)
        self.assertEqual(info["screen_size"], 0)
        self.assertEqual(info["footer"]["signature"], b"MLD")

    def test_parse_raises_on_missing_signature(self):
        data = make_mld(signature=b"ZZZ")
        with self.assertRaises(mld2rom.MLDParseError):
            mld2rom.parse_mld(data, "no_sig")

    def test_parse_raises_on_non_multiple_size(self):
        data = make_mld()[:100]
        with self.assertRaises(mld2rom.MLDParseError):
            mld2rom.parse_mld(data, "trunc")


@unittest.skip(_MLD_PARKED)
class BuildGameStructTests(unittest.TestCase):
    """Test 4: build_game_struct() byte-level output."""

    def test_struct_size_is_131_bytes(self):
        gs = mld2rom.build_game_struct(0, "Foo", mld2rom.MLD_TYPE_48K, 28, 2)
        self.assertEqual(len(gs), mld2rom.GAME_STRUCT_SIZE)

    def test_struct_encodes_type_slot_and_size(self):
        gs = mld2rom.build_game_struct(0, "Foo", mld2rom.MLD_TYPE_48K, 28, 2)
        self.assertEqual(gs[mld2rom._GS_TYPE_ID], mld2rom.MLD_TYPE_48K)
        self.assertEqual(gs[mld2rom._GS_COMPRESSED], 0)
        cb = mld2rom._GS_CBLOCKS
        self.assertEqual(gs[cb], 28)
        self.assertEqual(struct.unpack_from("<H", gs, cb + 1)[0], 0)
        self.assertEqual(struct.unpack_from("<H", gs, cb + 3)[0], 2)
        for i in range(5, 40):
            self.assertEqual(gs[cb + i], 0xFF, f"CBlock pad byte {i} not 0xFF")

    def test_struct_encodes_name_with_slot_digit_prefix(self):
        gs = mld2rom.build_game_struct(2, "Adventure", mld2rom.MLD_TYPE_48K, 25, 3)
        name_bytes = gs[mld2rom._GS_GAMENAME : mld2rom._GS_GAMENAME + mld2rom.GAMENAME_SIZE]
        self.assertEqual(name_bytes[0:1], b"3")
        self.assertEqual(name_bytes[1:3], b"  ")
        self.assertTrue(name_bytes.startswith(b"3  Adventure\x00"))
        self.assertEqual(name_bytes[-1], 0)

    def test_struct_truncates_long_names(self):
        long_name = "A" * 50
        gs = mld2rom.build_game_struct(0, long_name, mld2rom.MLD_TYPE_48K, 28, 1)
        self.assertEqual(len(gs), mld2rom.GAME_STRUCT_SIZE)
        self.assertEqual(gs[mld2rom._GS_GAMENAME + mld2rom.GAMENAME_SIZE - 1], 0)


@unittest.skip(_MLD_PARKED)
class Mld2RomEndToEndTests(unittest.TestCase):
    """Test 5, 6, 7, 8: full pipeline through mld2rom()."""

    def _write(self, data, name):
        path = Path(self._tmp.name) / name
        path.write_bytes(bytes(data))
        return str(path)

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self._tmp.cleanup()

    def _run(self, *mld_files, base=None, autoboot=False, names=None):
        base_path = self._write(base if base is not None else make_base_rom_firmware_only(), "base.rom")
        out_path = str(Path(self._tmp.name) / "out.rom")
        mld2rom.mld2rom(
            base_rom_path=base_path,
            mld_paths=list(mld_files),
            output_path=out_path,
            names=names or [],
            autoboot=autoboot,
            verbose=False,
            validate=True,
        )
        return bytearray(Path(out_path).read_bytes())

    def test_single_game_writes_valid_rom(self):
        mld = make_mld(num_slots=2)
        mld_path = self._write(mld, "g1.mld")
        out = self._run(mld_path)

        self.assertEqual(len(out), ROM_SIZE)
        self.assertEqual(out[mld2rom.GAME_COUNT_OFFSET], 1)

        used = mld2rom.read_existing_uncompressed_slots(out)
        self.assertEqual(len(used), 1)
        start_slot, num_slots = used[0]
        self.assertEqual(num_slots, 2)

        # MLDoffset patched to start_slot
        patched = out[start_slot * SLOT + HDR]
        self.assertEqual(patched, start_slot & 0xFF)

        # Signature survives at start_slot
        self.assertEqual(
            bytes(out[start_slot * SLOT + SIG_OFF : start_slot * SLOT + SIG_OFF + 3]),
            b"MLD",
        )

    def test_autoboot_sets_byte(self):
        mld = make_mld()
        mld_path = self._write(mld, "g.mld")
        out = self._run(mld_path, autoboot=True)
        self.assertEqual(out[mld2rom.AUTOBOOT_OFFSET], 1)

        out_no_auto = self._run(mld_path, autoboot=False)
        self.assertEqual(out_no_auto[mld2rom.AUTOBOOT_OFFSET], 0)

    def test_two_games_in_one_invocation(self):
        m1 = make_mld(num_slots=2)
        m2 = make_mld(num_slots=3, mld_type=mld2rom.MLD_TYPE_128K)
        p1 = self._write(m1, "g1.mld")
        p2 = self._write(m2, "g2.mld")
        out = self._run(p1, p2)

        self.assertEqual(out[mld2rom.GAME_COUNT_OFFSET], 2)
        used = mld2rom.read_existing_uncompressed_slots(out)
        self.assertEqual(len(used), 2)

        # Slot ranges must not overlap
        ranges = sorted([(s, s + n) for s, n in used])
        for (a_lo, a_hi), (b_lo, _) in zip(ranges, ranges[1:]):
            self.assertLessEqual(a_hi, b_lo, f"slots {ranges} overlap")

        # Both signatures land at their respective start_slot
        for s, _n in used:
            sig = bytes(out[s * SLOT + SIG_OFF : s * SLOT + SIG_OFF + 3])
            self.assertEqual(sig, b"MLD", f"missing MLD signature at slot {s}")

    def test_append_to_rom_with_existing_game(self):
        """Regression A2: adding a second game to a ROM that already has one
        must not overwrite the first."""
        # First invocation: add one game to a clean ROM.
        m1 = make_mld(num_slots=2)
        p1 = self._write(m1, "g1.mld")
        first_out = self._run(p1)
        first_used = mld2rom.read_existing_uncompressed_slots(first_out)
        self.assertEqual(len(first_used), 1)
        first_slot, first_n = first_used[0]
        first_sig = bytes(
            first_out[first_slot * SLOT + SIG_OFF : first_slot * SLOT + SIG_OFF + 3]
        )

        # Second invocation: use the previous output as base, add a second game.
        m2 = make_mld(num_slots=3)
        p2 = self._write(m2, "g2.mld")
        second_out = self._run(p2, base=first_out)

        # The first game's signature must still be intact.
        still_there = bytes(
            second_out[first_slot * SLOT + SIG_OFF : first_slot * SLOT + SIG_OFF + 3]
        )
        self.assertEqual(still_there, first_sig, "first MLD was overwritten")

        used = mld2rom.read_existing_uncompressed_slots(second_out)
        self.assertEqual(len(used), 2)
        # Both ranges must be disjoint
        ranges = sorted([(s, s + n) for s, n in used])
        for (_, a_hi), (b_lo, _) in zip(ranges, ranges[1:]):
            self.assertLessEqual(a_hi, b_lo, f"slot ranges overlap: {ranges}")

    def test_validation_errors_abort_with_systemexit(self):
        """A malformed MLD must abort the run (sys.exit) rather than producing
        a silent bad ROM."""
        bad = make_mld(mld_type=0x77)  # unknown type → SEV_ERROR
        bad_path = self._write(bad, "bad.mld")
        base_path = self._write(make_base_rom_firmware_only(), "base.rom")
        out_path = str(Path(self._tmp.name) / "out.rom")
        with self.assertRaises(SystemExit):
            mld2rom.mld2rom(
                base_rom_path=base_path,
                mld_paths=[bad_path],
                output_path=out_path,
                names=[],
                autoboot=False,
                verbose=False,
                validate=True,
            )


if __name__ == "__main__":
    unittest.main()
