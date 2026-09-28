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


PROSE = [
    "En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho "
    "tiempo que vivia un hidalgo de los de lanza en astillero.",
    "Una olla de algo mas vaca que carnero, salpicon las mas noches, duelos y "
    "quebrantos los sabados, lentejas los viernes.",
    "El resto della concluian sayo de velarte, calzas de velludo para las "
    "fiestas, con sus pantuflos de lo mismo.",
] * 4


class TestEncoding(TxtCompressBase):
    def _uses(self, text_bytes):
        uses = {}
        for encoded in text_bytes:
            for b in encoded:
                if b ^ 255 >= 128:
                    uses[(b ^ 255) - 128] = uses.get((b ^ 255) - 128, 0) + 1
        return uses

    def test_tokens_sorted_by_use_and_all_used(self):
        # The Z80 finds token k by walking the k tokens before it.
        text_bytes, _tb, tokens = self._compress(PROSE, 3, 12)
        uses = self._uses(text_bytes)
        counts = [uses.get(i, 0) for i in range(len(tokens))]
        self.assertGreater(len(tokens), 10)
        self.assertEqual(counts, sorted(counts, reverse=True))
        self.assertNotIn(0, counts)

    def test_bytes_saved_message_is_the_real_saving(self):
        c = CydcTextCompressor(gettext, superset_limit=100)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            text_bytes, token_bytes, _ = c.compress(list(PROSE), 3, 12)
        before = sum(len(s) + 1 for s in PROSE)
        after = sum(map(len, text_bytes)) + len(token_bytes)
        self.assertIn(f"{before - after} bytes saved", out.getvalue())

    def test_parallel_and_sequential_agree(self):
        saved = cydc_txt_compress.PARALLEL_MIN_CHARS
        try:
            cydc_txt_compress.PARALLEL_MIN_CHARS = 0
            parallel = self._compress(PROSE, 3, 8)
            cydc_txt_compress.PARALLEL_MIN_CHARS = 10**9
            sequential = self._compress(PROSE, 3, 8)
        finally:
            cydc_txt_compress.PARALLEL_MIN_CHARS = saved
        self.assertEqual(parallel, sequential)

    def test_optimal_parse_beats_replacing_in_order(self):
        # Replacing "ab" first leaves "ab|c|d" (3 codes); "a|bcd" is 2.
        codes = cydc_txt_compress.optimal_parse("abcd", ["ab", "bcd"])
        self.assertEqual(codes, [ord("a"), 129])


if __name__ == "__main__":
    unittest.main()
