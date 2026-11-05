#!/usr/bin/env python3
"""Builds the documentation site (GitHub Pages) from the manuals and tutorials.

    python tools/build_site.py                  # from this repo's docs
    python tools/build_site.py --source DIR     # from another checkout (a release's)
    python tools/build_site.py --no-build       # only prepare build/site_docs

The manuals and tutorials are canonical in the repo: they are copied, with the
images they show, to build/site_docs, next to a home page, and MkDocs
(mkdocs.yml, tools/site_requirements.txt) makes build/site from them.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS = ["MANUAL_en.md", "MANUAL_es.md", "TUTORIAL_en.md", "TUTORIAL_es.md"]
SITE_DOCS = REPO / "build" / "site_docs"

HOME = """# Choose Your Destiny

<p class="cyd-home-logo"><img src="assets/cydlogo_2.png" alt="Choose Your Destiny"></p>

**Choose Your Destiny** (CYD) is an engine and a compiler for making
"choose your own adventure" games, interactive fiction and gamebooks for the
ZX Spectrum: 48K, 128K, +3, esxDOS (divMMC) and Dandanator.

**Choose Your Destiny** (CYD) es un motor y un compilador para crear juegos de
"elige tu propia aventura", ficción interactiva y librojuegos para el ZX
Spectrum: 48K, 128K, +3, esxDOS (divMMC) y Dandanator.

| English | Español |
|---------|---------|
| [Manual](MANUAL_en.md) | [Manual](MANUAL_es.md) |
| [Tutorial](TUTORIAL_en.md) | [Tutorial](TUTORIAL_es.md) |

- [Download / Descargas](https://github.com/cronomantic/ChooseYourDestiny/releases)
- [Source code / Código fuente](https://github.com/cronomantic/ChooseYourDestiny)
- [Syntax highlighter for VS Code / Resaltador para VS Code](https://github.com/cronomantic/chooseyourdestiny-highlighter)
"""


def images(text):
    """The assets/... images a document shows."""
    return sorted(set(re.findall(r"assets/[A-Za-z0-9_.-]+", text)))


def prepare(source, out=SITE_DOCS):
    """Copies the docs of `source`, their images and the home page to `out`."""
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    wanted = {"assets/cydlogo_2_gui.png", "assets/cydlogo_2.png"}
    for name in DOCS:
        text = (source / name).read_text(encoding="utf-8")
        (out / name).write_text(text, encoding="utf-8")
        wanted.update(images(text))
    (out / "index.md").write_text(HOME, encoding="utf-8")
    (out / "stylesheets").mkdir()
    shutil.copyfile(REPO / "tools" / "site" / "cyd.css", out / "stylesheets" / "cyd.css")
    for rel in sorted(wanted):
        src = source / rel
        if not src.is_file():
            src = REPO / rel  # an older checkout may lack a newer logo
        if src.is_file():
            shutil.copyfile(src, out / rel)
        else:
            print(f"warning: missing image {rel}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=REPO,
                        help="the checkout whose docs to publish (default: this repo)")
    parser.add_argument("--no-build", action="store_true",
                        help="only prepare build/site_docs")
    args = parser.parse_args()
    prepare(args.source.resolve())
    if args.no_build:
        return 0
    return subprocess.run([sys.executable, "-m", "mkdocs", "build", "--clean",
                           "-f", str(REPO / "mkdocs.yml")], cwd=REPO).returncode


if __name__ == "__main__":
    sys.exit(main())
