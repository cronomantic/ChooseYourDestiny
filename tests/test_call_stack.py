"""GOSUB/RETURN: the compiler's call-stack warnings and the interpreter's stack.

The interpreter keeps GOSUB return addresses on a stack it doesn't check. A
RETURN with no GOSUB pending jumps to garbage, and a subroutine left with GOTO
leaves its return address behind until the stack runs into the variables.
``check_call_stack`` warns about both at compile time; ``--debug-stack`` makes
the interpreter stop with a system error instead.

The runtime tests also cover CHOOSE IF WAIT, whose GOSUBs (the chosen option or
the timeout one) used to push a return address inside the options table, so
their RETURN reset the Spectrum.
"""

import gettext
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parent.parent
CYDC = REPO / "src" / "cydc" / "cydc" / "cydc.py"
sys.path.insert(0, str(CYDC.parent))
sys.path.insert(0, str(Path(__file__).parent))

from cydc_codegen import CydcCodegen
from cydc_parser import CydcParser
from emu_harness import emulator_available, run_cyd_ex


class TestCallStackWarnings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = CydcParser(gettext)
        cls.parser.build()

    def _warnings(self, src):
        code = self.parser.parse(input=src)
        self.assertEqual(self.parser.errors, [])
        g = CydcCodegen(gettext)
        g.generate_code(code=code)
        return g.call_stack_warnings

    def assertClean(self, src):
        self.assertEqual(self._warnings(src), [])

    def test_return_in_the_main_code(self):
        self.assertEqual(
            self._warnings("[[ SET 0 TO 1\nRETURN ]]"),
            ["RETURN at line 2 can run with no GOSUB pending"],
        )

    def test_goto_into_a_subroutine(self):
        src = ("[[ GOSUB inv\nGOTO inv\nLABEL inv\n"
               "SET 0 TO 1\nRETURN ]]")
        self.assertEqual(self._warnings(src), [
            "RETURN at line 5 can run with no GOSUB pending: the jump at line 2 "
            "goes into subroutine 'inv' instead of calling it with GOSUB",
        ])

    def test_option_goto_into_a_subroutine(self):
        src = ("[[ OPTION GOSUB inv\nOPTION GOTO inv\nCHOOSE\nGOTO fin\n"
               "LABEL inv\nRETURN\nLABEL fin\nEND ]]")
        (w,) = self._warnings(src)
        self.assertIn("the jump at line 2 goes into subroutine 'inv'", w)

    def test_falling_into_a_subroutine(self):
        # include_demo did this: the subroutines were included at the top.
        src = "[[ SET 0 TO 1\nLABEL status\nPRINT 1\nRETURN\nLABEL go\nGOSUB status ]]"
        self.assertEqual(self._warnings(src), [
            "RETURN at line 4 can run with no GOSUB pending: execution runs into "
            "subroutine 'status' from the code above it (put a GOTO or END before it)",
        ])

    def test_option_gosub_returns_after_the_choose(self):
        # The RETURN of an OPTION GOSUB comes back after the CHOOSE, so code
        # right after it runs into the subroutine again.
        src = ("[[ OPTION GOSUB take\nOPTION GOTO fin\nCHOOSE\n"
               "LABEL take\nSET 0 TO 1\nRETURN\nLABEL fin\nEND ]]")
        (w,) = self._warnings(src)
        self.assertIn("RETURN at line 6", w)
        self.assertIn("runs into subroutine 'take'", w)

    def test_subroutine_left_with_goto(self):
        src = ("[[ LABEL room\nGOSUB enemies\nGOTO room\n"
               "LABEL enemies\nSET 0 TO 1\nGOTO room ]]")
        self.assertEqual(self._warnings(src), [
            "Subroutine 'enemies' can end without RETURN at line 6, going on to "
            "code that runs outside any subroutine; each time a GOSUB level is "
            "left on the stack, and after a few hundred the game crashes",
        ])

    def test_jump_into_a_subroutine_and_one_left_with_goto(self):
        # Both checks in one program: the first used to leave "jump" set to a
        # bool, and the second then failed with "'bool' object is not callable".
        src = ("[[ LABEL room\nGOSUB inv\nIF @0 = 1 THEN GOTO inv\nENDIF\n"
               "GOSUB enemies\nEND\nLABEL enemies\nGOTO room\n"
               "LABEL inv\nRETURN ]]")
        warnings = self._warnings(src)
        self.assertEqual(len(warnings), 2, warnings)
        self.assertTrue(any("the jump at line 3 goes into subroutine 'inv'" in w
                            for w in warnings), warnings)
        self.assertTrue(any("Subroutine 'enemies' can end without RETURN at line 8" in w
                            for w in warnings), warnings)

    def test_one_mistake_does_not_hide_the_others(self):
        # "room2" falls into "used" (no GOTO/END), code the menu subroutine also
        # uses. That used to make the whole menu count as main code, so the
        # GOTO that leaves the menu (line 9) was not reported.
        src = ("[[ LABEL room\nGOSUB menu\nIF @0 = 1 THEN GOTO room2\nENDIF\nGOTO room\n"
               "LABEL menu\nOPTION GOTO used\nOPTION GOTO back\nCHOOSE\n"
               "LABEL room2\nSET 2 TO 1\n"
               "LABEL used\nIF @1 = 1 THEN GOTO room\nENDIF\nGOTO menu\n"
               "LABEL back\nRETURN ]]")
        warnings = self._warnings(src)
        self.assertTrue(any(w.startswith("Subroutine 'menu' can end without RETURN")
                            for w in warnings), warnings)
        self.assertTrue(any(w.startswith("RETURN at line 17 can run with no GOSUB pending")
                            for w in warnings), warnings)

    def test_gosub_to_a_place_that_never_returns(self):
        # "attack" is a place of the game (reached with GOTO) that a timeout
        # calls with GOSUB: the GOSUB is the mistake, reported where it is.
        src = ("[[ LABEL room\nOPTION GOTO attack\nCHOOSE IF WAIT 100 THEN GOSUB attack\n"
               "LABEL attack\nSET 0 TO 1\nGOTO room ]]")
        self.assertEqual(self._warnings(src), [
            "The GOSUB at line 3 never comes back: 'attack' has no RETURN and the "
            "game goes on from there; each time a GOSUB level is left on the "
            "stack, and after a few hundred the game crashes (use GOTO instead)",
        ])

    def test_subroutine_left_through_a_menu(self):
        src = ("[[ LABEL room\nCHOOSE IF WAIT 100 THEN GOSUB enemies\n"
               "LABEL enemies\nOPTION GOTO room\nCHOOSE ]]")
        (w,) = self._warnings(src)
        self.assertIn("Subroutine 'enemies' can end without RETURN at line 4", w)

    def test_correct_programs_do_not_warn(self):
        cases = {
            "nested calls": "[[ GOSUB a\nEND\nLABEL a\nGOSUB b\nRETURN\nLABEL b\nRETURN ]]",
            "menu with GOSUB options": (
                "[[ LABEL room\nOPTION GOSUB inv\nOPTION GOTO out\nCHOOSE\nGOTO room\n"
                "LABEL inv\nRETURN\nLABEL out\nEND ]]"),
            "CHOOSE IF WAIT ... THEN GOSUB": (
                "[[ LABEL room\nOPTION GOSUB inv\nCHOOSE IF WAIT 100 THEN GOSUB enemies\n"
                "GOTO room\nLABEL inv\nRETURN\nLABEL enemies\nRETURN ]]"),
            "CHOOSE IF CHANGED THEN GOSUB": (
                "[[ OPTION GOTO out\nCHOOSE IF CHANGED THEN GOSUB moved\n"
                "LABEL moved\nRETURN\nLABEL out\nEND ]]"),
            "subroutine ending the game": (
                "[[ GOSUB dead\nEND\nLABEL dead\nIF @0 = 1 THEN END ENDIF\nRETURN ]]"),
            "subroutine that never returns": (
                "[[ GOSUB spin\nLABEL spin\nGOTO spin ]]"),
            "shared tail": (
                "[[ GOSUB a\nGOSUB b\nEND\nLABEL a\nSET 0 TO 1\nGOTO done\n"
                "LABEL b\nSET 0 TO 2\nLABEL done\nRETURN ]]"),
            "library skipped with GOTO": (
                "[[ GOTO start\nLABEL lib\nRETURN\nLABEL start\nGOSUB lib\nEND ]]"),
            "recursion": (
                "[[ SET 0 TO 3\nGOSUB down\nEND\nLABEL down\n"
                "IF @0 > 0 THEN SET 0 TO @0 - 1 : GOSUB down ENDIF\nRETURN ]]"),
            "options declared by a subroutine": (
                "[[ GOSUB menu\nCHOOSE\nEND\nLABEL menu\nOPTION GOSUB a\nRETURN\n"
                "LABEL a\nRETURN ]]"),
        }
        for name, src in cases.items():
            with self.subTest(name):
                self.assertClean(src)


class TestCallStackCli(unittest.TestCase):
    def _run(self, source, *args):
        with tempfile.TemporaryDirectory() as wd:
            (Path(wd) / "main.cyd").write_text(source, encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(CYDC), "--check", *args, "48k", "main.cyd"],
                cwd=wd, capture_output=True, text=True, timeout=120,
            )

    def test_warning_is_printed_with_the_file_location(self):
        r = self._run("Hi\n[[ RETURN ]]")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(
            "WARNING [CODEGEN]: RETURN at main.cyd:2 can run with no GOSUB pending", r.stdout
        )

    def test_no_warn_gosub(self):
        r = self._run("Hi\n[[ RETURN ]]", "--no-warn-gosub")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("WARNING", r.stdout)

    def test_include_demo_is_clean(self):
        demo = REPO / "examples" / "include_demo"
        r = subprocess.run(
            [sys.executable, str(CYDC), "--check", "--no-warn-unused", "48k", "main.cyd"],
            cwd=demo, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("WARNING", r.stdout)


# FLAGS[0] = 1 at the start, FLAGS[1] = 11 in the subroutine, FLAGS[2] = 22 back
# after the menu: a RETURN that goes wrong never gets there (it used to reset).
WAIT_TIMEOUT_GOSUB = """[[ SET 0 TO 1
OPTION GOTO never
CHOOSE IF WAIT 20 THEN GOSUB enemies
SET 2 TO 22
LABEL spin
GOTO spin
LABEL never
SET 3 TO 33
GOTO spin
LABEL enemies
SET 1 TO 11
RETURN ]]"""

MENU_GOSUB = """[[ SET 0 TO 1
OPTION GOSUB inventory
{choose}
SET 2 TO 22
LABEL spin
GOTO spin
LABEL never
SET 3 TO 33
GOTO spin
LABEL moved
SET 4 TO 44
RETURN
LABEL inventory
SET 1 TO 11
RETURN ]]"""

RETURN_WITHOUT_GOSUB = "[[ SET 0 TO 1\nRETURN ]]"

# Every lap leaves a return address behind.
GOSUB_LEAK = """[[ SET 0 TO 1
LABEL room
GOSUB inventory
LABEL inventory
SET 1 TO @1 + 1
GOTO room ]]"""

ENTER = 13
# SYS_ERROR prints its number through TEXT_BUFFER ("00009").
ERROR_NUMBER = ("BUFFER", 0, 6)


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestCallStackRuntime(unittest.TestCase):
    def test_choose_if_wait_timeout_gosub_returns(self):
        for model in ("48k", "128k"):
            with self.subTest(model):
                flags = run_cyd_ex(WAIT_TIMEOUT_GOSUB, model=model)
                self.assertEqual(list(flags[:4]), [1, 11, 22, 0])

    def test_option_gosub_chosen_in_each_kind_of_menu_returns(self):
        menus = {
            "CHOOSE": ("CHOOSE", 0),
            "CHOOSE IF WAIT": ("CHOOSE IF WAIT 60000 THEN GOTO never", 0),
            "CHOOSE IF CHANGED": ("CHOOSE IF CHANGED THEN GOSUB moved", 44),
        }
        for name, (choose, moved) in menus.items():
            with self.subTest(name):
                flags = run_cyd_ex(
                    MENU_GOSUB.format(choose=choose), model="48k", keys=[(4, ENTER)]
                )
                self.assertEqual(list(flags[:5]), [1, 11, 22, 0, moved])

    def test_debug_stack_return_without_gosub(self):
        _, (number,) = run_cyd_ex(
            RETURN_WITHOUT_GOSUB, model="48k", reads=[ERROR_NUMBER],
            extra_args=["--debug-stack"],
        )
        self.assertEqual(bytes(number), b"00009\x00")

    def test_debug_stack_overflow(self):
        flags, (number,) = run_cyd_ex(
            GOSUB_LEAK, model="48k", reads=[ERROR_NUMBER], extra_args=["--debug-stack"],
        )
        self.assertEqual(bytes(number), b"00010\x00")
        self.assertGreater(flags[1], 200, "stopped too early")

    def test_debug_stack_leaves_correct_programs_alone(self):
        flags = run_cyd_ex(WAIT_TIMEOUT_GOSUB, model="48k", extra_args=["--debug-stack"])
        self.assertEqual(list(flags[:4]), [1, 11, 22, 0])


if __name__ == "__main__":
    unittest.main()
