"""Test suite for CydcCodegen — bytecode generation from parsed CYD code.

The code generator (``cydc_codegen.py``) turns the parser's statement list into
the 1-byte-opcode bytecode executed by the Z80 runtime. It is the most critical
subsystem and was previously untested. These tests drive it through the real
parser (parser -> codegen), lock the opcode/bytecode contract, and verify correct
emission for representative statements.

The parser's LALR table is built once per class (``setUpClass``) and reused
across parses, which is both correct (verified: no state leaks between parses)
and much faster than rebuilding it per test.
"""

import gettext
import sys
import unittest
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

from cydc_parser import CydcParser
from cydc_codegen import CydcCodegen


class CodegenTestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = CydcParser()
        cls.parser.build()

    def _chunks(self, src, offsets=None, sizes=None):
        """Parse ``src`` and generate bytecode; returns the list of banks."""
        code = self.parser.parse(input=src)
        self.assertEqual(
            self.parser.errors, [], f"unexpected parser errors: {self.parser.errors}"
        )
        g = CydcCodegen(gettext)
        g.set_bank_offset_list(offsets or [0xC000])
        g.set_bank_size_list(sizes or [16 * 1024])
        return g.generate_code(code=code)

    def _bytecode(self, src):
        """Return the single bank of a small (single-bank) program."""
        chunks = self._chunks(src)
        self.assertEqual(len(chunks), 1, "expected a single-bank program")
        return chunks[0]


class TestBytecodeEmission(CodegenTestBase):
    """Exact byte output for representative statements."""

    def test_clear(self):
        # CLEAR (0x36) + auto END (0x00)
        self.assertEqual(self._bytecode("[[CLEAR]]"), [0x36, 0x00])

    def test_border_literal(self):
        # BORDER_D (0x1F) 2 + END
        self.assertEqual(self._bytecode("[[BORDER 2]]"), [0x1F, 0x02, 0x00])

    def test_ink_paper_sequence(self):
        # INK_D 7, PAPER_D 0, END
        self.assertEqual(
            self._bytecode("[[INK 7 : PAPER 0]]"), [0x1D, 0x07, 0x1E, 0x00, 0x00]
        )

    def test_waitkey(self):
        self.assertEqual(self._bytecode("[[WAITKEY]]"), [0x2F, 0x00])

    def test_declare_and_set_literal(self):
        # SET_D var#0 = 5, END
        self.assertEqual(
            self._bytecode("[[DECLARE 0 AS x : SET x TO 5]]"), [0x08, 0x00, 0x05, 0x00]
        )


class TestBytecodeInvariants(CodegenTestBase):
    """Structural properties that must always hold."""

    def test_end_is_auto_appended(self):
        # A program without an explicit END still terminates with END (0x00).
        self.assertEqual(self._bytecode("[[CLEAR]]")[-1], 0x00)

    def test_label_goto_emits_goto_opcode(self):
        # The GOTO address depends on memory layout, so assert only that the
        # GOTO opcode (0x02) is emitted and the stream still ends with END.
        bc = self._bytecode("[[LABEL A : GOTO A]]")
        self.assertEqual(bc[0], 0x02)
        self.assertEqual(bc[-1], 0x00)

    def test_output_is_banks_of_bytes(self):
        chunks = self._chunks("[[INK 1 : PAPER 2 : BORDER 3 : WAITKEY]]")
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)
        for bank in chunks:
            self.assertIsInstance(bank, list)
            for b in bank:
                self.assertIsInstance(b, int)
                self.assertGreaterEqual(b, 0)
                self.assertLessEqual(b, 255)

    def test_generation_is_deterministic(self):
        prog = "[[INK 7 : PAPER 0 : WAITKEY]]"
        self.assertEqual(self._bytecode(prog), self._bytecode(prog))


class TestUnusedOpcodes(CodegenTestBase):
    """``get_unused_opcodes`` drives the -trim optimization / conditional handlers."""

    def test_used_excluded_absent_included(self):
        code = self.parser.parse(input="[[CLEAR]]")
        self.assertEqual(self.parser.errors, [])
        g = CydcCodegen(gettext)
        unused = g.get_unused_opcodes(code)
        self.assertIn("BORDER_D", unused)  # not used by this program
        self.assertNotIn("CLEAR", unused)  # used by this program


class TestOpcodeContract(CodegenTestBase):
    """Guard the bytecode ABI.

    The runtime jump table (``interpreter.asm``) is indexed by these exact opcode
    values. An accidental reordering here would silently break the runtime and
    every previously compiled game, so pin the canonical values.
    """

    def test_canonical_opcode_values(self):
        g = CydcCodegen(gettext)
        expected = {
            "END": 0x00,
            "TEXT": 0x01,
            "GOTO": 0x02,
            "GOSUB": 0x03,
            "RETURN": 0x04,
            "SET_D": 0x08,
            "IF_GOTO": 0x0D,
            "INK_D": 0x1D,
            "PAPER_D": 0x1E,
            "BORDER_D": 0x1F,
            "WAITKEY": 0x2F,
            "CLEAR": 0x36,
        }
        for name, val in expected.items():
            self.assertEqual(
                g.opcodes[name], val, f"opcode {name} changed canonical value"
            )


if __name__ == "__main__":
    unittest.main()
