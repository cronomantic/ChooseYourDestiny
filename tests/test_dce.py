"""Unit tests for the dead-code elimination pass (CydcCodegen).

These are deterministic and need no emulator: they exercise the reachability
analysis directly on hand-built opcode streams, covering the cases that make the
pass safe — in particular that a label reached only by sequential fall-through
(with no GOTO to it) is kept, and that terminators stop the fall-through.
"""

import gettext
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "cydc", "cydc"))
from cydc_codegen import CydcCodegen  # noqa: E402


def _labels(code):
    return [t[1] for t in code if t and t[0] == "LABEL"]


def _arrays(code):
    return [t[1] for t in code if t and t[0] == "ARRAY"]


class TestDeadCodeElimination(unittest.TestCase):
    def setUp(self):
        self.g = CydcCodegen(gettext)

    def dce(self, code):
        return self.g.dead_code_elimination(code)

    def test_fallthrough_label_is_kept(self):
        # A label with NO goto to it, reached only by sequential fall-through,
        # must survive (execution falls into it).
        code = [("SET_D", 5, 0), ("LABEL", "here"), ("SET_D", 6, 1), ("END",)]
        out = self.dce(code)
        self.assertIn("here", _labels(out))
        self.assertIn(("SET_D", 6, 1), out)

    def test_uncalled_routine_is_removed(self):
        code = [
            ("GOSUB", "used", 0, 0),
            ("END",),
            ("LABEL", "used"),
            ("RETURN",),
            ("LABEL", "dead"),
            ("SET_D", 9, 0),
            ("RETURN",),
        ]
        out = self.dce(code)
        self.assertIn("used", _labels(out))
        self.assertNotIn("dead", _labels(out))
        self.assertNotIn(("SET_D", 9, 0), out)

    def test_transitive_helper_is_kept(self):
        # 'a' is called and calls 'b'; 'b' must survive, 'c' (never called) must not.
        code = [
            ("GOSUB", "a", 0, 0),
            ("END",),
            ("LABEL", "a"),
            ("GOSUB", "b", 0, 0),
            ("RETURN",),
            ("LABEL", "b"),
            ("RETURN",),
            ("LABEL", "c"),
            ("RETURN",),
        ]
        out = _labels(self.dce(code))
        self.assertIn("a", out)
        self.assertIn("b", out)
        self.assertNotIn("c", out)

    def test_goto_stops_fallthrough(self):
        # Code right after an unconditional GOTO is unreachable unless jumped to.
        code = [
            ("GOTO", "end", 0, 0),
            ("SET_D", 1, 0),
            ("LABEL", "end"),
            ("END",),
        ]
        out = self.dce(code)
        self.assertNotIn(("SET_D", 1, 0), out)
        self.assertIn("end", _labels(out))

    def test_return_and_end_stop_fallthrough(self):
        code = [
            ("GOSUB", "r", 0, 0),
            ("END",),
            ("SET_D", 7, 0),   # after END: unreachable
            ("LABEL", "r"),
            ("RETURN",),
            ("SET_D", 8, 0),   # after RETURN: unreachable
        ]
        out = self.dce(code)
        self.assertNotIn(("SET_D", 7, 0), out)
        self.assertNotIn(("SET_D", 8, 0), out)
        self.assertIn("r", _labels(out))

    def test_referenced_array_kept_unreferenced_removed(self):
        # An array named by reachable code survives even though its declaration
        # is not reached by control flow; an array only in dead code does not.
        code = [
            ("PUSH_VAL_ARRAY", "arr", 0),
            ("END",),
            ("ARRAY", "arr", [1, 2, 3]),
            ("LABEL", "dead"),
            ("ARRAY", "deadarr", [9]),
            ("RETURN",),
        ]
        out = _arrays(self.dce(code))
        self.assertIn("arr", out)
        self.assertNotIn("deadarr", out)

    def test_result_ends_with_end(self):
        code = [("SET_D", 1, 0)]  # no terminator
        out = self.dce(code)
        self.assertEqual(out[-1][0], "END")

    def test_disabled_by_default(self):
        # The pass only runs when explicitly enabled.
        self.assertFalse(self.g.eliminate_dead_code)


if __name__ == "__main__":
    unittest.main()
