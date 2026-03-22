import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

from pyZX7.compress import compress_data


class TestZX7Compression(unittest.TestCase):
    def test_empty_input_returns_empty(self):
        self.assertEqual(compress_data(b""), b"")

    def test_is_deterministic(self):
        data = bytes((i * 7) & 0xFF for i in range(512))
        out1 = compress_data(data)
        out2 = compress_data(data)
        self.assertEqual(out1, out2)

    def test_repetitive_data_compresses(self):
        data = (b"ABCD" * 128) + (b"1234" * 64)
        out = compress_data(data)
        self.assertGreater(len(out), 0)
        self.assertLess(len(out), len(data))


if __name__ == "__main__":
    unittest.main()
