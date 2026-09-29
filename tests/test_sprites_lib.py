"""lib/sprites.cyd: masked sprites, run in ZEsarUX and checked against a model.

A generated picture (random bytes, fixed seed) holds the sprites, their masks
and the background. The program shows it with DISPLAY, runs every routine of
the library once, and the whole screen is compared with the same steps done in
Python: sprDraw (masked, with and without attributes), sprXor, sprSave /
sprRestore, clipping at the screen edges and the sprErr overflow flag.
"""

import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import emulator_available, run_cyd_ex

LIB = Path(__file__).parent.parent / "lib" / "sprites.cyd"


def pxl(col, row, line):
    """Offset of a character line in the Spectrum screen layout."""
    return ((row & 0x18) << 8) | (line << 8) | ((row & 7) << 5) | col


def att(col, row):
    return 6144 + row * 32 + col


def make_picture():
    rnd = random.Random(1234)
    scr = bytearray(rnd.randrange(256) for _ in range(6144))
    scr += bytes(rnd.randrange(128) for _ in range(768))  # no FLASH
    # The mask of the second attribute sprite has an empty cell: (11, 0).
    for line in range(8):
        scr[pxl(11, 0, line)] = 0
    return scr


class Screen:
    """What the library does to the screen, byte for byte."""

    def __init__(self, picture):
        self.buf = picture                # the picture in the buffer
        self.scr = bytearray(picture)     # DISPLAY 1 copied it to the screen
        self.saved = None

    def clip(self, w, h, dx, dy):
        if dx >= 32 or dy >= 24:
            return 0, 0
        return min(w, 32 - dx), min(h, 24 - dy)

    def draw(self, sx, sy, w, h, mx, my, dx, dy, attr=0):
        w, h = self.clip(w, h, dx, dy)
        for r in range(h):
            for c in range(w):
                for line in range(8):
                    d = pxl(dx + c, dy + r, line)
                    m = self.buf[pxl(mx + c, my + r, line)]
                    s = self.buf[pxl(sx + c, sy + r, line)]
                    self.scr[d] = (self.scr[d] & ~m & 0xFF) | s
                if attr and any(self.buf[pxl(mx + c, my + r, n)] for n in range(8)):
                    self.scr[att(dx + c, dy + r)] = self.buf[att(sx + c, sy + r)]

    def xor(self, sx, sy, w, h, dx, dy):
        w, h = self.clip(w, h, dx, dy)
        for r in range(h):
            for c in range(w):
                for line in range(8):
                    self.scr[pxl(dx + c, dy + r, line)] ^= self.buf[pxl(sx + c, sy + r, line)]

    def region(self, w, h, dx, dy):
        cells = [(dx + c, dy + r) for r in range(h) for c in range(w)]
        return [self.scr[pxl(x, y, n)] for x, y in cells for n in range(8)] + [
            self.scr[att(x, y)] for x, y in cells]


def params(sx, sy, w, h, mx, my, dx, dy, attr=0):
    names = ("sprX", "sprY", "sprW", "sprH", "sprMX", "sprMY", "sprDX", "sprDY", "sprAttr")
    return " : ".join(f"SET {n} TO {v}" for n, v in zip(names, (sx, sy, w, h, mx, my, dx, dy, attr)))


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestSpritesLibrary(unittest.TestCase):
    def test_routines_against_the_model(self):
        picture = make_picture()
        model = Screen(picture)
        steps = []

        # A 2x2 sprite with its mask, keeping the screen's colours.
        steps.append(params(4, 0, 2, 2, 6, 0, 12, 3) + " : GOSUB sprDraw")
        model.draw(4, 0, 2, 2, 6, 0, 12, 3)
        # XOR, no mask.
        steps.append(params(0, 0, 1, 1, 0, 0, 15, 4) + " : GOSUB sprXor")
        model.xor(0, 0, 1, 1, 15, 4)
        # Save, draw, restore: the background comes back.
        before = model.region(2, 2, 16, 8)
        steps.append(params(4, 0, 2, 2, 6, 0, 16, 8)
                     + " : GOSUB sprSave : GOSUB sprDraw : GOSUB sprRestore")
        # Clipped at the bottom-right corner: only column 31, rows 22-23.
        steps.append(params(4, 0, 2, 2, 6, 0, 31, 22) + " : GOSUB sprDraw")
        model.draw(4, 0, 2, 2, 6, 0, 31, 22)
        # Colours only where the mask isn't empty: (8,0) yes, (9,0) no ((11,0) empty).
        steps.append(params(8, 0, 2, 1, 10, 0, 20, 10, attr=1) + " : GOSUB sprDraw")
        model.draw(8, 0, 2, 1, 10, 0, 20, 10, attr=1)
        # Too big to save (40 characters): sprErr = 1 and nothing else changes.
        steps.append(params(0, 0, 8, 5, 0, 0, 0, 12) + " : GOSUB sprSave : SET 1 TO @sprErr")

        src = (
            '[[\nINCLUDE "sprites.cyd"\nPICTURE 0 : DISPLAY 1\n'
            + "\n".join(steps)
            + "\nSET 0 TO 42\nLABEL spin\nGOTO spin\n]]\n"
        )
        self.assertEqual(model.region(2, 2, 16, 8), before, "model sanity")
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
                self.assertEqual(flags[1], 1, "sprErr not set for a save that doesn't fit")
                diff = [i for i in range(6912) if screen[i] != model.scr[i]]
                self.assertEqual(diff, [], f"{len(diff)} bytes differ, first at {diff[:5]}")


if __name__ == "__main__":
    unittest.main()
