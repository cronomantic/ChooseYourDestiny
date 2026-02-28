"""
Regression tests for example programs in the examples/ directory.

This module tests that each example program in the examples/ folder
parses successfully through the full preprocessor + parser pipeline.
"""

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "cydc" / "cydc"))

from cydc_preprocessor import CydcPreprocessor
from cydc_parser import CydcParser

# Path to examples directory
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def _parse_example(filepath):
    """
    Run a CYD example file through the preprocessor and parser.

    Returns (parsed_result, errors) tuple.
    """
    pp = CydcPreprocessor()
    preprocessed = pp.preprocess(str(filepath))

    parser = CydcParser(strict_colon_mode=False)
    parser.build()
    parser.errors = []
    result = parser.parse(input=preprocessed)
    return result, parser.errors


class TestExamplesRegression(unittest.TestCase):
    """Regression tests ensuring all example programs parse without errors."""

    def _assert_example_parses(self, example_path):
        """Assert that an example file parses without errors."""
        result, errors = _parse_example(example_path)
        self.assertIsNotNone(result, f"Parser returned None for {example_path}")
        self.assertEqual(
            errors, [], f"Parse errors in {example_path}: {errors[:3]}"
        )

    def test_example_test(self):
        """Test the main test example."""
        self._assert_example_parses(EXAMPLES_DIR / "test" / "test.cyd")

    def test_example_guess_the_number(self):
        """Test the guess-the-number example."""
        self._assert_example_parses(EXAMPLES_DIR / "guess_the_number" / "test.cyd")

    def test_example_input_test(self):
        """Test the keyboard input example."""
        self._assert_example_parses(EXAMPLES_DIR / "input_test" / "test.cyd")

    def test_example_windows(self):
        """Test the windowed display example."""
        self._assert_example_parses(EXAMPLES_DIR / "windows" / "test.cyd")

    def test_example_blit(self):
        """Test the blit graphics example."""
        self._assert_example_parses(EXAMPLES_DIR / "blit" / "test.cyd")

    def test_example_blit_island(self):
        """Test the blit island graphics example."""
        self._assert_example_parses(EXAMPLES_DIR / "blit_island" / "test.cyd")

    def test_example_cyd_presents(self):
        """Test the CYD presents example."""
        self._assert_example_parses(EXAMPLES_DIR / "CYD_presents" / "test.cyd")

    def test_example_etpa_ejemplo(self):
        """Test the ETPA example."""
        self._assert_example_parses(EXAMPLES_DIR / "ETPA_ejemplo" / "test.cyd")

    def test_example_golden_axe(self):
        """Test the Golden Axe character selection example."""
        self._assert_example_parses(
            EXAMPLES_DIR / "Golden_Axe_select_character" / "test.cyd"
        )

    def test_example_rocky_horror_show(self):
        """Test the Rocky Horror Show example."""
        self._assert_example_parses(EXAMPLES_DIR / "Rocky_Horror_Show" / "test.cyd")

    def test_example_scumm_16(self):
        """Test the SCUMM 16 example."""
        self._assert_example_parses(EXAMPLES_DIR / "SCUMM_16" / "test.cyd")

    def test_example_multicolumn_menu(self):
        """Test the multicolumn menu example."""
        self._assert_example_parses(EXAMPLES_DIR / "multicolumn_menu" / "test.cyd")

    def test_example_delerict(self):
        """Test the Delerict adventure example."""
        self._assert_example_parses(EXAMPLES_DIR / "Delerict" / "delerict.cyd")

    def test_example_include_demo(self):
        """Test the include demo multi-file example."""
        self._assert_example_parses(EXAMPLES_DIR / "include_demo" / "main.cyd")


if __name__ == "__main__":
    unittest.main()
