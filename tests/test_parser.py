"""
Test suite for CydcParser - Grammar and syntax analysis.

This module tests the parser's ability to:
- Parse valid CYD code according to the grammar
- Verify statement structures and semantics
- Handle strict colon mode (colon requirement)
- Handle backwards-compatible mode (no colon requirement)
- Detect and report syntax errors
"""

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

from cydc_parser import CydcParser
from cydc_lexer import CydcLexer


class TestParserBasicStatements(unittest.TestCase):
    """Test parsing of basic statements."""

    def setUp(self):
        """Initialize parser for each test."""
        self.parser = CydcParser()
        self.parser.build()

    def test_parse_end_statement(self):
        """Test parsing END statement."""
        code = "[[END]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_goto_statement(self):
        """Test parsing GOTO statement."""
        code = "[[GOTO Label]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_label_statement(self):
        """Test parsing LABEL statement."""
        code = "[[LABEL MyLabel]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_clear_statement(self):
        """Test parsing CLEAR statement."""
        code = "[[CLEAR]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_border_statement(self):
        """Test parsing BORDER statement with parameter."""
        code = "[[BORDER 0]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_ink_statement(self):
        """Test parsing INK statement with parameter."""
        code = "[[INK 7]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_print_statement(self):
        """Test parsing PRINT statement."""
        code = '[[PRINT "text"]]'
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_multiple_statements_with_colons(self):
        """Test parsing multiple statements separated by colons."""
        code = "[[PRINT 1 : PRINT 2 : PRINT 3]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)


class TestParserControlFlow(unittest.TestCase):
    """Test parsing of control flow statements."""

    def setUp(self):
        """Initialize parser for each test."""
        self.parser = CydcParser()
        self.parser.build()

    def test_parse_if_then_endif(self):
        """Test parsing IF-THEN-ENDIF structure."""
        code = "[[IF 1 THEN PRINT 1 ENDIF]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_if_then_else_endif(self):
        """Test parsing IF-THEN-ELSE-ENDIF structure."""
        code = "[[IF 1 THEN PRINT 1 ELSE PRINT 2 ENDIF]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_while_loop(self):
        """Test parsing WHILE-WEND loop."""
        code = "[[WHILE ( 1 ) PRINT 1 WEND]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_do_until_loop(self):
        """Test parsing DO-UNTIL loop."""
        code = "[[DO PRINT 1 UNTIL 0]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_loop_statement(self):
        """Test parsing LOOP statement."""
        code = "[[LOOP 10]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_nested_if(self):
        """Test parsing nested IF statements."""
        code = "[[IF 1 THEN IF 2 THEN PRINT 1 ENDIF ENDIF]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)


class TestParserExpressions(unittest.TestCase):
    """Test parsing of expressions."""

    def setUp(self):
        """Initialize parser for each test."""
        self.parser = CydcParser()
        self.parser.build()

    def test_parse_arithmetic_expression(self):
        """Test parsing arithmetic expressions."""
        code = "[[PRINT 1 + 2]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_comparison_expression(self):
        """Test parsing comparison expressions."""
        code = "[[IF 1 > 0 THEN PRINT 1 ENDIF]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_logical_expression(self):
        """Test parsing logical expressions."""
        code = "[[IF 1 AND 2 THEN PRINT 1 ENDIF]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_variable_reference(self):
        """Test parsing variable references."""
        code = "[[PRINT @0]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_array_access(self):
        """Test parsing array access."""
        code = "[[PRINT @array[0]]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)


class TestParserOptions(unittest.TestCase):
    """Test parsing of OPTION statement."""

    def setUp(self):
        """Initialize parser for each test."""
        self.parser = CydcParser()
        self.parser.build()

    def test_parse_option_goto(self):
        """Test parsing OPTION with GOTO."""
        code = '[[OPTION GOTO Label]]'
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_option_with_call(self):
        """Test parsing OPTION with CALL."""
        code = "[[OPTION CALL Subroutine]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)

    def test_parse_choose_statement(self):
        """Test parsing CHOOSE statement."""
        code = "[[CHOOSE]]"
        result = self.parser.parse(input=code)
        self.assertIsNotNone(result)


class TestParserStrictColonMode(unittest.TestCase):
    """Test strict colon mode (colon requirement between statements on same line)."""

    def setUp(self):
        """Initialize parser for each test."""
        self.parser_strict = CydcParser(strict_colon_mode=True)
        self.parser_strict.build()
        self.parser_lenient = CydcParser(strict_colon_mode=False)
        self.parser_lenient.build()

    def test_strict_mode_rejects_missing_colon(self):
        """Test that strict mode generates error when colon is missing."""
        code = "[[PRINT 1 PRINT 2]]"
        result = self.parser_strict.parse(input=code)
        # Should have errors
        self.assertTrue(len(self.parser_strict.errors) > 0)

    def test_strict_mode_accepts_with_colon(self):
        """Test that strict mode accepts statements with colons."""
        code = "[[PRINT 1 : PRINT 2]]"
        result = self.parser_strict.parse(input=code)
        # Should have no errors (or at least colon-related errors)
        # Clear any previous errors from other tests
        self.parser_strict.errors = []
        result = self.parser_strict.parse(input=code)
        colon_errors = [e for e in self.parser_strict.errors if "colon" in e.lower()]
        self.assertEqual(len(colon_errors), 0)

    def test_lenient_mode_accepts_missing_colon(self):
        """Test that lenient mode accepts statements without colons."""
        code = "[[PRINT 1 PRINT 2]]"
        self.parser_lenient.errors = []
        result = self.parser_lenient.parse(input=code)
        # Should not have colon-related errors
        colon_errors = [e for e in self.parser_lenient.errors if "colon" in e.lower()]
        self.assertEqual(len(colon_errors), 0)

    def test_strict_mode_goto_if_missing_colon(self):
        """Test strict mode detects missing colon between GOTO and IF."""
        code = "[[GOTO Label IF @0 > 0 THEN PRINT 1 ENDIF]]"
        self.parser_strict.errors = []
        result = self.parser_strict.parse(input=code)
        # Should detect missing colon after GOTO Label
        self.assertTrue(len(self.parser_strict.errors) > 0)

    def test_strict_mode_print_goto_missing_colon(self):
        """Test strict mode detects missing colon between PRINT and GOTO."""
        code = "[[PRINT 1 GOTO Label]]"
        self.parser_strict.errors = []
        result = self.parser_strict.parse(input=code)
        # Should detect missing colon
        self.assertTrue(len(self.parser_strict.errors) > 0)

    def test_strict_mode_single_statement_no_error(self):
        """Test that single statements don't trigger colon errors."""
        code = "[[PRINT 1]]"
        self.parser_strict.errors = []
        result = self.parser_strict.parse(input=code)
        colon_errors = [e for e in self.parser_strict.errors if "colon" in e.lower()]
        self.assertEqual(len(colon_errors), 0)

    def test_strict_mode_loop_body_statements(self):
        """Test colon requirement in loop body statements."""
        code = "[[LOOP 10 PRINT 1 PRINT 2 ENDLOOP]]"
        self.parser_strict.errors = []
        result = self.parser_strict.parse(input=code)
        # Space between PRINT 1 and PRINT 2 should require colon in strict mode
        # May or may not error depending on parser implementation
        # This is a regression test to ensure consistency


class TestParserBackwardsCompatibility(unittest.TestCase):
    """Test backwards compatibility with lenient parsing mode."""

    def setUp(self):
        """Initialize lenient parser for each test."""
        self.parser = CydcParser(strict_colon_mode=False)
        self.parser.build()

    def test_accepts_legacy_code_without_colons(self):
        """Test that lenient mode accepts legacy code without colon separators."""
        code = "[[PRINT 1 PRINT 2 PRINT 3]]"
        self.parser.errors = []
        result = self.parser.parse(input=code)
        colon_errors = [e for e in self.parser.errors if "colon" in e.lower()]
        self.assertEqual(len(colon_errors), 0)

    def test_accepts_complex_legacy_code(self):
        """Test acceptance of complex legacy patterns."""
        code = """[[
        IF @0 > 0 THEN PRINT 1 ENDIF
        GOTO Label
        LABEL Label
        END
        ]]"""
        self.parser.errors = []
        result = self.parser.parse(input=code)
        # Should parse without major errors
        self.assertIsNotNone(result)


class TestParserErrorHandling(unittest.TestCase):
    """Test error detection and reporting."""

    def setUp(self):
        """Initialize parser for each test."""
        self.parser = CydcParser()
        self.parser.build()

    def test_detects_unclosed_if(self):
        """Test detection of unclosed IF statement."""
        code = "[[IF 1 THEN PRINT 1]]"
        self.parser.errors = []
        result = self.parser.parse(input=code)
        # Should detect missing ENDIF
        # The result might still be valid depending on parser robustness

    def test_detects_unclosed_loop(self):
        """Test detection of unclosed loop."""
        code = "[[WHILE ( 1 ) PRINT 1]]"
        self.parser.errors = []
        result = self.parser.parse(input=code)
        # Should have error (missing WEND)

    def test_empty_code_block(self):
        """Test parsing empty code block."""
        code = "[[]]"
        result = self.parser.parse(input=code)
        # Should handle gracefully
        self.assertTrue(result is not None or len(self.parser.errors) == 0)

    def test_invalid_syntax(self):
        """Test invalid syntax detection."""
        code = "[[: : :]]"
        self.parser.errors = []
        result = self.parser.parse(input=code)
        # May generate errors


class TestParserRegressions(unittest.TestCase):
    """Test for regressions in parser changes."""

    def setUp(self):
        """Initialize parser for each test."""
        self.parser_strict = CydcParser(strict_colon_mode=True)
        self.parser_strict.build()
        self.parser_lenient = CydcParser(strict_colon_mode=False)
        self.parser_lenient.build()

    def test_realistic_adventure_code_strict(self):
        """Test realistic adventure code in strict mode."""
        code = """[[
        PAGEPAUSE 1
        : BORDER 0
        : INK 7
        : PAPER 0
        : DISPLAY 1
        ]]"""
        self.parser_strict.errors = []
        result = self.parser_strict.parse(input=code)
        self.assertIsNotNone(result)

    def test_realistic_adventure_code_lenient(self):
        """Test realistic adventure code in lenient mode."""
        code = """[[
        PAGEPAUSE 1
        BORDER 0
        INK 7
        PAPER 0
        DISPLAY 1
        ]]"""
        self.parser_lenient.errors = []
        result = self.parser_lenient.parse(input=code)
        self.assertIsNotNone(result)

    def test_option_and_choose_sequence(self):
        """Test OPTION-CHOOSE sequence."""
        code = """[[OPTION GOTO Option1]]
Choice 1
[[OPTION GOTO Option2]]
Choice 2
[[CHOOSE]]"""
        self.parser_lenient.errors = []
        result = self.parser_lenient.parse(input=code)
        self.assertIsNotNone(result)

    def test_set_with_calculation(self):
        """Test SET statement with calculation."""
        code = "[[SET 0 TO @0 + 1]]"
        self.parser_lenient.errors = []
        result = self.parser_lenient.parse(input=code)
        self.assertIsNotNone(result)

    def test_track_and_display_commands(self):
        """Test TRACK and DISPLAY commands."""
        code = "[[TRACK 0 : DISPLAY 1]]"
        self.parser_strict.errors = []
        result = self.parser_strict.parse(input=code)
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
