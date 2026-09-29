"""Runtime checks of interpreter routines that were rewritten for size or speed.

- Comparisons (CP_EQ ... CP_LE) compute their 0/1 result without branching.
- The CHOOSE variants share MENU_MOVE to move the selection.
- PUT_VAR_CHAR rotates each character row the shorter way round.

Each one must behave exactly as before, so the tests pin the old results: the
comparison truth table, the option picked (and CHOOSE IF CHANGED's calls) for a
sequence of key presses, and the screen the previous renderer printed.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import emulator_available, run_cyd_ex

FIXTURES = Path(__file__).parent / "fixtures"

PAIRS = [(0, 0), (0, 1), (1, 0), (127, 128), (128, 127), (255, 255), (255, 0), (0, 255)]
OPS = [
    ("=", lambda a, b: a == b),
    ("<>", lambda a, b: a != b),
    ("<", lambda a, b: a < b),
    (">=", lambda a, b: a >= b),
    (">", lambda a, b: a > b),
    ("<=", lambda a, b: a <= b),
]


def comparison_program():
    # Operands come from variables so the compiler can't fold them. FLAGS[1 + k]
    # holds the k-th (pair, operator) result.
    lines = ["SET 0 TO 1"]
    k = 1
    for a, b in PAIRS:
        lines += [f"SET 200 TO {a}", f"SET 201 TO {b}"]
        for op, _ in OPS:
            lines.append(f"IF @200 {op} @201 THEN SET {k} TO 1 ENDIF")
            k += 1
    lines += ["SET 0 TO 42", "LABEL spin", "GOTO spin"]
    return "[[ " + "\n".join(lines) + " ]]"


MENU = """[[ SET 2 TO 1 ]]{pre}[[ OPTION GOTO o0 ]]Uno [[ OPTION GOTO o1 ]]Dos
[[ OPTION GOTO o2 ]]Tres [[ OPTION GOTO o3 ]]Cuatro
[[ {choose}
LABEL o0
SET 1 TO 10 : GOTO fin
LABEL o1
SET 1 TO 11 : GOTO fin
LABEL o2
SET 1 TO 12 : GOTO fin
LABEL o3
SET 1 TO 13 : GOTO fin
LABEL never
SET 1 TO 99 : GOTO fin
LABEL moved
SET 3 TO @3 + 1
RETURN
LABEL fin
SET 0 TO 42
LABEL spin
GOTO spin ]]"""

Q, A, O, P, ENTER = 113, 97, 111, 112, 13

# The same text in both charsets, at odd margins and cursor positions, so every
# pixel offset inside a byte is printed. text_render_48k.scr is what the
# interpreter printed before the rotation change.
TEXT = """[[ CLEAR ]]En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho tiempo que vivía un hidalgo de los de lanza en astillero, adarga antigua, rocín flaco y galgo corredor. ¿Qué? ¡Sí! Ñandú, pingüino.
[[ CHARSET 1 ]]Una olla de algo más vaca que carnero, salpicón las más noches, duelos y quebrantos los sábados, lentejas los viernes, algún palomino de añadidura los domingos.
[[ CHARSET 0 : MARGINS 1, 13, 29, 10 ]]El resto della concluían sayo de velarte, calzas de velludo para las fiestas, con sus pantuflos de lo mismo. iiii llll mmmm WWWW
[[ AT 3, 5 : CHAR 65 : CHAR 128 : REPCHAR 45, 7 : PRINT 123 : CHARSET 1 : AT 1, 6 ]]abcdefghijklmnopqrstuvwxyz ABCDEFGHIJKLMNOPQRSTUVWXYZ 0123456789
[[ SET 0 TO 42
LABEL spin
GOTO spin
]]"""


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestInterpreterRuntime(unittest.TestCase):
    def test_comparisons(self):
        flags = run_cyd_ex(comparison_program(), model="48k", n_bytes=1 + len(PAIRS) * len(OPS))
        self.assertEqual(flags[0], 42, "program did not finish")
        k = 1
        for a, b in PAIRS:
            for op, expected in OPS:
                with self.subTest(f"{a} {op} {b}"):
                    self.assertEqual(flags[k], int(expected(a, b)))
                k += 1

    def test_menu_navigation(self):
        # (setup, menu, keys, option picked, CHOOSE IF CHANGED calls)
        cases = {
            # Q and the last A press can't move (first / last option).
            "CHOOSE": ("", "CHOOSE", [Q, A, A, A, A, Q, ENTER], 12, 0),
            "CHOOSE IF WAIT": ("", "CHOOSE IF WAIT 60000 THEN GOTO never",
                               [Q, A, A, A, A, Q, ENTER], 12, 0),
            # Called on entry and after each of the 4 moves.
            "CHOOSE IF CHANGED": ("", "CHOOSE IF CHANGED THEN GOSUB moved",
                                  [Q, A, A, A, A, Q, ENTER], 12, 5),
            # Two columns: O/P move by 1, Q/A by 2.
            "columns": ("[[ MENUCONFIG 1, 2, 0, 1 ]]", "CHOOSE IF CHANGED THEN GOSUB moved",
                        [P, A, O, Q, P, ENTER], 11, 6),
        }
        for name, (pre, choose, keys, picked, calls) in cases.items():
            with self.subTest(name):
                flags = run_cyd_ex(
                    MENU.format(pre=pre, choose=choose), model="48k", max_wait=20,
                    keys=[(4 if i == 0 else 0.9, k) for i, k in enumerate(keys)],
                )
                self.assertEqual(list(flags[:4]), [42, picked, 1, calls])

    def test_text_is_printed_as_before(self):
        expected = (FIXTURES / "text_render_48k.scr").read_bytes()
        for model in ("48k", "128k"):
            with self.subTest(model):
                flags, (screen,) = run_cyd_ex(TEXT, model=model, reads=[(0x4000, 6912)])
                self.assertEqual(flags[0], 42, "program did not finish")
                self.assertEqual(bytes(screen), expected)


if __name__ == "__main__":
    unittest.main()
