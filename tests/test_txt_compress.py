"""Test suite for CydcTextCompressor — the token-based text compressor.

Every adventure's text is packed by this compressor (a DAAD-Reborn-derived
tokenizer). A silent regression here corrupts text in every game, yet it had no
tests. The core guarantee is *losslessness*: decompressing the emitted bytes with
the emitted token table must reproduce the original strings exactly.

Encoding recap (from ``compress``):
- Each output byte is ``char_code ^ 255``.
- A decoded value >= 128 is a token reference (index ``value - 128`` into the
  final token table); < 128 is a literal character.
- Each string is terminated with ``0x0A`` (newline), also XOR-ed.
"""

import contextlib
import gettext
import io
import sys
import unittest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

import cydc_txt_compress
from cydc_txt_compress import CydcTextCompressor, NUM_TOKENS


def decode(byte_list, tokens):
    """Reverse the compressor's encoding back into the original string."""
    out = ""
    for b in byte_list:
        c = b ^ 255
        if c >= 128:
            out += tokens[c - 128]
        else:
            out += chr(c)
    return out


class TxtCompressBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Disable the optional progress bar so tests don't spew to the terminal.
        cls._pbar_saved = cydc_txt_compress.pbarAvailable
        cydc_txt_compress.pbarAvailable = False

    @classmethod
    def tearDownClass(cls):
        cydc_txt_compress.pbarAvailable = cls._pbar_saved

    def _compress(self, strings, min_len=2, max_len=6, final_tokens=None):
        c = CydcTextCompressor(gettext, superset_limit=100, verbose=False)
        # compress() prints progress/summary lines unconditionally; mute them.
        with contextlib.redirect_stdout(io.StringIO()):
            return c.compress(list(strings), min_len, max_len, final_tokens=final_tokens)


class TestLosslessRoundtrip(TxtCompressBase):
    def test_roundtrip_with_repetition(self):
        strings = [
            "HELLO WORLD",
            "HELLO THERE",
            "A WONDERFUL WORLD",
            "THE THREE THIEVES",
        ]
        text_bytes, _token_bytes, tokens = self._compress(strings)
        for original, encoded in zip(strings, text_bytes):
            self.assertEqual(decode(encoded, tokens), original + "\n")

    def test_roundtrip_without_repetition(self):
        # No shared substrings -> few or no tokens, but still lossless.
        strings = ["ABC", "XYZ", "123"]
        text_bytes, _tb, tokens = self._compress(strings)
        for original, encoded in zip(strings, text_bytes):
            self.assertEqual(decode(encoded, tokens), original + "\n")

    def test_roundtrip_single_string(self):
        strings = ["THE QUICK BROWN FOX JUMPS OVER THE LAZY DOG"]
        text_bytes, _tb, tokens = self._compress(strings)
        self.assertEqual(decode(text_bytes[0], tokens), strings[0] + "\n")


class TestEncodingInvariants(TxtCompressBase):
    def test_each_string_terminated_by_newline(self):
        strings = ["ONE", "TWO", "THREE"]
        text_bytes, _tb, _tokens = self._compress(strings)
        for encoded in text_bytes:
            self.assertEqual(encoded[-1] ^ 255, 0x0A)

    def test_all_emitted_bytes_in_range(self):
        strings = ["SOME TEXT WITH SOME REPEATS SOME TEXT"]
        text_bytes, token_bytes, _tokens = self._compress(strings)
        for encoded in text_bytes:
            for b in encoded:
                self.assertTrue(0 <= b <= 255)
        for b in token_bytes:
            self.assertTrue(0 <= b <= 255)

    def test_num_tokens_constant(self):
        self.assertEqual(NUM_TOKENS, 128)


class TestProvidedTokens(TxtCompressBase):
    """The -t import path: reuse a previously computed token table."""

    def test_provided_tokens_are_reused_and_lossless(self):
        strings = ["HELLO WORLD", "HELLO THERE", "WORLD PEACE WORLD"]
        _tb, _tokb, tokens = self._compress(strings)
        # Recompress the same texts forcing the previously found tokens.
        text_bytes2, _tb2, tokens2 = self._compress(strings, final_tokens=tokens)
        self.assertEqual(tokens2, tokens)
        for original, encoded in zip(strings, text_bytes2):
            self.assertEqual(decode(encoded, tokens2), original + "\n")


if __name__ == "__main__":
    unittest.main()
