"""Checks for the compiler's gettext translations (domain ``cydc``).

gettext looks messages up by their exact text, so ``_(f"... {x}")`` never
matches the catalog: the f-string is formatted before the lookup. Messages
must be written as ``_("... {x}").format(x=x)``, and since the translated
string is formatted afterwards, every translation must keep the same
placeholders as its msgid or the compiler raises KeyError in that language.
"""

import ast
import gettext
import string
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).parent.parent
CYDC = REPO / "src" / "cydc" / "cydc"
LOCALE = CYDC / "locale"
PO = LOCALE / "es" / "LC_MESSAGES" / "cydc.po"

sys.path.insert(0, str(CYDC))

from cydc_parser import CydcParser


def _gettext_calls(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and node.args:
            func = node.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if name == "_":
                yield node


def _po_entries(path):
    """(msgid, msgstr) pairs of a .po file, header excluded."""
    entries, current, key = [], {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("msgid "):
            if current:
                entries.append(current)
            current, key = {"msgid": ast.literal_eval(line[6:])}, "msgid"
        elif line.startswith("msgstr "):
            current["msgstr"], key = ast.literal_eval(line[7:]), "msgstr"
        elif line.startswith('"') and key:
            current[key] += ast.literal_eval(line)
    if current:
        entries.append(current)
    return [(e["msgid"], e.get("msgstr", "")) for e in entries if e["msgid"]]


def _fields(s):
    return sorted({f for _, f, _, _ in string.Formatter().parse(s) if f is not None})


class TestTranslatableMessages(unittest.TestCase):
    def test_no_fstring_passed_to_gettext(self):
        offenders = []
        for path in sorted(CYDC.glob("*.py")):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for call in _gettext_calls(tree):
                if isinstance(call.args[0], ast.JoinedStr):
                    offenders.append(f"{path.name}:{call.lineno}")
        self.assertEqual(offenders, [], "use _(\"... {x}\").format(x=x) instead")

    def test_spanish_placeholders_match_msgid(self):
        mismatches = [
            (msgid, msgstr)
            for msgid, msgstr in _po_entries(PO)
            if msgstr and _fields(msgid) != _fields(msgstr)
        ]
        self.assertEqual(mismatches, [])


class TestSpanishParserErrors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        translation = gettext.translation("cydc", str(LOCALE), languages=["es"])
        cls.parser = CydcParser(translation)
        cls.parser.build()

    def test_error_is_translated_and_formatted(self):
        self.parser.parse(input="[[ GOTO nowhere ]]")
        self.assertEqual(
            self.parser.errors, ["La etiqueta 'nowhere' en línea 1 no está declarada."]
        )


if __name__ == "__main__":
    unittest.main()
