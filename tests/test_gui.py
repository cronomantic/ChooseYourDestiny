"""make_adventure_gui.py: what can be checked without looking at it.

- The compiler runs with the GUI's language (its messages were in English with
  the GUI in Spanish) and unbuffered, and its output reaches the log line by
  line while it runs, not all at the end.
- The log tells errors and warnings apart, and "game.cyd:12" in it leads to
  the file.
- Run finds the compiled game under the name the compiler gives it (cut to
  10 characters on tape, lowercase extension).
- "Game error" turns a system error's chunk:address into a line with the .map.
- The internal emulator is found where tools/build_emu_tools.sh leaves it
  (tools/ZEsarUX-<version>/), and the command the GUI runs it with boots the
  game on every target it supports. This one needs sjasmplus and ZEsarUX.
- Changing the language rebuilds the window (it used to raise AttributeError)
  and keeps the log. The window tests need a display; they are skipped without
  one.
"""

import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tests"))
from emu_harness import (  # noqa: E402
    _read_mem, _recv_until_prompt, compile_cyd, emulator_available,
)

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


MAP = """# chunk:address\tlocation\topcode\tcolumn
0:42500\tgame.cyd:3\tSET\t1
0:42510\tgame.cyd:4\tSET\t17
0:42580\tlib/sprites.cyd:12\tGOSUB\t-
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
            self.assertEqual(gui.lookup_debug_map(path, "0:42510"), ("game.cyd:4", "SET", 17))
            self.assertEqual(gui.lookup_debug_map(path, "0:42579"), ("game.cyd:4", "SET", 17))
            self.assertEqual(gui.lookup_debug_map(path, "SYSTEM ERROR 7 at 0:42582"),
                             ("lib/sprites.cyd:12", "GOSUB", None))
            # A map without columns (an older build) still works.
            self.assertEqual(gui.lookup_debug_map(path, "1 : 40001"),
                             ("game.cyd:30", "PRINT", None))
            self.assertIsNone(gui.lookup_debug_map(path, "0:100"))
            self.assertIsNone(gui.lookup_debug_map(path, "5:42582"))
            with self.assertRaises(ValueError):
                gui.lookup_debug_map(path, "SYSTEM ERROR 7")
            with self.assertRaises(FileNotFoundError):
                gui.lookup_debug_map(os.path.join(wd, "other.map"), "0:1")

    def test_error_number_and_meaning(self):
        self.assertEqual(gui.system_error_number("SYSTEM ERROR No:7 at 0:42582"), 7)
        self.assertEqual(gui.system_error_number("system error 10"), 10)
        self.assertIsNone(gui.system_error_number("0:42582"))
        for number in range(1, 11):
            self.assertTrue(gui.system_error_meaning(number))
        self.assertIsNone(gui.system_error_meaning(42))

    def test_statement_within_its_line(self):
        line = '  SET 0 TO 42 : SET 1 TO t(@0) : PRINT "a:b"'
        self.assertEqual(gui.statement_span(line, 3), (2, 13))    # SET 0 TO 42
        self.assertEqual(gui.statement_span(line, 17), (16, 30))  # SET 1 TO t(@0)
        self.assertEqual(gui.statement_span(line, 34), (33, 44))  # ':' in quotes
        self.assertEqual(gui.statement_span("GOSUB x ]]Hola: adiós[[ END", 11, True), (10, 21))
        self.assertEqual(gui.statement_span("LABEL a ]]", 1), (0, 7))
        self.assertIsNone(gui.statement_span("SET 1 TO 2", 40))
        self.assertIsNone(gui.statement_span("SET 1 TO 2", None))

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

    def test_zesarux_is_found_under_tools(self):
        exe = "zesarux.exe" if os.name == "nt" else "zesarux"
        with tempfile.TemporaryDirectory() as wd:
            def make(folder):
                os.makedirs(os.path.join(wd, folder))
                open(os.path.join(wd, folder, exe), "w").close()
                return os.path.join(wd, folder, exe)

            make("ZEsarUX-9.0")
            newest = make("ZEsarUX-13.0")
            make("ZEsarUX_win-11.0")
            self.assertEqual(gui.find_zesarux(wd), newest)  # 13 > 11 > 9
            plain = make("zesarux")
            self.assertEqual(gui.find_zesarux(wd), plain)  # the old place first


@unittest.skipIf(gui is None, "tkinter not available")
@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestRunInZesarux(unittest.TestCase):
    def test_the_game_boots(self):
        zesarux = gui.find_zesarux(str(REPO / "tools"))
        for port, model in enumerate(("48k", "128k", "plus3", "esxdos"), 10240):
            with self.subTest(model), tempfile.TemporaryDirectory() as wd:
                _, flags = compile_cyd("[[ SET 0 TO 42 ]]Hola.[[ WAITKEY ]]", model, wd)
                game = gui.find_compiled_file(model, "test", wd)
                args = gui.zesarux_arguments(model, game, wd)
                # Headless, and listening, so the test can look at the game.
                args[-1:-1] = ["--vo", "null", "--ao", "null", "--enable-remoteprotocol",
                               "--remoteprotocol-port", str(port)]
                proc = subprocess.Popen([zesarux] + args, cwd=os.path.dirname(zesarux),
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    for _ in range(40):
                        try:
                            s = socket.create_connection(("127.0.0.1", port), timeout=1)
                            break
                        except OSError:
                            time.sleep(0.25)
                    else:
                        self.fail("ZEsarUX did not start")
                    with s:
                        _recv_until_prompt(s, 5)
                        deadline, value = time.time() + 40, None
                        while time.time() < deadline and value != 42:
                            time.sleep(1)
                            value = (_read_mem(s, flags, 1) or b"\0")[0]
                    self.assertEqual(value, 42)
                finally:
                    proc.kill()
                    proc.wait()


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
            gui.set_language("en")  # it is global: don't leave it changed


@unittest.skipUnless(_display(), "no display for tkinter")
class TestMainWindow(unittest.TestCase):
    def setUp(self):
        gui.set_language("en")  # the messages below are checked in English
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
            self.assertIn("Show where system errors happen",
                          self.app.log.get(*self.app.log.tag_ranges("warning")))

    def test_game_error_shows_the_script(self):
        with tempfile.TemporaryDirectory() as wd:
            with open(os.path.join(wd, "juego.cyd"), "w", encoding="utf-8") as f:
                f.write("[[ DIM t(3)\n  SET 0 TO 42 : SET 1 TO t(@0) ]]\n")
            with open(os.path.join(wd, "juego.map"), "w", encoding="utf-8") as f:
                f.write("0:100\tjuego.cyd:2\tSET_D\t3\n0:103\tjuego.cyd:2\tPUSH_VAL_ARRAY\t17\n")
            self.app.paths["curr_path"] = wd
            self.app.var_game_name.set("juego")
            self.app.var_output_path.set(wd)
            self.app.var_find_error.set("SYSTEM ERROR No:7 at 0:105")
            self.app._on_find_error()
            self.root.update()
            log = self.app.log.get("1.0", "end")
            self.assertIn("Error 7:", log)
            self.assertIn("juego.cyd, line 2:", log)
            self.assertIn("    " + "  SET 0 TO 42 : SET 1 TO t(@0)", log)
            self.assertIn("\n    " + " " * 16 + "^" * 14 + "\n", log)
            self.assertNotIn("PUSH_VAL_ARRAY", log)  # nothing of the interpreter
            viewers = [w for w in self.root.winfo_children() if isinstance(w, gui.SourceViewer)]
            self.assertEqual(len(viewers), 1)


if __name__ == "__main__":
    unittest.main()
