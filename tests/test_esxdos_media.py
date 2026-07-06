"""Runtime verification of the esxdos disk-media paths: savegame, image streaming
and Vortex music streaming.

The existing esxdos coverage (text/DATA) only exercises F1 (resident text + the
``.DAT`` read path). These tests close the gap on the disk code that F1 alone never
touches, by actually running in ZEsarUX (headless, ``--enable-esxdos-handler`` with
the workdir as SD root) and reading engine state back over ZRCP:

* **savegame** — ``SAVE`` writes ``000.SAV`` (F_OPEN create-trunc + F_WRITE) and
  ``LOAD`` reads it back (F_READ); asserted via ``SAVERESULT()`` (0 = OK) and the
  restored FLAGS values.
* **image** — ``PICTURE``/``DISPLAY`` streams ``000.CSC`` from disk, ZX0-decompresses
  it and blits it to the screen; asserted by comparing screen RAM ($4000) to the
  original ``000.scr`` (lossless round-trip).
* **music** — ``TRACK``/``PLAY`` streams ``000.BIN`` (Vortex PT3) into the staging
  bank; asserted via the player state byte ``VTR_STAT`` (loaded+playing bits).

Real assets are reused from ``examples/test/``. Skips if the emulator is absent.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from emu_harness import run_cyd, run_cyd_ex, emulator_available

REPO = Path(__file__).resolve().parent.parent
SCR = REPO / "examples" / "test" / "IMAGES" / "000.scr"   # 6912-byte screen
PT3 = REPO / "examples" / "test" / "TRACKS" / "000.pt3"   # Vortex Tracker module

# Save vars 0..1, read SAVERESULT, corrupt them in RAM, LOAD them back, read
# SAVERESULT again. Results go to high indices so LOAD (range 0..1) can't clobber
# them. End spinning so the interpreter stays live while FLAGS is sampled.
SAVE_PROGRAM = """[[
SET 0 TO 42
SET 1 TO 99
SAVE 0, 0, 2
SET 20 TO SAVERESULT()
SET 0 TO 7
SET 1 TO 8
LOAD 0
SET 21 TO SAVERESULT()
LABEL spin
GOTO spin
]]"""

IMAGE_PROGRAM = """[[
PICTURE 0
DISPLAY 1
SET 0 TO 1
LABEL spin
GOTO spin
]]"""

MUSIC_PROGRAM = """[[
TRACK 0
LOOP 1
PLAY 1
SET 0 TO 1
LABEL spin
GOTO spin
]]"""


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
class TestEsxdosMedia(unittest.TestCase):
    def test_savegame(self):
        flags = run_cyd(SAVE_PROGRAM, model="esxdos", n_bytes=32)
        self.assertEqual(flags[20], 0, "SAVERESULT after SAVE should be 0 (OK)")
        self.assertEqual(flags[21], 0, "SAVERESULT after LOAD should be 0 (OK)")
        self.assertEqual(flags[0], 42, "LOAD must restore FLAGS[0]")
        self.assertEqual(flags[1], 99, "LOAD must restore FLAGS[1]")

    def test_image_streaming(self):
        flags, (screen,) = run_cyd_ex(
            IMAGE_PROGRAM, model="esxdos", n_bytes=8,
            images=[str(SCR)], reads=[(0x4000, 6144)],
        )
        self.assertEqual(flags[0], 1, "program did not reach the spin loop")
        expected_pixels = SCR.read_bytes()[:6144]
        self.assertEqual(
            screen, expected_pixels,
            "streamed+decompressed image on screen must match 000.scr pixels",
        )

    def test_music_streaming(self):
        flags, (stat,) = run_cyd_ex(
            MUSIC_PROGRAM, model="esxdos", n_bytes=8,
            tracks=[str(PT3)], reads=[("VTR_START", 10, 1)],
        )
        self.assertEqual(flags[0], 1, "program did not reach the spin loop")
        self.assertEqual(
            stat[0] & 0x06, 0x06,
            "VTR_STAT must have module-loaded (bit1) + playing (bit2) set",
        )


if __name__ == "__main__":
    unittest.main()
