# -- coding: utf-8 -*-
#
# Choose Your Destiny.
#
# Copyright (C) 2025 Sergio Chico <cronomantic@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import re
from typing import List, Set, Tuple, Dict, NamedTuple


class SourceLocation(NamedTuple):
    """Tracks the original source location of a line."""
    filename: str
    line_num: int


class PreprocessorError(Exception):
    """Exception raised for errors during preprocessing."""
    def __init__(self, message: str, filename: str = None, line_num: int = None):
        self.message = message
        self.filename = filename
        self.line_num = line_num
        super().__init__(self._format_message())
    
    def _format_message(self) -> str:
        if self.filename and self.line_num:
            return f"{self.filename}:{self.line_num}: {self.message}"
        elif self.filename:
            return f"{self.filename}: {self.message}"
        else:
            return self.message


class CydcPreprocessor:
    """Preprocessor for CYD source files that handles INCLUDE directives."""
    
    # Pattern to match INCLUDE directives with quoted filenames
    # Supports: INCLUDE "filename.cyd" (case-insensitive)
    # Can be followed by optional comments
    # Note: This will match INCLUDE anywhere on the line, not just at the start
    INCLUDE_PATTERN = re.compile(
        r'INCLUDE\s+["\']([^"\']+)["\']\s*(?://.*)?(?:\]\])?$',
        re.IGNORECASE | re.MULTILINE
    )
    
    # Pattern to match code block delimiters
    CODE_OPEN = re.compile(r'\[\[')
    CODE_CLOSE = re.compile(r'\]\]')
    
    def __init__(self, max_depth: int = 20, base_path: str = None):
        """
        Initialize the preprocessor.
        
        Args:
            max_depth: Maximum nesting depth for includes (default: 20)
            base_path: Base directory for resolving relative includes
        """
        self.max_depth = max_depth
        self.base_path = base_path
        self.included_files: Set[str] = set()
        self.errors: List[PreprocessorError] = []
        self.line_map: Dict[int, SourceLocation] = {}  # Maps output line -> original source location
        self._output_line_num = 1  # Track current output line number
        
    def _normalize_path(self, filepath: str) -> str:
        """
        Normalize a file path to absolute path.
        
        Args:
            filepath: The file path to normalize
            
        Returns:
            Absolute normalized path
        """
        if os.path.isabs(filepath):
            return os.path.normpath(filepath)
        
        if self.base_path:
            return os.path.normpath(os.path.join(self.base_path, filepath))
        
        return os.path.normpath(os.path.abspath(filepath))
    
    def _read_file(self, filepath: str) -> Tuple[str, str]:
        """
        Read a source file.
        
        Args:
            filepath: Path to the file to read
            
        Returns:
            Tuple of (file content, normalized path)
            
        Raises:
            PreprocessorError: If file cannot be read
        """
        normalized_path = self._normalize_path(filepath)
        
        try:
            with open(normalized_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content, normalized_path
        except FileNotFoundError:
            raise PreprocessorError(
                f"Include file not found: {filepath}",
                filepath
            )
        except IOError as e:
            raise PreprocessorError(
                f"Error reading file: {str(e)}",
                filepath
            )
    
    def _is_include_in_code_block(self, lines: List[str], line_idx: int, include_match) -> bool:
        """
        Check if an INCLUDE directive at the given line is inside a code block [[ ]].
        
        Args:
            lines: All lines in the file
            line_idx: Index of the line to check (0-based)
            include_match: The regex match object for the INCLUDE directive
            
        Returns:
            True if the INCLUDE is inside a code block, False otherwise
        """
        line = lines[line_idx]
        include_pos = include_match.start()
        
        # Count [[ and ]] on this line before the INCLUDE
        line_before_include = line[:include_pos]
        
        # Count opening and closing brackets on this line before INCLUDE
        opens_before = len(self.CODE_OPEN.findall(line_before_include))
        closes_before = len(self.CODE_CLOSE.findall(line_before_include))
        
        # Track nesting level from start of file
        nesting_level = 0
        
        # Process all lines before this one
        for i in range(line_idx):
            opens = len(self.CODE_OPEN.findall(lines[i]))
            closes = len(self.CODE_CLOSE.findall(lines[i]))
            nesting_level += opens - closes
        
        # Add the brackets before INCLUDE on current line
        nesting_level += opens_before - closes_before
        
        # INCLUDE is valid if we're inside a code block (nesting_level > 0)
        return nesting_level > 0
    
    def _process_file(
        self, 
        filepath: str, 
        depth: int = 0,
        parent_file: str = None
    ) -> List[Tuple[str, SourceLocation]]:
        """
        Recursively process a file and its includes.
        
        Args:
            filepath: Path to the file to process
            depth: Current nesting depth
            parent_file: Path to the parent file (for relative includes)
            
        Returns:
            List of tuples (line_content, source_location)
            
        Raises:
            PreprocessorError: If processing fails
        """
        # Check recursion depth
        if depth > self.max_depth:
            raise PreprocessorError(
                f"Maximum include depth ({self.max_depth}) exceeded",
                filepath
            )
        
        # Read the file
        content, normalized_path = self._read_file(filepath)
        
        # Check for circular includes
        if normalized_path in self.included_files:
            raise PreprocessorError(
                f"Circular include detected: {filepath}",
                normalized_path
            )
        
        # Mark file as included
        self.included_files.add(normalized_path)
        
        # Get directory of current file for resolving relative includes
        current_dir = os.path.dirname(normalized_path)
        
        # Get display name (basename for cleaner error messages)
        display_name = os.path.basename(normalized_path)
        
        # Process the file line by line
        result_lines = []
        lines = content.splitlines(keepends=True)
        
        for line_num, line in enumerate(lines, start=1):
            # Check if this line contains an include directive
            match = self.INCLUDE_PATTERN.search(line)
            
            if match:
                # Validate that INCLUDE is inside a code block
                if not self._is_include_in_code_block(lines, line_num - 1, match):
                    raise PreprocessorError(
                        f"INCLUDE directive must be inside [[ ]] code blocks",
                        normalized_path,
                        line_num
                    )
                
                include_file = match.group(1)
                
                # Resolve the include path relative to current file's directory
                if not os.path.isabs(include_file):
                    include_path = os.path.join(current_dir, include_file)
                else:
                    include_path = include_file
                
                try:
                    # Extract the part of the line before and after the INCLUDE directive
                    line_before = line[:match.start()]
                    line_after = line[match.end():]
                    
                    # Check if we're inside a code block (we validated this above)
                    # We need to close the block before including, then reopen it after
                    # to prevent nested [[ ]] blocks
                    
                    # Close the current code block before the include
                    result_lines.append(("]] /* Close block for INCLUDE */\n", SourceLocation(display_name, line_num)))
                    
                    # Add a comment marker for debugging/tracing
                    marker_line = f"/* BEGIN INCLUDE: {include_file} (from {display_name}:{line_num}) */\n"
                    result_lines.append((marker_line, SourceLocation(display_name, line_num)))
                    
                    # Recursively process the included file
                    included_content = self._process_file(
                        include_path,
                        depth + 1,
                        normalized_path
                    )
                    
                    result_lines.extend(included_content)
                    
                    # Add end marker
                    end_marker = f"/* END INCLUDE: {include_file} */\n"
                    result_lines.append((end_marker, SourceLocation(display_name, line_num)))
                    
                    # Reopen the code block after the include
                    result_lines.append(("[[ /* Reopen block after INCLUDE */\n", SourceLocation(display_name, line_num)))
                    
                except PreprocessorError as e:
                    # Add context about where the include was found
                    raise PreprocessorError(
                        f"In file included from {display_name}:{line_num}: {e.message}",
                        e.filename,
                        e.line_num
                    )
            else:
                # Regular line, add it with its source location
                result_lines.append((line, SourceLocation(display_name, line_num)))
        
        return result_lines
    
    def preprocess(self, filepath: str) -> Tuple[str, Dict[int, SourceLocation]]:
        """
        Preprocess a source file, expanding all includes.
        
        Args:
            filepath: Path to the main source file
            
        Returns:
            Tuple of (preprocessed source code, line mapping dict)
            line_map maps output line numbers (1-based) to SourceLocation
            
        Raises:
            PreprocessorError: If preprocessing fails
        """
        # Reset state
        self.included_files.clear()
        self.errors.clear()
        self.line_map.clear()
        self._output_line_num = 1
        
        # Update base path if not set
        if self.base_path is None:
            self.base_path = os.path.dirname(os.path.abspath(filepath))
        
        try:
            # Process the main file - returns list of (line, source_location) tuples
            processed_lines_with_locs = self._process_file(filepath)
            
            # Build the output and line map
            output_lines = []
            for line_content, source_loc in processed_lines_with_locs:
                # Record the mapping for this line
                self.line_map[self._output_line_num] = source_loc
                output_lines.append(line_content)
                
                # Count newlines in this content to track output line number
                # (some content might have multiple lines)
                newline_count = line_content.count('\n')
                if newline_count > 0:
                    # For multi-line content, map all lines to same source
                    for i in range(1, newline_count):
                        self._output_line_num += 1
                        self.line_map[self._output_line_num] = source_loc
                    self._output_line_num += 1
                elif line_content:  # Non-empty content without newline
                    self._output_line_num += 1
            
            # Join all lines into a single string
            result = ''.join(output_lines)
            
            return result, self.line_map.copy()
            
        except PreprocessorError as e:
            self.errors.append(e)
            raise
    
    def get_source_location(self, line_num: int) -> SourceLocation:
        """
        Get the original source location for a line in the preprocessed output.
        
        Args:
            line_num: Line number in preprocessed output (1-based)
            
        Returns:
            SourceLocation with original filename and line number,
            or None if not found
        """
        return self.line_map.get(line_num)
    
    def preprocess_string(self, content: str, base_path: str = None) -> Tuple[str, Dict[int, SourceLocation]]:
        """
        Preprocess source code from a string.
        
        Args:
            content: Source code content
            base_path: Base directory for resolving includes
            
        Returns:
            Tuple of (preprocessed source code, line mapping dict)
            
        Raises:
            PreprocessorError: If preprocessing fails
        """
        # Save to a temporary location and process
        import tempfile
        
        # Use provided base_path or current directory
        if base_path:
            temp_dir = base_path
        else:
            temp_dir = self.base_path or os.getcwd()
        
        # Create a temporary file
        temp_fd, temp_path = tempfile.mkstemp(
            suffix='.cyd',
            dir=temp_dir,
            text=True
        )
        
        try:
            # Write content to temp file
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Process the temp file
            result, line_map = self.preprocess(temp_path)
            
            return result, line_map
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass


def preprocess_file(filepath: str, max_depth: int = 20) -> Tuple[str, Dict[int, SourceLocation]]:
    """
    Convenience function to preprocess a single file.
    
    Args:
        filepath: Path to the source file
        max_depth: Maximum include nesting depth
        
    Returns:
        Tuple of (preprocessed source code, line mapping dict)
        
    Raises:
        PreprocessorError: If preprocessing fails
    """
    preprocessor = CydcPreprocessor(max_depth=max_depth)
    return preprocessor.preprocess(filepath)

