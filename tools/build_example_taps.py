#!/usr/bin/env python3
"""Builds the .tap of every example with the current compiler (src/cydc).

Each example ships its .tap so it can be loaded straight into an emulator as a
demo. Run this after changing the interpreter or an example, and commit the
regenerated tapes:

    python tools/build_example_taps.py            # every example
    python tools/build_example_taps.py sprites    # only the ones named

Each example is a project: its cyd_project.ini says its main .cyd file and its
target, and the build uses the same compiler options make_adventure.py gives
it (images, tracks, effects, loading screen, tokens...). The tape is written
next to the main file, with its name (test.cyd -> test.tap). A missing
tokens.json is not created: the abbreviations are searched for each time.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
EXAMPLES = REPO / "examples"
CYDC = REPO / "src" / "cydc" / "cydc" / "cydc.py"

sys.path.insert(0, str(REPO / "src" / "cydc" / "cydc"))
import cyd_project  # noqa: E402


def examples():
    """Every example directory, sorted by name."""
    return sorted(d for d in EXAMPLES.iterdir() if d.is_dir() and not d.name.startswith((".", "_")))


def project(example):
    return cyd_project.load(str(example))


def source(example):
    return Path(project(example).main_path)


def model(example):
    return project(example).target


def tape(example):
    return source(example).with_suffix(".tap")


def sjasmplus():
    for name in ("sjasmplus", "sjasmplus.exe"):
        path = REPO / "tools" / name
        if path.is_file():
            return path
    sys.exit("sjasmplus not found under tools/ (see tools/build_emu_tools.sh)")


def build(example, asm):
    proj = project(example)
    if not Path(proj.path("tokens")).is_file():
        proj.values["tokens"] = ""  # don't leave a new tokens.json in the example
    args = [sys.executable, str(CYDC)] + cyd_project.compiler_args(proj, proj.target)
    with tempfile.TemporaryDirectory() as out:
        args += [proj.target, proj.main_path, str(asm), out]
        r = subprocess.run(args, cwd=proj.root, capture_output=True, text=True)
        # A tape name has 10 characters at most, so the compiler may shorten it.
        built = list(Path(out).glob("*.tap"))
        if r.returncode != 0 or len(built) != 1:
            sys.exit(f"{example.name}: compilation failed\n{r.stdout}{r.stderr}")
        shutil.copyfile(built[0], tape(example))


def main(names):
    asm = sjasmplus()
    todo = examples()
    if names:
        unknown = set(names) - {e.name for e in todo}
        if unknown:
            sys.exit(f"unknown examples: {', '.join(sorted(unknown))}")
        todo = [e for e in todo if e.name in names]
    for example in todo:
        print(f"{example.name}: {model(example)} -> "
              f"{tape(example).relative_to(REPO).as_posix()}", flush=True)
        build(example, asm)


if __name__ == "__main__":
    main(sys.argv[1:])
