"""lib/sprites.cyd: masked sprites, run in ZEsarUX and checked against a model.

A generated picture (random bytes, fixed seed) holds the sprites, their masks
and the background. The program shows it with DISPLAY, runs the library's
routines, and the whole screen is compared with the same steps done in Python:
sprDraw (masked, with and without attributes, at character and pixel heights),
sprXor, sprSave / sprRestore in several slots, clipping at the screen edges and
both sprErr codes.
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
EXAMPLE = REPO / "examples" / "sprites"


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
    def clip(w, h, dx, dy, py):
        """(columns, first pixel line, lines) left on screen, or None."""
        if dx >= 32 or dy >= 24:
            return None
        y = dy * 8 + py
        if y >= 192:
            return None
        cols, lines = min(w, 32 - dx), min(min(h, 24) * 8, 192 - y)
        return (cols, y, lines) if cols and lines else None

    def _lines(self, sx, sy, w, h, dx, dy, py):
        c = self.clip(w, h, dx, dy, py)
        if c is None:
            return
        cols, y, lines = c
        for k in range(lines):
            for col in range(cols):
                yield (pxl_y(dx + col, y + k), col, k)

    def draw(self, sx, sy, w, h, mx, my, dx, dy, py=0, attr=0):
        for d, c, k in self._lines(sx, sy, w, h, dx, dy, py):
            m = self.buf[pxl(mx + c, my + k // 8, k % 8)]
            s = self.buf[pxl(sx + c, sy + k // 8, k % 8)]
            self.scr[d] = (self.scr[d] & ~m & 0xFF) | s
        c = self.clip(w, h, dx, dy, py)
        if attr and c:
            cols, y, _ = c
            arow = (y + 4) // 8           # where most of the first row falls
            for r in range(min(h, 24 - arow)):
                for col in range(cols):
                    if any(self.buf[pxl(mx + col, my + r, n)] for n in range(8)):
                        self.scr[att(dx + col, arow + r)] = self.buf[att(sx + col, sy + r)]

    def xor(self, sx, sy, w, h, dx, dy, py=0):
        for d, c, k in self._lines(sx, sy, w, h, dx, dy, py):
            self.scr[d] ^= self.buf[pxl(sx + c, sy + k // 8, k % 8)]

    def cells(self, w, h, dx, dy, py=0):
        c = self.clip(w, h, dx, dy, py)
        cols, y, lines = c
        return [(dx + col, row) for row in range(y // 8, (y + lines - 1) // 8 + 1)
                for col in range(cols)]

    def region(self, cells):
        return [self.scr[pxl(x, r, n)] for x, r in cells for n in range(8)] + [
            self.scr[att(x, r)] for x, r in cells]


def params(sx, sy, w, h, mx, my, dx, dy, py=0, attr=0, slot=0):
    names = ("sprX", "sprY", "sprW", "sprH", "sprMX", "sprMY", "sprDX", "sprDY",
             "sprPY", "sprAttr", "sprSlot")
    vals = (sx, sy, w, h, mx, my, dx, dy, py, attr, slot)
    return " : ".join(f"SET {n} TO {v}" for n, v in zip(names, vals))


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestSpritesLibrary(unittest.TestCase):
    def test_routines_against_the_model(self):
        picture = make_picture()
        model = Screen(picture)
        steps = []

        # A 2x2 sprite with its mask at a character position.
        steps.append(params(4, 0, 2, 2, 6, 0, 12, 3) + " : GOSUB sprDraw")
        model.draw(4, 0, 2, 2, 6, 0, 12, 3)
        # The same at pixel height 13: it straddles three character rows.
        steps.append(params(4, 0, 2, 2, 6, 0, 5, 0, py=13) + " : GOSUB sprDraw")
        model.draw(4, 0, 2, 2, 6, 0, 5, 0, py=13)
        # XOR, no mask, 3 pixels below row 4.
        steps.append(params(0, 0, 1, 1, 0, 0, 15, 4, py=3) + " : GOSUB sprXor")
        model.xor(0, 0, 1, 1, 15, 4, py=3)
        # Two overlapping sprites in two slots, restored in reverse order: the
        # background comes back.
        area = sorted(set(model.cells(2, 3, 16, 0, 60)) | set(model.cells(2, 3, 17, 0, 70)))
        before = model.region(area)
        steps.append(params(4, 0, 2, 3, 6, 0, 16, 0, py=60, slot=0)
                     + " : GOSUB sprSave : GOSUB sprDraw")
        steps.append(params(4, 0, 2, 3, 6, 0, 17, 0, py=70, slot=1)
                     + " : GOSUB sprSave : GOSUB sprDraw")
        steps.append("SET sprSlot TO 1 : GOSUB sprRestore : SET sprSlot TO 0 : GOSUB sprRestore")
        # Clipped at the bottom-right corner: column 31, lines 180-191.
        steps.append(params(4, 0, 2, 2, 6, 0, 31, 0, py=180) + " : GOSUB sprDraw")
        model.draw(4, 0, 2, 2, 6, 0, 31, 0, py=180)
        # Colours where the mask isn't empty ((11,0) is), at pixel 86: 6 lines
        # into row 10, so most of the sprite row falls in row 11.
        steps.append(params(8, 0, 2, 1, 10, 0, 20, 0, py=86, attr=1) + " : GOSUB sprDraw")
        model.draw(8, 0, 2, 1, 10, 0, 20, 0, py=86, attr=1)
        # Errors: too big for a slot (40 characters), and no slot 7.
        steps.append(params(0, 0, 8, 5, 0, 0, 0, 12) + " : GOSUB sprSave : SET 1 TO @sprErr")
        steps.append("SET sprSlot TO 7 : GOSUB sprSave : SET 2 TO @sprErr")

        self.assertEqual(model.region(area), before, "model sanity")
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
                    files={"sprites.cyd": LIB.read_text(encoding="utf-8")},
                )
                self.assertEqual(flags[0], 42, "program did not finish")
                self.assertEqual(flags[1], 1, "sprErr not 1 for a save that doesn't fit")
                self.assertEqual(flags[2], 2, "sprErr not 2 for a slot that doesn't exist")
                diff = [i for i in range(6912) if screen[i] != model.scr[i]]
                self.assertEqual(diff, [], f"{len(diff)} bytes differ, first at {diff[:5]}")


class TestSpritesExample(unittest.TestCase):
    def test_example_compiles(self):
        r = subprocess.run(
            [sys.executable, str(REPO / "src" / "cydc" / "cydc" / "cydc.py"), "--check",
             "48k", "test.cyd"],
            cwd=EXAMPLE, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("WARNING", r.stdout)

    def test_images_match_their_generator(self):
        spec = importlib.util.spec_from_file_location("make_images", EXAMPLE / "make_images.py")
        gen = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gen)
        self.assertEqual(gen.scene(), (EXAMPLE / "IMAGES" / "000.scr").read_bytes())
        self.assertEqual(gen.sheet(), (EXAMPLE / "IMAGES" / "001.scr").read_bytes())


if __name__ == "__main__":
    unittest.main()
