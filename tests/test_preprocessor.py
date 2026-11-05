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

    def test_repeated_include_is_not_circular(self):
        """The same file included through two branches (a diamond: main ->
        a -> c, main -> b -> c) is a repetition, not a cycle: the error says
        where it was included first."""
        self._write_file("c.cyd", '[[\nCONST K = 1\n]]')
        self._write_file("a.cyd", '[[\nINCLUDE "c.cyd"\n]]')
        self._write_file("b.cyd", '[[\nINCLUDE "c.cyd"\n]]')
        filepath = self._write_file("main.cyd", '[[\nINCLUDE "a.cyd"\nINCLUDE "b.cyd"\n]]')

        with self.assertRaises(PreprocessorError) as context:
            self.preprocessor.preprocess(filepath)

        message = str(context.exception)
        self.assertNotIn("Circular include", message)
        self.assertIn("already included from a.cyd:2", message)

    def test_same_file_twice_from_one_file(self):
        """Two INCLUDEs of the same file in one file: also a repetition."""
        self._write_file("c.cyd", '[[\nCONST K = 1\n]]')
        filepath = self._write_file("main.cyd", '[[\nINCLUDE "c.cyd"\nINCLUDE "c.cyd"\n]]')

        with self.assertRaises(PreprocessorError) as context:
            self.preprocessor.preprocess(filepath)

        message = str(context.exception)
        self.assertNotIn("Circular include", message)
        self.assertIn("already included from main.cyd:2", message)

    def test_cycle_through_a_branch_is_circular(self):
        """main -> a -> b -> a is a cycle even after a sibling branch."""
        self._write_file("s.cyd", '[[\nCONST S = 1\n]]')
        self._write_file("a.cyd", '[[\nINCLUDE "b.cyd"\n]]')
        self._write_file("b.cyd", '[[\nINCLUDE "a.cyd"\n]]')
        filepath = self._write_file("main.cyd", '[[\nINCLUDE "s.cyd"\nINCLUDE "a.cyd"\n]]')

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

    def test_line_map_after_include_without_final_newline(self):
        """An included file that doesn't end in a newline shares its last output
        line with the END INCLUDE marker; the lines after it must still map to
        their own source lines."""
        self._write_file("a.cyd", "[[\nINK 1\n]]")
        self._write_file("b.cyd", "[[\nINK 2\nMARK\n]]")
        filepath = self._write_file("main.cyd", '[[\nINCLUDE "a.cyd"\nINCLUDE "b.cyd"\n]]')

        result, line_map = self.preprocessor.preprocess(filepath)
        out_line = result.splitlines().index("MARK") + 1
        self.assertEqual(line_map[out_line].filename, "b.cyd")
        self.assertEqual(line_map[out_line].line_num, 3)


class TestSearchPaths(unittest.TestCase):
    """INCLUDE "x": next to its file, then the project root, then the include
    paths. INCLUDE LIB "x": only the library paths. A library included again
    with INCLUDE LIB is skipped; any other repetition is an error."""

    def setUp(self):
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir, True)
        self.project = os.path.join(self.test_dir, "proyecto")
        self.libs = os.path.join(self.test_dir, "libs")
        self.extra = os.path.join(self.test_dir, "extra")

    def _write(self, path, content):
        full = os.path.join(self.test_dir, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return full

    def _run(self, main, **kwargs):
        kwargs.setdefault("lib_paths", [self.libs])
        pre = CydcPreprocessor(base_path=os.path.dirname(main), **kwargs)
        return pre.preprocess(main)[0]

    def test_include_falls_back_to_the_project_root(self):
        self._write("proyecto/comun/vars.cyd", "[[\nCONST V = 1\n]]")
        self._write("proyecto/capitulos/cap1.cyd", '[[\nINCLUDE "comun/vars.cyd"\n]]')
        main = self._write("proyecto/main.cyd", '[[\nINCLUDE "capitulos/cap1.cyd"\n]]')
        self.assertIn("CONST V = 1", self._run(main))

    def test_next_to_the_file_wins_over_the_root(self):
        self._write("proyecto/x.cyd", "[[\nCONST RAIZ = 1\n]]")
        self._write("proyecto/sub/x.cyd", "[[\nCONST JUNTO = 1\n]]")
        self._write("proyecto/sub/a.cyd", '[[\nINCLUDE "x.cyd"\n]]')
        main = self._write("proyecto/main.cyd", '[[\nINCLUDE "sub/a.cyd"\n]]')
        out = self._run(main)
        self.assertIn("JUNTO", out)
        self.assertNotIn("RAIZ", out)

    def test_include_paths_after_the_root(self):
        self._write("extra/util.cyd", "[[\nCONST U = 1\n]]")
        main = self._write("proyecto/main.cyd", '[[\nINCLUDE "util.cyd"\n]]')
        self.assertIn("CONST U = 1", self._run(main, include_paths=[self.extra]))
        with self.assertRaises(PreprocessorError) as ctx:
            self._run(main)
        self.assertIn("Include file not found: util.cyd", str(ctx.exception))

    def test_project_root_can_be_given(self):
        self._write("proyecto/comun.cyd", "[[\nCONST C = 1\n]]")
        main = self._write("proyecto/src/main.cyd", '[[\nINCLUDE "comun.cyd"\n]]')
        self.assertIn("CONST C = 1", self._run(main, project_root=self.project))

    def test_include_lib(self):
        self._write("libs/strings.cyd", "[[\nCONST S = 1\n]]")
        main = self._write("proyecto/main.cyd", '[[\ninclude lib "strings.cyd"\n]]')
        self.assertIn("CONST S = 1", self._run(main))

    def test_include_lib_only_in_library_paths(self):
        self._write("proyecto/strings.cyd", "[[\nCONST PROPIO = 1\n]]")
        main = self._write("proyecto/main.cyd", '[[\nINCLUDE LIB "strings.cyd"\n]]')
        with self.assertRaises(PreprocessorError) as ctx:
            self._run(main)
        self.assertIn("Library file not found: strings.cyd", str(ctx.exception))

    def test_old_library_include_suggests_include_lib(self):
        self._write("libs/strings.cyd", "[[\nCONST S = 1\n]]")
        main = self._write("proyecto/main.cyd", '[[\nINCLUDE "lib/strings.cyd"\n]]')
        with self.assertRaises(PreprocessorError) as ctx:
            self._run(main)
        self.assertIn('Did you mean INCLUDE LIB "strings.cyd"?', str(ctx.exception))

    def test_library_paths_in_order(self):
        self._write("extra/strings.cyd", "[[\nCONST PRIMERO = 1\n]]")
        self._write("libs/strings.cyd", "[[\nCONST SEGUNDO = 1\n]]")
        main = self._write("proyecto/main.cyd", '[[\nINCLUDE LIB "strings.cyd"\n]]')
        out = self._run(main, lib_paths=[self.extra, self.libs])
        self.assertIn("PRIMERO", out)
        self.assertNotIn("SEGUNDO", out)

    def test_library_twice_is_included_once(self):
        self._write("libs/strings.cyd", "[[\nCONST S = 1\n]]")
        self._write("proyecto/a.cyd", '[[\nINCLUDE LIB "strings.cyd"\n]]')
        main = self._write("proyecto/main.cyd",
                           '[[\nINCLUDE LIB "strings.cyd"\nINCLUDE "a.cyd"\n]]')
        self.assertEqual(self._run(main).count("CONST S = 1"), 1)

    def test_library_then_plain_is_an_error(self):
        self._write("libs/strings.cyd", "[[\nCONST S = 1\n]]")
        main = self._write("proyecto/main.cyd",
                           '[[\nINCLUDE LIB "strings.cyd"\nINCLUDE "../libs/strings.cyd"\n]]')
        with self.assertRaises(PreprocessorError) as ctx:
            self._run(main)
        self.assertIn("File already included from main.cyd:2", str(ctx.exception))

    def test_plain_then_library_is_an_error(self):
        self._write("libs/strings.cyd", "[[\nCONST S = 1\n]]")
        main = self._write("proyecto/main.cyd",
                           '[[\nINCLUDE "../libs/strings.cyd"\nINCLUDE LIB "strings.cyd"\n]]')
        with self.assertRaises(PreprocessorError) as ctx:
            self._run(main)
        self.assertIn("already included as a normal file from main.cyd:2", str(ctx.exception))

    def test_cycle_between_libraries_is_circular(self):
        self._write("libs/a.cyd", '[[\nINCLUDE LIB "b.cyd"\n]]')
        self._write("libs/b.cyd", '[[\nINCLUDE LIB "a.cyd"\n]]')
        main = self._write("proyecto/main.cyd", '[[\nINCLUDE LIB "a.cyd"\n]]')
        with self.assertRaises(PreprocessorError) as ctx:
            self._run(main)
        self.assertIn("Circular include", str(ctx.exception))


class TestIncludeLeavesNoText(unittest.TestCase):
    """What the preprocessor adds around an included file compiles to nothing:
    its markers used to end up outside [[ ]], as text of the game. And an
    INCLUDE can share its line with [[ and ]], as the manual shows it."""

    def setUp(self):
        self.test_dir = os.path.realpath(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.test_dir, True)

    def _write(self, name, content):
        path = os.path.join(self.test_dir, name)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def _texts(self, main, **kwargs):
        from cydc_lexer import CydcLexer
        text, line_map = CydcPreprocessor(**kwargs).preprocess(main)
        lexer = CydcLexer()
        lexer.build()
        lexer.input(text)
        return [t.value[1] for t in iter(lexer.token, None) if t.type == "TEXT"], line_map, text

    def test_include_on_its_own_line(self):
        self._write("inc.cyd", "[[\nCONST K = 1\n]]")
        main = self._write("main.cyd", 'Hola\n[[\nINCLUDE "inc.cyd"\n]]Adios[[ WAITKEY ]]')
        texts, _, _ = self._texts(main)
        self.assertEqual(texts, ["Hola\r", "Adios"])

    def test_text_of_the_included_file_stays(self):
        self._write("inc.cyd", "Dentro\n[[ CONST K = 1 ]]")
        main = self._write("main.cyd", '[[\nINCLUDE "inc.cyd"\n]]Fuera')
        texts, _, _ = self._texts(main)
        self.assertEqual(texts, ["Dentro\r", "Fuera"])

    def test_include_on_one_line_with_the_brackets(self):
        self._write("cap/cap1.cyd", "[[\nCONST K = 1\n]]Cap1")
        main = self._write("main.cyd", 'Hola [[ INCLUDE "cap/cap1.cyd" ]]Sigue')
        texts, _, _ = self._texts(main)
        self.assertEqual(texts, ["Hola ", "Cap1", "Sigue"])

    def test_library_already_included_on_one_line(self):
        libs = os.path.join(self.test_dir, "libs")
        self._write("libs/l.cyd", "[[\nCONST L = 1\n]]")
        main = self._write("main.cyd",
                           '[[ INCLUDE LIB "l.cyd" ]]A\n[[ INCLUDE LIB "l.cyd" ]]B')
        texts, _, out = self._texts(main, lib_paths=[libs])
        self.assertEqual(texts, ["A\r", "B"])
        self.assertEqual(out.count("CONST L = 1"), 1)

    def test_lines_still_map_to_their_files(self):
        self._write("inc.cyd", "PRIMERA\nSEGUNDA")
        main = self._write("main.cyd", 'x\n[[ INCLUDE "inc.cyd" ]]\nDESPUES')
        _, line_map, out = self._texts(main)
        lines = out.split("\n")
        where = {word: line_map[i + 1] for i, l in enumerate(lines)
                 for word in ("PRIMERA", "SEGUNDA", "DESPUES") if word in l}
        self.assertEqual((where["PRIMERA"].filename, where["PRIMERA"].line_num), ("inc.cyd", 1))
        self.assertEqual((where["SEGUNDA"].filename, where["SEGUNDA"].line_num), ("inc.cyd", 2))
        self.assertEqual((where["DESPUES"].filename, where["DESPUES"].line_num), ("main.cyd", 3))


class TestFindCydHome(unittest.TestCase):
    """CYD_HOME: the environment variable, else the first folder up that holds
    lib/ and version.txt."""

    def test_environment_variable(self):
        from unittest import mock
        import cydc_preprocessor
        with mock.patch.dict(os.environ, {"CYD_HOME": "/donde/sea"}):
            self.assertEqual(cydc_preprocessor.find_cyd_home(), os.path.abspath("/donde/sea"))

    def test_found_from_the_repository_source(self):
        from unittest import mock
        import cydc_preprocessor
        repo = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
        env = {k: v for k, v in os.environ.items() if k != "CYD_HOME"}
        with mock.patch.dict(os.environ, env, clear=True):
            for start in (os.path.join(repo, "src", "cydc", "cydc"), os.path.join(repo, "dist", "cydc")):
                self.assertEqual(os.path.realpath(cydc_preprocessor.find_cyd_home(start)), repo)


if __name__ == '__main__':
    unittest.main()
