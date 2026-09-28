"""Runtime check of text compression: the Z80 decoder must print exactly the
same thing whether a text was compressed or not.

The same program is built with each token format (flat, and nested, where a
token can contain others and EXPAND_TOKEN expands it recursively) and once
importing an empty token list (``-t``, so every text is stored as plain
characters), and the screens are compared byte for byte. A token expanded
wrongly, or an index the Z80 table walk resolves to the wrong entry, changes
the screen.
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import run_cyd_ex, emulator_available

# Enough repetitive prose (with accents) to fill the table with dozens of
# tokens, short enough to fit one screen without a page pause.
PROGRAM = """[[ CLEAR ]]En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho tiempo que vivía un hidalgo de los de lanza en astillero, adarga antigua, rocín flaco y galgo corredor. Una olla de algo más vaca que carnero, salpicón las más noches, duelos y quebrantos los sábados, lentejas los viernes, algún palomino de añadidura los domingos, consumían las tres partes de su hacienda. El resto della concluían sayo de velarte, calzas de velludo para las fiestas, con sus pantuflos de lo mismo, y los días de entresemana se honraba con su vellorí de lo más fino.
[[ SET 0 TO 42
LABEL spin
GOTO spin
]]"""

SCREEN = (0x4000, 6912)

# An imported nested table at the maximum depth (3): "la casa roja " contains
# "la casa ", which contains "la ". The fillers in front make the lookup skip
# entries, and the unused ones check that skipping by length is right.
FILLERS = ["qx", "zzw", "kkkk", "jj"]
DEEP_TOKENS = FILLERS + ["la ", chr(128 + 4) + "casa ", chr(128 + 5) + "roja "]
DEEP_PROGRAM = """[[ CLEAR ]]la casa roja la casa roja la casa la la casa roja y la casa.
[[ SET 0 TO 42
LABEL spin
GOTO spin
]]"""


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestCompressedTextRuntime(unittest.TestCase):
    def _screen(self, model, extra_args, files=None):
        flags, (screen,) = run_cyd_ex(
            PROGRAM, model=model, reads=[SCREEN], extra_args=extra_args, files=files
        )
        self.assertEqual(flags[0], 42, f"program did not finish on {model} {extra_args}")
        return screen

    def _check(self, model):
        plain = self._screen(model, ["-t", "no_tokens.json"], {"no_tokens.json": "[]"})
        self.assertTrue(any(plain), "nothing was printed")
        for token_format in ("flat", "nested"):
            packed = self._screen(model, ["--token-format", token_format])
            self.assertEqual(
                packed, plain, f"{token_format} tokens print differently on {model}"
            )

    def test_48k(self):
        self._check("48k")

    def test_nested_depth_3(self):
        flags, (plain,) = run_cyd_ex(
            DEEP_PROGRAM, model="48k", reads=[SCREEN],
            extra_args=["-t", "none.json"], files={"none.json": "[]"},
        )
        self.assertEqual(flags[0], 42)
        flags, (deep,) = run_cyd_ex(
            DEEP_PROGRAM, model="48k", reads=[SCREEN],
            extra_args=["-t", "deep.json"], files={"deep.json": json.dumps(DEEP_TOKENS)},
        )
        self.assertEqual(flags[0], 42)
        self.assertTrue(any(plain), "nothing was printed")
        self.assertEqual(deep, plain, "depth-3 nested tokens print differently")

    def test_128k(self):
        self._check("128k")

    def test_plus3(self):
        self._check("plus3")

    def test_esxdos(self):
        self._check("esxdos")


if __name__ == "__main__":
    unittest.main()
