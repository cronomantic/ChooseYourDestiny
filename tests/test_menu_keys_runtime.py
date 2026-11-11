"""The menu keys in the emulator, on the six targets: the default keys, MENUKEY,
MENUJOY, the keys that always work and the page pause.

Every program runs rounds of a three-option menu (MENUCONFIG 1,1, so Q/A and O/P
both move one option). Each round presses some keys and stores the option it
ended up choosing: 10, 11 or 12. Most rounds are built so that a key that should
be ignored changes the result if it is not: e.g. pressing the select key that no
longer selects before moving makes the round choose the first option.

The joystick is ZEsarUX's emulated one (--joystickemulated), held with
set-ui-io-ports: Kempston is read from its port, Sinclair and cursor joysticks
are keys of the keyboard. See doc/dev/MENU_KEYS_DESIGN.md.
"""

import sys
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import run_cyd, emulator_available

MODELS = ("48k", "128k", "plus3", "esxdos", "mld", "mld128")
DONE = 42
GAP = 1.0  # seconds between key presses

UP, DOWN, LEFT, RIGHT, FIRE = 8, 4, 2, 1, 16
SPACE, ENTER = 32, 13


def joy(mask):
    return ("joy", mask)


def menu_round(n, var):
    """A three-option menu; the option chosen goes to variable ``var``."""
    return f"""
LABEL r{n}
CLEAR
OPTION GOTO r{n}a ]]Uno[[
OPTION GOTO r{n}b ]]Dos[[
OPTION GOTO r{n}c ]]Tres[[
CHOOSE
LABEL r{n}a
SET {var} TO 10 : GOTO r{n}z
LABEL r{n}b
SET {var} TO 11 : GOTO r{n}z
LABEL r{n}c
SET {var} TO 12
LABEL r{n}z
"""


def program(*parts):
    """``parts``: code strings and ("round", var) items, in order."""
    code, n = ["[[\nSET 1 TO 1\nMENUCONFIG 1, 1\n"], 0
    for part in parts:
        if isinstance(part, tuple):
            n += 1
            code.append(menu_round(n, part[1]))
        else:
            code.append(part + "\n")
    code.append(f"SET 0 TO {DONE}\nLABEL spin\nGOTO spin\n]]")
    return "".join(code)


def keys(*ks):
    return tuple((GAP, k) for k in ks)


# --- Without MENUKEY / MENUJOY: the default keys, M no longer selects ----------

# A window of two rows: the last one is kept for the page pause's arrow, so
# every page holds one line. The first pause comes before "Linea 2", the
# second before "Linea 3".
PAGES = """
MARGINS 0, 0, 32, 2
PAGEPAUSE 1
CLEAR
]]Linea 1
Linea 2[[
SET 6 TO 1
]]
Linea 3[[
SET 7 TO 1
"""

DEFAULT = program(
    ("round", 2),          # M (ignored), A, SPACE                  -> 11
    ("round", 3),          # P, P, O, ENTER                         -> 11
    ("round", 4),          # A, A, Q, SPACE                         -> 11
    ("round", 5),          # cursor down (CAPS SHIFT + 6), ENTER    -> 11
    f"SET 11 TO {DONE}",   # it stays in the second page: this is its end mark
    PAGES,                 # M must not pass the page; ENTER passes one page
)
DEFAULT_KEYS = keys(ord("m"), ord("a"), SPACE,
                    ord("p"), ord("p"), ord("o"), ENTER,
                    ord("a"), ord("a"), ord("q"), SPACE,
                    joy(DOWN), ENTER,
                    ord("m"), ENTER)
# r2..r5 = 11; ENTER passed the first page (6) but M did not pass any (7).
DEFAULT_EXPECTED = {2: 11, 3: 11, 4: 11, 5: 11, 6: 1, 7: 0, 11: DONE}


# --- MENUKEY ------------------------------------------------------------------

CONFIG = program(
    ("round", 2),                                   # A, SPACE -> 11 (defaults)
    "MENUKEY 1, 's'\nMENUKEY 4, 'x'",
    ("round", 3),                                   # SPACE, A (both ignored), S, X -> 11
    ("round", 4),                                   # cursor down, ENTER (always) -> 11
    "MENUKEY 1, 0",
    ("round", 5),                                   # S, A (ignored), cursor down, X -> 11
    "MENUKEY 1, 's'\nSET 9 TO 7\nMENUKEY @9, 'z'\nSET 9 TO 255\nMENUKEY @9, 'z'",
    ("round", 6),                                   # Z (ignored), S, X -> 11
    "SET 9 TO 0\nMENUKEY @9, 'w'\nSET 9 TO 9\nMENUJOY @9",
    ("round", 7),                                   # Q (ignored), W, ... -> see below
)
CONFIG_KEYS = keys(ord("a"), SPACE,
                   SPACE, ord("a"), ord("s"), ord("x"),
                   joy(DOWN), ENTER,
                   ord("s"), ord("a"), joy(DOWN), ord("x"),
                   ord("z"), ord("s"), ord("x"),
                   ord("s"), ord("s"), ord("q"), ord("w"), ord("x"))
# r7: S, S -> option 2; Q no longer moves up; W (the new up, set through a
# variable) -> option 1; X -> 11.
CONFIG_EXPECTED = {0: DONE, 2: 11, 3: 11, 4: 11, 5: 11, 6: 11, 7: 11}


# --- MENUJOY: the joystick and the keyboard at once ---------------------------

def joy_program(kind):
    return program(
        f"MENUJOY {kind}",
        ("round", 2),                               # joy down, joy fire      -> 11
        ("round", 3),                               # A, joy fire             -> 11
        ("round", 4),                               # joy down, SPACE         -> 11
        "MENUJOY 0",
        ("round", 5),                               # joy down (ignored), A, SPACE -> 11
    )


JOY_KEYS = keys(joy(DOWN), joy(FIRE),
                ord("a"), joy(FIRE),
                joy(DOWN), SPACE,
                joy(DOWN), ord("a"), SPACE)
JOY_EXPECTED = {0: DONE, 2: 11, 3: 11, 4: 11, 5: 11}
JOYSTICKS = {1: "Sinclair 1", 2: "Sinclair 2", 3: "Cursor"}


# --- Kempston: menus, the page pause and LET v = KEMPSTON() --------------------

KEMPSTON = program(
    ("round", 2),                                   # joy down, joy fire -> 11
    PAGES.replace("SET 7 TO 1", "SET 7 TO 1\nLABEL k\nSET 10 TO KEMPSTON()\n"
                  "IF @10 = 0 THEN GOTO k ENDIF"),
)
KEMPSTON_KEYS = keys(joy(DOWN), joy(FIRE), joy(FIRE), joy(FIRE), joy(RIGHT))
# Fire passes both pages; then KEMPSTON() reads the right direction (1).
KEMPSTON_EXPECTED = {0: DONE, 2: 11, 6: 1, 7: 1, 10: 1}


# --- INKEY with shifted keys -----------------------------------------------------
# On MLD the keyboard decoding is a RAM copy of the ROM's (inkey.asm), which
# indexed its tables without the ROM's offset: CAPS SHIFT + 6 (cursor down) and
# SYMBOL SHIFT + a letter gave wrong codes there.

# set-ui-io-ports rows: FEFE FDFE FBFE F7FE EFFE DFFE BFFE 7FFE, then the joystick.
SYM_P = ("ports", "ffffffffff1eff1d00")      # SYMBOL SHIFT + P -> '"'
CAPS_6 = ("ports", "feffffffefffffff00")     # CAPS SHIFT + 6   -> cursor down ($0A)
CAPS_5 = ("ports", "feffffefffffffff00")     # CAPS SHIFT + 5   -> cursor left ($08)

SHIFTED = program("SET 2 TO INKEY(0)", "SET 3 TO INKEY(0)", "SET 4 TO INKEY(0)")
SHIFTED_KEYS = keys(SYM_P, CAPS_6, CAPS_5)
SHIFTED_EXPECTED = {0: DONE, 2: 34, 3: 10, 4: 8}


def check(job):
    name, model, source, presses, expected, joystick, port = job[:7]
    extra = job[7] if len(job) > 7 else ()
    flags = run_cyd(source, model=model, n_bytes=16, keys=presses, joystick=joystick,
                    port=port, max_wait=60.0, extra_args=extra)
    got = {k: flags[k] for k in expected}
    return name, model, got == expected, f"got={got} expected={expected}"


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestMenuKeysRuntime(unittest.TestCase):
    def _run(self, cases, extra_args=()):
        jobs = [(name, model, src, ks, exp, joy_, 10300 + i, extra_args)
                for i, (name, model, src, ks, exp, joy_) in enumerate(cases)]
        with ThreadPoolExecutor(3) as pool:
            for name, model, ok, detail in pool.map(check, jobs):
                with self.subTest(case=name, model=model):
                    self.assertTrue(ok, detail)

    def test_default_keys(self):
        self._run([("default", m, DEFAULT, DEFAULT_KEYS, DEFAULT_EXPECTED, None)
                   for m in MODELS])

    def test_default_keys_trimmed(self):
        # With -trim and no MENUKEY/MENUJOY, POP_CONFIG is left out and INKEY_MENU
        # compares with its fixed keys instead of the setting table.
        self._run([("default -trim", m, DEFAULT, DEFAULT_KEYS, DEFAULT_EXPECTED, None)
                   for m in MODELS], extra_args=("-trim",))

    def test_menukey(self):
        self._run([("menukey", m, CONFIG, CONFIG_KEYS, CONFIG_EXPECTED, None)
                   for m in MODELS])

    def test_menujoy(self):
        self._run([(f"menujoy {kind} ({name})", m, joy_program(kind), JOY_KEYS,
                    JOY_EXPECTED, name)
                   for kind, name in JOYSTICKS.items() for m in MODELS])

    def test_inkey_shifted_keys(self):
        self._run([("inkey", m, SHIFTED, SHIFTED_KEYS, SHIFTED_EXPECTED, None)
                   for m in MODELS])

    def test_kempston(self):
        self._run([("kempston", m, KEMPSTON, KEMPSTON_KEYS, KEMPSTON_EXPECTED, "Kempston")
                   for m in MODELS])


if __name__ == "__main__":
    unittest.main()
