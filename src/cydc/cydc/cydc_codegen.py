# -- coding: utf-8 -*-
#
# Choose Your Destiny.
#
# Copyright (C) 2024 Sergio Chico <cronomantic@gmail.com>
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

import sys
from cydc_font import CydcFont


class CydcCodegen(object):
    BANK_SIZE = 16 * 1024

    opcodes = {
        "END": 0x00,
        "TEXT": 0x01,
        "GOTO": 0x02,
        "GOSUB": 0x03,
        "RETURN": 0x04,
        "MARGINS": 0x05,
        "CENTER": 0x06,
        "AT": 0x07,
        "SET_D": 0x08,
        "SET_I": 0x09,
        "POP_SET": 0x0A,
        "PUSH_D": 0x0B,
        "PUSH_I": 0x0C,
        "IF_GOTO": 0x0D,
        "IF_N_GOTO": 0x0E,
        "PUSH_INKEY": 0x0F,
        "PUSH_RANDOM": 0x10,
        "NOT": 0x11,
        "NOT_B": 0x12,
        "AND": 0x13,
        "OR": 0x14,
        "ADD": 0x15,
        "SUB": 0x16,
        "CP_EQ": 0x17,
        "CP_NE": 0x18,
        "CP_LE": 0x19,
        "CP_ME": 0x1A,
        "CP_LT": 0x1B,
        "CP_MT": 0x1C,
        "INK_D": 0x1D,
        "PAPER_D": 0x1E,
        "BORDER_D": 0x1F,
        "PRINT_D": 0x20,
        "INK_I": 0x21,
        "PAPER_I": 0x22,
        "READ": 0x23,
        "PRINT_I": 0x24,
        "BRIGHT_D": 0x25,
        "FLASH_D": 0x26,
        "RESTORE": 0x27,
        "DATAEND": 0x28,
        "PICTURE_D": 0x29,
        "DISPLAY_D": 0x2A,
        "PICTURE_I": 0x2B,
        "DISPLAY_I": 0x2C,
        "RANDOM": 0x2D,
        "OPTION": 0x2E,
        "WAITKEY": 0x2F,
        "INKEY": 0x30,
        "WAIT": 0x31,
        "PAUSE": 0x32,
        "CHOOSE": 0x33,
        "CHOOSE_W": 0x34,
        "TYPERATE": 0x35,
        "CLEAR": 0x36,
        "PAGEPAUSE": 0x37,
        "CHAR_D": 0x38,
        "TAB": 0x39,
        "REPCHAR": 0x3A,
        "SFX_D": 0x3B,
        "SFX_I": 0x3C,
        "TRACK_D": 0x3D,
        "TRACK_I": 0x3E,
        "PLAY_D": 0x3F,
        "PLAY_I": 0x40,
        "LOOP_D": 0x41,
        "LOOP_I": 0x42,
        "RANDOMIZE": 0x43,
        "POP_AT": 0x44,
        "NEWLINE": 0x45,
        "SET_DI": 0x46,
        "POP_SET_DI": 0x47,
        "PUSH_DI": 0x48,
        "POP_INK": 0x49,
        "POP_PAPER": 0x4A,
        "POP_BORDER": 0x4B,
        "POP_BRIGHT": 0x4C,
        "POP_FLASH": 0x4D,
        "POP_PRINT": 0x4E,
        "CHAR_I": 0x4F,
        "POP_CHAR": 0x50,
        "POP_PICTURE": 0x51,
        "POP_DISPLAY": 0x52,
        "POP_SFX": 0x53,
        "POP_TRACK": 0x54,
        "POP_PLAY": 0x55,
        "POP_LOOP": 0x56,
        "POP_PUSH_I": 0x57,
        "SET_XPOS": 0x58,
        "SET_YPOS": 0x59,
        "PUSH_XPOS": 0x5A,
        "PUSH_YPOS": 0x5B,
        "MIN": 0x5C,
        "MAX": 0x5D,
        "BLIT": 0x5E,
        "POP_BLIT": 0x5F,
        "MENUCONFIG": 0x60,
        "POP_MENUCONFIG": 0x61,
        "PUSH_IS_DISK": 0x62,
        "BACKSPACE": 0x63,
        "RAMLOAD": 0x64,
        "RAMSAVE": 0x65,
        "POP_SLOT_LOAD": 0x66,
        "POP_SLOT_SAVE": 0x67,
        "PUSH_SAVE_RESULT": 0x68,
        "FADEOUT": 0x69,
        "FILLATTR": 0x6A,
        "PUTATTR": 0x6B,
        "POP_PUTATTR": 0x6C,
        "CHOOSE_CH": 0x6D,
        "PUSH_OPTION_ST": 0x6E,
        "CLEAR_OPTIONS": 0x6F,
        "PUSH_GET_ATTR": 0x70,
        "POP_ALL_BLIT": 0x71,
        "SHIFT_R": 0x72,
        "SHIFT_L": 0x73,
        "POP_ALL_PUTATTR": 0x74,
        "POP_FILLATTR": 0x75,
        "POP_VAL_OPTION": 0x76,
        "WINDOW": 0x77,
        "CHARSET": 0x78,
        "SKIP_ARRAY": 0x79,
        "PUSH_VAL_ARRAY": 0x7A,
        "POP_VAL_ARRAY": 0x7B,
        "PUSH_LEN_ARRAY": 0x7C,
        "SET_KEMPSTON": 0x7D,
        "PUSH_KEMPSTON": 0x7E,
        "EXTERN": 0x7F,
    }

    def __init__(self, gettext):
        self._ = gettext.gettext
        self.symbols = {}
        self.array_lengths = {}
        # Immutable DATA stream (DATA/READ/RESTORE/DATAEND): the concatenated
        # read-only blob and its length, filled by code_extract_data. Placed by
        # cydc.py as a single TYPE_DATA chunk (<=16 KB, one chunk).
        self.data_blob = []
        self.data_len = 0
        self.variables = {}
        self.constants = {}
        # Native routine table. block_name -> {"source": ("file", path) |
        # ("inline", body), "exports": [callable names], "uses": [names called via
        # CYD_CALL]}. IMPORT and inline ASM blocks share this table.
        self.externs = {}
        # callable name -> block_name it resolves to (an IMPORT name, or one of a
        # block's EXPORTS). This is what a CALL target is checked against.
        self.extern_exports = {}
        # Positions of every emitted OP_EXTERN operand, filled during
        # symbol_replacement: list of (name, chunk_index, byte_offset). The
        # address of a native routine is only known after memory allocation
        # (it runs after generate_code), so these are patched late by the build.
        self.extern_calls = []
        self.code = []
        self.bank_offset_list = [0xC000]
        self.bank_size_list = [16 * 1024]
        self.optimize = True
        self.eliminate_dead_code = False

    def set_bank_offset_list(self, offset_list):
        if offset_list is not None:
            self.bank_offset_list = offset_list

    def set_bank_size_list(self, size_list):
        if size_list is not None:
            self.bank_size_list = size_list

    def constant_calculation(self, constants, is_word=False):
        f_constants = {}
        while len(constants) > 0:
            count_before = len(constants)
            tmp_const = constants.copy()
            # Get flattened constants (without reference to other constants)
            for k in constants.keys():
                is_flattened = True
                for c in constants[k]:
                    if isinstance(c, tuple):
                        if c[0] == "C_REPL":
                            is_flattened = False
                    else:
                        sys.exit(self._(f"ERROR: Invalid constant {k}!"))
                if is_flattened:
                    c = tmp_const.pop(k)
                    f_constants[k] = c
            constants = tmp_const
            # If no constant could be flattened this round, the remaining ones
            # reference each other (or themselves) and can never resolve; without
            # this guard the while-loop would spin forever.
            if len(constants) == count_before:
                names = ", ".join(sorted(constants.keys()))
                sys.exit(
                    self._(
                        f"ERROR: Circular or self-referential constant definition "
                        f"involving: {names}"
                    )
                )
            # Replace references on non flattened constants
            for k in constants.keys():
                l = []
                for c in constants[k]:
                    if isinstance(c, tuple):
                        if c[0] == "C_REPL":
                            k2 = c[1]
                            v2 = f_constants.get(k2)
                            if v2 is None:  # Non flattened reference found
                                l.append(c)
                            elif isinstance(v2, list):
                                l += v2
                            else:
                                l.append(v2)
                        else:
                            l.append(c)
                    else:
                        sys.exit(self._(f"ERROR: Invalid constant {k}, {c}!"))
                constants[k] = l

        # Calculate constants
        for k in f_constants.keys():
            stack = []
            for c in f_constants[k]:
                if isinstance(c, tuple) and len(c) in range(1, 3):
                    op = c[0]
                    try:
                        if op == "C_VAL":
                            stack.append(c[1])
                        elif op == "C_+":
                            b = stack.pop()
                            a = stack.pop()
                            stack.append(a + b)
                        elif op == "C_-":
                            b = stack.pop()
                            a = stack.pop()
                            stack.append(a - b)
                        elif op == "C_*":
                            b = stack.pop()
                            a = stack.pop()
                            stack.append(a * b)
                        elif op == "C_/":
                            b = stack.pop()
                            a = stack.pop()
                            stack.append(a / b)
                        elif op == "C_&":
                            b = stack.pop()
                            a = stack.pop()
                            stack.append(a & b)
                        elif op == "C_|":
                            b = stack.pop()
                            a = stack.pop()
                            stack.append(a | b)
                        elif op == "C_<<":
                            b = stack.pop()
                            a = stack.pop()
                            stack.append(a << b)
                        elif op == "C_>>":
                            b = stack.pop()
                            a = stack.pop()
                            stack.append(a >> b)
                        else:
                            sys.exit(self._(f"ERROR: Invalid constant {k}, {op}!"))
                    except IndexError:
                        sys.exit(
                            self._(f"ERROR: Invalid constant operation {k}, {op}!")
                        )
                else:
                    sys.exit(self._(f"ERROR: Invalid constant {k}, {c}!"))
            if len(stack) != 1:
                sys.exit(self._(f"ERROR: Invalid constant operation {k}!"))
            else:
                c = stack.pop()
                if isinstance(c, int):
                    if c >= 0:
                        f_constants[k] = c
                    else:
                        sys.exit(
                            self._(
                                f"ERROR: Invalid constant value {k}, must not be negative!"
                            )
                        )
                else:
                    sys.exit(self._(f"ERROR: Invalid constant value {k}, {c}!"))
        return f_constants

    def constant_expression_calculation(self, expression, constants, is_word=False):
        stack = []
        for c in expression:
            if isinstance(c, tuple) and len(c) in range(1, 3):
                op = c[0]
                try:
                    if op == "C_REPL":
                        a = constants.get(c[1])
                        if a is not None:
                            stack.append(a)
                        else:
                            sys.exit(self._(f"ERROR: Constant {c[1]} does not exists!"))
                    elif op == "C_VAL":
                        stack.append(c[1])
                    elif op == "C_+":
                        b = stack.pop()
                        a = stack.pop()
                        stack.append(a + b)
                    elif op == "C_-":
                        b = stack.pop()
                        a = stack.pop()
                        stack.append(a - b)
                    elif op == "C_*":
                        b = stack.pop()
                        a = stack.pop()
                        stack.append(a * b)
                    elif op == "C_/":
                        b = stack.pop()
                        a = stack.pop()
                        stack.append(a / b)
                    elif op == "C_&":
                        b = stack.pop()
                        a = stack.pop()
                        stack.append(a & b)
                    elif op == "C_|":
                        b = stack.pop()
                        a = stack.pop()
                        stack.append(a | b)
                    elif op == "C_<<":
                        b = stack.pop()
                        a = stack.pop()
                        stack.append(a << b)
                    elif op == "C_>>":
                        b = stack.pop()
                        a = stack.pop()
                        stack.append(a >> b)
                    else:
                        sys.exit(self._(f"ERROR: Invalid constant expression, {op}!"))
                except IndexError:
                    sys.exit(
                        self._(f"ERROR: Invalid constant expression operation {op}!")
                    )
            else:
                sys.exit(self._(f"ERROR: Invalid constant expression {c}!"))
        if len(stack) != 1:
            sys.exit(self._(f"ERROR: Invalid constant expression operation!"))
        else:
            c = stack.pop()
            if isinstance(c, int):
                if is_word:
                    if c in range(0, 1 << 16) and is_word:
                        return c
                    else:
                        sys.exit(
                            self._(
                                f"ERROR: Invalid constant expression value {c} is not a word!"
                            )
                        )
                else:
                    if c in range(0, 1 << 8):
                        return c
                    else:
                        sys.exit(
                            self._(
                                f"ERROR: Invalid constant expression value {c} is not a byte!"
                            )
                        )
            else:
                sys.exit(self._(f"ERROR: Invalid constant expression value {c}!"))

    def _eval_const_raw(self, expression, constants):
        """Evaluate a constant-expression postfix to its raw non-negative integer,
        WITHOUT the byte/word range cap that constant_expression_calculation
        applies. Used for wide constants (WORD/DWORD) and DATA/array width
        auto-detection, where values legitimately exceed a byte or a word. The
        caller applies the width-specific range check."""
        stack = []
        for c in expression:
            if isinstance(c, tuple) and len(c) in range(1, 3):
                op = c[0]
                try:
                    if op == "C_REPL":
                        a = constants.get(c[1])
                        if a is None:
                            sys.exit(self._(f"ERROR: Constant {c[1]} does not exists!"))
                        stack.append(a)
                    elif op == "C_VAL":
                        stack.append(c[1])
                    elif op == "C_+":
                        b = stack.pop(); a = stack.pop(); stack.append(a + b)
                    elif op == "C_-":
                        b = stack.pop(); a = stack.pop(); stack.append(a - b)
                    elif op == "C_*":
                        b = stack.pop(); a = stack.pop(); stack.append(a * b)
                    elif op == "C_/":
                        b = stack.pop(); a = stack.pop(); stack.append(a // b)
                    elif op == "C_&":
                        b = stack.pop(); a = stack.pop(); stack.append(a & b)
                    elif op == "C_|":
                        b = stack.pop(); a = stack.pop(); stack.append(a | b)
                    elif op == "C_<<":
                        b = stack.pop(); a = stack.pop(); stack.append(a << b)
                    elif op == "C_>>":
                        b = stack.pop(); a = stack.pop(); stack.append(a >> b)
                    else:
                        sys.exit(self._(f"ERROR: Invalid constant expression, {op}!"))
                except IndexError:
                    sys.exit(self._(f"ERROR: Invalid constant expression operation {op}!"))
            else:
                sys.exit(self._(f"ERROR: Invalid constant expression {c}!"))
        if len(stack) != 1 or not isinstance(stack[0], int):
            sys.exit(self._(f"ERROR: Invalid constant expression operation!"))
        if stack[0] < 0:
            sys.exit(self._(f"ERROR: Constant expression value {stack[0]} must not be negative!"))
        return stack[0]

    def _check_wide_fits(self, val, width):
        """Range-check a wide constant against its forced width (2 or 4 bytes),
        with one message shared by DATA/DIM and LET/SET so they read identically."""
        if val >= (1 << (8 * width)):
            kw = "WORD" if width == 2 else "DWORD"
            sys.exit(
                self._(f"ERROR: {kw} value {val} does not fit in {8 * width} bits.")
            )

    def _expand_data_element(self, elem, constants):
        """Expand one DATA/array init element into its little-endian bytes.

        Elements (produced by the parser): ("CONSTANT", postfix) auto-detects the
        width by magnitude (0..255 -> 1 byte, ..65535 -> 2, ..2^32-1 -> 4);
        ("CONSTANT_WORD", postfix) forces 2 bytes; ("CONSTANT_DWORD", postfix)
        forces 4; ("CONSTANT_STR", [bytes]) is the string's glyph bytes. 0 runtime:
        everything is resolved here at compile time."""
        tag = elem[0]
        if tag == "CONSTANT_STR":
            return [b & 0xFF for b in elem[1]]
        if not (len(elem) == 2 and isinstance(elem[1], list)):
            sys.exit(self._(f"ERROR: Invalid data element {elem}"))
        val = self._eval_const_raw(elem[1], constants)
        if tag == "CONSTANT":
            if val < (1 << 8):
                width = 1
            elif val < (1 << 16):
                width = 2
            elif val < (1 << 32):
                width = 4
            else:
                sys.exit(self._(f"ERROR: DATA/array value {val} too big (max 2^32-1)."))
        elif tag == "CONSTANT_WORD":
            self._check_wide_fits(val, 2)
            width = 2
        elif tag == "CONSTANT_DWORD":
            self._check_wide_fits(val, 4)
            width = 4
        else:
            sys.exit(self._(f"ERROR: Invalid data element {elem}"))
        return [(val >> (8 * k)) & 0xFF for k in range(width)]

    def code_extract_declarations(self, code):
        variables = {}
        constants = {}
        arrays = {}
        labels = {}
        externs = {}
        extern_exports = {}

        def _register_export(callable_name, block_name):
            if extern_exports.get(callable_name) is not None:
                sys.exit(
                    self._(f"ERROR: Native routine {callable_name} defined two times!")
                )
            extern_exports[callable_name] = block_name

        code_tmp = []
        for t in code:
            opcode = t[0]  # get opcode type
            if opcode == "IMPORT":
                q = t[1]  # routine name
                p = t[2]  # assembler file path
                if externs.get(q) is not None:
                    sys.exit(self._(f"ERROR: Native routine {q} imported two times!"))
                # A file-backed block with a single callable = its own name; its
                # entry is the block start (not a named label), so explicit=False.
                externs[q] = {
                    "source": ("file", p),
                    "exports": [q],
                    "explicit": False,
                    "uses": [],
                    "line": None,
                }
                _register_export(q, q)
            elif opcode == "ASM":
                # ("ASM", block, body, exports, uses, line) from the parser.
                block, body, exports, uses, line = t[1], t[2], t[3], t[4], t[5]
                if externs.get(block) is not None:
                    sys.exit(self._(f"ERROR: Native routine {block} defined two times!"))
                # explicit EXPORTS -> callables are labels in the body; otherwise
                # the block name itself is the single callable (entry = start).
                explicit = bool(exports)
                callables = list(exports) if explicit else [block]
                externs[block] = {
                    "source": ("inline", body),
                    "exports": callables,
                    "explicit": explicit,
                    "uses": list(uses),
                    "line": line,
                }
                for e in callables:
                    _register_export(e, block)
            elif opcode == "CONST":
                p = t[2]  # get value
                q = t[1]  # get symbol
                if variables.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Constant {q} is already declared as variable")
                    )
                elif labels.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Variable {q} is already declared as label")
                    )
                elif arrays.get(q) is not None:
                    sys.exit(self._(f"ERROR: Label {q} is already declared as array"))
                elif constants.get(q) is None:
                    constants[q] = p  # Add to cosntants table
                else:
                    sys.exit(self._(f"ERROR: Constant {q} declared two times!"))
            elif opcode == "DECLARE":
                p = t[1]  # get variable number
                q = t[2]  # get symbol
                if constants.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Variable {q} is already declared as constant")
                    )
                elif labels.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Variable {q} is already declared as label")
                    )
                elif arrays.get(q) is not None:
                    sys.exit(self._(f"ERROR: Label {q} is already declared as array"))
                elif variables.get(q) is None:
                    variables[q] = p  # Add to variable table
                else:
                    sys.exit(self._(f"ERROR: Variable {q} declared two times!"))
            elif opcode == "ARRAY":
                p = t[2]  # get constant list
                q = t[1]  # get symbol
                if variables.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Array {q} is already declared as variable")
                    )
                elif labels.get(q) is not None:
                    sys.exit(self._(f"ERROR: Array {q} is already declared as label"))
                elif constants.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Array {q} is already declared as constant")
                    )
                elif arrays.get(q) is None:
                    arrays[q] = 0
                    code_tmp.append(t)
                else:
                    sys.exit(self._(f"ERROR: Array {q} declared two times!"))
            elif opcode == "LABEL":
                q = t[1]  # get symbol
                if variables.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Label {q} is already declared as variable")
                    )
                elif constants.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Label {q} is already declared as constant")
                    )
                elif arrays.get(q) is not None:
                    sys.exit(self._(f"ERROR: Label {q} is already declared as array"))
                elif labels.get(q) is None:
                    labels[q] = 0  # Add to symbol table
                    code_tmp.append(t)
                else:
                    sys.exit(self._(f"ERROR: Label {q} declared two times!"))
            else:  # Append any other code
                code_tmp.append(t)
        constants = self.constant_calculation(constants)
        code = []
        for instruction in code_tmp:
            if (
                len(instruction) == 4 and instruction[0] == "ARRAY"
            ):  # Special case for arrays
                if isinstance(instruction[1], str) and isinstance(instruction[3], list):
                    size = instruction[2]
                    # Expand every init element to its bytes (a WORD/DWORD/string
                    # element yields several bytes). Arrays are byte-plano.
                    lc = []
                    for c in instruction[3]:
                        lc += self._expand_data_element(c, constants)
                    if (
                        isinstance(size, tuple)
                        and isinstance(size[1], list)
                        and size[0] == "CONSTANT"
                    ):
                        array_len = self.constant_expression_calculation(
                            size[1], constants, True
                        )
                    elif instruction[2] is None:
                        array_len = len(lc)  # byte count after expansion
                    else:
                        sys.exit(self._(f"ERROR: Invalid array declaration"))
                    if array_len not in range(1, 257):
                        sys.exit(
                            self._(
                                f"ERROR: The array {instruction[1]} has an invalid size."
                            )
                        )
                    if len(lc) > array_len:
                        sys.exit(
                            self._(
                                f"ERROR: The array {instruction[1]} is too small for the supplied initialization data."
                            )
                        )
                    elif len(lc) < array_len:
                        lc += [0 for x in range(array_len - len(lc))]
                    tup = (instruction[0], instruction[1], lc)
                else:
                    sys.exit(self._(f"ERROR: Invalid array declaration"))
            elif len(instruction) == 2 and instruction[0] == "DATA":
                # Immutable DATA: expand each element to its bytes now (auto-detect
                # width / WORD / DWORD / string). code_extract_data later
                # concatenates every ("DATA", [bytes]) into the global blob.
                lc = []
                for c in instruction[1]:
                    lc += self._expand_data_element(c, constants)
                tup = ("DATA", lc)
            else:
                tup = ()
                for c in instruction:
                    if isinstance(c, tuple):
                        # Variable with displacement or constant expression
                        if (
                            len(c) == 3 and c[0] == "VARIABLE"
                        ):  # Variable with displacement
                            disp = c[2]
                            c = c[1]
                            if isinstance(c, str):
                                t = variables.get(c)
                                if t is None:
                                    # print(variables)
                                    sys.exit(
                                        self._(f"ERROR: Variable {c} does not exists!")
                                    )
                                elif (t + disp) not in range(256):
                                    sys.exit(
                                        self._(
                                            f"ERROR: Multiple assignation of variable {c} is out of bounds!"
                                        )
                                    )
                                else:
                                    c = t + disp  # Adds displacement
                            else:
                                # Numeric variable index. Same bounds check as the
                                # named path: a displacement (multi-slot SET/LET or a
                                # wide constant) must not push the target past 255,
                                # otherwise we would emit an invalid (>255) operand.
                                if (c + disp) not in range(256):
                                    sys.exit(
                                        self._(
                                            f"ERROR: Multiple assignation of variable {c} is out of bounds!"
                                        )
                                    )
                                c = c + disp
                        elif (
                            len(c) == 2
                            and c[0] == "CONSTANT"
                            and isinstance(c[1], list)
                        ):  # Constant expression
                            c = self.constant_expression_calculation(
                                c[1], constants, False
                            )
                        elif (
                            len(c) == 2
                            and c[0] == "CONSTANT_L"
                            and isinstance(c[1], list)
                        ):
                            c = self.constant_expression_calculation(
                                c[1], constants, True
                            )
                            c = c & 0xFF
                        elif (
                            len(c) == 2
                            and c[0] == "CONSTANT_H"
                            and isinstance(c[1], list)
                        ):
                            c = self.constant_expression_calculation(
                                c[1], constants, True
                            )
                            c = (c >> 8) & 0xFF
                        elif (
                            len(c) == 4
                            and c[0] == "CONSTANT_WIDE"
                            and isinstance(c[1], list)
                        ):  # byte c[2] of a width-c[3] wide constant (WORD/DWORD LET)
                            v = self._eval_const_raw(c[1], constants)
                            self._check_wide_fits(v, c[3])
                            c = (v >> (8 * c[2])) & 0xFF
                    tup += (c,)
            code.append(tup)
        self.externs = externs
        self.extern_exports = extern_exports
        return (code, variables, constants)

    def code_extract_data(self, code):
        """Concatenate every DATA statement into one read-only blob (source order),
        map each label to the offset of the first DATA following it (for RESTORE
        label), strip the DATA statements from the executable stream, and bake each
        RESTORE label into a 16-bit blob offset. Sets self.data_blob / data_len.

        Runs before optimize/DCE, so label offsets are captured even if a
        DATA-marker label is later dropped as dead code."""
        blob = []
        label_offsets = {}
        pending_labels = []
        for t in code:
            if t[0] == "LABEL":
                pending_labels.append(t[1])
            elif t[0] == "DATA":
                off = len(blob)
                for lbl in pending_labels:
                    label_offsets[lbl] = off
                pending_labels = []
                blob += t[1]
        # v1: a single TYPE_DATA chunk, 16-bit cursor -> <= 16 KB.
        if len(blob) > 16 * 1024:
            sys.exit(
                self._(
                    f"ERROR: DATA block too big ({len(blob)} bytes, max 16384)."
                )
            )
        out = []
        for t in code:
            if t[0] == "DATA":
                continue  # not executable: it lives in the blob
            elif t[0] == "RESTORE_LABEL":
                name = t[1]
                off = label_offsets.get(name)
                if off is None:
                    sys.exit(
                        self._(
                            f"ERROR: RESTORE {name}: no DATA appears after that label."
                        )
                    )
                out.append(("RESTORE", off & 0xFF, (off >> 8) & 0xFF))
            else:
                out.append(t)
        self.data_blob = blob
        self.data_len = len(blob)
        return out

    def code_simple_optimize(self, code):
        code_tmp = []
        skip = False
        for i, c in enumerate(code):
            if skip:
                skip = False
            elif (i + 1) < len(code):
                next = code[i + 1]
                if next[0] == "POP_SET":
                    if c[0] == "PUSH_D":
                        c = ("SET_D", next[1], c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("SET_I", next[1], c[1])
                        skip = True
                    elif c[0] == "PUSH_RANDOM":
                        c = ("RANDOM", next[1], c[1])
                        skip = True
                    elif c[0] == "PUSH_INKEY":
                        c = ("INKEY", next[1], c[1])
                        skip = True
                    elif c[0] == "PUSH_KEMPSTON":
                        c = ("SET_KEMPSTON", next[1])
                        skip = True
                    elif c[0] == "PUSH_XPOS":
                        c = ("SET_XPOS", next[1])
                        skip = True
                    elif c[0] == "PUSH_YPOS":
                        c = ("SET_YPOS", next[1])
                        skip = True
                    elif c[0] == "PUSH_DI":
                        c = ("SET_DI", next[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_PUSH_I":
                    if c[0] == "PUSH_I":
                        c = ("PUSH_DI", c[1])
                        skip = True
                    elif c[0] == "PUSH_D":
                        c = ("PUSH_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_INK":
                    if c[0] == "PUSH_D":
                        c = ("INK_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("INK_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_PAPER":
                    if c[0] == "PUSH_D":
                        c = ("PAPER_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("PAPER_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_BORDER":
                    # Only the immediate form is fused; the _I (from-variable) form
                    # was dropped to free opcode 0x23 for READ (BORDER @v is rare and
                    # falls back to PUSH_I:POP_BORDER, 2 opcodes).
                    if c[0] == "PUSH_D":
                        c = ("BORDER_D", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_BRIGHT":
                    # _I form dropped to free opcode 0x27 for RESTORE (see BORDER).
                    if c[0] == "PUSH_D":
                        c = ("BRIGHT_D", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_FLASH":
                    # _I form dropped to free opcode 0x28 for DATAEND (see BORDER).
                    if c[0] == "PUSH_D":
                        c = ("FLASH_D", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_PRINT":
                    if c[0] == "PUSH_D":
                        c = ("PRINT_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("PRINT_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_CHAR":
                    if c[0] == "PUSH_D":
                        c = ("CHAR_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("CHAR_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_PICTURE":
                    if c[0] == "PUSH_D":
                        c = ("PICTURE_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("PICTURE_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_DISPLAY":
                    if c[0] == "PUSH_D":
                        c = ("DISPLAY_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("DISPLAY_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_SFX":
                    if c[0] == "PUSH_D":
                        c = ("SFX_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("SFX_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_TRACK":
                    if c[0] == "PUSH_D":
                        c = ("TRACK_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("TRACK_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_PLAY":
                    if c[0] == "PUSH_D":
                        c = ("PLAY_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("PLAY_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_LOOP":
                    if c[0] == "PUSH_D":
                        c = ("LOOP_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("LOOP_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "IF_N_GOTO":
                    if c[0] == "NOT":
                        c = ("IF_GOTO", next[1], next[3])
                        skip = True
                    code_tmp.append(c)
                else:
                    code_tmp.append(c)
            else:
                code_tmp.append(c)
        # MENUCONFIG
        run = True
        while run:
            run = False
            if len(code_tmp) >= 5:
                for i in range(4, len(code_tmp)):
                    t0 = code_tmp[i - 4]
                    t1 = code_tmp[i - 3]
                    t2 = code_tmp[i - 2]
                    t3 = code_tmp[i - 1]
                    t4 = code_tmp[i]
                    if (
                        t4[0] == "POP_MENUCONFIG"
                        and t3[0] == "PUSH_D"
                        and t2[0] == "PUSH_D"
                        and t1[0] == "PUSH_D"
                        and t0[0] == "PUSH_D"
                    ):
                        l = []
                        if (i - 4) > 0:
                            l += code_tmp[: i - 4]
                        l.append(("MENUCONFIG", t0[1], t1[1], t2[1], t3[1]))
                        if (i + 1) < len(code_tmp):
                            l += code_tmp[i + 1 :]
                        code_tmp = l
                        run = True
                        break
        # AT
        run = True
        while run:
            run = False
            if len(code_tmp) >= 3:
                for i in range(2, len(code_tmp)):
                    t0 = code_tmp[i - 2]
                    t1 = code_tmp[i - 1]
                    t2 = code_tmp[i]
                    if t2[0] == "POP_AT" and t1[0] == "PUSH_D" and t0[0] == "PUSH_D":
                        l = []
                        if (i - 2) > 0:
                            l += code_tmp[: i - 2]
                        l.append(("AT", t0[1], t1[1]))
                        if (i + 1) < len(code_tmp):
                            l += code_tmp[i + 1 :]
                        code_tmp = l
                        run = True
                        break
        # FILLATTR
        run = True
        while run:
            run = False
            if len(code_tmp) >= 6:
                for i in range(5, len(code_tmp)):
                    t0 = code_tmp[i - 5]
                    t1 = code_tmp[i - 4]
                    t2 = code_tmp[i - 3]
                    t3 = code_tmp[i - 2]
                    t4 = code_tmp[i - 1]
                    t5 = code_tmp[i]
                    if (
                        t5[0] == "POP_FILLATTR"
                        and t4[0] == "PUSH_D"
                        and t3[0] == "PUSH_D"
                        and t2[0] == "PUSH_D"
                        and t1[0] == "PUSH_D"
                        and t0[0] == "PUSH_D"
                    ):
                        l = []
                        if (i - 5) > 0:
                            l += code_tmp[: i - 5]
                        l.append(("FILLATTR", t0[1], t1[1], t2[1], t3[1], t4[1]))
                        if (i + 1) < len(code_tmp):
                            l += code_tmp[i + 1 :]
                        code_tmp = l
                        run = True
                        break
        # PUTATTR
        run = True
        while run:
            run = False
            if len(code_tmp) >= 5:
                for i in range(4, len(code_tmp)):
                    t0 = code_tmp[i - 4]
                    t1 = code_tmp[i - 3]
                    t2 = code_tmp[i - 2]
                    t3 = code_tmp[i - 1]
                    t4 = code_tmp[i]
                    if (
                        t4[0] == "POP_ALL_PUTATTR"
                        and t3[0] == "PUSH_D"
                        and t2[0] == "PUSH_D"
                        and t1[0] == "PUSH_D"
                        and t0[0] == "PUSH_D"
                    ):
                        l = []
                        if (i - 4) > 0:
                            l += code_tmp[: i - 4]
                        l.append(("PUTATTR", t0[1], t1[1], t2[1], t3[1]))
                        if (i + 1) < len(code_tmp):
                            l += code_tmp[i + 1 :]
                        code_tmp = l
                        run = True
                        break
        # POP_PUTATTR
        run = True
        while run:
            run = False
            if len(code_tmp) >= 3:
                for i in range(2, len(code_tmp)):
                    t0 = code_tmp[i - 2]
                    t1 = code_tmp[i - 1]
                    t2 = code_tmp[i]
                    if (
                        t2[0] == "POP_ALL_PUTATTR"
                        and t1[0] == "PUSH_D"
                        and t0[0] == "PUSH_D"
                    ):
                        l = []
                        if (i - 2) > 0:
                            l += code_tmp[: i - 2]
                        l.append(("POP_PUTATTR", t0[1], t1[1]))
                        if (i + 1) < len(code_tmp):
                            l += code_tmp[i + 1 :]
                        code_tmp = l
                        run = True
                        break
        # BLIT
        run = True
        while run:
            run = False
            if len(code_tmp) >= 7:
                for i in range(6, len(code_tmp)):
                    t0 = code_tmp[i - 6]
                    t1 = code_tmp[i - 5]
                    t2 = code_tmp[i - 4]
                    t3 = code_tmp[i - 3]
                    t4 = code_tmp[i - 2]
                    t5 = code_tmp[i - 1]
                    t6 = code_tmp[i]
                    if (
                        t6[0] == "POP_ALL_BLIT"
                        and t5[0] == "PUSH_D"
                        and t4[0] == "PUSH_D"
                        and t3[0] == "PUSH_D"
                        and t2[0] == "PUSH_D"
                        and t1[0] == "PUSH_D"
                        and t0[0] == "PUSH_D"
                    ):
                        l = []
                        if (i - 6) > 0:
                            l += code_tmp[: i - 6]
                        l.append(("BLIT", t0[1], t1[1], t2[1], t3[1], t4[1], t5[1]))
                        if (i + 1) < len(code_tmp):
                            l += code_tmp[i + 1 :]
                        code_tmp = l
                        run = True
                        break
        # POP_BLIT
        run = True
        while run:
            run = False
            if len(code_tmp) >= 5:
                for i in range(4, len(code_tmp)):
                    t0 = code_tmp[i - 4]
                    t1 = code_tmp[i - 3]
                    t2 = code_tmp[i - 2]
                    t3 = code_tmp[i - 1]
                    t4 = code_tmp[i]
                    if (
                        t4[0] == "POP_ALL_BLIT"
                        and t3[0] == "PUSH_D"
                        and t2[0] == "PUSH_D"
                        and t1[0] == "PUSH_D"
                        and t0[0] == "PUSH_D"
                    ):
                        l = []
                        if (i - 4) > 0:
                            l += code_tmp[: i - 4]
                        l.append(("POP_BLIT", t0[1], t1[1], t2[1], t3[1]))
                        if (i + 1) < len(code_tmp):
                            l += code_tmp[i + 1 :]
                        code_tmp = l
                        run = True
                        break

        # Append an END just in case...
        last_opcode = code_tmp[-1]
        if last_opcode[0] != "END":
            code_tmp.append(("END",))
        # for c in code:
        #    print(c)
        # print(code)
        # print()
        # for c in code_tmp:
        #     print(c)
        return code_tmp

    def dead_code_elimination(self, code):
        """Remove instructions that can never be reached.

        Reachability is traced from the entry point (index 0). An instruction is
        *executed* when control flow reaches it, via:
          * a label jump — any operand naming a LABEL (covers GOTO/GOSUB/IF_GOTO/
            IF_N_GOTO/OPTION/CHOOSE, whatever position the name sits at);
          * sequential fall-through to the next instruction, for every opcode
            that is NOT an unconditional terminator (GOTO / RETURN / END).

        Arrays are different: an operand naming an ARRAY is a reference to inline
        *data* by address. Such an array is kept, but control flow does NOT flow
        through it just because it is referenced (execution reaches the array
        only if it also falls/jumps into its SKIP_ARRAY, in which case it is
        executed normally and its fall-through is traced).

        This is a deliberately safe over-approximation: the only opcodes that do
        not fall through are GOTO/RETURN/END (certain), so live code is never
        dropped; at worst some dead code survives. A label reached only by
        falling into it (no GOTO to it) is kept via the fall-through edge.
        Library routines guarded by a `GOTO skip` at the top are reachable only
        through GOSUB, so the unused ones become unreachable and are removed.
        Runs on the optimized opcode stream, before code_translate, so all
        addresses are recomputed from the surviving instructions.
        """
        if not code:
            return code
        label_index = {}
        array_index = {}
        for i, t in enumerate(code):
            if not t:
                continue
            if t[0] == "LABEL":
                label_index[t[1]] = i
            elif t[0] == "ARRAY":
                array_index[t[1]] = i
        terminators = ("GOTO", "RETURN", "END")
        executed = set()      # reached by control flow (trace fall-through)
        kept_data = set()     # arrays referenced by address (keep, do not trace)
        stack = [0]
        n = len(code)
        while stack:
            i = stack.pop()
            if i < 0 or i >= n or i in executed:
                continue
            executed.add(i)
            t = code[i]
            for operand in t[1:]:
                if isinstance(operand, str):
                    if operand in label_index:      # jump target -> executed
                        stack.append(label_index[operand])
                    elif operand in array_index:    # data reference -> keep only
                        kept_data.add(array_index[operand])
            if t[0] not in terminators:             # sequential fall-through
                stack.append(i + 1)
        keep = executed | kept_data
        result = [t for i, t in enumerate(code) if i in keep]
        # Keep a terminating END if the last surviving instruction is not one.
        if not result or result[-1][0] != "END":
            result.append(("END",))
        return result

    def check_code_paramenters(self, code):
        code_tmp = []
        for t in code:
            opcode = t[0]  # get opcode type
            if opcode == "MARGINS" or opcode == "FADEOUT":
                (row, col, width, height) = self._fix_borders(t[1], t[2], t[3], t[4])
                t = (opcode, col, row, width, height)
            elif opcode == "AT":
                col = t[1]
                row = t[2]
                if col >= 32:
                    col = 31
                if col < 0:
                    col = 0
                if row >= 24:
                    row = 23
                if row < 0:
                    row = 0
                t = (opcode, col, row)
            elif opcode == "MENUCONFIG":
                col = t[1]
                row = t[2]
                init = t[3]
                show = t[4]
                if col >= 32:
                    col = 31
                if col < 0:
                    col = 0
                if row >= 24:
                    row = 23
                if row < 0:
                    row = 0
                if init_d >= 32:
                    init_d = 0
                t = (opcode, col, row, init, show)
            elif opcode == "BLIT":
                col_d = t[5]
                row_d = t[6]
                if col_d >= 32:
                    col_d = 31
                if row_d < 0:
                    row_d = 0
                if col_d < 0:
                    col_d = 0
                (row, col, width, height) = self._fix_borders(t[1], t[2], t[3], t[4])
                t = (opcode, col, row, width, height, col_d, row_d)
            elif opcode == "POP_BLIT":
                (row, col, width, height) = self._fix_borders(t[1], t[2], t[3], t[4])
                t = (opcode, col, row, width, height)
            code_tmp.append(t)
        return code_tmp

    def code_translate(self, code, slice_text=False):
        code_banks = []
        code_tmp = []
        labels = {}
        arrays = {}
        self.array_lengths = {}  # array name -> element count (for the injected ABI)
        offset = 0
        bank = 0
        for t in code:
            opcode = t[0]  # get opcode type
            if opcode == "LABEL":
                q = t[1]  # get symbol
                if arrays.get(q) is not None:
                    sys.exit(self._(f"ERROR: Label {q} is already declared as array"))
                elif labels.get(q) is None:
                    labels[q] = (bank, offset)  # Add to symbol table
                else:
                    sys.exit(self._(f"ERROR: Label {q} declared two times!"))
            elif opcode == "ARRAY":
                p = t[2]  # get constant list
                q = t[1]  # get symbol
                if labels.get(q) is not None:
                    sys.exit(self._(f"ERROR: Array {q} is already declared as label"))
                elif arrays.get(q) is None:
                    # if we have not space on the current bank, change to the next
                    if (len(p) + 3 + offset + 4) >= self._get_bank_size(bank):
                        bank += 1
                        offset = 0  # reset offset counter
                        code_tmp += [
                            self.opcodes["GOTO"],
                            bank,
                        ] + self._convert_address(offset, bank)
                        # Jump to next bank
                        code_banks.append(code_tmp)  # add new bank
                        code_tmp = []
                    arrays[q] = (
                        bank,
                        offset + 1,
                    )  # Add to symbol table (skipping the SKIP_ARRAY opcode)
                    self.array_lengths[q] = len(p)  # element count for the ABI
                    c = [self.opcodes.get("SKIP_ARRAY"), len(p) - 1] + p
                    code_tmp += c
                    offset += len(c)
                else:
                    sys.exit(self._(f"ERROR: Array {q} declared two times!"))
            else:
                # transform to byte representation
                q = self.opcodes.get(opcode)
                if q is None:
                    sys.exit(self._(f"ERROR: Invalid opcode {opcode}!"))
                if opcode == "TEXT":
                    p = t[1]  # Get text
                    while len(p) > 1:  # A string of less than 1 character is not valid
                        l = self._get_bank_size(bank) - offset - 5  # remaining size
                        if len(p) >= l:  # Too big!, we slice it...
                            # print(f"DEBUG: Text:{len(p)} - space:{l}")
                            # print(f"DEBUG: Text too big! {self.BANK_SIZE - offset} {len(code_tmp)}")
                            bank += 1
                            offset = 0  # reset offset counter
                            if slice_text and l > 0:
                                # print(f"DEBUG: Slice! {l-1}")
                                code_tmp.append(q)
                                code_tmp += p[0 : l - 1] + [
                                    245
                                ]  # Adding end of string character
                                p = p[l - 1 :]
                            code_tmp += [
                                self.opcodes["GOTO"],
                                bank,
                            ] + self._convert_address(
                                offset, bank
                            )  # adding goto to next bank
                            code_banks.append(code_tmp)  # add new bank
                            code_tmp = []
                        else:
                            code_tmp.append(q)  # Add opcode
                            code_tmp += p  # add list of the text
                            offset += len(p) + 1
                            p = []
                else:
                    # if we have not space on the current bank, change to the next
                    if (len(t) + offset + 4) >= self._get_bank_size(bank):
                        # print(f"DEBUG: :{len(t) + offset + 4}")
                        # print("Change bank!")
                        bank += 1
                        offset = 0  # reset offset counter
                        code_tmp += [
                            self.opcodes["GOTO"],
                            bank,
                        ] + self._convert_address(offset, bank)
                        # Jump to next bank
                        code_banks.append(code_tmp)  # add new bank
                        code_tmp = []
                    code_tmp.append(q)  # append opcode byte
                    q = list(t)  # transform tuple on list
                    code_tmp += q[1:]  # add the rest of parameters
                    offset += len(t)  # Add new length
        if len(code_tmp) > 0:
            code_banks.append(code_tmp)
        return (code_banks, labels | arrays)

    def symbol_replacement(self, code, symbols, chunk_index=0):
        code_tmp = []
        queue = []
        for c in code:
            if len(queue) > 0 and c == 0:
                c = queue.pop()
            elif isinstance(c, str):  # Merged labels & arrays
                t = symbols.get(c)
                if t is not None:  # label/array found
                    c = t[0]  # Extract bank
                    queue = self._convert_address(
                        t[1], c
                    )  # Convert offset to bank address
                    queue.reverse()
                elif c in self.extern_exports:
                    # Native routine (IMPORT or inline ASM export): its (bank,
                    # address) is not known
                    # until after memory allocation, so emit a [bank, lo, hi]
                    # placeholder now and record its position for late patching.
                    self.extern_calls.append((c, chunk_index, len(code_tmp)))
                    c = 0  # placeholder bank byte
                    queue = [0, 0]  # placeholder address bytes (lo, hi)
                else:
                    sys.exit(self._(f"ERROR: Label {c} does not exists!"))
            code_tmp.append(c)
        return code_tmp

    def _word_to_list(self, value):
        if value > 0xFFFF:
            sys.exit(self._("ERROR: Invalid offset"))
        return [(value & 0xFF), ((value >> 8) & 0xFF)]

    def _convert_address(self, address, bank=None):
        if bank is None:
            b_offset = self.bank_offset_list[0]
        elif bank >= len(self.bank_offset_list):
            b_offset = self.bank_offset_list[-1]
        else:
            b_offset = self.bank_offset_list[bank]
        return self._word_to_list(address + b_offset)

    def _get_bank_size(self, bank=None):
        if bank is None:
            return self.bank_size_list[0]
        elif bank >= len(self.bank_offset_list):
            return self.bank_size_list[-1]
        else:
            return self.bank_size_list[bank]

    def _get_index_offset(self, idx, offset):
        if offset > 0x7FFFFF:  # Max 8 Mb
            sys.exit(self._("ERROR: Invalid offset"))
        hl = (offset >> 16) & 0xFF
        lh = (offset >> 8) & 0xFF
        ll = offset & 0xFF
        return [ll, lh, hl, idx]

    def _fix_borders(self, row, col, width, height):
        (row, height) = self._fix_rows(row, height)
        (col, width) = self._fix_cols(col, width)
        return (row, col, width, height)

    def _fix_rows(self, row, height):
        if row >= 24:
            row = 23
        if row < 0:
            row = 0
        if height <= 0:
            height = 1
        if (height + row) > 24:
            height = 24 - row
        return (row, height)

    def _fix_cols(self, col, width):
        if col >= 32:
            col = 31
        if col < 0:
            col = 0
        if width <= 0:
            width = 1
        if (width + col) > 32:
            width = 32 - col
        return (col, width)

    # Sentinel "bank" byte for an array relocated to the resident RAM pool
    # (MLD targets, where the array's own chunk lives in read-only Dandanator
    # flash). The array-access opcodes recognise it under IS_MLD_DAN and address
    # ARR_POOL + offset directly instead of paging the flash slot.
    ARR_RESIDENT_BANK = 0xFE

    def generate_code(
        self,
        code,
        slice_text=False,
        show_debug=False,
        relocate_arrays_resident=False,
        array_bank_map=None,
    ):

        (code, self.variables, self.constants) = self.code_extract_declarations(code)
        if show_debug:
            print("\nConstants resolved:\n-------------------")
            print(self.constants)

        # Pull the immutable DATA stream out into self.data_blob and resolve
        # RESTORE labels; must run before optimize/DCE.
        code = self.code_extract_data(code)

        if code is None or len(code) == 0:
            code = [("END",)]

        if self.optimize:
            code = self.code_simple_optimize(code)

        if self.eliminate_dead_code:
            code = self.dead_code_elimination(code)

        if show_debug:
            print("\nVirtual machine opcode:\n-------------------")
            for c in code:
                print(c)

        self.code = self.check_code_paramenters(self.code)
        (code, self.symbols) = self.code_translate(code, slice_text)

        # MLD only: arrays live inline in their bytecode chunk, which on Dandanator
        # is a read-only flash slot, so writes are lost. Relocate each array to
        # writable RAM; the operand becomes [bank, addr] and the boot routine
        # (ARR_INIT) copies the array's [len-1][data] record from flash to that RAM
        # location. self.symbols is remapped BEFORE symbol_replacement bakes the
        # operands. 48k/128k/+3 keep arrays in place (already in writable RAM).
        #
        # Two MLD variants:
        #  - strict mld (48K, no banks): a single resident pool ARR_POOL. Operand
        #    [ARR_RESIDENT_BANK, pool_offset]; ARR_INIT -> ARR_POOL+pool_offset.
        #  - mld128 (banked): each array in a real 128K RAM bank at $C000+offset,
        #    given by array_bank_map (allocated so it never collides with music).
        #    Operand [real_bank, $C000+offset]; the array opcodes page that bank in
        #    ($7FFD) per access. Entry: (name, src_chunk, src_off, bank, addr, nbytes).
        self.arr_init_table = []
        self.arr_pool_size = 0
        if relocate_arrays_resident:
            pool_off = 0
            for name in sorted(self.array_lengths):
                chunk, sym_off = self.symbols[name]  # points at the len-1 byte
                nbytes = self.array_lengths[name] + 1  # len byte + data bytes
                self.arr_init_table.append((name, chunk, sym_off, pool_off, nbytes))
                self.symbols[name] = (self.ARR_RESIDENT_BANK, pool_off)
                pool_off += nbytes
            self.arr_pool_size = pool_off
        elif array_bank_map is not None:
            for name in sorted(self.array_lengths):
                chunk, sym_off = self.symbols[name]  # points at the len-1 byte
                nbytes = self.array_lengths[name] + 1  # len byte + data bytes
                dest_bank, dest_addr = array_bank_map[name]
                self.arr_init_table.append(
                    (name, chunk, sym_off, dest_bank, dest_addr, nbytes)
                )
                self.symbols[name] = (dest_bank, dest_addr)

        self.extern_calls = []
        self.code = [
            self.symbol_replacement(c, self.symbols, i) for i, c in enumerate(code)
        ]
        return self.code

    def get_unused_opcodes(self, code):
        excluded_ops = [
            "DECLARE",
            "LABEL",
            "TEXT",
            "GOSUB",
            "GOTO",
            "IF_GOTO",
            "IF_N_GOTO",
            "RETURN",
            "END",
        ]
        code = self.code_simple_optimize(code)
        used_opcodes = {c[0] for c in code if c[0] not in excluded_ops}
        # RESTORE label is emitted as the marker RESTORE_LABEL (resolved to a real
        # RESTORE opcode only later, in code_extract_data); count it so a program
        # that uses ONLY "RESTORE label" doesn't get the RESTORE opcode trimmed.
        if "RESTORE_LABEL" in used_opcodes:
            used_opcodes.add("RESTORE")
        all_opcodes = {c for c in self.opcodes.keys() if c not in excluded_ops}
        return all_opcodes - used_opcodes
