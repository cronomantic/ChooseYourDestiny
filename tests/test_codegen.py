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


class TestMld128ArrayRelocation(CodegenTestBase):
    """mld128 relocates DIM arrays to real RAM banks (writable) via array_bank_map.

    On MLD the array's inline data is read-only flash, so writes are lost. For
    mld128 each array is moved to a 128K RAM bank at $C000+offset: the operand
    becomes [bank, $C000+off] and the boot routine copies flash -> that bank.
    """

    def _relocate(self, src, array_bank_map):
        code = self.parser.parse(input=src)
        self.assertEqual(self.parser.errors, [], f"parser errors: {self.parser.errors}")
        g = CydcCodegen(gettext)
        # MLD addresses bytecode slot-relative (bank_offset_list=[0,0]).
        g.set_bank_offset_list([0, 0])
        g.set_bank_size_list([16 * 1024, 16 * 1024])
        chunks = g.generate_code(code=code, array_bank_map=array_bank_map)
        return g, chunks

    def test_symbol_and_operand_are_banked(self):
        g, chunks = self._relocate(
            "[[DIM t(4)={10,20,30,40}\nLET t(1)=99]]", {"t": (7, 0xC000)}
        )
        # symbol remapped to (bank, $C000+off)
        self.assertEqual(g.symbols["t"], (7, 0xC000))
        # the POP_VAL_ARRAY operand (0x7B) bakes [bank, lo, hi] = [7, $00, $C0]
        bc = chunks[0]
        i = bc.index(0x7B)
        self.assertEqual(bc[i + 1 : i + 4], [7, 0x00, 0xC0])

    def test_arr_init_table_entry(self):
        g, _c = self._relocate("[[DIM t(4)={10,20,30,40}]]", {"t": (3, 0xC100)})
        self.assertEqual(len(g.arr_init_table), 1)
        name, chunk, src_off, dest_bank, dest_addr, nbytes = g.arr_init_table[0]
        self.assertEqual(name, "t")
        self.assertEqual((dest_bank, dest_addr), (3, 0xC100))
        self.assertEqual(nbytes, 5)  # [len-1] byte + 4 data bytes

    def test_build_arrays_inc_uses_real_bank(self):
        # The native-routine ABI (ARR_<n>/_BANK) must report the array's REAL
        # relocated bank, not spectrum_banks[bank]. Element 0 is dest_addr+1.
        from cyd import build_arrays_inc

        g, _c = self._relocate("[[DIM t(4)={10,20,30,40}]]", {"t": (7, 0xC100)})
        inc = build_arrays_inc(g, [0, 1, 3, 4])  # spectrum_banks WITHOUT bank 7
        self.assertIn("ARR_t_BANK EQU $07", inc)
        self.assertIn("ARR_t EQU $C101", inc)
        self.assertIn("ARR_t_LEN EQU 4", inc)

    def test_no_map_keeps_arrays_in_place(self):
        # Without array_bank_map (and without resident relocation) arrays stay put.
        code = self.parser.parse(input="[[DIM t(4)={10,20,30,40}\nLET t(1)=99]]")
        g = CydcCodegen(gettext)
        g.set_bank_offset_list([0, 0])
        g.set_bank_size_list([16 * 1024, 16 * 1024])
        g.generate_code(code=code)
        self.assertEqual(g.arr_init_table, [])
        # symbol keeps its logical (bank, offset), not a $Cxxx banked address
        self.assertNotEqual(g.symbols["t"][1] & 0xC000, 0xC000)


class TestMld128ArrayBankPlanner(unittest.TestCase):
    """plan_mld128_array_banks: bin-pack arrays into dedicated RAM banks."""

    @classmethod
    def setUpClass(cls):
        import gettext as _gt

        _gt.install("cydc")  # make _() available for the planner's error paths
        import cydc

        cls.plan = staticmethod(cydc.plan_mld128_array_banks)
        cls.RAM = [0, 1, 3, 4, 6, 7]

    def test_single_array_top_bank(self):
        m, banks = self.plan({"x": 4}, self.RAM)
        self.assertEqual(m, {"x": (7, 0xC000)})
        self.assertEqual(banks, [7])

    def test_packs_multiple_in_one_bank(self):
        m, banks = self.plan({"a": 250, "b": 250, "c": 100}, self.RAM)
        self.assertEqual(banks, [7])  # 251+251+101 fits in one 16K bank
        # packed at increasing offsets, largest first
        self.assertEqual(m["a"][0], 7)
        self.assertEqual({v[0] for v in m.values()}, {7})

    def test_spills_to_second_bank(self):
        al = {f"a{i}": 250 for i in range(70)}  # 70*251 = 17570 > 16384
        m, banks = self.plan(al, self.RAM)
        self.assertEqual(banks, [7, 6])
        self.assertEqual(len(m), 70)

    def test_never_uses_bank_zero(self):
        al = {f"a{i}": 250 for i in range(70)}
        _m, banks = self.plan(al, self.RAM)
        self.assertNotIn(0, banks)

    def test_overflow_errors(self):
        al = {f"a{i}": 250 for i in range(400)}  # far more than the pool holds
        with self.assertRaises(SystemExit):
            self.plan(al, self.RAM)


class TestImmutableData(CodegenTestBase):
    """DATA / READ / RESTORE / DATAEND: the immutable-data stream.

    The compiler concatenates every DATA statement into one read-only blob
    (self.data_blob), strips them from the executable stream, and bakes RESTORE
    labels into blob offsets. Verified end-to-end on 48k in the emulator; these
    tests lock the compile-time contract.
    """

    def _gen(self, src):
        code = self.parser.parse(input=src)
        self.assertEqual(self.parser.errors, [], f"parser errors: {self.parser.errors}")
        g = CydcCodegen(gettext)
        g.set_bank_offset_list([0xC000])
        g.set_bank_size_list([16 * 1024])
        chunks = g.generate_code(code=code)
        return g, chunks

    def test_blob_concatenates_in_source_order(self):
        g, _ = self._gen("[[DATA 11, 22, 33 : DATA 44, 55]]")
        self.assertEqual(g.data_blob, [11, 22, 33, 44, 55])
        self.assertEqual(g.data_len, 5)

    def test_data_is_stripped_from_bytecode(self):
        # DATA is not executable: the bytecode is just END (0x00).
        g, chunks = self._gen("[[DATA 1, 2, 3]]")
        self.assertEqual(chunks[0], [0x00])

    def test_read_direct_emits_read_then_pop_set(self):
        g, chunks = self._gen("[[DATA 1 : READ 4]]")
        self.assertEqual(
            chunks[0], [g.opcodes["READ"], g.opcodes["POP_SET"], 0x04, 0x00]
        )

    def test_read_indirect_emits_read_then_pop_set_di(self):
        # Newline (not ':') before ']]' so the ']' of [4] is not eaten by ']]'.
        g, chunks = self._gen("[[\nDATA 1\nREAD [4]\n]]")
        self.assertEqual(
            chunks[0], [g.opcodes["READ"], g.opcodes["POP_SET_DI"], 0x04, 0x00]
        )

    def test_restore_bare_is_offset_zero(self):
        g, chunks = self._gen("[[DATA 1, 2 : RESTORE]]")
        self.assertEqual(chunks[0], [g.opcodes["RESTORE"], 0x00, 0x00, 0x00])

    def test_restore_label_bakes_offset_of_next_data(self):
        # 'second' sits between the two DATA blocks -> offset of the first byte of
        # the second block (index 3).
        g, chunks = self._gen(
            "[[DATA 11, 22, 33 : LABEL second : DATA 44, 55 : RESTORE second]]"
        )
        self.assertEqual(g.data_blob, [11, 22, 33, 44, 55])
        self.assertEqual(chunks[0], [g.opcodes["RESTORE"], 0x03, 0x00, 0x00])

    def test_restore_label_survives_code_between_label_and_data(self):
        # Intervening code does not affect the blob offset (BASIC RESTORE-line).
        g, chunks = self._gen(
            "[[DATA 1, 2, 3 : LABEL foo : SET 3 TO 5 : DATA 100 : RESTORE foo]]"
        )
        self.assertEqual(g.data_blob, [1, 2, 3, 100])
        self.assertIn(g.opcodes["RESTORE"], chunks[0])
        i = chunks[0].index(g.opcodes["RESTORE"])
        off = chunks[0][i + 1] | (chunks[0][i + 2] << 8)
        self.assertEqual(off, 3)

    def test_dataend_emits_opcode(self):
        g, chunks = self._gen("[[DATA 1 : SET 2 TO DATAEND()]]")
        self.assertIn(g.opcodes["DATAEND"], chunks[0])

    def test_restore_to_label_with_no_following_data_errors(self):
        code = self.parser.parse(
            input="[[DATA 1 : RESTORE tail : LABEL tail]]"
        )
        self.assertEqual(self.parser.errors, [])
        g = CydcCodegen(gettext)
        with self.assertRaises(SystemExit) as cm:
            g.generate_code(code=code)
        self.assertIn("tail", str(cm.exception.code))

    def test_blob_over_16k_errors(self):
        values = ", ".join(["1"] * (16 * 1024 + 1))
        code = self.parser.parse(input=f"[[DATA {values}]]")
        self.assertEqual(self.parser.errors, [])
        g = CydcCodegen(gettext)
        with self.assertRaises(SystemExit) as cm:
            g.generate_code(code=code)
        self.assertIn("too big", str(cm.exception.code))

    def test_opcodes_trimmed_when_no_data_used(self):
        code = self.parser.parse(input="[[CLEAR]]")
        self.assertEqual(self.parser.errors, [])
        g = CydcCodegen(gettext)
        unused = g.get_unused_opcodes(code)
        self.assertIn("READ", unused)
        self.assertIn("RESTORE", unused)
        self.assertIn("DATAEND", unused)

    def test_restore_label_only_keeps_restore_opcode(self):
        # A program that uses ONLY "RESTORE label" (marker RESTORE_LABEL) must still
        # keep the RESTORE opcode (it is what the marker compiles to).
        code = self.parser.parse(
            input="[[DATA 1 : LABEL a : DATA 2 : RESTORE a : READ 0]]"
        )
        self.assertEqual(self.parser.errors, [])
        g = CydcCodegen(gettext)
        unused = g.get_unused_opcodes(code)
        self.assertNotIn("RESTORE", unused)
        self.assertNotIn("READ", unused)


class TestForLoop(CodegenTestBase):
    """FOR ... NEXT: a counted loop lowered entirely in the front-end (0 runtime).

    It compiles to existing opcodes with compiler-generated labels: init SET, a
    guard (i<=b for step>0, i>=b for step<0) checked BEFORE the body (BASIC
    semantics, may run 0 times), the body, an increment (ADD/SUB |step|) and a
    jump back. STEP is a compile-time signed literal (default +1)."""

    def _tuples(self, src):
        code = self.parser.parse(input=src)
        self.assertEqual(self.parser.errors, [], f"parser errors: {self.parser.errors}")
        return code

    def _errors(self, src):
        self.parser.parse(input=src)
        return self.parser.errors

    def test_ascending_uses_gt_compare_and_add(self):
        t = self._tuples("[[ DECLARE 0 AS i \n FOR i = 1 TO 3 \n PRINT @i \n NEXT ]]")
        ops = [x[0] for x in t]
        self.assertIn("CP_MT", ops)  # stop-if i > b (both top and pass-limit guards)
        self.assertIn("IF_GOTO", ops)
        self.assertIn("ADD", ops)
        self.assertEqual(ops.count("GOTO"), 1)
        self.assertEqual(ops.count("LABEL"), 2)
        # counter initialised before the loop label
        self.assertEqual(t[1], ("PUSH_D", ("CONSTANT", [("C_VAL", 1)])))
        self.assertEqual(t[2], ("POP_SET", ("VARIABLE", "i", 0)))
        # overflow guard against the compile-time constant 255-step
        self.assertIn(("PUSH_D", ("CONSTANT", [("C_VAL", 254)])), t)

    def test_descending_uses_lt_compare_and_sub(self):
        t = self._tuples(
            "[[ DECLARE 0 AS j \n FOR j = 10 TO 0 STEP -2 \n PRINT @j \n NEXT j ]]"
        )
        ops = [x[0] for x in t]
        self.assertIn("CP_LT", ops)
        self.assertIn("SUB", ops)
        self.assertNotIn("CP_MT", ops)
        self.assertNotIn("ADD", ops)
        self.assertIn(("PUSH_D", ("CONSTANT", [("C_VAL", 2)])), t)  # |step|

    def test_default_step_is_one(self):
        t = self._tuples("[[ DECLARE 0 AS i \n FOR i = 0 TO 5 \n NEXT ]]")
        self.assertIn(("PUSH_D", ("CONSTANT", [("C_VAL", 1)])), t)
        self.assertIn(("ADD",), t)

    def test_variable_limit_is_re_read(self):
        t = self._tuples(
            "[[ DECLARE 0 AS n \n DECLARE 1 AS i \n FOR i = 0 TO @n \n NEXT ]]"
        )
        self.assertIn(("PUSH_I", ("VARIABLE", "n", 0)), t)

    def test_top_guard_is_before_body(self):
        # May run 0 times: the top guard (compare + IF_GOTO end) precedes the body.
        t = self._tuples("[[ DECLARE 0 AS i \n FOR i = 5 TO 0 \n PRINT @i \n NEXT ]]")
        ops = [x[0] for x in t]
        self.assertLess(ops.index("IF_GOTO"), ops.index("POP_PRINT"))

    def test_step_zero_errors(self):
        errs = self._errors("[[ DECLARE 0 AS i \n FOR i = 0 TO 5 STEP 0 \n NEXT ]]")
        self.assertTrue(any("STEP" in e for e in errs), errs)

    def test_step_out_of_range_errors(self):
        errs = self._errors("[[ DECLARE 0 AS i \n FOR i = 0 TO 5 STEP 300 \n NEXT ]]")
        self.assertTrue(any("STEP" in e for e in errs), errs)

    def test_next_variable_mismatch_errors(self):
        errs = self._errors(
            "[[ DECLARE 0 AS i \n DECLARE 1 AS k \n FOR i = 1 TO 3 \n NEXT k ]]"
        )
        self.assertTrue(any("NEXT" in e for e in errs), errs)

    def test_nested_for_uses_distinct_labels(self):
        t = self._tuples(
            "[[ DECLARE 0 AS i \n DECLARE 1 AS j \n"
            " FOR i = 0 TO 2 \n FOR j = 0 TO 2 \n NEXT \n NEXT ]]"
        )
        labels = [x[1] for x in t if x[0] == "LABEL"]
        self.assertEqual(len(labels), 4)
        self.assertEqual(len(labels), len(set(labels)))

    def test_for_opcodes_present_only_from_existing_set(self):
        # FOR adds NO new opcode: it must not introduce a "FOR"/"NEXT" tuple.
        t = self._tuples("[[ DECLARE 0 AS i \n FOR i = 0 TO 3 \n NEXT ]]")
        ops = {x[0] for x in t}
        self.assertNotIn("FOR", ops)
        self.assertNotIn("NEXT", ops)


class TestWideConstants(CodegenTestBase):
    """WORD/DWORD/string constants expanded to little-endian bytes (0 runtime).

    In DATA and DIM init the width auto-detects by magnitude, and WORD/DWORD force
    a wider slot. In LET the width is fixed by the keyword (the slot count must be
    known while lowering). CONST references resolve normally."""

    def _gen(self, src):
        code = self.parser.parse(input=src)
        self.assertEqual(self.parser.errors, [], f"parser errors: {self.parser.errors}")
        g = CydcCodegen(gettext)
        g.set_bank_offset_list([0xC000])
        g.set_bank_size_list([16 * 1024])
        chunks = g.generate_code(code=code)
        return g, chunks

    def _sysexit(self, src):
        code = self.parser.parse(input=src)
        self.assertEqual(self.parser.errors, [])
        g = CydcCodegen(gettext)
        with self.assertRaises(SystemExit) as cm:
            g.generate_code(code=code)
        return str(cm.exception.code)

    def test_data_autodetects_width_by_magnitude(self):
        g, _ = self._gen("[[ DATA 5, 300, 70000 ]]")
        # 5->[5]; 300=0x012C->[44,1]; 70000=0x011170->[112,17,1,0]
        self.assertEqual(g.data_blob, [5, 44, 1, 112, 17, 1, 0])

    def test_data_word_and_dword_force_width(self):
        g, _ = self._gen("[[ DATA WORD 5, DWORD 5 ]]")
        self.assertEqual(g.data_blob, [5, 0, 5, 0, 0, 0])

    def test_data_string_is_glyph_bytes(self):
        g, _ = self._gen('[[ DATA "HI" ]]')
        self.assertEqual(g.data_blob, [ord("H"), ord("I")])

    def test_word_value_overflow_errors(self):
        self.assertIn("16 bits", self._sysexit("[[ DATA WORD 70000 ]]"))

    def test_let_word_overflow_shares_data_message(self):
        # LET WORD and DATA WORD report the same "does not fit in 16 bits" wording.
        msg = self._sysexit("[[ CONST K = 70000 : DECLARE 0 AS s : LET s = WORD K ]]")
        self.assertIn("WORD value 70000 does not fit in 16 bits", msg)

    def test_dim_wide_init_is_byte_plano(self):
        g, _ = self._gen('[[ DIM t() = { WORD 1000, 42, "AB" } ]]')
        self.assertEqual(g.array_lengths["t"], 5)  # 2 + 1 + 2

    def test_dim_declared_size_pads(self):
        g, _ = self._gen("[[ DIM t(8) = { WORD 1000, 42 } ]]")
        self.assertEqual(g.array_lengths["t"], 8)

    def test_dim_wide_too_small_errors(self):
        self.assertIn("too small", self._sysexit("[[ DIM t(2) = { DWORD 1 } ]]"))

    def test_let_word_writes_two_le_bytes(self):
        g, chunks = self._gen("[[ DECLARE 0 AS s : LET s = WORD 1000 ]]")
        sd = g.opcodes["SET_D"]
        # 1000 = 0x03E8 -> low 0xE8=232, high 0x03=3
        self.assertEqual(chunks[0], [sd, 0, 232, sd, 1, 3, 0x00])

    def test_let_dword_writes_four_le_bytes(self):
        g, chunks = self._gen("[[ DECLARE 0 AS d : LET d = DWORD 100000 ]]")
        sd = g.opcodes["SET_D"]
        # 100000 = 0x000186A0 -> A0 86 01 00
        self.assertEqual(
            chunks[0], [sd, 0, 0xA0, sd, 1, 0x86, sd, 2, 0x01, sd, 3, 0x00, 0x00]
        )

    def test_let_string_writes_glyph_bytes(self):
        g, chunks = self._gen('[[ DECLARE 0 AS b : LET b = "HI" ]]')
        sd = g.opcodes["SET_D"]
        self.assertEqual(chunks[0], [sd, 0, ord("H"), sd, 1, ord("I"), 0x00])

    def test_const_reference_inside_word_resolves(self):
        g, chunks = self._gen("[[ CONST K = 1000 : DECLARE 0 AS s : LET s = WORD K ]]")
        sd = g.opcodes["SET_D"]
        self.assertEqual(chunks[0], [sd, 0, 232, sd, 1, 3, 0x00])

    def test_plain_let_stays_one_byte(self):
        # Without a keyword, LET is unchanged (1 byte); no auto-widening in LET.
        g, chunks = self._gen("[[ DECLARE 0 AS x : LET x = 5 ]]")
        sd = g.opcodes["SET_D"]
        self.assertEqual(chunks[0], [sd, 0, 5, 0x00])

    def test_wide_numeric_index_overflow_errors(self):
        # LET 255 = WORD writes indices 255 AND 256; 256 is out of the variable
        # space, so it must error at compile time (not emit an invalid operand).
        self.assertIn("out of bounds", self._sysexit("[[ LET 255 = WORD 65000 ]]"))

    def test_wide_dword_numeric_index_overflow_errors(self):
        self.assertIn("out of bounds", self._sysexit("[[ LET 254 = DWORD 100000 ]]"))

    def test_wide_string_numeric_index_overflow_errors(self):
        self.assertIn("out of bounds", self._sysexit('[[ LET 255 = "AB" ]]'))

    def test_multislot_set_numeric_index_overflow_errors(self):
        # The same displacement bounds check must guard the pre-existing multi-slot
        # SET/LET with a numeric index (SET 255 TO {1,2} targets 255 and 256).
        self.assertIn("out of bounds", self._sysexit("[[ SET 255 TO {1, 2} ]]"))

    def test_wide_indirect_destination_is_rejected(self):
        # Wide constants require a direct destination (the target index of an
        # indirect [..] store is only known at runtime and v+1 could leave the
        # 0..255 space). This must be a clear parser error, not silent code.
        self.parser.parse(input="[[ LET [1] = WORD 56000 ]]")
        self.assertTrue(
            any("direct destination" in e for e in self.parser.errors),
            self.parser.errors,
        )


if __name__ == "__main__":
    unittest.main()
