"""The opcode numbers agree everywhere they are written.

- The compiler's ``CydcCodegen.opcodes`` is the source of truth.
- ``OPCODES`` in interpreter.asm must have each handler at its number, guarded
  by ``UNUSED_OP_<name>`` with exactly the compiler's name: with a different
  name -trim either never removes the handler, or drops the entry and shifts
  every opcode after it (as MIN/MAX did: a program using only one of them did
  not build with -trim).
- The opcode table of doc/dev/VM.md must list the same codes and names, so the
  document can't go stale when an opcode changes.
"""

import gettext
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src" / "cydc" / "cydc"))

from cydc_codegen import CydcCodegen  # noqa: E402

INTERPRETER = REPO / "src" / "cydc" / "cydc" / "cyd" / "interpreter.asm"
VM_DOC = REPO / "doc" / "dev" / "VM.md"

# The opcodes -trim never removes (get_unused_opcodes leaves them out).
ALWAYS = {"END", "TEXT", "GOTO", "GOSUB", "RETURN", "IF_GOTO", "IF_N_GOTO"}


def jump_table():
    """[(handler label, guard name or None)] of the 128 OPCODES entries."""
    lines = [l.split(";")[0].strip() for l in INTERPRETER.read_text(encoding="utf-8").splitlines()]
    i = lines.index("OPCODES:") + 1
    entries = []
    while len(entries) < 128:
        line = lines[i]
        m = re.fullmatch(r"IFNDEF (UNUSED_OP_\w+)", line)
        if m:
            guard = m.group(1)
            block = [l for l in lines[i:i + 6]]
            expected = [f"IFNDEF {guard}", None, "ENDIF", f"IFDEF {guard}", "DW ERROR_NOP", "ENDIF"]
            for got, want in zip(block, expected):
                if want is not None and got != want:
                    raise AssertionError(f"entry {len(entries):#04x}: {got!r}, expected {want!r}")
            entries.append((block[1].split()[1], guard))
            i += 6
        elif line.startswith("DW "):
            entries.append((line.split()[1], None))
            i += 1
        elif not line:
            i += 1
        else:
            raise AssertionError(f"unexpected line in OPCODES: {line!r}")
    return entries


def doc_table():
    """[(code, name)] of the rows between the OPCODES markers of VM.md."""
    text = VM_DOC.read_text(encoding="utf-8")
    body = text[text.index("<!-- OPCODES:BEGIN -->"):text.index("<!-- OPCODES:END -->")]
    return [(int(code, 16), name)
            for code, name in re.findall(r"^\| `(0x[0-9A-F]{2})` \| `(\w+)` \|", body, re.M)]


class TestOpcodeNumbers(unittest.TestCase):
    def setUp(self):
        self.opcodes = CydcCodegen(gettext.NullTranslations()).opcodes
        self.by_number = {v: k for k, v in self.opcodes.items()}

    def test_numbers_are_unique_and_fill_the_table(self):
        self.assertEqual(sorted(self.opcodes.values()), list(range(128)))

    def test_jump_table_matches_the_compiler(self):
        for number, (label, guard) in enumerate(jump_table()):
            name = self.by_number[number]
            with self.subTest(f"{number:#04x} {name}"):
                self.assertEqual(label, f"OP_{name}")
                if name in ALWAYS:
                    self.assertIsNone(guard)
                else:
                    self.assertEqual(guard, f"UNUSED_OP_{name}")

    def test_handler_guards_name_real_opcodes(self):
        # A guard with a name the compiler never defines keeps the handler forever.
        text = INTERPRETER.read_text(encoding="utf-8")
        unknown = sorted({n for n in re.findall(r"UNUSED_OP_(\w+)", text) if n not in self.opcodes})
        self.assertEqual(unknown, [])

    def test_vm_doc_lists_every_opcode(self):
        expected = sorted((v, k) for k, v in self.opcodes.items())
        self.assertEqual(doc_table(), expected)


if __name__ == "__main__":
    unittest.main()
