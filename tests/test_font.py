"""Test suite for CydcFont — charset JSON export/import (-C / -c).

Authors can export the built-in 6x8 charset, edit it, and re-import it. The core
guarantee is that export -> import is lossless, and that a partial/edited charset
is merged sanely over the defaults.
"""

import json
import sys
import unittest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

from cydc_font import CydcFont


class TestFontExport(unittest.TestCase):
    def test_default_font_dimensions(self):
        f = CydcFont()
        self.assertEqual(len(f.font_chars), 256 * 8)
        self.assertEqual(len(f.font_sizes), 256)

    def test_getjson_structure(self):
        f = CydcFont()
        data = json.loads(f.getJson())
        self.assertEqual(len(data), 256)
        self.assertEqual(sorted(data[0].keys()), ["Character", "Id", "Width"])
        self.assertEqual(len(data[0]["Character"]), 8)
        # Ids are the character indices 0..255
        self.assertEqual([e["Id"] for e in data], list(range(256)))


class TestFontRoundtrip(unittest.TestCase):
    def test_default_roundtrip_is_lossless(self):
        f = CydcFont()
        g = CydcFont()
        g.loadCharset(json.loads(f.getJson()))
        self.assertEqual(g.font_chars, f.font_chars)
        self.assertEqual(g.font_sizes, f.font_sizes)

    def test_edited_glyph_roundtrips(self):
        f = CydcFont()
        # Edit glyph 65 ('A'): new bitmap + width.
        data = json.loads(f.getJson())
        data[65]["Character"] = [1, 2, 3, 4, 5, 6, 7, 8]
        data[65]["Width"] = 5
        g = CydcFont()
        g.loadCharset(data)
        self.assertEqual(g.font_chars[65 * 8 : 65 * 8 + 8], [1, 2, 3, 4, 5, 6, 7, 8])
        self.assertEqual(g.font_sizes[65], 5)
        # Untouched glyphs stay at their defaults.
        self.assertEqual(g.font_chars[:8], f.font_chars[:8])


class TestFontMerge(unittest.TestCase):
    def test_loadcharset_sorts_by_id(self):
        f = CydcFont()
        charset = [
            {"Id": 1, "Character": [11] * 8, "Width": 4},
            {"Id": 0, "Character": [10] * 8, "Width": 3},
        ]
        f.loadCharset(charset)
        # Assembled in Id order regardless of input order.
        self.assertEqual(f.font_chars[0:8], [10] * 8)
        self.assertEqual(f.font_chars[8:16], [11] * 8)
        self.assertEqual(f.font_sizes[0], 3)
        self.assertEqual(f.font_sizes[1], 4)

    def test_loadcharset_pads_short_input_with_defaults(self):
        default = CydcFont()
        f = CydcFont()
        # Provide only the first two glyphs; the rest must fall back to defaults.
        f.loadCharset(
            [
                {"Id": 0, "Character": [1] * 8, "Width": 2},
                {"Id": 1, "Character": [2] * 8, "Width": 2},
            ]
        )
        self.assertEqual(len(f.font_chars), len(default.font_chars))
        self.assertEqual(len(f.font_sizes), len(default.font_sizes))
        # Glyph 100 was not provided -> equals the default.
        self.assertEqual(
            f.font_chars[100 * 8 : 100 * 8 + 8],
            default.font_chars[100 * 8 : 100 * 8 + 8],
        )


if __name__ == "__main__":
    unittest.main()
