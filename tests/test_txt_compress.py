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
sys.path.insert(0, str(Path(__file__).parent))

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

    def _compress(self, strings, min_len=2, max_len=6, final_tokens=None, token_format="flat"):
        c = CydcTextCompressor(gettext, superset_limit=100, verbose=False, token_format=token_format)
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


def decode_table(text_bytes, table, nested):
    """Decode like the Z80 does, reading the token table bytes."""
    tokens = []
    pos = 0
    while pos < len(table):
        if nested:  # [number of symbols][symbols]
            n = table[pos]
            tokens.append(table[pos + 1 : pos + 1 + n])
            pos += 1 + n
        else:  # characters, the last one with bit 7 set
            end = pos
            while table[end] < 128:
                end += 1
            tokens.append(table[pos:end] + [table[end] - 128])
            pos = end + 1

    def expand(symbols, depth):
        out = ""
        for s in symbols:
            if s >= 128:
                assert depth < cydc_txt_compress.NESTED_MAX_DEPTH, "too deep for the Z80 stack"
                out += expand(tokens[s - 128], depth + 1)
            else:
                out += chr(s)
        return out

    return [expand([b ^ 255 for b in encoded], 0) for encoded in text_bytes]


class TestNestedTokens(TxtCompressBase):
    def _run(self, strings, token_format, final_tokens=None):
        c = CydcTextCompressor(gettext, superset_limit=100, token_format=token_format)
        with contextlib.redirect_stdout(io.StringIO()):
            result = c.compress(list(strings), 3, 12, final_tokens=final_tokens)
        return c.nested, result

    def test_nested_roundtrip_through_the_table(self):
        nested, (text_bytes, table, tokens) = self._run(PROSE, "nested")
        self.assertTrue(nested)
        self.assertTrue(cydc_txt_compress.is_nested(tokens))
        self.assertLessEqual(cydc_txt_compress.token_depth(tokens), cydc_txt_compress.NESTED_MAX_DEPTH)
        self.assertEqual(decode_table(text_bytes, table, True), [s + "\n" for s in PROSE])

    def test_auto_keeps_the_smaller_format(self):
        sizes = {}
        for fmt in ("flat", "nested"):
            _, (text_bytes, table, _) = self._run(PROSE, fmt)
            sizes[fmt] = sum(map(len, text_bytes)) + len(table)
        nested, (text_bytes, table, _) = self._run(PROSE, "auto")
        self.assertEqual(sum(map(len, text_bytes)) + len(table), min(sizes.values()))
        self.assertEqual(nested, sizes["nested"] < sizes["flat"])
        self.assertEqual(decode_table(text_bytes, table, nested), [s + "\n" for s in PROSE])

    def test_auto_stays_flat_when_nesting_gains_nothing(self):
        strings = ["abc abc", "xyz"]
        nested, (text_bytes, table, _) = self._run(strings, "auto")
        self.assertFalse(nested)
        self.assertEqual(decode_table(text_bytes, table, False), [s + "\n" for s in strings])

    def test_imported_nested_tokens_are_used_as_given(self):
        tokens = ["la ", chr(128) + "casa "]
        nested, (text_bytes, table, out) = self._run(["la casa la"], "auto", tokens)
        self.assertTrue(nested)
        self.assertEqual(out, tokens)
        self.assertEqual(table, [3, ord("l"), ord("a"), 32, 6, 128] + [ord(c) for c in "casa "])
        self.assertEqual(decode_table(text_bytes, table, True), ["la casa la\n"])

    def test_invalid_imported_nested_tokens_are_rejected(self):
        for bad in ([chr(128 + 5) + "a"],           # no such token
                    [chr(128) + "x"],                 # references itself
                    [chr(129) + "a", chr(128) + "b"],  # cycle
                    ["a", chr(128) + "b", chr(129) + "c", chr(130) + "d"],  # depth 4
                    ["ab", ""],                       # empty entry (flat)
                    [chr(129) + "a", ""],             # empty entry (nested)
                    ["x", chr(128) * 256]):           # longer than the length byte
            with self.assertRaises(ValueError):
                self._run(["abcd"], "auto", bad)


@unittest.skipUnless(
    __import__("emu_harness").find_sjasmplus() if (Path(__file__).parent / "emu_harness.py").exists() else None,
    "sjasmplus not available",
)
class TestNestedDecoderSize(unittest.TestCase):
    """NESTED_DECODER_EXTRA_BYTES must be what the assembled decoders differ by,
    or auto would pick the nested format when it isn't really smaller."""

    def _decoder_size(self, token_format):
        import re
        import tempfile
        import emu_harness
        with tempfile.TemporaryDirectory() as wd:
            emu_harness.compile_cyd("Hola hola hola\n", "48k", wd,
                                    extra_args=["--token-format", token_format])
            syms = {}
            for line in (Path(wd) / "cyd.sym").read_text().splitlines():
                m = re.match(r"([A-Za-z_][A-Za-z0-9_]*):?\s+EQU\s+0x([0-9A-F]+)", line)
                if m:
                    syms[m.group(1)] = int(m.group(2), 16)
        # PRINT_TOKEN_STR up to the routine that follows the decoder(s).
        return syms["PRINT_A_BYTE"] - syms["PRINT_TOKEN_STR"]

    def test_constant_matches_the_assembled_code(self):
        extra = self._decoder_size("nested") - self._decoder_size("flat")
        self.assertEqual(extra, cydc_txt_compress.NESTED_DECODER_EXTRA_BYTES)


if __name__ == "__main__":
    unittest.main()
