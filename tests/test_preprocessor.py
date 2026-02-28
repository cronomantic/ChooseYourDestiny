# -- coding: utf-8 -*-
"""
Tests for the CYD preprocessor (INCLUDE directive).

These tests verify that the preprocessor correctly handles:
- Basic include functionality
- Nested includes
- Circular include detection
- File not found errors
- Path resolution (absolute and relative)
- Maximum depth checking
"""

import unittest
import sys
import os
import tempfile
import shutil

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "cydc", "cydc"))

from cydc_preprocessor import CydcPreprocessor, PreprocessorError, SourceLocation


class TestPreprocessorBasic(unittest.TestCase):
    """Test basic preprocessor functionality."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.preprocessor = CydcPreprocessor(base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def _write_file(self, filename, content):
        """Helper to write a test file."""
        filepath = os.path.join(self.test_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_no_includes(self):
        """Test preprocessing a file without any includes."""
        content = """
START:
    PRINT "Hello World"
    END
"""
        filepath = self._write_file("main.cyd", content)
        result, line_map = self.preprocessor.preprocess(filepath)
        
        # Should be identical except for newlines
        self.assertIn('PRINT "Hello World"', result)
        self.assertIn('START:', result)
        self.assertIn('END', result)
        
        # Line map should track all lines to main.cyd
        self.assertIsNotNone(line_map)
        self.assertTrue(len(line_map) > 0)
    
    def test_simple_include(self):
        """Test including a single file."""
        # Create included file
        self._write_file("lib.cyd", """
[[
LIB_FUNC:
    PRINT "From library"
    RETURN
]]
""")
        
        # Create main file with include
        main_content = """
[[
START:
    INCLUDE "lib.cyd"
    GOSUB LIB_FUNC
    END
]]
"""
        filepath = self._write_file("main.cyd", main_content)
        result, line_map = self.preprocessor.preprocess(filepath)
        
        # Check that included content is present
        self.assertIn('LIB_FUNC:', result)
        self.assertIn('PRINT "From library"', result)
        self.assertIn('GOSUB LIB_FUNC', result)
        
        # Check that include directive is replaced with markers
        self.assertIn('/* BEGIN INCLUDE: lib.cyd', result)
        self.assertIn('/* END INCLUDE: lib.cyd', result)
        self.assertNotIn('INCLUDE "lib.cyd"', result)
    
    def test_include_case_insensitive(self):
        """Test that INCLUDE is case-insensitive."""
        self._write_file("lib.cyd", "[[// Library content\n]]")
        
        # Test various cases
        for include_stmt in ['INCLUDE', 'include', 'Include', 'InClUdE']:
            filepath = self._write_file("test.cyd", f'[[{include_stmt} "lib.cyd"\n]]')
            result, _ = self.preprocessor.preprocess(filepath)
            self.assertIn('// Library content', result)
    
    def test_include_with_single_quotes(self):
        """Test include with single quotes."""
        self._write_file("lib.cyd", "[[// Library\n]]")
        filepath = self._write_file("main.cyd", "[[INCLUDE 'lib.cyd'\n]]")
        result, _ = self.preprocessor.preprocess(filepath)
        self.assertIn('// Library', result)
    
    def test_include_with_comment(self):
        """Test include followed by a comment."""
        self._write_file("lib.cyd", "[[// Library\n]]")
        filepath = self._write_file("main.cyd", '[[INCLUDE "lib.cyd" // Load library\n]]')
        result, _ = self.preprocessor.preprocess(filepath)
        self.assertIn('// Library', result)


class TestPreprocessorNested(unittest.TestCase):
    """Test nested includes."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.preprocessor = CydcPreprocessor(base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def _write_file(self, filename, content):
        """Helper to write a test file."""
        filepath = os.path.join(self.test_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_nested_includes(self):
        """Test file including another file that includes a third file."""
        # Level 2
        self._write_file("utils.cyd", "[[// Utilities\n]]")
        
        # Level 1 includes level 2
        self._write_file("lib.cyd", """
[[// Library
INCLUDE "utils.cyd"
]]
""")
        
        # Main includes level 1
        filepath = self._write_file("main.cyd", """
[[// Main
INCLUDE "lib.cyd"
]]
""")
        
        result, line_map = self.preprocessor.preprocess(filepath)
        
        # All content should be present
        self.assertIn('// Utilities', result)
        self.assertIn('// Library', result)
        self.assertIn('// Main', result)
        
        # Should have nested markers
        self.assertIn('/* BEGIN INCLUDE: lib.cyd', result)
        self.assertIn('/* BEGIN INCLUDE: utils.cyd', result)
    
    def test_max_depth_exceeded(self):
        """Test that maximum include depth is enforced."""
        # Create a chain of includes that exceeds max depth
        preprocessor = CydcPreprocessor(base_path=self.test_dir, max_depth=3)
        
        # Create 5 files that include each other in a chain
        for i in range(5):
            if i < 4:
                content = f'[[INCLUDE "file{i+1}.cyd"\n]]'
            else:
                content = '[[// End of chain\n]]'
            self._write_file(f"file{i}.cyd", content)
        
        filepath = os.path.join(self.test_dir, "file0.cyd")
        
        # Should raise PreprocessorError about max depth
        with self.assertRaises(PreprocessorError) as context:
            preprocessor.preprocess(filepath)
        
        self.assertIn("Maximum include depth", str(context.exception))
    
    def test_subdirectory_include(self):
        """Test including files from subdirectories."""
        # Create subdirectory with file
        self._write_file("lib/helper.cyd", "[[// Helper\n]]")
        
        # Main file includes from subdirectory
        filepath = self._write_file("main.cyd", '[[INCLUDE "lib/helper.cyd"\n]]')
        
        result, _ = self.preprocessor.preprocess(filepath)
        self.assertIn('// Helper', result)
    
    def test_relative_path_from_included_file(self):
        """Test that relative paths in included files work correctly."""
        # Create directory structure:
        # main.cyd
        # lib/
        #   loader.cyd (includes utils.cyd)
        #   utils.cyd
        
        self._write_file("lib/utils.cyd", "[[// Utils\n]]")
        self._write_file("lib/loader.cyd", '[[INCLUDE "utils.cyd"\n]]')
        filepath = self._write_file("main.cyd", '[[INCLUDE "lib/loader.cyd"\n]]')
        
        result, _ = self.preprocessor.preprocess(filepath)
        self.assertIn('// Utils', result)


class TestPreprocessorErrors(unittest.TestCase):
    """Test error handling in preprocessor."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.preprocessor = CydcPreprocessor(base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def _write_file(self, filename, content):
        """Helper to write a test file."""
        filepath = os.path.join(self.test_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_file_not_found(self):
        """Test error when included file doesn't exist."""
        filepath = self._write_file("main.cyd", '[[INCLUDE "nonexistent.cyd"\n]]')
        
        with self.assertRaises(PreprocessorError) as context:
            self.preprocessor.preprocess(filepath)
        
        self.assertIn("not found", str(context.exception).lower())
    
    def test_circular_include_direct(self):
        """Test detection of direct circular includes."""
        # File includes itself
        filepath = self._write_file("circular.cyd", '[[INCLUDE "circular.cyd"\n]]')
        
        with self.assertRaises(PreprocessorError) as context:
            self.preprocessor.preprocess(filepath)
        
        self.assertIn("Circular include", str(context.exception))
    
    def test_circular_include_indirect(self):
        """Test detection of indirect circular includes."""
        # a includes b, b includes c, c includes a
        self._write_file("a.cyd", '[[INCLUDE "b.cyd"\n]]')
        self._write_file("b.cyd", '[[INCLUDE "c.cyd"\n]]')
        self._write_file("c.cyd", '[[INCLUDE "a.cyd"\n]]')
        
        filepath = os.path.join(self.test_dir, "a.cyd")
        
        with self.assertRaises(PreprocessorError) as context:
            self.preprocessor.preprocess(filepath)
        
        self.assertIn("Circular include", str(context.exception))
    
    def test_error_message_includes_location(self):
        """Test that error messages include file and line information."""
        filepath = self._write_file("main.cyd", """
[[// Line 2
INCLUDE "missing.cyd"
// Line 4
]]
""")
        
        with self.assertRaises(PreprocessorError) as context:
            self.preprocessor.preprocess(filepath)
        
        error_msg = str(context.exception)
        # Should mention the file that tried to include
        self.assertIn("main.cyd", error_msg.lower())

    def test_collects_multiple_include_errors(self):
        """Test that preprocessor accumulates multiple include errors before stopping."""
        preprocessor = CydcPreprocessor(base_path=self.test_dir, max_errors=10)
        filepath = self._write_file("main.cyd", """[[
INCLUDE "missing1.cyd"
INCLUDE "missing2.cyd"
INCLUDE "missing3.cyd"
]]""")

        with self.assertRaises(PreprocessorError):
            preprocessor.preprocess(filepath)

        self.assertEqual(len(preprocessor.errors), 3)
        self.assertFalse(preprocessor.max_errors_reached)

    def test_preprocessor_respects_max_error_limit(self):
        """Test preprocessor stops collecting errors at configured max_errors."""
        preprocessor = CydcPreprocessor(base_path=self.test_dir, max_errors=2)
        filepath = self._write_file("main.cyd", """[[
INCLUDE "missing1.cyd"
INCLUDE "missing2.cyd"
INCLUDE "missing3.cyd"
]]""")

        with self.assertRaises(PreprocessorError):
            preprocessor.preprocess(filepath)

        self.assertEqual(len(preprocessor.errors), 2)
        self.assertTrue(preprocessor.max_errors_reached)


class TestPreprocessorEdgeCases(unittest.TestCase):
    """Test edge cases and special scenarios."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.test_dir = tempfile.mkdtemp()
        self.preprocessor = CydcPreprocessor(base_path=self.test_dir)
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def _write_file(self, filename, content):
        """Helper to write a test file."""
        filepath = os.path.join(self.test_dir, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath
    
    def test_multiple_includes_in_one_file(self):
        """Test file with multiple include directives."""
        self._write_file("lib1.cyd", "[[// Library 1\n]]")
        self._write_file("lib2.cyd", "[[// Library 2\n]]")
        self._write_file("lib3.cyd", "[[// Library 3\n]]")
        
        filepath = self._write_file("main.cyd", """
[[
INCLUDE "lib1.cyd"
PRINT "Middle"
INCLUDE "lib2.cyd"
INCLUDE "lib3.cyd"
]]
""")
        
        result, _ = self.preprocessor.preprocess(filepath)
        
        # All libraries should be included
        self.assertIn('// Library 1', result)
        self.assertIn('// Library 2', result)
        self.assertIn('// Library 3', result)
        self.assertIn('PRINT "Middle"', result)
    
    def test_include_not_recognized_in_string(self):
        """Test that INCLUDE inside strings is not processed."""
        filepath = self._write_file("main.cyd", """
This text mentions INCLUDE but not in code
""")
        
        result, _ = self.preprocessor.preprocess(filepath)
        
        # The text should remain unchanged
        self.assertIn('INCLUDE', result)
        # No include markers should be present
        self.assertNotIn('/* BEGIN INCLUDE:', result)
    
    def test_include_with_whitespace_variations(self):
        """Test include with various whitespace patterns."""
        self._write_file("lib.cyd", "[[// Lib\n]]")
        
        test_cases = [
            '[[  INCLUDE "lib.cyd"]]',  # Leading spaces
            '[[\tINCLUDE "lib.cyd"]]',  # Leading tab
            '[[INCLUDE  "lib.cyd"]]',   # Extra space before quote
            '[[INCLUDE "lib.cyd"  ]]',  # Trailing spaces
        ]
        
        for include_line in test_cases:
            filepath = self._write_file("test.cyd", include_line + '\n')
            result, _ = self.preprocessor.preprocess(filepath)
            self.assertIn('// Lib', result, f"Failed for: {repr(include_line)}")
    
    def test_empty_file(self):
        """Test preprocessing an empty file."""
        filepath = self._write_file("empty.cyd", "")
        result, _ = self.preprocessor.preprocess(filepath)
        self.assertEqual(result, "")
    
    def test_file_with_only_comments(self):
        """Test file containing only comments."""
        content = """
[[// This is a comment
// Another comment
]]
"""
        filepath = self._write_file("comments.cyd", content)
        result, _ = self.preprocessor.preprocess(filepath)
        self.assertIn('// This is a comment', result)
    
    def test_include_must_be_in_code_block(self):
        """Test that INCLUDE outside code blocks raises an error."""
        filepath = self._write_file("main.cyd", """
This is text mode
INCLUDE "lib.cyd"
More text
""")
        
        with self.assertRaises(PreprocessorError) as context:
            self.preprocessor.preprocess(filepath)
        
        self.assertIn("must be inside", str(context.exception).lower())
    
    def test_include_in_code_block_valid(self):
        """Test that INCLUDE inside code blocks works correctly."""
        self._write_file("lib.cyd", "[[// Library code]]")
        filepath = self._write_file("main.cyd", """
Some text
[[
INCLUDE "lib.cyd"
]]
More text
""")
        
        result, _ = self.preprocessor.preprocess(filepath)
        self.assertIn('// Library code', result)
    
    def test_line_mapping_tracks_sources(self):
        """Test that line mapping correctly tracks source locations."""
        self._write_file("vars.cyd", "[[DECLARE 0 AS x]]")
        filepath = self._write_file("main.cyd", """[[
#Start
INCLUDE "vars.cyd"
PRINT "Hello"
]]""")
        
        result, line_map = self.preprocessor.preprocess(filepath)
        
        # Line map should exist and have entries
        self.assertIsNotNone(line_map)
        self.assertTrue(len(line_map) > 0)
        
        # Check that source locations are tracked
        for line_num, loc in line_map.items():
            self.assertIsInstance(loc, SourceLocation)
            self.assertIsNotNone(loc.filename)
            self.assertIsInstance(loc.line_num, int)
            self.assertGreater(loc.line_num, 0)
    
    def test_multiline_code_blocks(self):
        """Test INCLUDE in multi-line code blocks."""
        self._write_file("lib.cyd", "[[// Lib]]")
        filepath = self._write_file("main.cyd", """[[
// Start of code block
INCLUDE "lib.cyd"
// End of code block
]]""")
        
        result, _ = self.preprocessor.preprocess(filepath)
        self.assertIn('// Lib', result)
    
    def test_include_on_same_line_as_code_delimiter(self):
        """Test INCLUDE on same line as opening delimiter."""
        self._write_file("lib.cyd", "[[// Lib]]")
        filepath = self._write_file("main.cyd", '[[ INCLUDE "lib.cyd" ]]')
        
        result, _ = self.preprocessor.preprocess(filepath)
        self.assertIn('// Lib', result)


if __name__ == '__main__':
    unittest.main()
