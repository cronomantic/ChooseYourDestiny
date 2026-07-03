"""Test suite for pyZX0 — guards the optimizer's compatibility contract.

pyZX0 ships two optimizers: the default ``_optimize_fast`` (a faster reimpl) and
``_optimize_legacy`` (the original reference, kept as a fallback). They MUST
produce byte-identical output. This test uses the legacy path as an oracle, so
any future change to the fast path that alters the compressed bytes fails here.

Inputs are kept small: both optimizers are O(n^2), so a few hundred bytes each
keeps the test fast while still exercising literal/match/offset paths.
"""

import sys
import unittest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

import pyZX0.optimize as zx0_optimize
from pyZX0.compress import compress_data

REAL_SCR = Path(__file__).parent.parent / "examples" / "test" / "IMAGES" / "000.scr"

CORPUS = [
    bytes(256),                                          # all zeros (worst case)
    bytes((i * 37) & 0xFF for i in range(256)),          # ramp
    b"ABCD" * 64,                                         # highly repetitive
    bytes((i * i) & 0xFF for i in range(300)),           # pseudo-structured
]
if REAL_SCR.is_file():
    CORPUS.append(REAL_SCR.read_bytes()[:512])           # slice of a real screen


def _compress(data, legacy):
    saved = zx0_optimize.USE_LEGACY_OPTIMIZE
    zx0_optimize.USE_LEGACY_OPTIMIZE = legacy
    try:
        out, _delta = compress_data(data, False, False, False, False)
        return bytes(out)
    finally:
        zx0_optimize.USE_LEGACY_OPTIMIZE = saved


class TestZX0Compatibility(unittest.TestCase):
    def test_fast_is_byte_identical_to_legacy(self):
        for data in CORPUS:
            with self.subTest(size=len(data)):
                self.assertEqual(
                    _compress(data, legacy=False),
                    _compress(data, legacy=True),
                    f"fast optimizer diverged from legacy for input of {len(data)} bytes",
                )

    def test_fast_is_deterministic(self):
        data = bytes((i * 7) & 0xFF for i in range(256))
        self.assertEqual(_compress(data, legacy=False), _compress(data, legacy=False))

    def test_compression_reduces_repetitive_data(self):
        out = _compress(b"ABCD" * 64, legacy=False)
        self.assertGreater(len(out), 0)
        self.assertLess(len(out), 256)


if __name__ == "__main__":
    unittest.main()
