"""make_adventure_gui.py: what can be checked without looking at it.

- The compiler runs with the GUI's language (its messages were in English with
  the GUI in Spanish) and unbuffered, and its output reaches the log line by
  line while it runs, not all at the end.
- Changing the language rebuilds the window (it used to raise AttributeError)
  and keeps the log. This one needs a display; it is skipped without one.
"""

import sys
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
            app._log("hello")
            root.update()
            app.lang_var.set("es" if app.current_language != "es" else "en")
            app._on_language_change()
            root.update()
            self.assertIn("hello", app.log.get("1.0", "end"))
            self.assertEqual(str(app.btn_compile["state"]), "normal")
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
