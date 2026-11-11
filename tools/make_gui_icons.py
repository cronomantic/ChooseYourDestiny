#!/usr/bin/env python3
"""Makes the GUI's window icons from the logo, assets/cydlogo_2.png:

- small (16 and 24 px, the title bar): only the red "CYD" letters, on black,
  as the whole logo cannot be read at that size;
- large (32 px and up: the taskbar, Alt+Tab): the whole logo.

They are written as assets/cyd_icon_<size>.png, for Tk's iconphoto (Linux,
macOS), and together as assets/cyd_icon.ico for Windows: there Tk makes the
small icon out of a large image whatever images it gets, so the GUI asks
Windows for each size of the .ico itself. Needs Pillow (an authoring tool, not
a dependency of CYD):

    python tools/make_gui_icons.py
"""

from pathlib import Path

from PIL import Image

ASSETS = Path(__file__).resolve().parent.parent / "assets"
LOGO = ASSETS / "cydlogo_2.png"
SMALL = (16, 24)
LARGE = (32, 48, 64, 128)


def squared(image, background):
    w, h = image.size
    side = max(w, h)
    out = Image.new("RGBA", (side, side), background)
    out.paste(image, ((side - w) // 2, (side - h) // 2), image)
    return out


def red_letters_box(image):
    """The box of the red "CYD" letters of the logo."""
    px = image.load()
    w, h = image.size
    red = [(x, y) for y in range(h) for x in range(w)
           if px[x, y][3] and px[x, y][0] > 120 and px[x, y][1] < 90 and px[x, y][2] < 90]
    xs = [x for x, _y in red]
    ys = [y for _x, y in red]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def main():
    logo = Image.open(LOGO).convert("RGBA")
    x0, y0, x1, y1 = red_letters_box(logo)
    letters = squared(logo.crop((x0 - 3, y0 - 3, x1 + 3, y1 + 3)), (0, 0, 0, 255))
    whole = squared(logo, (0, 0, 0, 0))
    icons = {}
    for sizes, source in ((SMALL, letters), (LARGE + (256,), whole)):
        for size in sizes:
            icons[size] = source.resize((size, size), Image.LANCZOS)
            if size == 256:
                continue  # only in the .ico (Windows' large views)
            path = ASSETS / f"cyd_icon_{size}.png"
            icons[size].save(path, optimize=True)
            print(path.relative_to(ASSETS.parent).as_posix())
    # Each size keeps its own drawing (append_images), not a scaled copy of one.
    sizes = sorted(icons)
    icons[sizes[-1]].save(ASSETS / "cyd_icon.ico", sizes=[(s, s) for s in sizes],
                          append_images=[icons[s] for s in sizes[:-1]])
    print("assets/cyd_icon.ico")


if __name__ == "__main__":
    main()
