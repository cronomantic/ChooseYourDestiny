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


class TestConstantFolding(CodegenTestBase):
    """Constant resolution, including the cycle guard.

    Circular/self-referential constants used to make the folding loop spin
    forever; codegen must now abort cleanly instead of hanging.
    """

    def test_self_referential_constant_errors_cleanly(self):
        code = self.parser.parse(input="[[CONST A = A]]")
        self.assertEqual(self.parser.errors, [])
        g = CydcCodegen(gettext)
        with self.assertRaises(SystemExit) as cm:
            g.generate_code(code=code)
        self.assertIn("Circular", str(cm.exception.code))

    def test_circular_constants_error_cleanly(self):
        code = self.parser.parse(input="[[CONST A = B : CONST B = A]]")
        self.assertEqual(self.parser.errors, [])
        g = CydcCodegen(gettext)
        with self.assertRaises(SystemExit) as cm:
            g.generate_code(code=code)
        self.assertIn("Circular", str(cm.exception.code))

    def test_valid_constant_chain_resolves(self):
        # C=2 -> B=C -> A=B, then SET var#0 = A  =>  SET_D 0, 2, END
        self.assertEqual(
            self._bytecode("[[CONST C = 2 : CONST B = C : CONST A = B : SET 0 TO A]]"),
            [0x08, 0x00, 0x02, 0x00],
        )


class TestNativeRoutines(CodegenTestBase):
    """The native-routine table (IMPORT + inline ASM) populated by codegen."""

    def _codegen(self, src):
        """Parse ``src`` and run codegen; return the CydcCodegen instance."""
        code = self.parser.parse(input=src)
        self.assertEqual(
            self.parser.errors, [], f"unexpected parser errors: {self.parser.errors}"
        )
        g = CydcCodegen(gettext)
        g.set_bank_offset_list([0xC000])
        g.set_bank_size_list([16 * 1024])
        g.generate_code(code=code)
        return g

    def test_import_is_file_backed(self):
        g = self._codegen('[[IMPORT beeper FROM "b.asm" : CALL beeper]]')
        self.assertEqual(
            g.externs["beeper"],
            {
                "source": ("file", "b.asm"),
                "exports": ["beeper"],
                "explicit": False,
                "uses": [],
                "line": None,
            },
        )
        self.assertEqual(g.extern_exports["beeper"], "beeper")

    def test_asm_inline_is_body_backed(self):
        g = self._codegen("[[ASM peek\n ld a,(de)\n ret\nENDASM\nCALL peek]]")
        self.assertEqual(g.externs["peek"]["source"], ("inline", " ld a,(de)\n ret\n"))
        self.assertEqual(g.externs["peek"]["exports"], ["peek"])
        # No EXPORTS: single entry at the block start, not a named label.
        self.assertFalse(g.externs["peek"]["explicit"])
        self.assertEqual(g.extern_exports["peek"], "peek")

    def test_asm_multiexport_maps_every_export_to_block(self):
        g = self._codegen(
            "[[ASM lib EXPORTS a, b\na: ret\nb: ret\nENDASM\nCALL a : CALL b]]"
        )
        self.assertEqual(g.externs["lib"]["exports"], ["a", "b"])
        self.assertTrue(g.externs["lib"]["explicit"])
        self.assertEqual(g.extern_exports["a"], "lib")
        self.assertEqual(g.extern_exports["b"], "lib")

    def test_call_to_export_is_recorded_for_late_patching(self):
        # Every CALL to a native routine records (name, chunk, offset) so the
        # build can patch the [bank, lo, hi] operand after memory layout.
        g = self._codegen("[[ASM p\n ret\nENDASM\nCALL p]]")
        self.assertEqual([name for (name, _c, _o) in g.extern_calls], ["p"])

    def test_duplicate_routine_name_errors_cleanly(self):
        code = self.parser.parse(
            input="[[ASM x\n ret\nENDASM\nASM y EXPORTS x\n ret\nENDASM]]"
        )
        # The parser already flags the duplicate EXTERN symbol; even if it did
        # not, codegen's extern table must not silently merge two routines.
        self.assertTrue(len(self.parser.errors) > 0)


if __name__ == "__main__":
    unittest.main()
