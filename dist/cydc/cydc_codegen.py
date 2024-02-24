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
        "IF_EQ_D": 0x09,
        "IF_NE_D": 0x0A,
        "IF_LE_D": 0x0B,
        "IF_ME_D": 0x0C,
        "IF_LT_D": 0x0D,
        "IF_MT_D": 0x0E,
        "ADD_D": 0x0F,
        "SUB_D": 0x10,
        "INK_D": 0x11,
        "PAPER_D": 0x12,
        "BORDER_D": 0x13,
        "PRINT_D": 0x14,
        "SET_I": 0x15,
        "IF_EQ_I": 0x16,
        "IF_NE_I": 0x17,
        "IF_LE_I": 0x18,
        "IF_ME_I": 0x19,
        "IF_LT_I": 0x1A,
        "IF_MT_I": 0x1B,
        "ADD_I": 0x1C,
        "SUB_I": 0x1D,
        "INK_I": 0x1E,
        "PAPER_I": 0x1F,
        "BORDER_I": 0x20,
        "PRINT_I": 0x21,
        "BRIGHT_D": 0x22,
        "FLASH_D": 0x23,
        "BRIGHT_I": 0x24,
        "FLASH_I": 0x25,
        "PICTURE_D": 0x26,
        "DISPLAY_D": 0x27,
        "PICTURE_I": 0x28,
        "DISPLAY_I": 0x29,
        "RANDOM": 0x2A,
        "AND_D": 0x2B,
        "OR_D": 0x2C,
        "AND_I": 0x2D,
        "OR_I": 0x2E,
        "NOT": 0x2F,
        "OPTION": 0x30,
        "WAITKEY": 0x31,
        "INKEY": 0x32,
        "WAIT": 0x33,
        "PAUSE": 0x34,
        "CHOOSE": 0x35,
        "CHOOSE_W": 0x36,
        "TYPERATE": 0x37,
        "CLEAR": 0x38,
        "PAGEPAUSE": 0x39,
        "CHAR": 0x3A,
        "TAB": 0x3B,
        "SFX_D": 0x3C,
        "SFX_I": 0x3D,
        "TRACK_D": 0x3E,
        "TRACK_I": 0x3F,
        "PLAY_D": 0x40,
        "PLAY_I": 0x41,
        "LOOP_D": 0x42,
        "LOOP_I": 0x43,
        "IF_EQ_D_GS": 0x44,
        "IF_NE_D_GS": 0x45,
        "IF_LE_D_GS": 0x46,
        "IF_ME_D_GS": 0x47,
        "IF_LT_D_GS": 0x48,
        "IF_MT_D_GS": 0x49,
        "IF_EQ_I_GS": 0x4A,
        "IF_NE_I_GS": 0x4B,
        "IF_LE_I_GS": 0x4C,
        "IF_ME_I_GS": 0x4D,
        "IF_LT_I_GS": 0x4E,
        "IF_MT_I_GS": 0x4F,
        "REPCHAR": 0x50,
    }

    def __init__(self, gettext):
        self._ = gettext.gettext
        self.symbols = {}
        self.code = []
        self.bank_offset_list = [0xC000]
        self.bank_size_list = [16 * 1024]

    def set_bank_offset_list(self, offset_list):
        if offset_list is not None:
            self.bank_offset_list = offset_list

    def set_bank_size_list(self, size_list):
        if size_list is not None:
            self.bank_size_list = size_list

    def code_translate(self, code, slice_text=False):
        code_banks = []
        code_tmp = []
        labels = {}
        offset = 0
        bank = 0
        for t in code:
            opcode = t[0]  # get opcode type
            if opcode == "LABEL":
                q = t[1]  # get symbol
                if labels.get(q) is None:
                    labels[q] = (bank, offset)  # Add to symbol table
                else:
                    sys.exit(self._(f"ERROR: Label {q} declared two times!"))
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
        return (code_banks, labels)

    def symbol_replacement(self, code, symbols):
        code_tmp = []
        queue = []
        for c in code:
            if len(queue) > 0 and c == 0:
                c = queue.pop()
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

    def generate_code_dsk(self, code, tokens, font=None, slice_text=False):
        if font is None:
            font = CydcFont()
        (code, self.symbols) = self.code_translate(code, slice_text)
        self.code = [self.symbol_replacement(c, self.symbols) for c in code]
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
        (code, self.symbols) = self.code_translate(code, slice_text)
        self.code = [self.symbol_replacement(c, self.symbols) for c in code]
        return self.code
