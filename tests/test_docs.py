"""The manuals and tutorials are canonical in this repo and published on GitHub
Pages by tools/build_site.py.

Every image they reference must exist here, build_site must copy the docs and
those images (and no others) next to a home page, and the distribution package
leaves the tutorial's screenshots out (the tutorial ships as a PDF).
"""

import importlib.util
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

import build_site  # noqa: E402
import make_dist  # noqa: E402


def referenced_images(doc):
    return sorted(set(re.findall(r"assets/[A-Za-z0-9_.-]+", (REPO / doc).read_text(encoding="utf-8"))))


class TestDocs(unittest.TestCase):
    def test_referenced_images_exist(self):
        for doc in build_site.DOCS:
            with self.subTest(doc):
                missing = [r for r in referenced_images(doc) if not (REPO / r).is_file()]
                self.assertEqual(missing, [])

    def test_site_gets_docs_and_their_images(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = Path(tmp) / "source", Path(tmp) / "out"
            (source / "assets").mkdir(parents=True)
            for doc in build_site.DOCS:
                (source / doc).write_text(f"# {doc}\n![x](assets/{doc}.png)\n", encoding="utf-8")
                (source / "assets" / f"{doc}.png").write_bytes(b"png")
            (source / "assets" / "unused.png").write_bytes(b"png")

            build_site.prepare(source, out)

            for doc in build_site.DOCS:
                self.assertEqual((out / doc).read_text(encoding="utf-8"),
                                 (source / doc).read_text(encoding="utf-8"))
                self.assertTrue((out / "assets" / f"{doc}.png").is_file())
            self.assertFalse((out / "assets" / "unused.png").exists())
            self.assertTrue((out / "index.md").is_file())
            # The home page's logo comes from this repo if the source lacks it.
            self.assertTrue((out / "assets" / "cydlogo_2_gui.png").is_file())

    @unittest.skipUnless(importlib.util.find_spec("pygments"), "needs Pygments (tools/site_requirements.txt)")
    def test_cyd_lexer(self):
        from cyd_pygments import CydLexer
        from pygments.token import Comment, Keyword, Name, String, Text

        def tokens(src):
            return [(t, v) for t, v in CydLexer().get_tokens(src) if v.strip()]

        got = tokens('Hola [[ IF x THEN PRINT "a]b" ENDIF ]] fin')
        self.assertEqual(got[0], (Text, "Hola "))
        self.assertIn((Comment.Preproc, "[["), got)
        self.assertIn((Keyword, "IF"), got)
        self.assertIn((Name.Builtin, "PRINT"), got)
        self.assertIn((String.Double, '"a]b"'), got)
        self.assertEqual(got[-1], (Text, " fin\n"))
        # A snippet without [[ is code (the manuals' one-line examples).
        self.assertEqual(tokens("GOTO fin")[0], (Keyword, "GOTO"))

    def test_package_leaves_tutorial_screenshots_out(self):
        files = make_dist.collect_files(str(REPO), ["assets"], [])
        names = [f.replace(os.sep, "/") for f in files]
        self.assertIn("assets/default_charset.png", names)
        self.assertFalse([n for n in names if re.match(r"assets/tut\d+\.png$", n)])


if __name__ == "__main__":
    unittest.main()
