"""dist/ holds the compiler as it ships, and must match src/.

make_adventure.py and the build scripts run the compiler from dist/, and the
packages are built from it, so a change to src/cydc has to be copied there:

    python make_dist.py --sync-only

This test fails when it hasn't been (a file differs, is missing, or is left over
in dist/ after being removed from src/), and when a translation's .mo is not the
compiled form of its .po.
"""

import fnmatch
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

import make_dist  # noqa: E402

SRC = REPO / "src" / "cydc"
DIST = REPO / "dist"
HINT = "dist/ is out of date: run python make_dist.py --sync-only"

# Translations: (source directory, its copy in dist/).
LOCALES = [(SRC / "cydc" / "locale", DIST / "cydc" / "locale"),
           (SRC / "locale", DIST / "locale")]


def content(path):
    """A file's bytes as git stores them: on a Windows checkout the same file can
    have CRLF in src/ and LF in dist/ (or the other way round) while the commit
    holds the same text, so text files are compared with LF line endings."""
    data = path.read_bytes()
    return data if b"\0" in data else data.replace(b"\r\n", b"\n")


def compiled(po):
    with tempfile.TemporaryDirectory() as tmp:
        mo = Path(tmp) / "out.mo"
        make_dist.compile_po_to_mo(str(po), str(mo))
        return mo.read_bytes()


class TestDistSync(unittest.TestCase):
    def test_compiler_matches_src(self):
        files = make_dist.get_source_files(REPO)
        differ = [f for f in files
                  if not (DIST / f).is_file() or content(DIST / f) != content(SRC / f)]
        self.assertEqual(differ, [], HINT)

    def test_nothing_left_over_in_dist(self):
        files = set(make_dist.get_source_files(REPO))
        extra = [f.relative_to(DIST).as_posix() for f in (DIST / "cydc").rglob("*") if f.is_file()]
        extra = [f for f in extra if f not in files
                 and not any(fnmatch.fnmatch(f, pat) for pat in make_dist.SOURCE_EXCLUDE)]
        self.assertEqual(extra, [], HINT)

    def test_translations_match_src_and_are_compiled(self):
        for src_dir, dist_dir in LOCALES:
            for po in sorted(src_dir.rglob("*.po")):
                rel = po.relative_to(src_dir)
                with self.subTest(str(po.relative_to(REPO))):
                    mo = compiled(po)
                    self.assertEqual(po.with_suffix(".mo").read_bytes(), mo,
                                     "the .mo is not compiled from its .po: " + HINT)
                    self.assertEqual(content(dist_dir / rel), content(po), HINT)
                    self.assertEqual((dist_dir / rel).with_suffix(".mo").read_bytes(), mo, HINT)


if __name__ == "__main__":
    unittest.main()
