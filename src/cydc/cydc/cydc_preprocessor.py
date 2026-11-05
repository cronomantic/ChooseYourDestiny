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
    path: str = None  # absolute path of the file (filename is its basename)


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


class MaxPreprocessorErrorsReached(Exception):
    """Internal exception to stop preprocessing when error cap is reached."""
    pass


def find_cyd_home(start=None):
    """The CYD installation folder (CYD_HOME), whose lib/ INCLUDE LIB looks in:
    the CYD_HOME environment variable if set, else the first folder up from
    this module's that holds lib/ and version.txt (the repo's src/cydc/cydc/
    and the distribution's dist/cydc/ are at different depths). None if there
    is none."""
    env = os.environ.get("CYD_HOME")
    if env:
        return os.path.abspath(env)
    d = os.path.abspath(start or os.path.dirname(__file__))
    while True:
        if os.path.isdir(os.path.join(d, "lib")) and os.path.isfile(os.path.join(d, "version.txt")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


class CydcPreprocessor:
    """Preprocessor for CYD source files that handles INCLUDE directives."""
    
    # Pattern to match INCLUDE directives with quoted filenames
    # Supports: INCLUDE "filename.cyd" and INCLUDE LIB "filename.cyd"
    # (case-insensitive). Group 1 is "LIB" or None, group 2 the path, group 3
    # the "]]" that may close the code block on the same line and group 4 what
    # follows it (text, or more code after a "[["). One INCLUDE per line.
    # Can be followed by optional comments
    # Note: This will match INCLUDE anywhere on the line, not just at the start
    INCLUDE_PATTERN = re.compile(
        r'INCLUDE\s+(?:(LIB)\s+)?["\']([^"\']+)["\'][ \t]*(?://.*|(\]\])(.*))?$',
        re.IGNORECASE | re.MULTILINE
    )
    
    # Pattern to match code block delimiters
    CODE_OPEN = re.compile(r'\[\[')
    CODE_CLOSE = re.compile(r'\]\]')
    
    def __init__(self, max_depth: int = 20, base_path: str = None, max_errors: int = 20,
                 project_root: str = None, include_paths=None, lib_paths=None):
        # project_root: INCLUDE "x" not found next to its file is looked for
        #   here (default: the main file's folder).
        # include_paths: more folders for INCLUDE "x", after the project root.
        # lib_paths: the folders INCLUDE LIB "x" looks in, in order (the
        #   user's ones, then CYD_HOME/lib).
        """
        Initialize the preprocessor.
        
        Args:
            max_depth: Maximum nesting depth for includes (default: 20)
            base_path: Base directory for resolving relative includes
        """
        self.max_depth = max_depth
        self.max_errors = max(1, int(max_errors))
        self.max_errors_reached = False
        self.base_path = base_path
        self.project_root = project_root
        self.include_paths = [os.path.abspath(d) for d in (include_paths or ())]
        self.lib_paths = [os.path.abspath(d) for d in (lib_paths or ())]
        self._root = None  # the project root in use, set by preprocess()
        self.included_files: Set[str] = set()
        # Where each file was first included ("main.cyd:3"; None for the main
        # file), and the files being processed right now (the include chain):
        # a file in the chain is a cycle; one already included, a repetition.
        self._included_from: Dict[str, str] = {}
        self._include_stack: List[str] = []
        # How each file was included: "lib" (INCLUDE LIB) or "plain".
        self._included_kind: Dict[str, str] = {}
        self.errors: List[PreprocessorError] = []
        self.line_map: Dict[int, SourceLocation] = {}  # Maps output line -> original source location
        self._output_line_num = 1  # Track current output line number

    def _append_error(self, error: PreprocessorError):
        if len(self.errors) >= self.max_errors:
            self.max_errors_reached = True
            raise MaxPreprocessorErrorsReached()
        self.errors.append(error)
        if len(self.errors) >= self.max_errors:
            self.max_errors_reached = True
            raise MaxPreprocessorErrorsReached()
        
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
    
    def _search_dirs(self, current_dir, is_lib):
        """The folders a relative INCLUDE (or INCLUDE LIB) looks in, in order."""
        if is_lib:
            return list(self.lib_paths)
        dirs = [current_dir]
        if self._root:
            dirs.append(self._root)
        return dirs + self.include_paths

    def _resolve_include(self, include_file, current_dir, is_lib):
        """The path of an included file: INCLUDE "x" next to the file with
        the INCLUDE, then in the project root, then in the include paths;
        INCLUDE LIB "x" in the library paths. An absolute path as it is.
        Raises PreprocessorError if it is nowhere."""
        if os.path.isabs(include_file):
            return include_file
        seen = []
        for d in self._search_dirs(current_dir, is_lib):
            if d in seen:
                continue
            seen.append(d)
            candidate = os.path.join(d, include_file)
            if os.path.isfile(candidate):
                return candidate
        if is_lib and not seen:
            raise PreprocessorError(
                f"Library file not found: {include_file} (there are no library folders)",
                include_file,
            )
        what = "Library file" if is_lib else "Include file"
        hint = ""
        if not is_lib:
            # A game from an older version: INCLUDE "lib/x.cyd" or
            # "../../lib/x.cyd" for a library that INCLUDE LIB finds.
            base = os.path.basename(include_file)
            if any(os.path.isfile(os.path.join(d, base)) for d in self.lib_paths):
                hint = f'. Did you mean INCLUDE LIB "{base}"?'
        raise PreprocessorError(
            f"{what} not found: {include_file} (searched in: {', '.join(seen)}){hint}",
            include_file,
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
        parent_file: str = None,
        included_from: str = None,
        kind: str = "plain",
    ) -> List[Tuple[str, SourceLocation]]:
        """
        Recursively process a file and its includes.
        
        Args:
            filepath: Path to the file to process
            depth: Current nesting depth
            parent_file: Path to the parent file (for relative includes)
            included_from: "file.cyd:line" of the INCLUDE (None for the main file)
            kind: "lib" for INCLUDE LIB, "plain" otherwise

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
        
        # A file in the current include chain includes itself: a cycle. One
        # included before through another chain is a repetition, not a cycle.
        if normalized_path in self._include_stack:
            raise PreprocessorError(
                f"Circular include detected: {filepath}",
                normalized_path
            )
        if normalized_path in self.included_files:
            # Never the main file: it stays in the chain until the end. (A
            # library included again with INCLUDE LIB never gets here: it is
            # skipped where the INCLUDE is.)
            first = self._included_from[normalized_path]
            if kind == "lib" and self._included_kind.get(normalized_path) == "plain":
                message = f"File already included as a normal file from {first}: {filepath}"
            else:
                message = f"File already included from {first}: {filepath}"
            raise PreprocessorError(message, normalized_path)

        # Mark file as included
        self.included_files.add(normalized_path)
        self._included_from[normalized_path] = included_from
        self._included_kind[normalized_path] = kind

        # Get display name (basename for cleaner error messages)
        display_name = os.path.basename(normalized_path)
        
        # Process the file line by line
        self._include_stack.append(normalized_path)
        try:
            return self._process_lines(content, normalized_path, display_name, depth)
        finally:
            self._include_stack.pop()

    def _process_lines(self, content, normalized_path, display_name, depth):
        """The lines of a file being processed, its includes expanded."""
        current_dir = os.path.dirname(normalized_path)
        result_lines = []
        lines = content.splitlines(keepends=True)
        
        for line_num, line in enumerate(lines, start=1):
            # Check if this line contains an include directive
            match = self.INCLUDE_PATTERN.search(line)
            
            if match:
                # Validate that INCLUDE is inside a code block
                if not self._is_include_in_code_block(lines, line_num - 1, match):
                    self._append_error(
                        PreprocessorError(
                            f"INCLUDE directive must be inside [[ ]] code blocks",
                            normalized_path,
                            line_num,
                        )
                    )
                    continue
                
                is_lib = match.group(1) is not None
                include_file = match.group(2)
                kind = "lib" if is_lib else "plain"
                here = SourceLocation(display_name, line_num, normalized_path)
                # What the line has around the INCLUDE stays: before it (say
                # "[[ " or text and "[["), and the "]]" that may close the
                # block after it with what follows, and the line's newline.
                before = line[:match.start()]
                close = "]]" + (match.group(4) or "") if match.group(3) else ""
                newline = "\n" if line.endswith("\n") else ""

                try:
                    include_path = self._resolve_include(include_file, current_dir, is_lib)
                    # A library already included with INCLUDE LIB: once is
                    # enough (a real cycle still goes on to be reported).
                    resolved = os.path.normpath(include_path)
                    if (is_lib and self._included_kind.get(resolved) == "lib"
                            and resolved not in self._include_stack):
                        result_lines.append((f"{before}/* INCLUDE LIB {include_file}: already included */"
                                             f"{close}{newline}", here))
                        continue

                    # Recursively process the included file
                    included_content = list(self._process_file(
                        include_path,
                        depth + 1,
                        normalized_path,
                        f"{display_name}:{line_num}",
                        kind,
                    ))

                    # The markers are comments in code, so they compile to
                    # nothing. The included file starts and ends outside code:
                    # its first line gets the "]]" that closes this block and
                    # its last one the "[[" that reopens it, so no newline is
                    # left between them to become text of the game.
                    result_lines.append((
                        f"{before}/* BEGIN INCLUDE: {include_file} (from {display_name}:{line_num}) */\n",
                        here))
                    if included_content:
                        text, loc = included_content[0]
                        included_content[0] = ("]]" + text, loc)
                        text, loc = included_content[-1]
                        if text.endswith("\n"):
                            included_content[-1] = (text[:-1] + "[[\n", loc)
                        else:
                            included_content[-1] = (text + "[[", loc)
                    result_lines.extend(included_content)
                    result_lines.append((f"/* END INCLUDE: {include_file} */{close}{newline}", here))

                except PreprocessorError as e:
                    # Add context about where the include was found
                    self._append_error(
                        PreprocessorError(
                            f"In file included from {display_name}:{line_num}: {e.message}",
                            e.filename,
                            e.line_num,
                        )
                    )
                    continue
            else:
                # Regular line, add it with its source location
                result_lines.append((line, SourceLocation(display_name, line_num, normalized_path)))
        
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
        self._included_from.clear()
        self._include_stack.clear()
        self._included_kind.clear()
        root = self.project_root or os.path.dirname(self._normalize_path(filepath))
        self._root = os.path.abspath(root)
        self.errors.clear()
        self.max_errors_reached = False
        self.line_map.clear()
        self._output_line_num = 1
        
        # Update base path if not set
        if self.base_path is None:
            self.base_path = os.path.dirname(os.path.abspath(filepath))
        
        fatal_error = None
        try:
            # Process the main file - returns list of (line, source_location) tuples
            processed_lines_with_locs = self._process_file(filepath)
        except MaxPreprocessorErrorsReached:
            processed_lines_with_locs = []
        except PreprocessorError as e:
            fatal_error = e
            if len(self.errors) == 0:
                self.errors.append(e)

        if len(self.errors) > 0 or fatal_error is not None:
            if len(self.errors) > self.max_errors:
                self.errors = self.errors[: self.max_errors]
                self.max_errors_reached = True
            raise self.errors[0] if len(self.errors) > 0 else fatal_error

        # Build the output and line map
        output_lines = []
        # A piece that doesn't end in a newline (the last line of an included
        # file) shares its output line with the next piece, which must not
        # count as a line of its own or everything after it maps one line early.
        at_line_start = True
        for line_content, source_loc in processed_lines_with_locs:
            if at_line_start:
                self.line_map[self._output_line_num] = source_loc
            output_lines.append(line_content)

            # Lines inside multi-line content map to the same source.
            newline_count = line_content.count('\n')
            for i in range(newline_count):
                self._output_line_num += 1
                if i < newline_count - 1:
                    self.line_map[self._output_line_num] = source_loc
            if newline_count:
                at_line_start = line_content.endswith('\n')
            elif line_content:
                at_line_start = False

        # Join all lines into a single string
        result = ''.join(output_lines)

        return result, self.line_map.copy()

    
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

