"""Every example ships a .tap that loads and runs as a demo.

tools/build_example_taps.py generates them. The static test checks that each
example has its tape and that the tape is for the right model; the emulator one
loads every tape in ZEsarUX and checks that the interpreter is running a few
seconds later, not the ROM after a reset.
"""

import os
import socket
import struct
import subprocess
import sys
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import (  # noqa: E402
    MACHINE_BY_MODEL, _cmd, _pc, _recv_until_prompt, emulator_available, find_zesarux,
)

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
import build_example_taps as bet  # noqa: E402

# Length of the BASIC loader in the first block of the tape.
LOADER_LENGTH = {"48k": 167, "128k": 211}


def tap_blocks(path):
    data, i, blocks = path.read_bytes(), 0, []
    while i < len(data):
        (n,) = struct.unpack_from("<H", data, i)
        blocks.append(data[i + 2:i + 2 + n])
        i += 2 + n
    return blocks


def runs(tap, machine, port, wait=10.0):
    """Load the tape; True if the PC is in the interpreter ($8000+) afterwards."""
    proc = subprocess.Popen(
        [find_zesarux(), "--noconfigfile", "--machine", machine, "--vo", "null", "--ao", "null",
         "--enable-remoteprotocol", "--remoteprotocol-port", str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        s = None
        for _ in range(40):
            try:
                s = socket.create_connection(("127.0.0.1", port), timeout=1.0)
                break
            except OSError:
                time.sleep(0.25)
        if s is None:
            raise RuntimeError("ZRCP port never opened")
        _recv_until_prompt(s, 5.0)
        time.sleep(2.5)
        _cmd(s, f"smartload {tap}", timeout=12.0)
        time.sleep(wait)
        # Several samples: an interrupt may catch the PC in the ROM for a moment.
        pcs = []
        for _ in range(5):
            pcs.append(_pc(s) or 0)
            time.sleep(0.2)
        _cmd(s, "quit", 2.0)
        s.close()
        return any(pc >= 0x8000 for pc in pcs), pcs
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


class TestExampleTaps(unittest.TestCase):
    def test_every_example_has_its_tap(self):
        for example in bet.examples():
            with self.subTest(example.name):
                self.assertTrue(bet.source(example).is_file(), "no source")
                tap = bet.tape(example)
                self.assertTrue(tap.is_file(), f"no {tap.name}: run tools/build_example_taps.py")
                header = tap_blocks(tap)[0]
                self.assertEqual(header[:2], b"\x00\x00", "first block is not a BASIC header")
                model = bet.MODELS.get(example.name, "48k")
                self.assertEqual(struct.unpack_from("<H", header, 12)[0], LOADER_LENGTH[model],
                                 f"not a {model} tape")

    @unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not available under tools/")
    def test_every_tap_runs(self):
        examples = bet.examples()

        def check(job):
            port, example = job
            machine = MACHINE_BY_MODEL[bet.MODELS.get(example.name, "48k")]
            return example.name, runs(bet.tape(example), machine, port)

        with ThreadPoolExecutor(4) as pool:
            results = list(pool.map(check, enumerate(examples, start=10400)))
        for name, (ok, pcs) in results:
            with self.subTest(name):
                self.assertTrue(ok, f"not running the interpreter, PC {[hex(p) for p in pcs]}")


if __name__ == "__main__":
    unittest.main()
