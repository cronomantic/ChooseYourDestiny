"""Warnings for variables shared between files.

Reusing a variable number under several names is a feature, but a variable a
library reserves (lib/sprites.cyd uses 200..211) that the game overwrites
breaks the library without a sound. check_shared_variables warns when a
number DECLAREd in one file is used from another one under another name, by
its number, or reached from another name (SET v TO {...} running past v).
Reuse within one file, and using a variable by its declared name from any
file, stay silent.
"""

import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parent.parent
CYDC = REPO / "src" / "cydc" / "cydc" / "cydc.py"

LIB = """[[
DECLARE 200 AS libA : DECLARE 201 AS libB : DECLARE 202 AS libC
GOTO libSkip
LABEL libRun : SET libA TO @libB + @libC : RETURN
LABEL libSkip
]]
"""


def check(main, files=None, *options):
    """Run cydc --check on main.cyd (and the other files); return its
    shared-variable warnings, the "Variable N is..." ones."""
    with tempfile.TemporaryDirectory() as wd:
        for name, text in {"main.cyd": main, **(files or {})}.items():
            path = Path(wd) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        r = subprocess.run(
            [sys.executable, str(CYDC), "--check", *options, "48k", "main.cyd"],
            cwd=wd, capture_output=True, text=True, timeout=120,
            env={**os.environ, "CYD_LANG": "en"},
        )
        assert r.returncode == 0, r.stdout + r.stderr
        return [line.split("]: ", 1)[1] for line in r.stdout.splitlines()
                if line.startswith("WARNING [CODEGEN]: Variable ")]


class TestSharedVariables(unittest.TestCase):
    def test_declared_again_under_another_name(self):
        main = '[[ INCLUDE "lib/l.cyd"\nDECLARE 201 AS lives\nSET lives TO 3\nGOSUB libRun ]]'
        self.assertEqual(check(main, {"lib/l.cyd": LIB}), [
            "Variable 201 is 'libB' in l.cyd, and at main.cyd:2 it is declared again "
            "as 'lives': both share it",
        ])

    def test_used_by_its_number(self):
        main = '[[ INCLUDE "lib/l.cyd"\nSET 202 TO 1\nSET 3 TO @202\nGOSUB libRun ]]'
        # Once per file and variable, at the first place it is used.
        self.assertEqual(check(main, {"lib/l.cyd": LIB}), [
            "Variable 202 is 'libC' in l.cyd, and at main.cyd:2 it is used by its number",
        ])

    def test_reached_from_another_name(self):
        main = ('[[ INCLUDE "lib/l.cyd"\nDECLARE 198 AS buf\n'
                "SET buf TO {1, 2, 3}\nGOSUB libRun ]]")
        self.assertEqual(check(main, {"lib/l.cyd": LIB}), [
            "Variable 200 is 'libA' in l.cyd, and at main.cyd:3 it is reached from 'buf'",
        ])

    def test_reuse_within_one_file_is_fine(self):
        main = ("[[ DECLARE 10 AS tmp : DECLARE 10 AS count\n"
                "SET tmp TO 1 : SET count TO 2 : SET 10 TO 3 ]]")
        self.assertEqual(check(main), [])

    def test_library_used_by_its_names_is_fine(self):
        main = ('[[ INCLUDE "lib/l.cyd"\nSET libB TO 1 : SET libC TO 2\n'
                "GOSUB libRun\nSET 3 TO @libA ]]")
        self.assertEqual(check(main, {"lib/l.cyd": LIB}), [])

    def test_a_library_setting_its_own_wide_values_is_fine(self):
        # SET libA TO {...} fills libA, libB, libC: the library's own layout.
        main = '[[ INCLUDE "lib/l.cyd"\nSET libA TO {1, 2, 3}\nGOSUB libRun ]]'
        self.assertEqual(check(main, {"lib/l.cyd": LIB}), [])

    def test_files_sharing_their_names_are_fine(self):
        # include_demo: the variables in one file, used by name everywhere.
        files = {"vars.cyd": "[[ DECLARE 0 AS gold : DECLARE 1 AS hp ]]",
                 "ch1.cyd": "[[ SET gold TO @gold + 1 : SET hp TO 3 ]]"}
        main = '[[ INCLUDE "vars.cyd"\nINCLUDE "ch1.cyd"\nSET 5 TO @gold ]]'
        self.assertEqual(check(main, files), [])

    def test_can_be_turned_off(self):
        main = '[[ INCLUDE "lib/l.cyd"\nSET 202 TO 1\nGOSUB libRun ]]'
        self.assertEqual(check(main, {"lib/l.cyd": LIB}, "--no-warn-shared-vars"), [])

    def test_examples_do_not_warn(self):
        # The examples that INCLUDE something (the libraries, include_demo).
        for example in sorted((REPO / "examples").iterdir()):
            sources = [s for s in example.glob("*.cyd")
                       if re.search(r"^\s*INCLUDE\b", s.read_text(encoding="utf-8",
                                                               errors="replace"), re.M)]
            for src in sources:
                with self.subTest(f"{example.name}/{src.name}"):
                    r = subprocess.run(
                        [sys.executable, str(CYDC), "--check", "48k", src.name],
                        cwd=example, capture_output=True, text=True, timeout=120,
                        env={**os.environ, "CYD_LANG": "en"},
                    )
                    self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                    self.assertNotIn("WARNING [CODEGEN]: Variable ", r.stdout)


if __name__ == "__main__":
    unittest.main()
