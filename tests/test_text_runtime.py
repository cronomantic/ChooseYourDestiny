"""Runtime check of text compression: the Z80 decoder must print exactly the
same thing whether a text was compressed or not.

The same program is built twice, once with the compiler's token table and once
importing an empty one (``-t``, so every text is stored as plain characters),
and both screens are compared byte for byte. A token expanded wrongly, or a
token index the Z80 table walk resolves to the wrong entry, changes the screen.
"""

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


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestCompressedTextRuntime(unittest.TestCase):
    def _screens(self, model):
        flags, (packed,) = run_cyd_ex(PROGRAM, model=model, reads=[SCREEN])
        self.assertEqual(flags[0], 42, f"program did not finish on {model}")
        flags, (plain,) = run_cyd_ex(
            PROGRAM, model=model, reads=[SCREEN],
            extra_args=["-t", "no_tokens.json"], files={"no_tokens.json": "[]"},
        )
        self.assertEqual(flags[0], 42, f"uncompressed program did not finish on {model}")
        return packed, plain

    def _check(self, model):
        packed, plain = self._screens(model)
        self.assertTrue(any(packed), "nothing was printed")
        self.assertEqual(packed, plain, f"compressed text prints differently on {model}")

    def test_48k(self):
        self._check("48k")

    def test_128k(self):
        self._check("128k")


if __name__ == "__main__":
    unittest.main()
