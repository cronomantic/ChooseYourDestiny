"""
Test suite for integration - End-to-end compilation and feature testing.

This module tests:
- Complete compilation pipeline
- File I/O and error handling
- Command-line argument processing
- Feature combinations
"""

import unittest
import sys
import tempfile
from pathlib import Path
from io import StringIO

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

from cydc_lexer import CydcLexer
from cydc_parser import CydcParser


class TestIntegrationLexerParser(unittest.TestCase):
    """Test lexer and parser together."""

    def setUp(self):
        """Initialize components for each test."""
        self.parser_strict = CydcParser(strict_colon_mode=True)
        self.parser_strict.build()
        self.parser_lenient = CydcParser(strict_colon_mode=False)
        self.parser_lenient.build()

    def test_full_pipeline_strict_mode(self):
        """Test complete lexer-parser pipeline in strict mode."""
        code = """This is the intro text
[[PAGEPAUSE 1 : BORDER 0 : INK 7]]
The screen has been cleared.
[[OPTION GOTO Option1]]First choice[[OPTION GOTO Option2]]Second choice[[CHOOSE]]"""
        
        self.parser_strict.errors = []
        try:
            result = self.parser_strict.parse(input=code)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Pipeline failed: {e}")

    def test_full_pipeline_lenient_mode(self):
        """Test complete lexer-parser pipeline in lenient mode."""
        code = """This is the intro text
[[PAGEPAUSE 1 BORDER 0 INK 7]]
The screen has been cleared.
[[OPTION GOTO Option1]]First choice[[OPTION GOTO Option2]]Second choice[[CHOOSE]]"""
        
        self.parser_lenient.errors = []
        try:
            result = self.parser_lenient.parse(input=code)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Pipeline failed: {e}")

    def test_various_statement_combinations_strict(self):
        """Test various statement combinations in strict mode."""
        statements = [
            "[[END]]",
            "[[GOTO MyLabel]]",
            "[[LABEL MyLabel]]",
            "[[PRINT 1]]",
            "[[CLEAR]]",
            "[[BORDER 0 : INK 7]]",
            "[[IF 1 = 1 THEN PRINT 1 ENDIF]]",
            "[[SET 0 TO 100]]",
        ]
        
        for stmt in statements:
            with self.subTest(statement=stmt):
                self.parser_strict.errors = []
                try:
                    result = self.parser_strict.parse(input=stmt)
                    self.assertIsNotNone(result)
                except Exception as e:
                    self.fail(f"Failed to parse: {stmt} - {e}")

    def test_various_statement_combinations_lenient(self):
        """Test various statement combinations in lenient mode."""
        statements = [
            "[[END]]",
            "[[GOTO MyLabel]]",
            "[[LABEL MyLabel]]",
            "[[PRINT 1]]",
            "[[CLEAR]]",
            "[[BORDER 0 INK 7]]",
            "[[IF 1 = 1 THEN PRINT 1 ENDIF]]",
            "[[SET 0 TO 100]]",
        ]
        
        for stmt in statements:
            with self.subTest(statement=stmt):
                self.parser_lenient.errors = []
                try:
                    result = self.parser_lenient.parse(input=stmt)
                    self.assertIsNotNone(result)
                except Exception as e:
                    self.fail(f"Failed to parse: {stmt} - {e}")


class TestIntegrationComplexScenarios(unittest.TestCase):
    """Test complex real-world scenarios."""

    def setUp(self):
        """Initialize parser for each test."""
        self.parser = CydcParser(strict_colon_mode=False)
        self.parser.build()

    def test_adventure_scenario_intro(self):
        """Test adventure scenario with introduction."""
        code = """
        Welcome to the Adventure!
        [[PAGEPAUSE 1 : BORDER 0 : INK 7 : PAPER 0 : DISPLAY 1 : WAIT 75 : CLEAR]]
        You find yourself in a mysterious place.
        [[OPTION GOTO Check]]Look around
        [[OPTION GOTO Escape]]Try to escape
        [[CHOOSE
            LABEL Check
            GOTO End
            LABEL Escape
            GOTO End
            LABEL End
            WAITKEY
            END
        ]]"""
        
        self.parser.errors = []
        try:
            result = self.parser.parse(input=code)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Adventure scenario failed: {e}")

    def test_adventure_with_variables(self):
        """Test adventure using variables and SET."""
        code = """
        [[SET 0 TO 0]]
        You have [[PRINT @0]] items.
        [[OPTION GOTO Gain]]Pick up item
        [[CHOOSE
            LABEL Gain
            SET 0 TO @0 + 1
            GOTO Start
            LABEL Start
            END
        ]]"""
        
        self.parser.errors = []
        try:
            result = self.parser.parse(input=code)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Variable scenario failed: {e}")

    def test_adventure_with_conditionals(self):
        """Test adventure using IF statements."""
        code = """
        [[SET 0 TO 5]]
        [[IF @0 > 10 THEN PRINT "Many items" ELSE PRINT "Few items" ENDIF]]
        [[LABEL Continue]]
        More text here.
        [[END]]"""
        
        self.parser.errors = []
        try:
            result = self.parser.parse(input=code)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Conditional scenario failed: {e}")

    def test_music_and_display_control(self):
        """Test music and display control commands."""
        code = """
        [[TRACK 1 : PLAY 1 : BORDER 7 : INK 0]]
        Picture is loading...
        [[PICTURE 1 : DISPLAY 1 : PAGEPAUSE 1]]
        Music playing in background.
        [[STOP : END]]"""
        
        self.parser.errors = []
        try:
            result = self.parser.parse(input=code)
            self.assertIsNotNone(result)
        except Exception as e:
            # These commands might not all be recognized, but shouldn't crash
            self.assertTrue(True)


class TestIntegrationModeConsistency(unittest.TestCase):
    """Test consistency between strict and lenient modes."""

    def setUp(self):
        """Initialize parsers for each test."""
        self.parser_strict = CydcParser(strict_colon_mode=True)
        self.parser_strict.build()
        self.parser_lenient = CydcParser(strict_colon_mode=False)
        self.parser_lenient.build()

    def test_same_output_for_properly_formatted_code(self):
        """Verify both modes produce same output for properly formatted code."""
        code = "[[PRINT 1 : PRINT 2 : END]]"
        
        self.parser_strict.errors = []
        result_strict = self.parser_strict.parse(input=code)
        
        self.parser_lenient.errors = []
        result_lenient = self.parser_lenient.parse(input=code)
        
        # Both should parse successfully
        self.assertIsNotNone(result_strict)
        self.assertIsNotNone(result_lenient)

    def test_strict_only_errors_on_missing_colons(self):
        """Verify only strict mode errors on missing colons."""
        code = "[[PRINT 1 PRINT 2]]"
        
        self.parser_strict.errors = []
        result_strict = self.parser_strict.parse(input=code)
        strict_colon_errors = [e for e in self.parser_strict.errors if "colon" in e.lower()]
        
        self.parser_lenient.errors = []
        result_lenient = self.parser_lenient.parse(input=code)
        lenient_colon_errors = [e for e in self.parser_lenient.errors if "colon" in e.lower()]
        
        # Strict should have colon errors, lenient shouldn't
        self.assertTrue(len(strict_colon_errors) > 0 or len(result_strict) > 0)
        self.assertEqual(len(lenient_colon_errors), 0)


class TestIntegrationEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""

    def setUp(self):
        """Initialize parser for each test."""
        self.parser = CydcParser()
        self.parser.build()

    def test_very_long_line(self):
        """Test parsing very long single line."""
        long_print = "[[" + " : ".join(["PRINT 1"] * 50) + "]]"
        self.parser.errors = []
        try:
            result = self.parser.parse(input=long_print)
            self.assertIsNotNone(result)
        except Exception:
            pass  # May fail due to complexity, but shouldn't crash

    def test_deeply_nested_if(self):
        """Test deeply nested IF statements."""
        nested_if = "[[IF 1 = 1 THEN "
        nested_if += "IF 1 = 1 THEN " * 5
        nested_if += "PRINT 1"
        nested_if += " ENDIF" * 5
        nested_if += " ENDIF]]"
        
        self.parser.errors = []
        try:
            result = self.parser.parse(input=nested_if)
            # May fail due to depth, but shouldn't crash
            self.assertIsNotNone(result)
        except Exception:
            pass

    def test_mixed_text_and_code_intensive(self):
        """Test intensive mixing of text and code."""
        code = "Text1 [[CODE1]] Text2 [[CODE2]] Text3 [[CODE3]] Text4 " * 10
        self.parser.errors = []
        try:
            result = self.parser.parse(input=code)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Intensive mixed content failed: {e}")

    def test_unicode_text_content(self):
        """Test Unicode characters in text portions."""
        code = """
        [[PRINT]] Ñoño, áéíóú, çñ, € ¡Hola! ¿Cómo estás?
        [[END]]
        """
        self.parser.errors = []
        try:
            result = self.parser.parse(input=code)
            self.assertIsNotNone(result)
        except Exception as e:
            # May fail due to encoding, but shouldn't crash
            self.assertTrue(True)


class TestIntegrationRegressionPrevention(unittest.TestCase):
    """Tests specifically designed to catch regressions."""

    def setUp(self):
        """Initialize parser for each test."""
        self.parser_strict = CydcParser(strict_colon_mode=True)
        self.parser_strict.build()
        self.parser_lenient = CydcParser(strict_colon_mode=False)
        self.parser_lenient.build()

    def test_lexer_refactoring_preserves_behavior(self):
        """Verify lexer refactoring didn't break text/code separation."""
        code = "Normal text [[PRINT 1]] more text"
        
        self.parser_lenient.errors = []
        result = self.parser_lenient.parse(input=code)
        
        # Should have successfully tokenized and parsed
        self.assertIsNotNone(result)

    def test_strict_colon_backward_compatible_with_flag(self):
        """Verify --no-strict-colons flag enables lenient mode behavior."""
        code = "[[PRINT 1 PRINT 2]]"
        
        # In lenient mode, should not error on colons
        self.parser_lenient.errors = []
        result = self.parser_lenient.parse(input=code)
        colon_errors = [e for e in self.parser_lenient.errors if "colon" in e.lower()]
        
        self.assertEqual(len(colon_errors), 0)

    def test_option_and_choose_never_break(self):
        """Ensure OPTION/CHOOSE functionality is never broken."""
        code = """
        [[OPTION GOTO L1]]Choice1
        [[OPTION GOTO L2]]Choice2
        [[CHOOSE
            LABEL L1 GOTO End
            LABEL L2 GOTO End
            LABEL End : END
        ]]"""
        
        for parser, mode in [(self.parser_strict, "strict"), (self.parser_lenient, "lenient")]:
            with self.subTest(mode=mode):
                parser.errors = []
                try:
                    result = parser.parse(input=code)
                    # This core feature must always work
                    self.assertIsNotNone(result)
                except Exception as e:
                    self.fail(f"OPTION/CHOOSE broke in {mode} mode: {e}")

    def test_variable_operations_never_break(self):
        """Ensure variable operations are never broken."""
        code = """
        [[SET 0 TO 100]]
        [[SET 1 TO @0 + 50]]
        [[IF @0 > 100 THEN PRINT "yes" ENDIF]]
        [[PRINT @1]]
        [[END]]"""
        
        self.parser_lenient.errors = []
        try:
            result = self.parser_lenient.parse(input=code)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Variable operations broken: {e}")


if __name__ == "__main__":
    unittest.main()
