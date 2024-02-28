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
        "END": 0x0,
        "TEXT": 0x1,
        "GOTO": 0x2,
        "GOSUB": 0x3,
        "RETURN": 0x4,
        "MARGINS": 0x5,
        "CENTER": 0x6,
        "AT": 0x7,
        "SET_D": 0x8,
        "SET_I": 0x9,
        "POP_SET": 0xA,
        "PUSH_D": 0xB,
        "PUSH_I": 0xC,
        "IF_GOTO": 0xD,
        "IF_GOSUB": 0xE,
        "IF_OPTION": 0xF,
        "IF_RETURN": 0x10,
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
        "CHAR": 0x38,
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
    }

    def __init__(self, gettext):
        self._ = gettext.gettext
        self.symbols = {}
        self.variables = {}
        self.code = []
        self.bank_offset_list = [0xC000]
        self.bank_size_list = [16 * 1024]

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
            elif (i+1) < len(code):
                next = code[i+1]
                if next[0] == "POP_SET":
                    if c[0] == "PUSH_D":
                        c = ("SET_D", next[1], c[1])
                        skip = True
                    elif c[0] == "PUSH_I":
                        c = ("SET_I", next[1], c[1])
                        skip = True
                    code_tmp.append(c)
                else:
                    code_tmp.append(c)
            else:
                code_tmp.append(c)
        #print(code)
        #print(code_tmp)
        return code_tmp

    def code_translate(self, code, slice_text=False):
        code_banks = []
        code_tmp = []
        labels = {}
        variables = {}
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
                elif labels.get(q) is None:
                    labels[q] = (bank, offset)  # Add to symbol table
                else:
                    sys.exit(self._(f"ERROR: Label {q} declared two times!"))
            elif opcode == "DECLARE":
                p = t[1]  # get variable number
                q = t[2]  # get symbol
                if labels.get(q) is not None:
                    sys.exit(
                        self._(f"ERROR: Variable {q} is already declared as label")
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
        return (code_banks, labels, variables)

    def symbol_replacement(self, code, symbols, variables):
        code_tmp = []
        queue = []
        for c in code:
            if len(queue) > 0 and c == 0:
                c = queue.pop()
            elif isinstance(c, str):
                t = symbols.get(c)
                if t is None:
                    t = variables.get(c)
                    if t is None:
                        sys.exit(self._(f"ERROR: Symbol {c} does not exists!"))
                    else:
                        c = t
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

    def generate_code_dsk(self, code, tokens, font=None, slice_text=False):
        if font is None:
            font = CydcFont()
        code = self.code_simple_optimize(code)
        (code, self.symbols, self.variables) = self.code_translate(code, slice_text)
        self.code = [
            self.symbol_replacement(c, self.symbols, self.variables) for c in code
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

    def generate_code(self, code, slice_text=False):
        code = self.code_simple_optimize(code)
        (code, self.symbols, self.variables) = self.code_translate(code, slice_text)
        self.code = [
            self.symbol_replacement(c, self.symbols, self.variables) for c in code
        ]
        return self.code
