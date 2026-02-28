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
from typing import List, Set, Tuple


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
    INCLUDE_PATTERN = re.compile(
        r'^\s*INCLUDE\s+["\']([^"\']+)["\']\s*(?://.*)?$',
        re.IGNORECASE | re.MULTILINE
    )

    # Pattern to match [[INCLUDE "filename.cyd"]] on its own line
    # This form inlines the file content directly (without [[ ]] wrappers)
    CODE_INCLUDE_PATTERN = re.compile(
        r'^\s*\[\[\s*INCLUDE\s+["\']([^"\']+)["\']\s*\]\]\s*$',
        re.IGNORECASE
    )
    
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
    
    def _process_file(
        self, 
        filepath: str, 
        depth: int = 0,
        parent_file: str = None
    ) -> List[str]:
        """
        Recursively process a file and its includes.
        
        Args:
            filepath: Path to the file to process
            depth: Current nesting depth
            parent_file: Path to the parent file (for relative includes)
            
        Returns:
            List of processed lines
            
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
        
        # Process the file line by line
        result_lines = []
        lines = content.splitlines(keepends=True)
        
        for line_num, line in enumerate(lines, start=1):
            # Check if this line is an include directive
            match = self.INCLUDE_PATTERN.match(line)
            if not match:
                match = self.CODE_INCLUDE_PATTERN.match(line)
            
            if match:
                include_file = match.group(1)
                
                # Resolve the include path relative to current file's directory
                if not os.path.isabs(include_file):
                    include_path = os.path.join(current_dir, include_file)
                else:
                    include_path = include_file
                
                try:
                    # Add a comment marker for debugging/tracing
                    result_lines.append(
                        f"// BEGIN INCLUDE: {include_file} (from {os.path.basename(normalized_path)}:{line_num})\n"
                    )
                    
                    # Recursively process the included file
                    included_content = self._process_file(
                        include_path,
                        depth + 1,
                        normalized_path
                    )
                    
                    result_lines.extend(included_content)
                    
                    # Add end marker
                    result_lines.append(
                        f"// END INCLUDE: {include_file}\n"
                    )
                    
                except PreprocessorError as e:
                    # Add context about where the include was found
                    raise PreprocessorError(
                        f"In file included from {os.path.basename(normalized_path)}:{line_num}: {e.message}",
                        e.filename,
                        e.line_num
                    )
            else:
                # Regular line, just add it
                result_lines.append(line)
        
        return result_lines
    
    def preprocess(self, filepath: str) -> str:
        """
        Preprocess a source file, expanding all includes.
        
        Args:
            filepath: Path to the main source file
            
        Returns:
            Preprocessed source code as a string
            
        Raises:
            PreprocessorError: If preprocessing fails
        """
        # Reset state
        self.included_files.clear()
        self.errors.clear()
        
        # Update base path if not set
        if self.base_path is None:
            self.base_path = os.path.dirname(os.path.abspath(filepath))
        
        try:
            # Process the main file
            processed_lines = self._process_file(filepath)
            
            # Join all lines into a single string
            return ''.join(processed_lines)
            
        except PreprocessorError as e:
            self.errors.append(e)
            raise
    
    def preprocess_string(self, content: str, base_path: str = None) -> str:
        """
        Preprocess source code from a string.
        
        Args:
            content: Source code content
            base_path: Base directory for resolving includes
            
        Returns:
            Preprocessed source code
            
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
            result = self.preprocess(temp_path)
            
            return result
            
        finally:
            # Clean up temp file
            try:
                os.unlink(temp_path)
            except:
                pass


def preprocess_file(filepath: str, max_depth: int = 20) -> str:
    """
    Convenience function to preprocess a single file.
    
    Args:
        filepath: Path to the source file
        max_depth: Maximum include nesting depth
        
    Returns:
        Preprocessed source code
        
    Raises:
        PreprocessorError: If preprocessing fails
    """
    preprocessor = CydcPreprocessor(max_depth=max_depth)
    return preprocessor.preprocess(filepath)
