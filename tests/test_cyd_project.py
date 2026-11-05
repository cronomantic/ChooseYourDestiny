"""cyd_project: a game's folder and its cyd_project.ini, as make_adventure.py
and the GUI read and write them (doc/dev/PROJECT_FOLDER_DESIGN.md)."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src" / "cydc" / "cydc"))
import cyd_project  # noqa: E402


class TempDir(unittest.TestCase):
    def setUp(self):
        self.dir = Path(os.path.realpath(tempfile.mkdtemp()))
        self.addCleanup(shutil.rmtree, self.dir, True)

    def write(self, name, text):
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path


class TestSettings(TempDir):
    def test_defaults_without_a_file(self):
        self.write("juego.cyd", "Hola")
        p = cyd_project.load(str(self.dir))
        self.assertFalse(p.has_file)
        self.assertEqual(p.main, "juego.cyd")  # the only .cyd there is
        self.assertEqual(p.name, "juego")
        self.assertEqual(p.target, "128k")
        self.assertEqual(p.path("output"), str(self.dir / "OUTPUT"))
        self.assertEqual(p.path("images"), str(self.dir / "IMAGES"))

    def test_main_must_be_said_with_several_files(self):
        self.write("a.cyd", "")
        self.write("b.cyd", "")
        with self.assertRaises(cyd_project.ProjectError) as ctx:
            cyd_project.load(str(self.dir)).main
        self.assertEqual(ctx.exception.code, "no_main")

    def test_file_values_and_lists(self):
        self.write("cyd_project.ini",
                   "; un comentario\n[project]\nmain = src/principal.cyd\nname = Mi Juego\n"
                   "target = 48K\n[paths]\nlib_paths = libs ; ../comunes\noutput = salida\n")
        p = cyd_project.load(str(self.dir))
        self.assertEqual(p.main_path, os.path.normpath(str(self.dir / "src" / "principal.cyd")))
        self.assertEqual(p.name, "Mi Juego")
        self.assertEqual(p.target, "48k")
        self.assertEqual(p.paths("lib_paths"),
                         [str(self.dir / "libs"), os.path.normpath(str(self.dir / ".." / "comunes"))])
        self.assertEqual(p.path("output"), str(self.dir / "salida"))

    def test_a_cyd_file_is_the_main_one(self):
        self.write("a.cyd", "")
        main = self.write("b.cyd", "")
        p = cyd_project.find(str(main))
        self.assertEqual(p.root, str(self.dir))
        self.assertEqual((p.main, p.name), ("b.cyd", "b"))

    def test_bad_target(self):
        self.write("cyd_project.ini", "[project]\ntarget = zx81\n")
        with self.assertRaises(cyd_project.ProjectError) as ctx:
            cyd_project.load(str(self.dir)).target
        self.assertEqual(ctx.exception.code, "bad_target")

    def test_install_root(self):
        self.assertTrue(cyd_project.is_install_root(str(self.dir), str(self.dir)))
        self.assertFalse(cyd_project.is_install_root(str(self.dir / "examples"), str(self.dir)))


class TestWriting(unittest.TestCase):
    def test_comments_order_and_unknown_keys_stay(self):
        text = ("; mi juego\n[project]\nname = viejo  \n; el target\ntarget = 48k\n"
                "otra = cosa\n\n[options]\nimage_lines = 192\n")
        new = cyd_project.update_ini_text(text, {"target": "plus3", "image_lines": 96,
                                                 "dead_code_elimination": "yes",
                                                 "images": "PANTALLAS"})
        self.assertEqual(new, (
            "; mi juego\n[project]\nname = viejo  \n; el target\ntarget = plus3\n"
            "otra = cosa\n\n[options]\nimage_lines = 96\ndead_code_elimination = yes\n"
            "\n[paths]\nimages = PANTALLAS\n"))

    def test_crlf_stays(self):
        new = cyd_project.update_ini_text("[project]\r\ntarget = 48k\r\n", {"target": "128k"})
        self.assertEqual(new, "[project]\r\ntarget = 128k\r\n")


class TestCompilerArgs(TempDir):
    def test_options_and_paths(self):
        for folder in ("IMAGES", "libs"):
            (self.dir / folder).mkdir()
        self.write("cyd_project.ini",
                   "[paths]\nlib_paths = libs\n[options]\nwarn_unused = no\n"
                   "dead_code_elimination = yes\nimage_lines = 96\n")
        args = cyd_project.compiler_args(cyd_project.load(str(self.dir)), "48k")
        self.assertEqual(args[:2], ["--project-root", str(self.dir)])
        self.assertIn("--lib-path", args)
        self.assertEqual(args[args.index("--lib-path") + 1], str(self.dir / "libs"))
        self.assertEqual(args[args.index("-img") + 1], str(self.dir / "IMAGES"))
        self.assertNotIn("-trk", args)  # no TRACKS folder
        self.assertEqual(args[args.index("-T") + 1], str(self.dir / "tokens.json"))
        self.assertIn("-dce", args)
        self.assertIn("--no-warn-unused", args)
        self.assertNotIn("--no-warn-gosub", args)
        self.assertEqual(args[args.index("-il") + 1], "96")


class TestMakeAdventure(TempDir):
    """make_adventure.py with projects: --new, --describe and what it refuses."""

    def run_it(self, *args):
        r = subprocess.run([sys.executable, str(REPO / "make_adventure.py"), *args],
                           capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=300, env={**os.environ, "LANGUAGE": "en", "CYD_LANG": "en"})
        return r.returncode, r.stdout + r.stderr

    def test_new_and_describe(self):
        code, out = self.run_it("--new", str(self.dir / "aventura"), "48k")
        self.assertEqual(code, 0, out)
        for name in ("aventura.cyd", "cyd_project.ini", "IMAGES", "TRACKS"):
            self.assertTrue((self.dir / "aventura" / name).exists(), name)
        code, out = self.run_it("--describe", str(self.dir / "aventura"))
        self.assertEqual(code, 0, out)
        values = dict(line.split("=", 1) for line in out.splitlines() if "=" in line)
        self.assertEqual(values["NAME"], "aventura")
        self.assertEqual(values["TARGET"], "48k")
        self.assertTrue(same(values["OUTPUT"], self.dir / "aventura" / "OUTPUT"))
        code, out = self.run_it("--describe", "-n", "otro", "plus3", str(self.dir / "aventura"))
        self.assertIn("NAME=otro", out)
        self.assertIn("TARGET=plus3", out)

    def test_new_project_compiles(self):
        sjasmplus = REPO / "tools" / ("sjasmplus.exe" if os.name == "nt" else "sjasmplus")
        if not sjasmplus.is_file():
            self.skipTest("sjasmplus not available")
        self.run_it("--new", str(self.dir / "nuevo"))
        code, out = self.run_it("--sjasmplus", str(sjasmplus), str(self.dir / "nuevo"), "48k")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.dir / "nuevo" / "OUTPUT" / "nuevo.tap").is_file(), out)

    def test_refused(self):
        code, out = self.run_it("48k")
        self.assertNotEqual(code, 0)
        self.assertIn("No project given", out)
        code, out = self.run_it("--check", str(REPO))
        self.assertNotEqual(code, 0)
        self.assertIn("CYD's own folder can't be a project", out)
        self.run_it("--new", str(self.dir / "ya"))
        code, out = self.run_it("--new", str(self.dir / "ya"))
        self.assertNotEqual(code, 0)
        self.assertIn("There is already a project", out)


def same(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


if __name__ == "__main__":
    unittest.main()
