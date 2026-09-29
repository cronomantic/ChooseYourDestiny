"""The manuals and tutorials are canonical in this repo and mirrored to the wiki.

Every image they reference must exist here, sync_docs_to_wiki must copy the
docs and those images to the wiki submodule, and the distribution package
leaves the tutorial's screenshots out (the tutorial ships as a PDF).
"""

import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

import make_dist  # noqa: E402


def referenced_images(doc):
    return sorted(set(re.findall(r"assets/[A-Za-z0-9_.-]+", (REPO / doc).read_text(encoding="utf-8"))))


class TestDocs(unittest.TestCase):
    def test_referenced_images_exist(self):
        for doc in make_dist.WIKI_DOCS:
            with self.subTest(doc):
                missing = [r for r in referenced_images(doc) if not (REPO / r).is_file()]
                self.assertEqual(missing, [])

    def test_sync_copies_docs_and_their_images(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            wiki = root / "external" / "ChooseYourDestiny.wiki"
            wiki.mkdir(parents=True)
            (root / "assets").mkdir()
            for doc in make_dist.WIKI_DOCS:
                (root / doc).write_text(f"# {doc}\n![x](assets/{doc}.png)\n", encoding="utf-8")
                (root / "assets" / f"{doc}.png").write_bytes(b"png")
            (root / "assets" / "unused.png").write_bytes(b"png")

            copied = make_dist.sync_docs_to_wiki(str(root))

            for doc in make_dist.WIKI_DOCS:
                self.assertEqual((wiki / doc).read_text(encoding="utf-8"),
                                 (root / doc).read_text(encoding="utf-8"))
                self.assertTrue((wiki / "assets" / f"{doc}.png").is_file())
            self.assertFalse((wiki / "assets" / "unused.png").exists())
            self.assertEqual(len(copied), 2 * len(make_dist.WIKI_DOCS))

    def test_sync_without_wiki_does_nothing(self):
        with tempfile.TemporaryDirectory() as root:
            self.assertIsNone(make_dist.sync_docs_to_wiki(root))

    def test_package_leaves_tutorial_screenshots_out(self):
        files = make_dist.collect_files(str(REPO), ["assets"], [])
        names = [f.replace(os.sep, "/") for f in files]
        self.assertIn("assets/default_charset.png", names)
        self.assertFalse([n for n in names if re.match(r"assets/tut\d+\.png$", n)])


if __name__ == "__main__":
    unittest.main()
