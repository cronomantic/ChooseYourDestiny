#!/usr/bin/env python3
"""Builds the .tap of every example with the current compiler (src/cydc).

Each example ships its .tap so it can be loaded straight into an emulator as a
demo. Run this after changing the interpreter or an example, and commit the
regenerated tapes:

    python tools/build_example_taps.py            # every example
    python tools/build_example_taps.py sprites    # only the ones named

For each example the source is its test.cyd (or the one in SOURCES) and the
target 48k (or the one in MODELS). IMAGES/, TRACKS/, SFX.asm and tokens.json are
used when the example has them. The tape is written next to the source, with
its name (test.cyd -> test.tap).
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"
CYDC = REPO / "src" / "cydc" / "cydc" / "cydc.py"

# Examples whose source is not test.cyd.
SOURCES = {
    "Delerict": "delerict.cyd",
    "import_demo": "import_demo.cyd",
    "include_demo": "main.cyd",
}
# Examples that need more than 48K (music, several banks of text).
MODELS = {
    "Delerict": "128k",
    "test": "128k",
}


def examples():
    """Every example directory, sorted by name."""
    return sorted(d for d in EXAMPLES.iterdir() if d.is_dir() and not d.name.startswith((".", "_")))


def source(example):
    return example / SOURCES.get(example.name, "test.cyd")


def tape(example):
    return source(example).with_suffix(".tap")


def sjasmplus():
    for name in ("sjasmplus", "sjasmplus.exe"):
        path = REPO / "tools" / name
        if path.is_file():
            return path
    sys.exit("sjasmplus not found under tools/ (see tools/build_emu_tools.sh)")


def build(example, asm):
    src = source(example)
    args = [sys.executable, str(CYDC)]
    for flag, name in (("-img", "IMAGES"), ("-trk", "TRACKS")):
        if (example / name).is_dir():
            args += [flag, name]
    if (example / "SFX.asm").is_file():
        args += ["-sfx", "SFX.asm"]
    if (example / "tokens.json").is_file():
        args += ["-t", "tokens.json"]
    with tempfile.TemporaryDirectory() as out:
        args += [MODELS.get(example.name, "48k"), src.name, str(asm), out]
        r = subprocess.run(args, cwd=example, capture_output=True, text=True)
        # A tape name has 10 characters at most, so the compiler may shorten it.
        built = list(Path(out).glob("*.tap"))
        if r.returncode != 0 or len(built) != 1:
            sys.exit(f"{example.name}: compilation failed\n{r.stdout}{r.stderr}")
        shutil.copyfile(built[0], tape(example))
    # The compiler leaves its compressed images next to the .scr files.
    for csc in (example / "IMAGES").glob("*.[cC][sS][cC]") if (example / "IMAGES").is_dir() else ():
        csc.unlink()


def main(names):
    asm = sjasmplus()
    todo = examples()
    if names:
        unknown = set(names) - {e.name for e in todo}
        if unknown:
            sys.exit(f"unknown examples: {', '.join(sorted(unknown))}")
        todo = [e for e in todo if e.name in names]
    for example in todo:
        print(f"{example.name}: {MODELS.get(example.name, '48k')} -> "
              f"{tape(example).relative_to(REPO).as_posix()}", flush=True)
        build(example, asm)


if __name__ == "__main__":
    main(sys.argv[1:])
