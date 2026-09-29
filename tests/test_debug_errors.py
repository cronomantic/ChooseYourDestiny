"""--debug-errors: a system error shows where it happened.

The opcodes that can end in a system error note their address (DEBUG_POS) and
SYS_ERROR prints it after the error number, as " at chunk:address". The
compiler writes a .map with the chunk and address of every statement, so that
turns into a file and a line: the last statement of that chunk whose address is
not greater. Without the option nothing is added to the interpreter.
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import (  # noqa: E402
    MACHINE_BY_MODEL, _parse_label_addr, compile_cyd, emulator_available, find_sjasmplus,
    run_in_zesarux,
)

REPO = Path(__file__).resolve().parent.parent
CYDC = REPO / "src" / "cydc" / "cydc" / "cydc.py"

# Error 7 on line 7: an array read out of range, after some other statements.
ARRAY_ERROR = """[[
DIM tabla(3)
SET 0 TO 42
SET 2 TO 9
]]Texto antes del error.[[
SET 1 TO 1
SET 3 TO tabla(@2)
SET 4 TO 1
]]
"""
# Error 9 (needs --debug-stack too) on line 5: a RETURN with no GOSUB.
RETURN_ERROR = """[[
SET 0 TO 42
GOSUB sub
SET 1 TO 1
RETURN
LABEL sub
SET 2 TO 1
RETURN
]]
"""


def read_map(path):
    """{chunk: [(address, location), ...]} from a .map file."""
    entries = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        where, loc, _opcode, _col = line.split("\t")
        chunk, address = (int(v) for v in where.split(":"))
        entries.setdefault(chunk, []).append((address, loc))
    return entries


def locate(entries, chunk, address):
    """The statement an error at chunk:address belongs to."""
    before = [loc for a, loc in entries.get(chunk, ()) if a <= address]
    return before[-1] if before else None


def run_and_locate(source, model, *options):
    """Compile with the options, run until the system error; return the
    location the .map gives for it."""
    with tempfile.TemporaryDirectory() as wd:
        image, flags_addr = compile_cyd(source, model, wd, extra_args=options)
        lst = Path(wd) / "cyd.lst"
        dbg = _parse_label_addr(lst, "DBG_PC")
        chunk = _parse_label_addr(lst, "CHUNK")
        flags, (pos, cur) = run_in_zesarux(
            image, flags_addr, machine=MACHINE_BY_MODEL[model],
            esxdos_root=wd if model == "esxdos" else None,
            extra_reads=((dbg, 2), (chunk, 1)),
        )
        assert flags[0] == 42, "the program did not run"
        address = (pos[0] | pos[1] << 8) - 1  # DEBUG_POS keeps the address + 1
        return locate(read_map(Path(wd) / "test.map"), cur[0], address)


class TestDebugMap(unittest.TestCase):
    @unittest.skipUnless(find_sjasmplus(), "sjasmplus not available under tools/")
    def test_map_and_interpreter(self):
        with tempfile.TemporaryDirectory() as wd:
            src = Path(wd) / "game.cyd"
            src.write_text(ARRAY_ERROR, encoding="utf-8")

            def build(*options):
                out = Path(wd) / ("out" + "".join(options).replace("-", "_"))
                out.mkdir()
                r = subprocess.run(
                    [sys.executable, str(CYDC), *options, "48k", "game.cyd",
                     str(find_sjasmplus()), str(out)],
                    cwd=wd, capture_output=True, text=True, timeout=120,
                    env={**os.environ, "CYD_LANG": "en", "LANGUAGE": "en"},
                )
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                return out

            plain = build()
            self.assertFalse((plain / "game.map").exists())
            self.assertNotIn("DBG_PC", (plain / "cyd.sym").read_text())

            debug = build("--debug-errors")
            self.assertIn("DBG_PC", (debug / "cyd.sym").read_text())
            entries = read_map(debug / "game.map")
            locs = [loc for chunk in entries.values() for _, loc in chunk]
            # Every statement of the script has its line.
            for line in (3, 4, 6, 7, 8):
                self.assertIn(f"game.cyd:{line}", locs)
            # The text after the last "]]" too: where it starts, not "line 10".
            self.assertIn("game.cyd:9", locs)
            # Each statement also says where it starts on its line.
            cols = {(loc, col) for loc, col in (
                ln.split("\t")[1::2] for ln in (debug / "game.map").read_text(
                    encoding="utf-8").splitlines() if not ln.startswith("#"))}
            self.assertIn(("game.cyd:7", "1"), cols)  # SET 3 TO tabla(@2)
            self.assertIn(("game.cyd:5", "3"), cols)  # the text after "]]"
            addresses = [a for a, _ in entries[0]]
            self.assertEqual(addresses, sorted(addresses))


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestDebugErrorsRuntime(unittest.TestCase):
    def test_array_error_points_at_its_line(self):
        for model in ("48k", "128k", "plus3", "esxdos"):
            with self.subTest(model):
                self.assertEqual(run_and_locate(ARRAY_ERROR, model, "--debug-errors"),
                                 "test.cyd:7")

    def test_return_without_gosub_points_at_its_line(self):
        self.assertEqual(
            run_and_locate(RETURN_ERROR, "48k", "--debug-errors", "--debug-stack"),
            "test.cyd:5")


if __name__ == "__main__":
    unittest.main()
