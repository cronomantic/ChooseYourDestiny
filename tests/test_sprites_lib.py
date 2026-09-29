"""lib/sprites.cyd and lib/sprites_px.cyd: masked sprites, run in ZEsarUX and
checked against a model.

A generated picture (random bytes, fixed seed) holds the sprites, their masks
and the background. The program shows it with DISPLAY, runs the library's
routines, and the whole screen is compared with the same steps done in Python:
sprDraw (masked, with and without attributes, at character and pixel positions),
sprXor, sprSave / sprRestore in several slots, clipping at the screen edges and
both sprErr codes. sprites_px.cyd also goes through the same cases at pixel X.
"""

import importlib.util
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import emulator_available, run_cyd_ex

REPO = Path(__file__).parent.parent
LIB = REPO / "lib" / "sprites.cyd"
LIB_PX = REPO / "lib" / "sprites_px.cyd"
EXAMPLE = REPO / "examples" / "sprites"
EXAMPLE_PX = REPO / "examples" / "sprites_px"


def pxl(col, row, line):
    """Offset of a character line in the Spectrum screen layout."""
    return pxl_y(col, row * 8 + line)


def pxl_y(col, y):
    """Offset of pixel line y (0..191) at a column."""
    return ((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | col


def att(col, row):
    return 6144 + row * 32 + col


def make_picture():
    rnd = random.Random(1234)
    scr = bytearray(rnd.randrange(256) for _ in range(6144))
    scr += bytes(rnd.randrange(128) for _ in range(768))  # no FLASH
    # The mask of the attribute sprite has an empty cell: (11, 0).
    for line in range(8):
        scr[pxl(11, 0, line)] = 0
    return scr


class Screen:
    """What the library does to the screen, byte for byte."""

    def __init__(self, picture):
        self.buf = picture                # the picture in the buffer
        self.scr = bytearray(picture)     # DISPLAY 1 copied it to the screen
        self.slots = {}

    @staticmethod
    def clip(w, h, dx, dy, py, px=0):
        """(first column, shift, columns, first pixel line, lines) on screen, or None."""
        if not w or dx >= 32 or dy >= 24:
            return None
        x, y = dx * 8 + px, dy * 8 + py
        if x >= 256 or y >= 192:
            return None
        col, shift = x // 8, x % 8
        cols = min(w + (1 if shift else 0), 32 - col)
        lines = min(min(h, 24) * 8, 192 - y)
        return (col, shift, cols, y, lines) if lines else None

    def _rows(self, sx, sy, w, h, dx, dy, py, px, mx=None, my=None):
        """(line, first screen address column, sprite bytes, mask bytes) per line,
        already shifted px pixels to the right and clipped."""
        c = self.clip(w, h, dx, dy, py, px)
        if c is None:
            return
        col, shift, cols, y, lines = c

        def shifted(x0, y0, k):
            row = bytes(self.buf[pxl(x0 + i, y0 + k // 8, k % 8)] for i in range(w))
            v = (int.from_bytes(row, "big") << 8) >> shift
            return v.to_bytes(w + 1, "big")[:cols]

        for k in range(lines):
            yield (y + k, col, shifted(sx, sy, k),
                   shifted(mx, my, k) if mx is not None else None)

    def draw(self, sx, sy, w, h, mx, my, dx, dy, py=0, attr=0, px=0):
        for line, col, s, m in self._rows(sx, sy, w, h, dx, dy, py, px, mx, my):
            for i in range(len(s)):
                d = pxl_y(col + i, line)
                self.scr[d] = (self.scr[d] & ~m[i] & 0xFF) | s[i]
        c = self.clip(w, h, dx, dy, py, px)
        if attr and c:
            col, shift, _, y, _ = c
            arow = (y + 4) // 8           # where most of the first row falls
            acol = col + (1 if shift >= 4 else 0)
            for r in range(min(h, 24 - arow)):
                for i in range(min(w, 32 - acol)):
                    if any(self.buf[pxl(mx + i, my + r, n)] for n in range(8)):
                        self.scr[att(acol + i, arow + r)] = self.buf[att(sx + i, sy + r)]

    def xor(self, sx, sy, w, h, dx, dy, py=0, px=0):
        for line, col, s, _ in self._rows(sx, sy, w, h, dx, dy, py, px):
            for i in range(len(s)):
                self.scr[pxl_y(col + i, line)] ^= s[i]

    def cells(self, w, h, dx, dy, py=0, px=0):
        col, _, cols, y, lines = self.clip(w, h, dx, dy, py, px)
        return [(col + i, row) for row in range(y // 8, (y + lines - 1) // 8 + 1)
                for i in range(cols)]

    def region(self, cells):
        return [self.scr[pxl(x, r, n)] for x, r in cells for n in range(8)] + [
            self.scr[att(x, r)] for x, r in cells]


def params(sx, sy, w, h, mx, my, dx, dy, py=0, attr=0, slot=0, px=None):
    """SETs for the parameters; sprPX only when given (sprites_px.cyd)."""
    names = ("sprX", "sprY", "sprW", "sprH", "sprMX", "sprMY", "sprDX", "sprDY",
             "sprPY", "sprAttr", "sprSlot") + (("sprPX",) if px is not None else ())
    vals = (sx, sy, w, h, mx, my, dx, dy, py, attr, slot) + ((px,) if px is not None else ())
    return " : ".join(f"SET {n} TO {v}" for n, v in zip(names, vals))


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestSpritesLibrary(unittest.TestCase):
    def test_sprites(self):
        self.check(LIB, pixel_x=False)

    def test_sprites_px(self):
        self.check(LIB_PX, pixel_x=True)

    def check(self, lib, pixel_x):
        picture = make_picture()
        model = Screen(picture)
        steps = []
        # sprites_px.cyd: sprPX set to 0 in the character cases.
        z = 0 if pixel_x else None

        # A 2x2 sprite with its mask at a character position.
        steps.append(params(4, 0, 2, 2, 6, 0, 12, 3, px=z) + " : GOSUB sprDraw")
        model.draw(4, 0, 2, 2, 6, 0, 12, 3)
        # The same at pixel height 13: it straddles three character rows.
        steps.append(params(4, 0, 2, 2, 6, 0, 5, 0, py=13, px=z) + " : GOSUB sprDraw")
        model.draw(4, 0, 2, 2, 6, 0, 5, 0, py=13)
        # XOR, no mask, 3 pixels below row 4.
        steps.append(params(0, 0, 1, 1, 0, 0, 15, 4, py=3, px=z) + " : GOSUB sprXor")
        model.xor(0, 0, 1, 1, 15, 4, py=3)
        # Two overlapping sprites in two slots, restored in reverse order: the
        # background comes back.
        area = sorted(set(model.cells(2, 3, 16, 0, 60)) | set(model.cells(2, 3, 17, 0, 70)))
        before = model.region(area)
        steps.append(params(4, 0, 2, 3, 6, 0, 16, 0, py=60, slot=0, px=z)
                     + " : GOSUB sprSave : GOSUB sprDraw")
        steps.append(params(4, 0, 2, 3, 6, 0, 17, 0, py=70, slot=1, px=z)
                     + " : GOSUB sprSave : GOSUB sprDraw")
        steps.append("SET sprSlot TO 1 : GOSUB sprRestore : SET sprSlot TO 0 : GOSUB sprRestore")
        # Clipped at the bottom-right corner: column 31, lines 180-191.
        steps.append(params(4, 0, 2, 2, 6, 0, 31, 0, py=180, px=z) + " : GOSUB sprDraw")
        model.draw(4, 0, 2, 2, 6, 0, 31, 0, py=180)
        # Colours where the mask isn't empty ((11,0) is), at pixel 86: 6 lines
        # into row 10, so most of the sprite row falls in row 11.
        steps.append(params(8, 0, 2, 1, 10, 0, 20, 0, py=86, attr=1, px=z) + " : GOSUB sprDraw")
        model.draw(8, 0, 2, 1, 10, 0, 20, 0, py=86, attr=1)
        if pixel_x:
            # Pixel X. At x = 75 (column 9, 3 pixels in) and y = 100: each byte is
            # spread over two columns, the sprite touches 3x3 cells.
            steps.append(params(4, 0, 2, 2, 6, 0, 0, 0, py=100, px=75) + " : GOSUB sprDraw")
            model.draw(4, 0, 2, 2, 6, 0, 0, 0, py=100, px=75)
            # 6 pixels into column 12, 3 lines into row 5.
            steps.append(params(4, 0, 2, 2, 6, 0, 0, 0, py=43, px=102) + " : GOSUB sprDraw")
            model.draw(4, 0, 2, 2, 6, 0, 0, 0, py=43, px=102)
            # XOR 7 pixels into column 2 (sprDX and sprPX add up).
            steps.append(params(0, 0, 1, 1, 0, 0, 2, 4, px=7) + " : GOSUB sprXor")
            model.xor(0, 0, 1, 1, 2, 4, px=7)
            # Clipped on the right while shifted: column 30 + 4 pixels keeps 2 of
            # its 3 columns, column 31 + 2 pixels keeps 1; x = 256 draws nothing.
            steps.append(params(4, 0, 2, 2, 6, 0, 30, 0, py=120, px=4) + " : GOSUB sprDraw")
            model.draw(4, 0, 2, 2, 6, 0, 30, 0, py=120, px=4)
            steps.append(params(4, 0, 2, 2, 6, 0, 31, 0, py=150, px=2) + " : GOSUB sprDraw")
            model.draw(4, 0, 2, 2, 6, 0, 31, 0, py=150, px=2)
            steps.append(params(4, 0, 2, 2, 6, 0, 31, 0, py=20, px=8) + " : GOSUB sprDraw")
            # Colours 5 pixels into column 24: most of each cell falls in the next
            # column, so they go to columns 25 and 26 ((11,0) is empty).
            steps.append(params(8, 0, 2, 1, 10, 0, 24, 14, px=5, attr=1) + " : GOSUB sprDraw")
            model.draw(8, 0, 2, 1, 10, 0, 24, 14, px=5, attr=1)
            # Two shifted sprites overlapping in two slots: 3x4 cells each, which
            # fills a slot; restored in reverse order, the background comes back.
            area2 = sorted(set(model.cells(2, 3, 0, 0, 60, 163))
                           | set(model.cells(2, 3, 0, 0, 67, 169)))
            before2 = model.region(area2)
            steps.append(params(4, 0, 2, 3, 6, 0, 0, 0, py=60, px=163, slot=2)
                         + " : GOSUB sprSave : SET 3 TO @sprErr : GOSUB sprDraw")
            steps.append(params(4, 0, 2, 3, 6, 0, 0, 0, py=67, px=169, slot=3)
                         + " : GOSUB sprSave : SET 4 TO @sprErr : GOSUB sprDraw")
            steps.append("SET sprSlot TO 3 : GOSUB sprRestore : SET sprSlot TO 2 : GOSUB sprRestore")
        # Errors: too big for a slot (40 characters), and no slot 7.
        steps.append(params(0, 0, 8, 5, 0, 0, 0, 12, px=z) + " : GOSUB sprSave : SET 1 TO @sprErr")
        steps.append("SET sprSlot TO 7 : GOSUB sprSave : SET 2 TO @sprErr")

        self.assertEqual(model.region(area), before, "model sanity")
        if pixel_x:
            self.assertEqual(model.region(area2), before2, "model sanity")
            self.assertEqual(len(model.cells(2, 3, 0, 0, 60, 163)), 12)
        src = (
            '[[\nINCLUDE "sprites.cyd"\nPICTURE 0 : DISPLAY 1\n'
            + "\n".join(steps)
            + "\nSET 0 TO 42\nLABEL spin\nGOTO spin\n]]\n"
        )
        # 128k: the native block runs from a paged bank.
        for target in ("48k", "128k"):
            with self.subTest(target), tempfile.TemporaryDirectory() as wd:
                img = Path(wd) / "000.scr"
                img.write_bytes(picture)
                flags, (screen,) = run_cyd_ex(
                    src, model=target, images=[str(img)], reads=[(0x4000, 6912)],
                    files={"sprites.cyd": lib.read_text(encoding="utf-8")},
                )
                self.assertEqual(flags[0], 42, "program did not finish")
                self.assertEqual(flags[1], 1, "sprErr not 1 for a save that doesn't fit")
                self.assertEqual(flags[2], 2, "sprErr not 2 for a slot that doesn't exist")
                if pixel_x:
                    self.assertEqual(flags[3:5], bytes(2), "a shifted 2x3 sprite does not fit a slot")
                diff = [i for i in range(6912) if screen[i] != model.scr[i]]
                self.assertEqual(diff, [], f"{len(diff)} bytes differ, first at {diff[:5]}")


class TestSpritesExample(unittest.TestCase):
    def test_examples_compile(self):
        for example in (EXAMPLE, EXAMPLE_PX):
            with self.subTest(example.name):
                r = subprocess.run(
                    [sys.executable, str(REPO / "src" / "cydc" / "cydc" / "cydc.py"),
                     "--check", "48k", "test.cyd"],
                    cwd=example, capture_output=True, text=True, timeout=120,
                )
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
                self.assertNotIn("WARNING", r.stdout)

    def test_images_match_their_generator(self):
        # sprites_px uses the same pictures, made by examples/sprites/make_images.py.
        spec = importlib.util.spec_from_file_location("make_images", EXAMPLE / "make_images.py")
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        for example in (EXAMPLE, EXAMPLE_PX):
            with self.subTest(example.name):
                self.assertEqual(gen.scene(), (example / "IMAGES" / "000.scr").read_bytes())
                self.assertEqual(gen.sheet(), (example / "IMAGES" / "001.scr").read_bytes())


if __name__ == "__main__":
    unittest.main()
