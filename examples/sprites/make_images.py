#!/usr/bin/env python3
"""Generates the two pictures of the sprites example (Spectrum .scr, 6912 bytes).

  IMAGES/000.scr  the scene: night sky, moon, stars and the ground
  IMAGES/001.scr  the sprite sheet: 4 walking frames of a 2x3 character at
                  columns 0, 2, 4, 6 (rows 0-2) and a 2x2 ball at column 8;
                  each mask 3 rows below its sprite (rows 3-5)

The masks are the sprites grown by one pixel, so each sprite gets a thin
outline in the paper colour over whatever it covers.
"""

import random
from pathlib import Path

W, H = 256, 192


def blank():
    return [[0] * W for _ in range(H)]


def to_scr(pix, attrs):
    scr = bytearray(6912)
    for y in range(H):
        for xb in range(32):
            b = 0
            for bit in range(8):
                b = (b << 1) | pix[y][xb * 8 + bit]
            scr[((y & 0xC0) << 5) | ((y & 7) << 8) | ((y & 0x38) << 2) | xb] = b
    for row in range(24):
        for col in range(32):
            scr[6144 + row * 32 + col] = attrs(col, row)
    return scr


def attr(ink, paper, bright=0):
    return (bright << 6) | (paper << 3) | ink


def blit_art(pix, x, y, art):
    for dy, line in enumerate(art):
        for dx, ch in enumerate(line):
            if ch == "#":
                pix[y + dy][x + dx] = 1


def grow(pix, x, y, w, h):
    """The mask of the sprite at (x, y) size w x h: its pixels plus neighbours."""
    out = [[0] * w for _ in range(h)]
    for j in range(h):
        for i in range(w):
            if pix[y + j][x + i]:
                for dj in (-1, 0, 1):
                    for di in (-1, 0, 1):
                        if 0 <= j + dj < h and 0 <= i + di < w:
                            out[j + dj][i + di] = 1
    return out


HEAD_AND_BODY = [
    "......####......",
    ".....######.....",
    ".....#.##.#.....",
    ".....######.....",
    ".....##..##.....",
    "......####......",
    ".......##.......",
    "....########....",
    "...##########...",
    "..###.####.###..",
    "..##..####..##..",
    "..##..####..##..",
    ".....######.....",
    ".....######.....",
    ".....######.....",
    ".....##..##.....",
]
LEGS_APART = [
    "....###..###....",
    "....##....##....",
    "...###....###...",
    "...##......##...",
    "..###......###..",
    "..##........##..",
    ".###........###.",
    ".####......####.",
]
LEGS_TOGETHER = [
    ".....##..##.....",
    ".....##..##.....",
    ".....##..##.....",
    ".....##..##.....",
    ".....##..##.....",
    ".....##..##.....",
    "....###..###....",
    "....####.####...",
]
LEGS_STRIDE = [
    ".....###.##.....",
    ".....##..##.....",
    "....###..##.....",
    "....##...##.....",
    "...###...##.....",
    "...##....###....",
    "..###.....##....",
    "..####....###...",
]
BALL = [
    ".....######.....",
    "...##########...",
    "..############..",
    ".####..########.",
    ".###....#######.",
    "####....########",
    "#####..#########",
    "################",
    "################",
    "################",
    "################",
    ".##############.",
    ".##############.",
    "..############..",
    "...##########...",
    ".....######.....",
]


def scene():
    rnd = random.Random(7)
    pix = blank()
    for _ in range(70):                      # stars in the sky
        pix[rnd.randrange(0, 110)][rnd.randrange(W)] = 1
    cx, cy, r = 212, 26, 12                  # the moon
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r and (x - cx + 5) ** 2 + (y - cy) ** 2 > r * r:
                pix[y][x] = 1
    for x in range(W):                        # the horizon and a textured ground
        pix[144][x] = 1
    for y in range(146, H, 2):
        for x in range((y // 2) % 4, W, 4):
            pix[y][x] = 1
    return to_scr(pix, lambda col, row: attr(6, 1, 1) if row < 18 else attr(0, 4))


def sheet():
    pix = blank()
    frames = [LEGS_APART, LEGS_TOGETHER, LEGS_STRIDE, LEGS_TOGETHER]
    sprites = []
    for n, legs in enumerate(frames):
        blit_art(pix, n * 16, 0, HEAD_AND_BODY + legs)
        sprites.append((n * 16, 0, 16, 24))
    blit_art(pix, 64, 0, BALL)
    sprites.append((64, 0, 16, 16))
    for x, y, w, h in sprites:                # masks, 3 character rows below
        blit_art(pix, x, y + 24, ["".join("#" if b else "." for b in line)
                                  for line in grow(pix, x, y, w, h)])
    return to_scr(pix, lambda col, row: attr(7, 0))


if __name__ == "__main__":
    out = Path(__file__).parent / "IMAGES"
    out.mkdir(exist_ok=True)
    (out / "000.scr").write_bytes(scene())
    (out / "001.scr").write_bytes(sheet())
    print("IMAGES/000.scr and IMAGES/001.scr written")
