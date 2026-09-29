"""make_adventure_gui.py: what can be checked without looking at it.

- The compiler runs with the GUI's language (its messages were in English with
  the GUI in Spanish) and unbuffered, and its output reaches the log line by
  line while it runs, not all at the end.
- The log tells errors and warnings apart, and "game.cyd:12" in it leads to
  the file.
- Run finds the compiled game under the name the compiler gives it (cut to
  10 characters on tape, lowercase extension).
- "Game error" turns a system error's chunk:address into a line with the .map.
- Changing the language rebuilds the window (it used to raise AttributeError)
  and keeps the log. The window tests need a display; they are skipped without
  one.
"""

import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

try:
    import tkinter as tk
    import make_adventure_gui as gui
except ImportError:  # a Python without tkinter
    gui = None


@unittest.skipIf(gui is None, "tkinter not available")
class TestCompilerProcess(unittest.TestCase):
    def test_environment_carries_the_language(self):
        env = gui._child_env("es")
        self.assertEqual(env["LANGUAGE"], "es")
        self.assertEqual(env["CYD_LANG"], "es")
        self.assertEqual(env["PYTHONUNBUFFERED"], "1")
        self.assertEqual(env["PYTHONIOENCODING"], "utf-8")

    def test_output_arrives_while_it_runs(self):
        start, seen = time.time(), []
        code = gui.stream_exec(
            sys.executable,
            ["-c", "import sys, time\nfor i in range(3):\n    print('line', i)\n"
                   "    time.sleep(0.4)\nprint('oops', file=sys.stderr)\nsys.exit(3)"],
            lambda line: seen.append((time.time() - start, line)),
        )
        self.assertEqual(code, 3)
        self.assertEqual([line for _, line in seen], ["line 0", "line 1", "line 2", "oops"])
        # The first line comes long before the process ends.
        self.assertLess(seen[0][0], seen[-1][0] - 0.6)

    def test_compiler_messages_follow_the_language(self):
        lines = []
        gui.stream_exec(sys.executable, [str(REPO / "src" / "cydc" / "cydc" / "cydc.py"), "-h"],
                        lines.append, language="es")
        self.assertTrue(any("abreviatura" in line for line in lines), lines[:5])


MAP = """# chunk:address\tlocation\topcode
0:42500\tgame.cyd:3\tSET
0:42510\tgame.cyd:4\tSET
0:42580\tlib/sprites.cyd:12\tGOSUB
1:40000\tgame.cyd:30\tPRINT
"""


@unittest.skipIf(gui is None, "tkinter not available")
class TestHelpers(unittest.TestCase):
    def test_log_lines_are_classified(self):
        self.assertEqual(gui.classify_log_line("ERROR [PARSER]: Syntax error at g.cyd:3"),
                         "error")
        self.assertEqual(gui.classify_log_line("WARNING [CODEGEN]: Variable 202 is..."),
                         "warning")
        self.assertIsNone(gui.classify_log_line("Compiling g.cyd"))
        self.assertIsNone(gui.classify_log_line("  Errors: 0"))

    def test_source_locations_in_messages(self):
        text = "Variable 201 is 'libB' in l.cyd, and at main.cyd:2 it is declared"
        self.assertEqual(gui.SOURCE_LOCATION_RE.search(text).groups(), ("main.cyd", "2"))
        text = "Label 'nada' on lib/g.cyd:14 is not declared."
        self.assertEqual(gui.SOURCE_LOCATION_RE.search(text).groups(), ("lib/g.cyd", "14"))

    def test_debug_map_lookup(self):
        with tempfile.TemporaryDirectory() as wd:
            path = os.path.join(wd, "game.map")
            with open(path, "w", encoding="utf-8") as f:
                f.write(MAP)
            # The last statement of that chunk at or before the address.
            self.assertEqual(gui.lookup_debug_map(path, "0:42510"), ("game.cyd:4", "SET"))
            self.assertEqual(gui.lookup_debug_map(path, "0:42579"), ("game.cyd:4", "SET"))
            self.assertEqual(gui.lookup_debug_map(path, "SYSTEM ERROR 7 at 0:42582"),
                             ("lib/sprites.cyd:12", "GOSUB"))
            self.assertEqual(gui.lookup_debug_map(path, "1 : 40001"), ("game.cyd:30", "PRINT"))
            self.assertIsNone(gui.lookup_debug_map(path, "0:100"))
            self.assertIsNone(gui.lookup_debug_map(path, "5:42582"))
            with self.assertRaises(ValueError):
                gui.lookup_debug_map(path, "SYSTEM ERROR 7")
            with self.assertRaises(FileNotFoundError):
                gui.lookup_debug_map(os.path.join(wd, "other.map"), "0:1")

    def test_compiled_file_as_the_compiler_names_it(self):
        with tempfile.TemporaryDirectory() as wd:
            open(os.path.join(wd, "aventurala.tap"), "w").close()  # 10 characters
            open(os.path.join(wd, "JUEGO.DSK"), "w").close()
            self.assertEqual(gui.find_compiled_file("48k", "aventuralarga", wd),
                             os.path.join(wd, "aventurala.tap"))
            self.assertEqual(gui.find_compiled_file("plus3", "juego", wd),
                             os.path.join(wd, "JUEGO.DSK"))
            self.assertIsNone(gui.find_compiled_file("128k", "juego", wd))
            self.assertIsNone(gui.find_compiled_file("48k", "juego", os.path.join(wd, "no")))

    def test_source_is_found_under_the_project(self):
        with tempfile.TemporaryDirectory() as wd:
            os.makedirs(os.path.join(wd, "lib"))
            os.makedirs(os.path.join(wd, "dist", "lib"))
            open(os.path.join(wd, "dist", "lib", "sprites.cyd"), "w").close()
            self.assertIsNone(gui.find_source("sprites.cyd", wd))  # not in dist/
            open(os.path.join(wd, "lib", "sprites.cyd"), "w").close()
            self.assertEqual(gui.find_source("sprites.cyd", wd),
                             os.path.join(wd, "lib", "sprites.cyd"))
            self.assertEqual(gui.find_source("lib/sprites.cyd", wd),
                             os.path.join(wd, "lib", "sprites.cyd"))
            self.assertIsNone(gui.find_source("nada.cyd", wd))


def _display():
    if gui is None:
        return False
    try:
        tk.Tk().destroy()
        return True
    except tk.TclError:
        return False


@unittest.skipUnless(_display(), "no display for tkinter")
class TestLanguageChange(unittest.TestCase):
    def test_rebuilds_the_window_and_keeps_the_log(self):
        root = tk.Tk()
        try:
            app = gui.MakeAdventureGUI(root)
            app._log("hello\nERROR [PARSER]: bad")
            root.update()
            app.lang_var.set("es" if app.current_language != "es" else "en")
            app._on_language_change()
            root.update()
            self.assertIn("hello", app.log.get("1.0", "end"))
            self.assertIn("ERROR [PARSER]", app.log.get(*app.log.tag_ranges("error")))
            self.assertEqual(str(app.btn_compile["state"]), "normal")
        finally:
            root.destroy()


@unittest.skipUnless(_display(), "no display for tkinter")
class TestMainWindow(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.app = gui.MakeAdventureGUI(self.root)
        self.root.update()

    def tearDown(self):
        self.root.destroy()

    def test_log_colours_errors_and_warnings(self):
        self.app._log("Compiling\nERROR [PARSER]: bad at g.cyd:3\nWARNING [CODEGEN]: hm")
        self.root.update()
        log = self.app.log
        end = log.index("end-1c")
        errors = log.tag_ranges("error")
        warnings = log.tag_ranges("warning")
        self.assertEqual(len(errors), 2)
        self.assertEqual(len(warnings), 2)
        self.assertIn("ERROR [PARSER]", log.get(*errors))
        self.assertIn("WARNING [CODEGEN]", log.get(*warnings))
        self.assertTrue(log.compare(errors[0], "<", end))

    def test_run_follows_the_compiled_game(self):
        with tempfile.TemporaryDirectory() as wd:
            self.app.var_target.set("48k")
            self.app.var_game_name.set("juego")
            self.app.var_output_path.set(wd)
            self.root.update()
            self.assertEqual(str(self.app.btn_run["state"]), "disabled")
            open(os.path.join(wd, "juego.tap"), "w").close()
            self.app.var_output_path.set(wd)  # any change checks again
            self.root.update()
            self.assertEqual(str(self.app.btn_run["state"]), "normal")

    def test_game_error_without_a_map(self):
        with tempfile.TemporaryDirectory() as wd:
            self.app.var_output_path.set(wd)
            self.app.var_find_error.set("0:42582")
            self.app._on_find_error()
            self.root.update()
            self.assertIn(".map", self.app.log.get(*self.app.log.tag_ranges("warning")))


if __name__ == "__main__":
    unittest.main()
