"""The error for an interpreter that does not fit in its target says what takes
the room: the sound effects, the music player, the text abbreviations, the
character set and the rest, so a bank of effects that is too big can be told
from an interpreter that has grown too much.

CYD_presents was made for 48K because of its effects: on 128K (where the
interpreter must fit in 16 KB, below the banks at $C000) it does not fit.
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
PRESENTS = REPO / "examples" / "CYD_presents"
TRACKS = REPO / "examples" / "test" / "TRACKS"

sys.path.insert(0, str(CYDC.parent))
import cydc  # noqa: E402


def compile_presents(model, *extra):
    with tempfile.TemporaryDirectory() as out:
        r = subprocess.run(
            [sys.executable, str(CYDC), "-img", "IMAGES", "-sfx", "SFX.asm", "-il", "192",
             *extra, model, "test.cyd", str(find_sjasmplus()), out],
            cwd=PRESENTS, capture_output=True, text=True, timeout=300,
            env={**os.environ, "LANGUAGE": "en"})
    return r.returncode, r.stdout + r.stderr


def breakdown(output):
    """{label: bytes} and the total of the error message."""
    total = int(re.search(r"The interpreter takes (\d+) bytes", output).group(1))
    parts = {m.group(1).strip(): int(m.group(2))
             for m in re.finditer(r"^  ([^:\n]+): +(\d+) bytes$", output, re.M)}
    return total, parts


@unittest.skipUnless(find_sjasmplus(), "sjasmplus not available under tools/")
class TestInterpreterTooBig(unittest.TestCase):
    def test_breakdown_adds_up(self):
        for model in ("128k", "plus3", "mld"):
            with self.subTest(model=model):
                code, out = compile_presents(model, "-trk", str(TRACKS))
                self.assertNotEqual(code, 0)
                total, parts = breakdown(out)
                self.assertGreater(total, 16384)
                self.assertEqual(sum(parts.values()), total, out)
                self.assertGreater(parts["Sound effects (-sfx)"], 10000)
                self.assertGreater(parts["Character set"], 0)
                self.assertIn("Rest of the interpreter", parts)
                # MLD 48K has no AY music player
                self.assertEqual("Music player" in parts, model != "mld", out)
                self.assertIn("With -trim", out)

    def test_no_trim_hint_with_trim(self):
        code, out = compile_presents("128k", "-trim")
        self.assertNotEqual(code, 0)
        self.assertIn("The interpreter takes", out)
        self.assertNotIn("With -trim", out)

    def test_it_fits_on_48k(self):
        code, out = compile_presents("48k")
        self.assertEqual(code, 0, out[-1500:])


class TestMessage(unittest.TestCase):
    def test_rest_alone_too_big(self):
        msg = cydc.interpreter_too_big_message(
            "128k", 17000, 16384, True, {"sfx": 0, "music": 0, "tokens": 100, "charset": 0})
        self.assertIn("Rest of the interpreter: 16900 bytes", msg)
        self.assertIn("alone does not fit on 128k", msg)
        self.assertNotIn("Sound effects", msg)

    def test_without_symbols(self):
        msg = cydc.interpreter_too_big_message("48k", 40000, 32768, False, None)
        self.assertEqual(msg.count("\n"), 0)
        self.assertIn("40000", msg)


if __name__ == "__main__":
    unittest.main()
