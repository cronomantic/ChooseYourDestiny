"""Images and tracks are found whatever the case of their names: Windows
ignores it, Linux and macOS do not, and a game must build the same on all of
them. The test example has TRACKS/000.pt3 while the compiler asks for 000.PT3,
so on Linux its music was left out without a word.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src" / "cydc" / "cydc"))
import cydc  # noqa: E402


class TestFindFileAnyCase(unittest.TestCase):
    def test_other_case_is_found(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "000.pt3").write_bytes(b"x")
            (Path(d) / "001.SCR").write_bytes(b"x")
            for asked, on_disk in (("000.PT3", "000.pt3"), ("001.scr", "001.SCR"),
                                   ("000.pt3", "000.pt3")):
                with self.subTest(asked=asked):
                    found = Path(cydc.find_file_any_case(d, asked))
                    self.assertTrue(found.is_file())
                    self.assertEqual(found.name.lower(), on_disk.lower())

    def test_missing_file(self):
        with tempfile.TemporaryDirectory() as d:
            found = Path(cydc.find_file_any_case(d, "002.PT3"))
            self.assertFalse(found.is_file())
            self.assertEqual(found.name, "002.PT3")

    def test_missing_folder(self):
        found = Path(cydc.find_file_any_case("/no/such/folder", "000.PT3"))
        self.assertFalse(found.exists())


if __name__ == "__main__":
    unittest.main()
