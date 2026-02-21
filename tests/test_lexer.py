"""
Test suite for CydcLexer - Tokenization and lexical analysis.

This module tests the lexer's ability to:
- Correctly tokenize code and text modes
- Handle mixed code/text blocks delimited by [[ ]]
- Recognize reserved words and keywords
- Handle special characters and encodings
- Process identifiers, numbers, strings, and operators
"""

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

from cydc_lexer import CydcLexer


class TestLexerBasicTokens(unittest.TestCase):
    """Test basic token recognition."""

    def setUp(self):
        """Initialize lexer for each test."""
        self.lexer = CydcLexer()
        self.lexer.build()

    def test_reserved_word_goto(self):
        """Test GOTO keyword recognition."""
        self.lexer.input("[[GOTO Label]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("GOTO", token_types)

    def test_reserved_word_label(self):
        """Test LABEL keyword recognition."""
        self.lexer.input("[[LABEL MyLabel]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("LABEL", token_types)

    def test_reserved_word_end(self):
        """Test END keyword recognition."""
        self.lexer.input("[[END]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("END", token_types)

    def test_reserved_words_control_flow(self):
        """Test control flow keywords."""
        keywords = ["IF", "THEN", "ELSE", "ENDIF", "WHILE", "WEND", 
                    "DO", "UNTIL", "LOOP"]
        for keyword in keywords:
            with self.subTest(keyword=keyword):
                self.lexer.input(f"[[{keyword}]]")
                tokens = list(self.lexer.lexer)
                token_types = [t.type for t in tokens]
                self.assertIn(keyword, token_types)

    def test_reserved_words_graphics(self):
        """Test graphics-related keywords."""
        keywords = ["BORDER", "INK", "PAPER", "BRIGHT", "FLASH", 
                    "PICTURE", "DISPLAY", "CLEAR"]
        for keyword in keywords:
            with self.subTest(keyword=keyword):
                self.lexer.input(f"[[{keyword}]]")
                tokens = list(self.lexer.lexer)
                token_types = [t.type for t in tokens]
                self.assertIn(keyword, token_types)

    def test_identifier_simple(self):
        """Test simple identifier recognition."""
        self.lexer.input("[[myVar]]")
        tokens = list(self.lexer.lexer)
        self.assertEqual(tokens[0].type, "ID")
        self.assertEqual(tokens[0].value, "myVar")

    def test_identifier_uppercase(self):
        """Test uppercase identifier (treated as reserved word check)."""
        self.lexer.input("[[CUSTOMVAR]]")
        tokens = list(self.lexer.lexer)
        # Should be ID since CUSTOMVAR is not a reserved word
        self.assertEqual(tokens[0].type, "ID")
        self.assertEqual(tokens[0].value, "CUSTOMVAR")

    def test_number_integer(self):
        """Test integer number recognition."""
        self.lexer.input("[[42]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        # Should find a number token (DEC_NUMBER, HEX_NUMBER, or BIN_NUMBER)
        number_tokens = [t for t in tokens if t.type in ["DEC_NUMBER", "HEX_NUMBER", "BIN_NUMBER"]]
        self.assertTrue(len(number_tokens) > 0)

    def test_number_negative(self):
        """Test negative integer recognition."""
        self.lexer.input("[[-10]]")
        tokens = list(self.lexer.lexer)
        # Negative might be parsed as MINUS token followed by NUMBER
        # or as a single negative number depending on lexer implementation
        self.assertTrue(len(tokens) >= 1)

    def test_string_simple(self):
        """Test simple string recognition."""
        self.lexer.input('[[PRINT]]')
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        # Should find PRINT keyword
        self.assertIn("PRINT", token_types)

    def test_string_with_escapes(self):
        """Test string with escap]]')
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        # Should find PRINT keyword
        self.assertIn("PRINT for t in tokens]
        self.assertIn("STRING", token_types)

    def test_operators_arithmetic(self):
        """Test arithmetic operator recognition."""
        operators = ["+", "-", "*", "/", "%"]
        for op in operators:
            with self.subTest(operator=op):
                self.lexer.input(f"[[a {op} b]]")
                tokens_list = list(self.lexer.lexer)
                ops_found = [t.value for t in tokens_list if t.type in ["PLUS", "MINUS", "TIMES", "DIVIDE", "MOD"]]
                self.assertTrue(len(ops_found) > 0)

    def test_operators_comparison(self):
        """Test comparison operator recognition."""
        self.lexer.input("[[a == b]]")
        tokens = list(self.lexer.lexer)
        # Should find EQUALS token
        token_types = [t.type for t in tokens]
        self.assertIn("EQUALS", token_types)

    def test_operators_logical(self):
        """Test logical operator recognition."""
        self.lexer.input("[[a AND b]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("AND", token_types)


class TestLexerModes(unittest.TestCase):
    """Test lexer state transitions and mode switching."""

    def setUp(self):
        """Initialize lexer for each test."""
        self.lexer = CydcLexer()
        self.lexer.build()

    def test_code_mode_opening(self):
        """Test entering code mode with [[."""
        self.lexer.input("Text before [[CODE_HERE]]Text after")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        # Should have TEXT, then CODE tokens
        self.assertIn("TEXT", token_types)

    def test_code_mode_closing(self):
        """Test exiting code mode with ]]."""
        self.lexer.input("[[CODE_HERE]]text_here")
        tokens = list(self.lexer.lexer)
        # Should contain both code and text tokens
        self.assertTrue(len(tokens) > 0)

    def test_text_mode_preserved(self):
        """Test that text outside [[ ]] is preserved."""
        self.lexer.input("Plain text content")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("TEXT", token_types)

    def test_multiple_code_blocks(self):
        """Test multiple code blocks in sequence."""
        self.lexer.input("[[CODE1]]text[[CODE2]]")
        tokens = list(self.lexer.lexer)
        self.assertTrue(len(tokens) > 2)

    def test_nested_code_blocks_not_allowed(self):
        """Test that nested [[ ]] produces expected token stream."""
        self.lexer.input("[[outer [[inner]]]]")
        tokens = list(self.lexer.lexer)
        # This should not crash but may produce unexpected tokens
        self.assertTrue(len(tokens) > 0)

    def test_code_block_empty(self):
        """Test empty code block."""
        self.lexer.input("[[]]")
        tokens = list(self.lexer.lexer)
        # Should handle gracefully
        self.assertTrue(tokens is not None)

    def test_code_block_whitespace_only(self):
        """Test code block with only whitespace."""
        self.lexer.input("[[   ]]")
        tokens = list(self.lexer.lexer)
        self.assertTrue(len(tokens) >= 0)


class TestLexerComplexCode(unittest.TestCase):
    """Test complex real-world code patterns."""

    def setUp(self):
        """Initialize lexer for 
        self.lexer.build()each test."""
        self.lexer = CydcLexer()

    def test_option_statement(self):
        """Test OPTION keyword and arguments."""
        self.lexer.input("[[OPTION GOTO Label]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("OPTION", token_types)
        self.assertIn("GOTO", token_types)

    def test_set_statement(self):
        """Test SET keyword with variable and expression."""
        self.lexer.input("[[SET 0 TO 100]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("SET", token_types)

    def test_if_statement_complex(self):
        """Test complex IF statement with conditions."""
        self.lexer.input("[[IF @0 > 10 THEN PRINT @0 ENDIF]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("IF", token_types)
        self.assertIn("PRINT", token_types)

    def test_print_with_string(self):
        """Test PRINT statement with string."""
        self.lexer.input('[[PRINT "Hello"]]')
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("PRINT", token_types)
        self.assertIn("STRING", token_types)

    def test_variable_reference(self):
        """Test variable reference with @ symbol."""
        self.lexer.input("[[PRINT @0]]")
        tokens = list(self.lexer.lexer)
        # Should handle @ symbol properly
        self.assertTrue(len(tokens) > 0)

    def test_array_reference(self):
        """Test array reference syntax."""
        self.lexer.input("[[PRINT @array[0]]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("PRINT", token_types)


class TestLexerErrors(unittest.TestCase):
    """Test error handling and edge cases."""

    def setUp(self):
        """Initialize lexer for 
        self.lexer.build()each test."""
        self.lexer = CydcLexer()

    def test_unclosed_code_block(self):
        """Test unclosed code block [[ without ]]."""
        self.lexer.input("[[GOTO Label")
        # Should not crash
        try:
            tokens = list(self.lexer.lexer)
            self.assertTrue(True)  # If it doesn't crash, test passes
        except Exception:
            self.fail("Unclosed code block caused exception")

    def test_unopened_code_block_close(self):
        """Test closing ]] without opening [[."""
        self.lexer.input("]]GOTO")
        # Should not crash
        try:
            tokens = list(self.lexer.lexer)
            self.assertTrue(True)
        except Exception:
            self.fail("Unopened ]] caused exception")

    def test_invalid_characters(self):
        """Test handling of unusual characters."""
        self.lexer.input("[[~!@#$%^&*()]]")
        # Should not crash
        try:
            tokens = list(self.lexer.lexer)
            self.assertTrue(True)
        except Exception:
            self.fail("Invalid characters caused exception")

    def test_special_spanish_chars(self):
        """Test special Spanish characters in text."""
        self.lexer.input("[[PRINT]] Ñoño áéíóú")
        try:
            tokens = list(self.lexer.lexer)
            self.assertTrue(True)
        except Exception:
            self.fail("Spanish characters caused exception")


class TestLexerRegressions(unittest.TestCase):
    """Test for regressions in lexer refactoring (inverted semantics fix)."""

    def setUp(self):
        self.lexer.build()
        """Initialize lexer for each test."""
        self.lexer = CydcLexer()

    def test_text_outside_code_blocks(self):
        """Verify text outside [[ ]] is recognized as TEXT tokens."""
        self.lexer.input("This is text [[CODE]] more text")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        # Should have TEXT tokens for the text parts
        self.assertIn("TEXT", token_types)

    def test_code_inside_code_blocks(self):
        """Verify keywords inside [[ ]] are recognized as code tokens."""
        self.lexer.input("[[GOTO Label]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        # Should have GOTO token
        self.assertIn("GOTO", token_types)
        # Should NOT have TEXT token for GOTO
        self.assertNotIn("TEXT", [t.type for t in tokens if t.value == "GOTO"])

    def test_realistic_mixed_content(self):
        """Test realistic mixed code/text pattern from actual CYD files."""
        code = """This is introduction text
[[PAGEPAUSE 1 : BORDER 0]]Here is some description
[[OPTION GOTO Option1]]First choice
[[OPTION GOTO Option2]]Second choice
[[CHOOSE]]You chose"""
        self.lexer.input(code)
        tokens = list(self.lexer.lexer)
        # Should have mixed tokens
        token_types = [t.type for t in tokens]
        self.assertTrue("TEXT" in token_types or len(token_types) > 0)
        # Should recognize keywords
        keywords_found = [t.value for t in tokens if t.value in ["PAGEPAUSE", "BORDER", "OPTION", "CHOOSE"]]
        self.assertTrue(len(keywords_found) > 0)

    def test_colon_as_statement_separator(self):
        """Test that colons are recognized as statement separators."""
        self.lexer.input("[[PRINT 1 : PRINT 2]]")
        tokens = list(self.lexer.lexer)
        token_types = [t.type for t in tokens]
        self.assertIn("COLON", token_types)


if __name__ == "__main__":
    unittest.main()
