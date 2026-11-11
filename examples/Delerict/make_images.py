#!/usr/bin/env python3
"""Generates the pictures of Delerict (Spectrum .scr, 6912 bytes), in pure
Python, so the example needs nothing else to rebuild them.

  IMAGES/011.scr .. 020.scr   one picture per location (1..10)
  IMAGES/026.scr .. 030.scr   variants once something has changed there
                              (027: the gallery without light)
  IMAGES/002.scr              the object icons: the new ones are added in row 3
                              (the existing ones in row 0 are left as they are)
  IMAGES/images.json          the location pictures keep only their 80 lines

A location picture fills character rows 1..9 (row 0 is the status bar); the
game copies it to the screen with BLIT 0,1,32,9 AT 0,1.

Each scene is drawn in 16 colours (0-7, and 8-15 for the bright ones) and then
converted to the Spectrum's two colours per 8x8 cell: the two most used colours
of each cell, and the rest of its pixels to the nearer of those two.

    python make_images.py
"""

import json
import math
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
IMAGES = HERE / "IMAGES"
W, H = 256, 192
TOP = 8          # scenes start at character row 1
BOTTOM = 80      # ... and end with row 9

# Spectrum colours: 0 black 1 blue 2 red 3 magenta 4 green 5 cyan 6 yellow 7 white
BLACK, BLUE, RED, MAGENTA, GREEN, CYAN, YELLOW, WHITE = range(8)
B = 8            # add to a colour for its bright version

RGB = [(0, 0, 0), (0, 0, 215), (215, 0, 0), (215, 0, 215),
       (0, 215, 0), (0, 215, 215), (215, 215, 0), (215, 215, 215),
       (0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255),
       (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 255, 255)]


# --- A tiny canvas -----------------------------------------------------------

class Canvas:
    def __init__(self, bg=BLACK):
        self.p = [[bg] * W for _ in range(H)]

    def put(self, x, y, c):
        if 0 <= x < W and TOP <= y < BOTTOM:
            self.p[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def frame(self, x0, y0, x1, y1, c):
        self.hline(x0, x1, y0, c)
        self.hline(x0, x1, y1, c)
        self.vline(x0, y0, y1, c)
        self.vline(x1, y0, y1, c)

    def hline(self, x0, x1, y, c):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            self.put(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            self.put(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.put(x0, y0, c)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def ellipse(self, cx, cy, rx, ry, c, fill=True):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                d = ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2
                if fill and d <= 1.0:
                    self.put(x, y, c)
                elif not fill and 0.78 <= d <= 1.0:
                    self.put(x, y, c)

    def poly(self, pts, c):
        """Filled polygon (even-odd scanlines)."""
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if y0 == y1:
                    continue
                if min(y0, y1) <= y < max(y0, y1):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b)) + 1):
                    self.put(x, y, c)

    def dither(self, x0, y0, x1, y1, c, step=2):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if (x + y) % step == 0:
                    self.put(x, y, c)

    def art(self, x, y, rows, colours, scale=1):
        """ASCII art: each character is a key of `colours` ('.' = leave)."""
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in colours:
                    self.rect(x + dx * scale, y + dy * scale,
                              x + dx * scale + scale - 1, y + dy * scale + scale - 1, colours[ch])

    def stars(self, x0, y0, x1, y1, n, seed, c=WHITE + B):
        rnd = random.Random(seed)
        for _ in range(n):
            self.put(rnd.randint(x0, x1), rnd.randint(y0, y1), c)


# --- Conversion to .scr ---------------------------------------------------------

def _dist(a, b):
    return sum((p - q) ** 2 for p, q in zip(RGB[a], RGB[b]))


def to_scr(canvas, base=None, rows=range(1, 10)):
    """The canvas cells of `rows` written into a copy of `base` (or a black screen)."""
    scr = bytearray(base) if base else bytearray(6912)
    for row in rows:
        for col in range(32):
            cell = [canvas.p[row * 8 + j][col * 8 + i] for j in range(8) for i in range(8)]
            count = {}
            for c in cell:
                count[c] = count.get(c, 0) + 1
            order = sorted(count, key=lambda c: -count[c])
            paper = order[0]
            ink = order[1] if len(order) > 1 else paper
            bright = 1 if (paper >= B or ink >= B) else 0
            for j in range(8):
                byte = 0
                for i in range(8):
                    c = cell[j * 8 + i]
                    byte = (byte << 1) | (1 if _dist(c, ink) < _dist(c, paper) else 0)
                y = row * 8 + j
                scr[((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | col] = byte
            scr[6144 + row * 32 + col] = (bright << 6) | ((paper & 7) << 3) | (ink & 7)
    return scr


# --- Location pictures: a 1-bit picture plus a colour per character ----------------
#
# Like most Spectrum adventure pictures: the detail (lines, shading by ordered
# dithering) is one bitmap, and each 8x8 cell gets its ink and paper, so colours
# never clash. Every scene uses one main ink, with accents in their own cells.

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


class Pic:
    def __init__(self, ink=CYAN, paper=BLACK, bright=0):
        self.bit = [[0] * W for _ in range(H)]
        self.attr = {(c, r): [ink, paper, bright] for r in range(1, 10) for c in range(32)}

    @staticmethod
    def inside(x, y):
        return 0 <= x < W and TOP <= y < BOTTOM

    def set(self, x, y, v=1):
        x, y = int(round(x)), int(round(y))
        if self.inside(x, y):
            self.bit[y][x] = v

    def shade(self, x, y, level):
        """Ordered dithering: level 0 (empty) .. 16 (solid)."""
        if BAYER[y & 3][x & 3] < level:
            self.set(x, y)

    def fill(self, x, y, how):
        if callable(how):
            self.shade(x, y, how(x, y))
        elif how is True:
            self.set(x, y, 1)
        elif how is None or how is False or how == 0:
            self.set(x, y, 0)
        else:
            self.shade(x, y, how)

    def rect(self, x0, y0, x1, y1, how=True):
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.fill(x, y, how)

    def clear(self, x0, y0, x1, y1):
        self.rect(x0, y0, x1, y1, 0)

    def box(self, x0, y0, x1, y1, v=1):
        self.line(x0, y0, x1, y0, v)
        self.line(x0, y1, x1, y1, v)
        self.line(x0, y0, x0, y1, v)
        self.line(x1, y0, x1, y1, v)

    def line(self, x0, y0, x1, y1, v=1):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.set(x0, y0, v)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def dotted(self, x0, y0, x1, y1, step=3):
        n = int(max(abs(x1 - x0), abs(y1 - y0)) // step)
        for k in range(n + 1):
            self.set(x0 + (x1 - x0) * k / max(n, 1), y0 + (y1 - y0) * k / max(n, 1))

    def poly(self, pts, how=True):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for i in range(len(pts)):
                (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
                if y0 == y1:
                    continue
                if min(y0, y1) <= y < max(y0, y1):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b)) + 1):
                    self.fill(x, y, how)

    def outline(self, pts, v=1):
        for i in range(len(pts)):
            self.line(*pts[i], *pts[(i + 1) % len(pts)], v)

    def ellipse(self, cx, cy, rx, ry, how=True):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                if ((x - cx) / max(rx, 0.5)) ** 2 + ((y - cy) / max(ry, 0.5)) ** 2 <= 1.0:
                    self.fill(x, y, how)

    def oval(self, cx, cy, rx, ry, v=1, a0=0, a1=360):
        """Outline of an ellipse, or of the arc from a0 to a1 degrees (0 = right, 90 = down)."""
        steps = int(max(rx, ry) * 7) + 8
        for k in range(steps + 1):
            a = math.radians(a0 + (a1 - a0) * k / steps)
            self.set(cx + rx * math.cos(a), cy + ry * math.sin(a), v)

    def colour(self, x0, y0, x1, y1, ink=None, paper=None, bright=None):
        """Ink/paper/bright of every cell touched by the pixel box."""
        for r in range(max(1, int(y0) // 8), min(9, int(y1) // 8) + 1):
            for c in range(max(0, int(x0) // 8), min(31, int(x1) // 8) + 1):
                a = self.attr[(c, r)]
                if ink is not None:
                    a[0] = ink
                if paper is not None:
                    a[1] = paper
                if bright is not None:
                    a[2] = bright

    def stars(self, region, n, seed, big=0):
        x0, y0, x1, y1 = region
        rnd = random.Random(seed)
        for _ in range(n):
            self.set(rnd.randint(x0, x1), rnd.randint(y0, y1))
        for _ in range(big):
            x, y = rnd.randint(x0 + 2, x1 - 2), rnd.randint(y0 + 2, y1 - 2)
            for d in (-1, 0, 1):
                self.set(x + d, y)
                self.set(x, y + d)


def pic_to_scr(pic, base=None):
    scr = bytearray(base) if base else bytearray(6912)
    for row in range(1, 10):
        for col in range(32):
            ink, paper, bright = pic.attr[(col, row)]
            for j in range(8):
                y = row * 8 + j
                byte = 0
                for i in range(8):
                    byte = (byte << 1) | pic.bit[y][col * 8 + i]
                scr[((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | col] = byte
            scr[6144 + row * 32 + col] = (bright << 6) | ((paper & 7) << 3) | (ink & 7)
    return scr


def room(p, back, ceil=3, floor=None, wall=2, rear=1, seams=(0.3, 0.55, 0.75, 0.9), grid=True):
    """A room in perspective: back wall `back` = (x0, y0, x1, y1)."""
    bx0, by0, bx1, by1 = back
    if floor is None:
        floor = lambda x, y: 1 + int(5 * (y - by1) / max(1, 79 - by1))
    p.poly([(0, 8), (255, 8), (bx1, by0), (bx0, by0)], ceil)
    p.poly([(bx0, by1), (bx1, by1), (255, 79), (0, 79)], floor)
    p.poly([(0, 8), (bx0, by0), (bx0, by1), (0, 79)], wall)
    p.poly([(255, 8), (bx1, by0), (bx1, by1), (255, 79)], wall)
    p.rect(bx0, by0, bx1, by1, rear)
    if grid:
        for k in range(-4, 13):
            t = k / 8
            xb, xf = bx0 + (bx1 - bx0) * t, -96 + (255 + 192) * t
            if 0 <= xb <= 255 or 0 <= xf <= 255:
                p.line(xb, by1, xf, 79)
        for f in (0.12, 0.3, 0.55, 0.85):
            y = by1 + (79 - by1) * f
            p.line(bx0 * (1 - f), y, bx1 + (255 - bx1) * f, y)
    for s in seams:
        x = bx0 * s
        p.line(x, 8 + (by0 - 8) * s, x, 79 + (by1 - 79) * s)
        x = 255 - (255 - bx1) * s
        p.line(x, 8 + (by0 - 8) * s, x, 79 + (by1 - 79) * s)
    for a, b, c, d in ((0, 8, bx0, by0), (255, 8, bx1, by0), (0, 79, bx0, by1), (255, 79, bx1, by1)):
        p.line(a, b, c, d)
    p.box(bx0, by0, bx1, by1)


def wall_x(back, side, s):
    """Pixel column at fraction s (0 = screen edge, 1 = back wall) of a side wall, and
    the top and bottom of the wall there."""
    bx0, by0, bx1, by1 = back
    x = bx0 * s if side == 0 else 255 - (255 - bx1) * s
    return x, 8 + (by0 - 8) * s, 79 + (by1 - 79) * s


def wall_quad(back, side, s0, s1, top, bottom):
    """A rectangle on a side wall, from fraction s0 to s1, between the heights
    `top` and `bottom` (0 = ceiling, 1 = floor): its four corners."""
    pts = []
    for s, h in ((s0, top), (s1, top), (s1, bottom), (s0, bottom)):
        x, yt, yb = wall_x(back, side, s)
        pts.append((x, yt + (yb - yt) * h))
    return pts


# 1 · Cabina de mandos
def cabin():
    p = Pic(CYAN)
    # The ceiling, with panels.
    p.rect(0, 8, 255, 15, 3)
    for x in range(0, 256, 32):
        p.line(x, 8, x + 4, 15)
    p.line(0, 15, 255, 15)
    # The windscreen: three panes.
    shield = [(28, 17), (228, 17), (250, 50), (6, 50)]
    p.poly(shield, 0)
    p.colour(0, 16, 255, 50, ink=WHITE)
    p.stars((8, 18, 248, 49), 70, 11, big=6)
    # A nebula in the left pane.
    p.ellipse(52, 30, 34, 10, lambda x, y: max(0, 6 - int(abs(x - 52) / 7 + abs(y - 30) / 2)))
    p.colour(16, 18, 95, 42, ink=MAGENTA)
    # The Carl Sagan: ring, spine, modules and engines.
    sx, sy = 176, 33
    p.oval(sx, sy, 12, 6)
    p.oval(sx, sy, 9, 4)
    p.line(sx - 30, sy, sx + 34, sy)
    p.line(sx - 30, sy + 1, sx + 34, sy + 1)
    p.rect(sx - 24, sy - 3, sx - 16, sy + 4, True)
    p.rect(sx + 18, sy - 2, sx + 30, sy + 3, True)
    p.rect(sx + 31, sy - 4, sx + 34, sy + 5, True)
    p.colour(sx - 32, sy - 8, sx + 36, sy + 8, ink=WHITE, bright=1)
    # The frame and struts.
    p.outline(shield)
    p.outline([(27, 16), (229, 16), (251, 51), (5, 51)])
    for (a, b) in ((98, 85), (158, 171)):
        p.line(a, 17, b, 50)
        p.line(a + 1, 17, b + 1, 50)
    # The console: a slanted top and its front.
    p.poly([(6, 52), (250, 52), (255, 62), (0, 62)], 4)
    p.line(0, 62, 255, 62)
    p.rect(0, 63, 255, 79, 2)
    p.line(6, 52, 250, 52)
    # Two screens: radar and readings.
    for x0 in (24, 184):
        p.clear(x0, 54, x0 + 47, 61)
        p.box(x0, 54, x0 + 47, 61)
        p.colour(x0, 54, x0 + 47, 61, ink=GREEN, bright=1)
    p.oval(48, 57, 8, 3)
    p.line(48, 57, 54, 55)
    for k in range(5):
        p.line(188 + k * 8, 58 + (k % 2) * 2, 194 + k * 8, 57 - (k % 3))
    # Buttons in rows.
    for i, x in enumerate(range(16, 240, 12)):
        if 88 <= x <= 160:
            continue
        p.clear(x, 66, x + 7, 71)
        p.rect(x + 1, 67, x + 5, 70, True)
        p.colour(x, 66, x + 7, 71, ink=(RED, YELLOW, GREEN)[i % 3], bright=1)
    # The yoke.
    p.clear(104, 56, 151, 79)
    p.rect(124, 60, 131, 79, 5)
    p.box(124, 60, 131, 79)
    p.rect(104, 58, 151, 61, True)
    p.rect(104, 56, 109, 66, True)
    p.rect(146, 56, 151, 66, True)
    p.colour(104, 56, 151, 79, ink=WHITE)
    return p


# 2 · Habitáculo
def main_area():
    back = (96, 26, 159, 58)
    p = Pic(CYAN)
    room(p, back, ceil=1, wall=1, rear=2)
    # Light strips along the ceiling.
    for f in (0.2, 0.5, 0.75):
        y = 8 + (back[1] - 8) * f
        w = 40 * (1 - f) + 10
        p.rect(128 - w, y, 128 + w, y + 1, True)
    # Sleeping pods along both walls: two rows.
    for side in (0, 1):
        for s0 in (0.08, 0.42):
            for top, bottom in ((0.12, 0.45), (0.52, 0.86)):
                q = wall_quad(back, side, s0, s0 + 0.26, top, bottom)
                p.poly(q, 0)
                p.outline(q)
                inner = wall_quad(back, side, s0 + 0.04, s0 + 0.22, top + 0.06, bottom - 0.06)
                lit = side == 1 and s0 == 0.08 and top == 0.52
                p.poly(inner, 9 if lit else 2)
                p.outline(inner)
                if lit:
                    xs = [pt[0] for pt in q]
                    ys = [pt[1] for pt in q]
                    p.colour(min(xs), min(ys), max(xs), max(ys), bright=1)
    # The door to the airlock, at the back.
    p.clear(112, 32, 143, 58)
    p.box(112, 32, 143, 58)
    p.box(115, 35, 140, 58)
    p.rect(122, 40, 133, 46, 0)
    p.box(122, 40, 133, 46)
    p.rect(124, 50, 131, 51, True)
    p.colour(120, 48, 135, 55, ink=YELLOW, bright=1)
    # The hatch in the floor, near.
    p.ellipse(128, 70, 30, 6, 0)
    p.oval(128, 70, 30, 6)
    p.oval(128, 70, 25, 4)
    p.rect(120, 69, 136, 70, True)
    p.colour(96, 64, 159, 79, ink=WHITE, bright=1)
    return p


# 3 · Esclusa
def airlock():
    back = (72, 18, 183, 66)
    p = Pic(CYAN)
    room(p, back, ceil=1, wall=1, rear=0, seams=(0.4, 0.75), grid=False)
    # Hazard frame around the outer door.
    p.rect(80, 18, 175, 66, lambda x, y: 16 if ((x + y) // 6) % 2 else 0)
    p.colour(80, 18, 175, 66, ink=YELLOW)
    # The outer door: rings, bolts and wheel.
    cx, cy = 128, 42
    p.ellipse(cx, cy, 40, 23, 0)
    p.ellipse(cx, cy, 38, 21, 3)
    p.oval(cx, cy, 38, 21)
    p.oval(cx, cy, 30, 16)
    p.ellipse(cx, cy, 29, 15, True)
    p.ellipse(cx, cy, 27, 14, 0)
    for a in range(0, 360, 30):
        r = math.radians(a)
        p.rect(cx + 34 * math.cos(r) - 1, cy + 18.5 * math.sin(r) - 1,
               cx + 34 * math.cos(r), cy + 18.5 * math.sin(r), 1)
    p.oval(cx, cy, 13, 7)
    p.oval(cx, cy, 12, 6)
    for a in range(0, 360, 60):
        r = math.radians(a)
        p.line(cx, cy, cx + 13 * math.cos(r), cy + 7 * math.sin(r))
    p.rect(cx - 2, cy - 1, cx + 2, cy + 1, True)
    p.colour(88, 24, 167, 63, ink=WHITE)
    # The control panel on the right wall.
    q = wall_quad(back, 1, 0.25, 0.7, 0.25, 0.7)
    p.poly(q, 0)
    p.outline(q)
    for j in range(4):
        for i in range(3):
            s = 0.33 + i * 0.12
            x, yt, yb = wall_x(back, 1, s)
            y = yt + (yb - yt) * (0.42 + j * 0.07)
            p.rect(x - 2, y, x + 1, y + 2, True)
    x, yt, yb = wall_x(back, 1, 0.3)
    p.colour(184, 24, 239, 56, ink=CYAN, bright=1)
    p.rect(200, 28, 232, 31, True)
    p.colour(200, 24, 239, 31, ink=GREEN, bright=1)
    # The warning beacon, on the ceiling, and its glow.
    p.clear(24, 8, 47, 15)
    p.ellipse(36, 10, 6, 3, True)
    for k in range(6):
        p.line(36, 13, 18 + k * 7, 23 + (k % 2) * 3)
    p.colour(16, 8, 55, 23, ink=RED, bright=1)
    return p


# 4 · Bodega
def hold():
    back = (88, 24, 167, 60)
    p = Pic(CYAN)
    room(p, back, ceil=1, wall=1, rear=2, seams=(0.6,))
    # The cabinet on the left wall.
    q = wall_quad(back, 0, 0.12, 0.62, 0.1, 0.93)
    p.poly(q, 0)
    p.outline(q)
    xm, ytm, ybm = wall_x(back, 0, 0.37)
    p.line(xm, ytm + (ybm - ytm) * 0.1, xm, ytm + (ybm - ytm) * 0.93)
    for s in (0.32, 0.42):
        x, yt, yb = wall_x(back, 0, s)
        p.rect(x - 1, yt + (yb - yt) * 0.45, x, yt + (yb - yt) * 0.55, True)
    for s0 in (0.16, 0.41):
        inner = wall_quad(back, 0, s0, s0 + 0.17, 0.18, 0.4)
        p.outline(inner)
        p.poly(inner, 3)
    xs = [pt[0] for pt in q]
    ys = [pt[1] for pt in q]
    p.colour(min(xs) + 2, min(ys) + 2, max(xs) - 2, max(ys) - 2, ink=YELLOW)
    # Shelves with crates on the right wall.
    for h in (0.33, 0.66):
        a, b = wall_x(back, 1, 0.05), wall_x(back, 1, 0.95)
        p.line(a[0], a[1] + (a[2] - a[1]) * h, b[0], b[1] + (b[2] - b[1]) * h)
        for s0 in (0.08, 0.36, 0.64):
            q = wall_quad(back, 1, s0, s0 + 0.22, h - 0.22, h)
            p.poly(q, 0)
            p.outline(q)
            p.poly(wall_quad(back, 1, s0 + 0.03, s0 + 0.19, h - 0.19, h - 0.03), 4)
    # Crates and nets at the back.
    for x0, y0, x1 in ((92, 44, 115), (116, 48, 135), (140, 40, 163)):
        p.clear(x0, y0, x1, 60)
        p.box(x0, y0, x1, 60)
        p.line(x0, y0, x1, 60)
        p.line(x1, y0, x0, 60)
    # The ladder up to the ceiling hatch, and light falling from it.
    p.poly([(112, 8), (143, 8), (160, 79), (96, 79)], lambda x, y: 2 + (79 - y) // 24)
    p.clear(116, 8, 139, 12)
    p.box(116, 8, 139, 12)
    for x in (118, 137):
        p.line(x, 13, x - 4 + (x > 128) * 8, 79)
    for k in range(9):
        y = 16 + k * 7
        d = (y - 13) * 4 / 66
        p.line(118 - d, y, 137 + d, y)
    p.colour(112, 8, 143, 79, ink=WHITE)
    return p


# 5 · Sala de máquinas
def engine_room():
    back = (80, 20, 175, 62)
    p = Pic(CYAN)
    room(p, back, ceil=1, wall=2, rear=1, seams=(0.5,))
    # Pipes along both walls.
    for side in (0, 1):
        for h in (0.15, 0.22, 0.75):
            a, b = wall_x(back, side, 0.0), wall_x(back, side, 1.0)
            for d in (0, 2):
                p.line(a[0], a[1] + (a[2] - a[1]) * h + d, b[0], b[1] + (b[2] - b[1]) * h + d)
        for s in (0.3, 0.65):
            x, yt, yb = wall_x(back, side, s)
            p.ellipse(x, yt + (yb - yt) * 0.18, 3, 4, True)
    # The reactor: a column with rings and a glowing core.
    p.clear(104, 8, 151, 79)
    p.rect(108, 8, 147, 79, 2)
    for x in (104, 151):
        p.line(x, 8, x, 79)
    for y in (12, 20, 66, 74):
        p.rect(104, y, 151, y + 1, True)
    p.rect(112, 26, 143, 60, 0)
    p.rect(112, 26, 143, 60, lambda x, y: 16 - int(abs(x - 127.5) / 1.3))
    p.box(112, 26, 143, 60)
    p.colour(104, 24, 151, 63, ink=RED, bright=1)
    p.colour(112, 32, 143, 55, ink=YELLOW, bright=1)
    # The radiation sign on the back wall.
    cx, cy = 164, 34
    p.clear(156, 26, 175, 41)
    p.ellipse(cx, cy, 8, 7, True)
    for a in (-90, 30, 150):
        r = math.radians(a)
        p.poly([(cx, cy), (cx + 9 * math.cos(r - 0.5), cy + 8 * math.sin(r - 0.5)),
                (cx + 9 * math.cos(r + 0.5), cy + 8 * math.sin(r + 0.5))], 0)
    p.ellipse(cx, cy, 2, 2, 0)
    p.set(cx, cy)
    p.colour(156, 26, 175, 41, ink=YELLOW, bright=1)
    # A railing in the foreground.
    for y in (66, 71):
        p.line(0, y, 255, y)
    for x in range(8, 256, 24):
        p.line(x, 66, x, 79)
    return p


# 6 · Pasillo de acceso del pecio
def corridor(open_door=False):
    p = Pic(GREEN)
    cx, cy = 128, 46
    # Ribs: arches that shrink towards the door, shaded.
    for k in range(7):
        f = k / 7
        rx, ry = 150 * (1 - f) + 26 * f, 46 * (1 - f) + 14 * f
        th = 7 * (1 - f) + 2
        p.oval(cx, cy + 6, rx, ry + 6, 1, 180, 360)
        for d in range(1, int(th)):
            p.oval(cx, cy + 6, rx - d, ry + 6 - d * 0.5, 1 if d < 2 else 0, 180, 360)
            if d >= 2:
                for a in range(180, 361, 2):
                    r = math.radians(a)
                    x, y = cx + (rx - d) * math.cos(r), cy + 6 + (ry + 6 - d * 0.5) * math.sin(r)
                    p.shade(int(x), int(y), 3 + 5 * (d % 2))
    # Membranes between the ribs.
    for y in range(8, 80):
        for x in range(0, 256):
            if (x * 7 + y * 13) % 97 == 0:
                p.set(x, y)
    # The floor: organic ridges.
    p.rect(0, 70, 255, 79, 0)
    for k, y in enumerate((70, 73, 77)):
        p.line(0, y, 255, y + (k % 2))
    for x in range(-200, 456, 40):
        p.line(cx, 62, x, 79)
    p.clear(0, 62, 255, 69)
    p.line(0, 66, 96, 62)
    p.line(255, 66, 160, 62)
    # The iris door.
    p.ellipse(cx, cy, 25, 16, 0)
    p.oval(cx, cy, 25, 16)
    p.oval(cx, cy, 22, 14)
    if open_door:
        p.ellipse(cx, cy, 19, 12, 0)
        for a in range(0, 360, 40):
            r = math.radians(a)
            p.line(cx + 19 * math.cos(r), cy + 12 * math.sin(r), cx + 22 * math.cos(r + 0.3), cy + 14 * math.sin(r + 0.3))
        p.ellipse(cx, cy + 6, 10, 3, lambda x, y: 3)
    else:
        for i, a in enumerate(range(0, 360, 45)):
            r0, r1 = math.radians(a), math.radians(a + 45)
            p.poly([(cx, cy), (cx + 22 * math.cos(r0), cy + 14 * math.sin(r0)),
                    (cx + 22 * math.cos(r1), cy + 14 * math.sin(r1))], 4 if i % 2 else 10)
            p.line(cx, cy, cx + 22 * math.cos(r0), cy + 14 * math.sin(r0))
        p.ellipse(cx, cy, 3, 2, True)
    p.colour(96, 24, 159, 63, ink=MAGENTA, bright=1)
    if not open_door:
        p.colour(120, 40, 135, 47, ink=RED, bright=1)
    return p


# 7 · Galería
def gallery():
    back = (104, 30, 151, 58)
    p = Pic(GREEN)
    # Vault ribs converging on the back.
    for k in range(-6, 7):
        p.line(128 + k * 44, 8, 128 + k * 4, 30)
    p.poly([(0, 8), (255, 8), (151, 30), (104, 30)], 2)
    # Rows of pillars, receding.
    for side in (0, 1):
        for k, (s, w) in enumerate(((0.0, 22), (0.42, 13), (0.68, 8), (0.84, 5))):
            x = 0 + (104 - 0) * s if side == 0 else 255 - (255 - 151) * s
            top = 8 + (30 - 8) * s
            bot = 79 + (58 - 79) * s
            x0 = x if side == 0 else x - w
            p.clear(x0 - 1, top, x0 + w + 1, bot)
            p.rect(x0, top, x0 + w, bot, lambda xx, yy: 3 + (5 if (xx - x0) < w / 3 else 0))
            p.line(x0, top, x0, bot)
            p.line(x0 + w, top, x0 + w, bot)
            p.rect(x0 - 2, top, x0 + w + 2, top + max(2, w // 4), True)
            p.rect(x0 - 2, bot - max(2, w // 4), x0 + w + 2, bot, True)
    # The floor: a dark, glossy pool reflecting the pillars.
    p.poly([(104, 58), (151, 58), (255, 79), (0, 79)], lambda x, y: 1 + (y - 58) // 7)
    for f in (0.2, 0.5, 0.85):
        y = 58 + 21 * f
        p.dotted(104 * (1 - f), y, 151 + 104 * f, y, 2)
    # The arch to the north, glowing, and the opening to the east.
    p.clear(108, 30, 147, 58)
    p.oval(128, 58, 18, 26, 1, 180, 360)
    p.oval(128, 58, 14, 22, 1, 180, 360)
    p.ellipse(128, 58, 13, 21, lambda x, y: 2 + (y - 36) // 6)
    p.colour(104, 32, 151, 58, ink=MAGENTA, bright=1)
    q = wall_quad(back, 1, 0.5, 0.75, 0.2, 1.0)
    p.poly(q, 0)
    p.outline(q)
    p.poly(wall_quad(back, 1, 0.53, 0.72, 0.25, 1.0), 4)
    xs = [pt[0] for pt in q]
    p.colour(min(xs), 24, max(xs), 71, ink=MAGENTA, bright=1)
    return p


def gallery_dark():
    """Without light: only the outlines nearest to the corridor's glow, behind you."""
    p = Pic(GREEN)
    for x0, w in ((0, 22), (233, 22)):
        p.rect(x0, 60, x0 + w, 79, lambda xx, yy: max(0, (yy - 60) // 5))
    p.poly([(60, 79), (196, 79), (150, 70), (106, 70)], lambda x, y: (y - 70) // 3)
    return p


CREATURE = [
    "..........GGGGGGGGGG..........",
    "........GGGGGGGGGGGGGG........",
    "......GGGGGGGGGGGGGGGGGG......",
    ".....GGGGRRGGGGGGGGRRGGGG.....",
    "....GGGGRRRRGGGGGGRRRRGGGG....",
    "....GGGGGRRGGGGGGGGRRGGGGG....",
    "...GGGGGGGGGGGGGGGGGGGGGGGG...",
    "...GGGGG.GGGGGGGGGGGG.GGGGG...",
    "..GGGGGG..WW.WW.WW.WW..GGGGG..",
    "..GGGGGGG..............GGGGGG.",
    "..GGGGGGGG.W..W..W..W.GGGGGGG.",
    "..GGGGGGGGGGGGGGGGGGGGGGGGGGG.",
    "...GGGG.GGGG.GGGGG.GGGG.GGGG..",
    "...GGG..GGG...GGG...GGG..GGG..",
    "..GGG..GGG....GGG....GGG..GGG.",
    "..GG..GGG.....GG......GGG..GG.",
    ".GG..GG......GG........GG...GG",
    ".G...G.......G..........G....G",
    "GG..GG......GG..........GG...G",
]


# 8 · Criadero
def nursery(creature=True):
    back = (88, 28, 167, 56)
    p = Pic(MAGENTA)
    room(p, back, ceil=1, wall=1, rear=2, seams=(), grid=False)
    p.poly([(88, 56), (167, 56), (255, 79), (0, 79)], lambda x, y: 1 + (y - 56) // 6)
    # Veins on the walls.
    rnd = random.Random(8)
    for _ in range(14):
        x, y = rnd.randint(0, 255), rnd.randint(10, 60)
        for _ in range(18):
            nx, ny = x + rnd.randint(-4, 4), y + rnd.randint(-1, 3)
            p.line(x, y, nx, ny)
            x, y = nx, ny
    # Egg pods in two rows, receding.
    for side in (0, 1):
        for s, rx, ry in ((0.12, 13, 17), (0.45, 9, 12), (0.72, 6, 8)):
            x, yt, yb = wall_x(back, side, s)
            x += 12 if side == 0 else -12
            cy = yb - ry - 2
            p.ellipse(x, cy, rx + 1, ry + 1, 0)
            p.oval(x, cy, rx, ry)
            p.ellipse(x, cy + 2, rx - 3, ry - 4, lambda xx, yy: 6 + (yy - cy) // 2)
            p.colour(x - rx, cy - ry, x + rx, cy + ry, ink=GREEN, bright=1)
    # The power cell on its pedestal.
    p.clear(184, 40, 215, 71)
    p.poly([(186, 71), (213, 71), (209, 58), (190, 58)], 5)
    p.outline([(186, 71), (213, 71), (209, 58), (190, 58)])
    hexagon = [(193, 44), (206, 44), (211, 50), (206, 56), (193, 56), (188, 50)]
    p.poly(hexagon, 12)
    p.outline(hexagon)
    p.colour(184, 40, 215, 56, ink=YELLOW, bright=1)
    p.colour(184, 57, 215, 71, ink=WHITE)
    if creature:
        x0, y0 = 72, 41
        body = set()
        for j, row in enumerate(CREATURE):
            for i, ch in enumerate(row):
                if ch != ".":
                    for dy in range(2):
                        for dx in range(2):
                            body.add((x0 + i * 2 + dx, y0 + j * 2 + dy, ch))
        for x, y, ch in body:                       # a black outline around it
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    p.set(x + dx, y + dy, 0)
        for x, y, ch in body:
            p.set(x, y, 0 if ch in "WR" else 1)
        for x, y, ch in body:
            if ch == "R" and (x + y) % 2:
                p.set(x, y, 1)                      # glinting eyes
        p.colour(x0, y0, x0 + 59, y0 + 37, ink=RED, bright=1)
    return p


# 9 · Sala de control
def control_room(powered=False):
    back = (64, 14, 191, 50)
    p = Pic(MAGENTA)
    room(p, back, ceil=1, wall=2, rear=0, seams=(0.5,), grid=False)
    p.poly([(64, 50), (191, 50), (255, 79), (0, 79)], lambda x, y: 1 + (y - 50) // 8)
    # The big screen.
    p.clear(72, 16, 183, 44)
    p.box(72, 16, 183, 44)
    p.box(74, 18, 181, 42)
    if powered:
        rnd = random.Random(3)
        for row in range(3):
            for col in range(12):
                x, y = 80 + col * 8, 21 + row * 7
                for _ in range(5):
                    p.set(x + rnd.randint(0, 4), y + rnd.randint(0, 4))
                p.line(x, y + 5, x + 4, y + 5)
        p.colour(72, 16, 183, 44, ink=GREEN, bright=1)
    # The door to the sanctuary, on the right wall.
    q = wall_quad((64, 14, 191, 50), 1, 0.35, 0.7, 0.15, 1.0)
    p.poly(q, 0 if powered else 3)
    p.outline(q)
    if powered:
        xs = [pt[0] for pt in q]
        p.colour(min(xs), 16, max(xs), 63, ink=GREEN, bright=1)
    # The curved console in front, with the hexagonal slot.
    desk = [(16, 79), (40, 60), (216, 60), (240, 79)]
    p.poly(desk, 0)
    p.poly([(40, 60), (216, 60), (224, 66), (32, 66)], 6)
    p.outline(desk)
    p.line(32, 66, 224, 66)
    for x in range(48, 210, 16):
        p.ellipse(x, 63, 3, 1, True)
    hexagon = [(120, 70), (135, 70), (140, 74), (135, 78), (120, 78), (115, 74)]
    p.poly(hexagon, 16 if powered else 0)
    p.outline(hexagon)
    if powered:
        p.colour(112, 68, 143, 79, ink=YELLOW, bright=1)
    return p


# 10 · Santuario
def sanctuary(artifact=True):
    p = Pic(GREEN)
    # A round chamber: curved back wall with niches.
    p.ellipse(128, 79, 150, 66, 2)
    p.oval(128, 79, 150, 66)
    p.ellipse(128, 79, 120, 52, 0)
    p.oval(128, 79, 120, 52)
    for a in range(200, 341, 20):
        r = math.radians(a)
        x, y = 128 + 135 * math.cos(r), 79 + 59 * math.sin(r)
        p.ellipse(x, y + 4, 6, 8, 0)
        p.oval(x, y + 4, 6, 8)
    # Steps and the pedestal.
    for k, (w, y) in enumerate(((70, 74), (56, 69), (42, 64))):
        p.rect(128 - w, y, 128 + w, y + 4, 0)
        p.box(128 - w, y, 128 + w, y + 4)
        p.rect(128 - w + 1, y + 1, 128 + w - 1, y + 3, 4 + k * 2)
    p.poly([(112, 64), (144, 64), (138, 56), (118, 56)], 8)
    p.outline([(112, 64), (144, 64), (138, 56), (118, 56)])
    p.colour(56, 56, 199, 79, ink=MAGENTA, bright=1)
    # Columns.
    for x in (8, 224):
        p.clear(x - 2, 8, x + 25, 79)
        p.rect(x, 12, x + 23, 79, 3)
        p.box(x, 12, x + 23, 79)
        for y in range(18, 76, 9):
            p.oval(x + 12, y, 7, 3)
        p.rect(x - 2, 8, x + 25, 12, True)
    if artifact:
        crystal = [(128, 18), (140, 34), (128, 52), (116, 34)]
        p.clear(100, 12, 155, 55)
        for a in range(0, 360, 20):
            r = math.radians(a)
            p.dotted(128 + 16 * math.cos(r), 34 + 12 * math.sin(r), 128 + 26 * math.cos(r), 34 + 20 * math.sin(r), 2)
        p.poly(crystal, 10)
        p.outline(crystal)
        p.line(128, 18, 128, 52)
        p.line(116, 34, 140, 34)
        p.colour(104, 16, 151, 55, ink=CYAN, bright=1)
        p.colour(120, 24, 135, 39, ink=WHITE, bright=1)
    else:
        p.ellipse(128, 50, 10, 3, 2)
    return p


LOCATIONS = {11: cabin, 12: main_area, 13: airlock, 14: hold, 15: engine_room,
             16: corridor, 17: gallery, 18: nursery, 19: control_room, 20: sanctuary}
VARIANTS = {26: lambda: corridor(open_door=True), 27: gallery_dark, 28: lambda: nursery(creature=False),
            29: lambda: control_room(powered=True), 30: lambda: sanctuary(artifact=False)}


# --- New icons (24x24, character row 3 of 002.scr) -------------------------------

ICONS = {
    # The capsule's console.
    0: (["........................",
         "..CCCCCCCCCCCCCCCCCCCC..",
         "..C..................C..",
         "..C.GGGGGGGGGGGGGGGG.C..",
         "..C.G..............G.C..",
         "..C.G.GGG..GGGG.GG.G.C..",
         "..C.G..............G.C..",
         "..C.GGGGGGGGGGGGGGGG.C..",
         "..C..................C..",
         "..CCCCCCCCCCCCCCCCCCCC..",
         "........................",
         "CCCCCCCCCCCCCCCCCCCCCCCC",
         "C......................C",
         "C.RR..YY..GG..RR..YY...C",
         "C.RR..YY..GG..RR..YY...C",
         "C......................C",
         "C.CCCC.CCCC.CCCC.CCCC..C",
         "C......................C",
         "CCCCCCCCCCCCCCCCCCCCCCCC",
         "..CC................CC..",
         "..CC................CC..",
         "..CC................CC..",
         ".CCCC..............CCCC.",
         "........................"],
        {"C": CYAN + B, "G": GREEN + B, "R": RED + B, "Y": YELLOW + B}),
    # The sealed iris door.
    1: ([".......MMMMMMMMMM.......",
         ".....MMMMMMMMMMMMMM.....",
         "...MMMM....MM....MMMM...",
         "..MMM.M....MM....M.MMM..",
         ".MMM...M...MM...M...MMM.",
         ".MM.....M..MM..M.....MM.",
         "MMM......M.MM.M......MMM",
         "MM........MMMM........MM",
         "MM.........MM.........MM",
         "MMMMMMMMMMMRRMMMMMMMMMMM",
         "MMMMMMMMMMRRRRMMMMMMMMMM",
         "MM.........RR.........MM",
         "MM........MMMM........MM",
         "MMM......M.MM.M......MMM",
         ".MM.....M..MM..M.....MM.",
         ".MMM...M...MM...M...MMM.",
         "..MMM.M....MM....M.MMM..",
         "...MMMM....MM....MMMM...",
         ".....MMMMMMMMMMMMMM.....",
         ".......MMMMMMMMMM.......",
         "........................",
         "........................",
         "........................",
         "........................"],
        {"M": MAGENTA + B, "R": RED + B}),
    # The creature.
    2: (["........................",
         "........................",
         "........GGGGGGGG........",
         "......GGGGGGGGGGGG......",
         ".....GGRRGGGGGGRRGG.....",
         "....GGRRRRGGGGRRRRGG....",
         "....GGGRRGGGGGGRRGGG....",
         "...GGGGGGGGGGGGGGGGGG...",
         "...GGGWWWWWWWWWWWWGGG...",
         "..GGGGWGWGWGWGWGWGWGGG..",
         "..GGGGGGGGGGGGGGGGGGGG..",
         "..GGGGGGGGGGGGGGGGGGGG..",
         "...GGG.GGG.GGGG.GGG.GG..",
         "...GG..GG...GG...GG..G..",
         "..GG..GG....GG....GG.GG.",
         "..G...G.....G......G..G.",
         ".GG..GG....GG.....GG..GG",
         ".G...G.....G.......G...G",
         "........................",
         "........................",
         "........................",
         "........................",
         "........................",
         "........................"],
        {"G": GREEN + B, "R": RED + B, "W": WHITE + B}),
    # The power cell.
    3: (["........................",
         ".........WWWWWW.........",
         ".........W....W.........",
         ".......YYYYYYYYYY.......",
         "......YYYYYYYYYYYY......",
         ".....YYYY......YYYY.....",
         "....YYYY..YYYY..YYYY....",
         "...YYYY..YYYYYY..YYYY...",
         "..YYYY..YYYYYYYY..YYYY..",
         "..YYYY..YYYYYYYY..YYYY..",
         "..YYYY..YYYYYYYY..YYYY..",
         "..YYYY..YYYYYYYY..YYYY..",
         "...YYYY..YYYYYY..YYYY...",
         "....YYYY..YYYY..YYYY....",
         ".....YYYY......YYYY.....",
         "......YYYYYYYYYYYY......",
         ".......YYYYYYYYYY.......",
         ".........W....W.........",
         ".........WWWWWW.........",
         "........................",
         "........................",
         "........................",
         "........................",
         "........................"],
        {"Y": YELLOW + B, "W": WHITE + B}),
    # The alien console.
    4: (["........................",
         "...MMMMMMMMMMMMMMMMMM...",
         "...M................M...",
         "...M.GGG.GG.GGG.GG..M...",
         "...M................M...",
         "...M.GG.GGG.G.GGGG..M...",
         "...M................M...",
         "...MMMMMMMMMMMMMMMMMM...",
         "........................",
         "..........MMMM..........",
         "........MMMMMMMM........",
         "......MMMMMMMMMMMM......",
         "....MMMMMMMMMMMMMMMM....",
         "..MMMMMMMMM..MMMMMMMMM..",
         ".MMMMMMMM......MMMMMMMM.",
         "MMMMMMMMM......MMMMMMMMM",
         "MMMMMMMMMM....MMMMMMMMMM",
         "MMMMMMMMMMMMMMMMMMMMMMMM",
         "........................",
         "........................",
         "........................",
         "........................",
         "........................",
         "........................"],
        {"M": MAGENTA + B, "G": GREEN + B}),
    # The artifact.
    5: (["...........WW...........",
         "...........CC...........",
         "..........CCCC..........",
         ".........CCCCCC.........",
         "........CCCWCCCC........",
         ".......CCCWCCCCCC.......",
         "......CCCWCCCCCCCC......",
         ".....CCCWCCCCCCCCCC.....",
         "....CCCWCCCCCCCCCCCC....",
         "...CCCWCCCCCCCCCCCCCC...",
         "..WWWWWWWWWWWWWWWWWWWW..",
         "...CCCCCCCCCCCCCCCCCC...",
         "....CCCCCCCCCCCCCCCC....",
         ".....CCCCCCCCCCCCCC.....",
         "......CCCCCCCCCCCC......",
         ".......CCCCCCCCCC.......",
         "........CCCCCCCC........",
         ".........CCCCCC.........",
         "..........CCCC..........",
         "...........CC...........",
         "...........WW...........",
         "........................",
         "........................",
         "........................"],
        {"C": CYAN + B, "W": WHITE + B}),
}


def icons():
    base = (IMAGES / "002.scr").read_bytes()
    cv = Canvas()
    # The canvas only draws rows 1..9; the icons go in rows 3..5.
    for slot, (rows, colours) in ICONS.items():
        cv.art(slot * 24, 24, rows, colours)
    return to_scr(cv, base, rows=range(3, 6))


def main():
    config = []
    for number, scene in {**LOCATIONS, **VARIANTS}.items():
        (IMAGES / f"{number:03d}.scr").write_bytes(pic_to_scr(scene()))
        config.append({"id": number, "num_lines": BOTTOM, "force_mirror": False})
    (IMAGES / "002.scr").write_bytes(icons())
    (IMAGES / "images.json").write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"{len(config)} pictures and the icons written to {IMAGES}")


if __name__ == "__main__":
    main()
