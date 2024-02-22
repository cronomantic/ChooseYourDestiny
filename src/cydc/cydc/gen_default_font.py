
import sys
import os

from cydc_font import CydcFont

font = CydcFont()
chars = font.font_chars
n_chars = int(len(chars)/8)

for c in range(256-n_chars):
    chars += [0 for x in range(8)]

try:
    with open("default_charset.chr", "wb") as f:
        f.write(bytes(chars))
except OSError as err:
    sys.exit(f"{err}")
sys.exit(0)
