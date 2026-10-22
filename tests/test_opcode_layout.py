"""The gap before the opcode table is filled.

OPCODES must start a 256-byte page, and the ALIGN 256 in front of it wasted
0..255 bytes, a different amount for each game: one byte more of interpreter
could cost 256. plan_opcode_layout() moves opcode handlers after the table so
the code in front ends on the page. These programs left gaps of 61 to 250
bytes; now only a few remain. That the moved handlers still work is what the
emulator tests check (test_interpreter_runtime, test_example_taps, ...).
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import find_sjasmplus  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
CYDC = REPO / "src" / "cydc" / "cydc" / "cydc.py"

PROGRAMS = {
    "small": '[[ SET 0 TO 1 ]]Hola[[ WAITKEY ]]',
    "menu": ('[[ DECLARE 1 AS x\nLABEL top\nCLEAR\nOPTION GOTO a]]Uno[[\n'
             'OPTION GOTO b]]Dos[[\nCHOOSE\nLABEL a\nSET x TO @x + 1 : PRINT @x : GOTO top\n'
             'LABEL b\nINK 2 : PAPER 1 : BORDER 3 : WAITKEY : GOTO top ]]'),
}


def gap_before_table(listing):
    lines = listing.splitlines()
    for i, line in enumerate(lines):
        if re.search(r"\bALIGN 256\b", line) and any("OPCODES:" in x for x in lines[i + 1:i + 3]):
            address = int(re.match(r"\s*\d+\+?\s+([0-9A-F]{4})", line).group(1), 16)
            return (-address) % 256
    raise AssertionError("no ALIGN before OPCODES in the listing")


@unittest.skipUnless(find_sjasmplus(), "sjasmplus not available under tools/")
class TestOpcodeLayout(unittest.TestCase):
    def test_gap_is_filled(self):
        for name, source in PROGRAMS.items():
            for model in ("48k", "128k", "plus3"):
                for trim in ([], ["-trim"]):
                    with self.subTest(program=name, model=model, trim=bool(trim)), \
                            tempfile.TemporaryDirectory() as wd:
                        (Path(wd) / "game.cyd").write_text(source, encoding="utf-8")
                        r = subprocess.run(
                            [sys.executable, str(CYDC), "-v", *trim, model, "game.cyd",
                             str(find_sjasmplus()), wd],
                            cwd=wd, capture_output=True, text=True, timeout=300)
                        self.assertEqual(r.returncode, 0, r.stdout[-2000:] + r.stderr)
                        listing = (Path(wd) / "cyd.lst").read_text(errors="replace")
                        # A tiny trimmed program may not have handlers enough to
                        # fill the gap; it must still build.
                        if not (trim and name == "small"):
                            self.assertLessEqual(gap_before_table(listing), 16)
                        self.assertEqual(
                            [f for f in os.listdir(wd) if f.startswith("cyd_layout")], [])


if __name__ == "__main__":
    unittest.main()
