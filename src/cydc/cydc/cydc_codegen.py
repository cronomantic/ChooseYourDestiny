#
# MIT License
#
# Copyright (c) 2023 Sergio Chico
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

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
        "BORDER_I": 0x23,
        "PRINT_I": 0x24,
        "BRIGHT_D": 0x25,
        "FLASH_D": 0x26,
        "BRIGHT_I": 0x27,
        "FLASH_I": 0x28,
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
        # "READ": 0x79,
        # "DATA": 0x7A,
        # "RESTORE": 0x7B,
    }

    def __init__(self, gettext):
        self._ = gettext.gettext
        self.symbols = {}
        self.variables = {}
        self.constants = {}
        self.code = []
        self.bank_offset_list = [0xC000]
        self.bank_size_list = [16 * 1024]
        self.optimize = True

    def set_bank_offset_list(self, offset_list):
        if offset_list is not None:
            self.bank_offset_list = offset_list

    def set_bank_size_list(self, size_list):
        if size_list is not None:
            self.bank_size_list = size_list

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
                    if c[0] == "PUSH_D":
                        c = ("BORDER_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("BORDER_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_BRIGHT":
                    if c[0] == "PUSH_D":
                        c = ("BRIGHT_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("BRIGHT_I", c[1])
                        skip = True
                    code_tmp.append(c)
                elif next[0] == "POP_FLASH":
                    if c[0] == "PUSH_D":
                        c = ("FLASH_D", c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("FLASH_I", c[1])
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

    def code_translate(self, code, slice_text=False):
        code_banks = []
        code_tmp = []
        labels = {}
        variables = {}
        constants = {}
        offset = 0
        bank = 0
        for t in code:
            opcode = t[0]  # get opcode type
            if opcode == "LABEL":
                q = t[1]  # get symbol
                if variables.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Label {q} is already declared as variable")
                    )
                elif constants.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Label {q} is already declared as constant")
                    )
                elif labels.get(q) is None:
                    labels[q] = (bank, offset)  # Add to symbol table
                else:
                    sys.exit(self._(f"ERROR: Label {q} declared two times!"))
            elif opcode == "CONST":
                p = t[2]  # get value
                q = t[1]  # get symbol
                if variables.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Constant {q} is already declared as variable")
                    )
                elif labels.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Constant {q} is already declared as label")
                    )
                if constants.get(q) is None:
                    constants[q] = p  # Add to symbol table
                else:
                    sys.exit(self._(f"ERROR: Constant {q} declared two times!"))
            elif opcode == "DECLARE":
                p = t[1]  # get variable number
                q = t[2]  # get symbol
                if labels.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Variable {q} is already declared as label")
                    )
                elif constants.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Variable {q} is already declared as constant")
                    )
                elif variables.get(q) is None:
                    variables[q] = p
                else:
                    sys.exit(self._(f"ERROR: Variable {q} declared two times!"))
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
        return (code_banks, labels, variables, constants)

    def constant_calculation(self, constants):
        f_constants = {}
        while len(constants) > 0:
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
                    if c in range(0, 256):
                        f_constants[k] = c
                    else:
                        sys.exit(
                            self._(f"ERROR: Invalid constant value {k} is not a byte!")
                        )
                else:
                    sys.exit(self._(f"ERROR: Invalid constant value {k}, {c}!"))

        return f_constants

    def constant_expression_calculation(self, expression, constants):
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
                if c in range(0, 256):
                    return c
                else:
                    sys.exit(
                        self._(
                            f"ERROR: Invalid constant expression value {c} is not a byte!"
                        )
                    )
            else:
                sys.exit(self._(f"ERROR: Invalid constant expression value {c}!"))

    def symbol_replacement(self, code, symbols, variables, constants):
        code_tmp = []
        queue = []
        for c in code:
            if len(queue) > 0 and c == 0:
                c = queue.pop()
            elif isinstance(
                c, tuple
            ):  # Variable with displacement or constant expression
                if len(c) == 3 and c[0] == "VARIABLE":  # Variable with displacement
                    disp = c[2]
                    c = c[1]
                    if isinstance(c, str):
                        t = variables.get(c)
                        if t is None:
                            # print(variables)
                            sys.exit(self._(f"ERROR: Variable {c} does not exists!"))
                        elif (t + disp) not in range(256):
                            sys.exit(self._(f"ERROR: Array {c} out of bounds!"))
                        else:
                            c = t + disp  # Adds displacement
                    else:
                        c = c + disp
                elif (
                    len(c) == 2 and c[0] == "CONSTANT" and isinstance(c[1], list)
                ):  # Constant expression
                    print(c)
                    c = self.constant_expression_calculation(c[1], constants)
                    print(c)
                else:
                    sys.exit(self._(f"ERROR: Invalid opcode translation!"))
            elif isinstance(c, str):
                t = symbols.get(c)
                if t is None:
                    sys.exit(self._(f"ERROR: Label {c} does not exists!"))
                else:  # label found
                    c = t[0]  # Extract bank
                    queue = self._convert_address(
                        t[1], c
                    )  # Convert offset to bank address
                    queue.reverse()
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

    def generate_code_dsk(
        self, code, tokens, font=None, slice_text=False, show_debug=False
    ):
        if font is None:
            font = CydcFont()
        if self.optimize:
            code = self.code_simple_optimize(code)
        if show_debug:
            for c in code:
                print(c)
        (code, self.symbols, self.variables, self.constants) = self.code_translate(
            code, slice_text
        )
        self.constants = self.constant_calculation(self.constants)
        if show_debug:
            print("\nConstants resolved:\n-------------------")
            print(self.constants)
        self.code = [
            self.symbol_replacement(c, self.symbols, self.variables, self.constants)
            for c in code
        ]
        index = []
        sizes = []
        code = []
        offset = (6 * len(self.code)) + len(tokens)
        offset += len(font.font_chars) + len(font.font_sizes)
        offset += 14 + 2
        for idx, c in enumerate(self.code):
            l = len(c)
            index += self._get_index_offset(idx, offset)
            sizes += self._word_to_list(l)
            code += c
            offset += l
        header = index + sizes + tokens + font.font_chars + font.font_sizes
        header = (
            self._word_to_list(
                14
                + len(sizes)
                + len(index)
                + len(tokens)
                + len(font.font_chars)
                + len(font.font_sizes)
            )
            + header
        )
        header = (
            self._word_to_list(
                14 + len(sizes) + len(index) + len(tokens) + len(font.font_chars)
            )
            + header
        )
        header = self._word_to_list(14 + len(sizes) + len(index) + len(tokens)) + header
        header = self._word_to_list(14 + len(sizes) + len(index)) + header
        header = self._word_to_list(14 + len(index)) + header
        header = self._word_to_list(14) + header
        header = self._word_to_list(len(self.code)) + header
        header = self._word_to_list(len(header)) + header
        return header + code

    def generate_code(self, code, slice_text=False, show_debug=False):
        if self.optimize:
            code = self.code_simple_optimize(code)
        if show_debug:
            for c in code:
                print(c)
        (code, self.symbols, self.variables, self.constants) = self.code_translate(
            code, slice_text
        )
        self.constants = self.constant_calculation(self.constants)
        if show_debug:
            print("\nConstants resolved:\n-------------------")
            print(self.constants)
        self.code = [
            self.symbol_replacement(c, self.symbols, self.variables, self.constants)
            for c in code
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
        all_opcodes = {c for c in self.opcodes.keys() if c not in excluded_ops}
        return all_opcodes - used_opcodes
