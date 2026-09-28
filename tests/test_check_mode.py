"""Unused-symbol warnings and the compiler's --check mode.

``--check`` runs the preprocessor, the parser and the code generator but not the
assembler, so it needs neither sjasmplus nor an output directory; its exit code
says whether the script compiles (memory layout aside).
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

from cydc_parser import CydcParser
from cydc_preprocessor import SourceLocation


class TestUnusedSymbolWarnings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = CydcParser(gettext)
        cls.parser.build()

    def tearDown(self):
        self.parser.set_line_map(None)

    def _warnings(self, src, project_dir=None):
        self.parser.parse(input=src)
        self.assertEqual(self.parser.errors, [])
        return self.parser.unused_symbol_warnings(project_dir)

    def test_unused_label_variable_and_array(self):
        warnings = self._warnings(
            "[[ DECLARE 0 AS used\nDECLARE 1 AS idle\nLABEL spare\n"
            "DIM table(2)\nSET used TO 1 ]]"
        )
        self.assertEqual(warnings, [
            "Variable 'idle' on line 2 is never used.",
            "Label 'spare' on line 3 is never used.",
            "Data array 'table' on line 4 is never used.",
        ])

    def test_used_symbols_and_constants_do_not_warn(self):
        warnings = self._warnings(
            "[[ CONST NEVER = 3\nDECLARE 0 AS v\nLABEL top\nSET v TO 1\nGOTO top ]]"
        )
        self.assertEqual(warnings, [])

    def test_symbols_from_files_outside_the_project_are_skipped(self):
        project = os.path.abspath("game")
        self.parser.set_line_map({
            1: SourceLocation("main.cyd", 1, os.path.join(project, "main.cyd")),
            2: SourceLocation("lib.cyd", 1, os.path.abspath(os.path.join("lib", "lib.cyd"))),
        })
        warnings = self._warnings("[[ LABEL mine ]]\n[[ LABEL routine ]]", project)
        self.assertEqual(warnings, ["Label 'mine' on main.cyd:1 is never used."])


class TestCheckMode(unittest.TestCase):
    def _run(self, source, *args):
        with tempfile.TemporaryDirectory() as wd:
            sub = Path(wd) / "game"
            sub.mkdir()
            (sub / "main.cyd").write_text(source, encoding="utf-8")
            # Relative path with a directory in it, run from the parent dir.
            return subprocess.run(
                [sys.executable, str(CYDC), *args, "48k", os.path.join("game", "main.cyd")],
                cwd=wd, capture_output=True, text=True, timeout=120,
            )

    def test_valid_script_passes_without_sjasmplus(self):
        r = self._run("Hi\n[[ DECLARE 0 AS spare ]]", "--check")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("WARNING [PARSER]: Variable 'spare' on main.cyd:2 is never used.", r.stdout)
        self.assertIn("No errors found", r.stdout)

    def test_no_warn_unused(self):
        r = self._run("[[ DECLARE 0 AS spare ]]", "--check", "--no-warn-unused")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("WARNING", r.stdout)

    def test_parser_error_fails(self):
        r = self._run("[[ GOTO nowhere ]]", "--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("Label 'nowhere' on main.cyd:1 is not declared.", r.stdout)

    def test_code_generator_error_fails(self):
        r = self._run("[[ LABEL tail ]]\n[[ RESTORE tail ]]", "--check")
        self.assertEqual(r.returncode, 1)
        self.assertIn("RESTORE tail", r.stderr)
        self.assertIn("(at main.cyd:2)", r.stderr)

    def test_assembler_paths_required_without_check(self):
        r = self._run("Hi")
        self.assertEqual(r.returncode, 2)
        self.assertIn("SJASMPLUS_PATH and OUTPUT_PATH are required", r.stderr)


if __name__ == "__main__":
    unittest.main()
