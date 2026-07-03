"""End-to-end build tests: compile a real adventure with resources all the way
to a TAP/DSK using sjasmplus, and check the artifact is produced.

Unlike the rest of the suite (which stops at parse/codegen), these tests exercise
the *whole* pipeline including text compression, image (.scr -> .csc) compression,
track packing, final assembly and container generation. They would have caught
the plus3+tracks crash fixed in the "Corregir 3 bugs" commit.

They require a real sjasmplus binary and are skipped if none is found. The sample
project is copied to a temp dir first so the repository tree is never polluted
with generated ``.csc``/output files.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from shutil import which

REPO = Path(__file__).parent.parent
CYDC = REPO / "src" / "cydc" / "cydc" / "cydc.py"
EXAMPLE = REPO / "examples" / "test"


def _find_sjasmplus():
    local = REPO / "tools" / ("sjasmplus.exe" if os.name == "nt" else "sjasmplus")
    if local.is_file():
        return str(local)
    return which("sjasmplus")


SJASM = _find_sjasmplus()


@unittest.skipUnless(SJASM, "sjasmplus binary not available")
@unittest.skipUnless(EXAMPLE.is_dir(), "examples/test not available")
class TestEndToEndBuild(unittest.TestCase):
    def _build_and_check(self, model, extension, with_tracks=False):
        work = tempfile.mkdtemp(prefix="cyd_e2e_")
        try:
            src = os.path.join(work, "src")
            out = os.path.join(work, "out")
            shutil.copytree(EXAMPLE, src)
            os.makedirs(out)

            args = [sys.executable, str(CYDC), "-img", "IMAGES"]
            if with_tracks:
                args += ["-trk", "TRACKS"]
            args += [model, "test.cyd", SJASM, out]

            proc = subprocess.run(
                args,
                cwd=src,
                capture_output=True,
                text=True,
                timeout=300,
            )
            self.assertEqual(
                proc.returncode,
                0,
                msg=(
                    f"compilation for '{model}' failed (exit {proc.returncode}).\n"
                    f"--- stdout ---\n{proc.stdout[-2000:]}\n"
                    f"--- stderr ---\n{proc.stderr[-2000:]}"
                ),
            )
            # Output is named after the input basename ("test"); match extension
            # case-insensitively (48k/128k -> .tap, plus3 -> .DSK).
            produced = [
                p
                for p in Path(out).iterdir()
                if p.suffix.lower() == extension.lower()
            ]
            self.assertTrue(
                produced, f"no {extension} artifact produced for '{model}' in {out}"
            )
            self.assertGreater(
                produced[0].stat().st_size,
                100,
                f"{produced[0].name} is suspiciously small",
            )
        finally:
            shutil.rmtree(work, ignore_errors=True)

    def test_build_48k_tape(self):
        # Tape path with an image resource.
        self._build_and_check("48k", ".tap")

    def test_build_plus3_with_tracks(self):
        # Regression guard: plus3 + PT3 tracks is the exact path that used to
        # crash with a TypeError right after generating the DSK.
        self._build_and_check("plus3", ".dsk", with_tracks=True)


if __name__ == "__main__":
    unittest.main()
