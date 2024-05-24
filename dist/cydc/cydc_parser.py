#
# MIT License
#
# Copyright (c) 2024 Sergio Chico
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

from ply import yacc as yacc
from cydc_lexer import CydcLexer
from enum import Enum


class SymbolType(Enum):
    LABEL = 1
    VARIABLE = 2


class CydcParser(object):

    def __init__(self):
        self.lexer = CydcLexer()
        self.tokens = self.lexer.get_tokens()
        self.parser = None
        self.errors = list()
        self.symbols = dict()
        self.symbols_used = dict()
        self.hidden_label_counter = 0

    precedence = (
        (
            "nonassoc",
            "NOT_EQUALS",
            "LESS_EQUALS",
            "MORE_EQUALS",
            "LESS_THAN",
            "MORE_THAN",
        ),
        ("left", "SHIFT_L", "SHIFT_R"),
        ("left", "PLUS", "MINUS"),
        ("left", "TIMES", "DIVIDE"),
        ("left", "OR_B"),
        ("left", "AND_B"),
        ("right", "UNOT_B"),
    )

    def p_program(self, p):
        """
        program : program statements_nl
                | program statements
                | statements_nl
                | statements
        """
        if len(p) == 2 and p[1]:
            p[0] = []
            if isinstance(p[1], list):
                p[0] += p[1]
            else:
                p[0].append(p[1])
        elif len(p) == 3:
            p[0] = p[1]
            if not p[0]:
                p[0] = []
            if p[2]:
                if isinstance(p[2], list):
                    p[0] += p[2]
                else:
                    p[0].append(p[2])

    def p_statements_nl(self, p):
        """
        statements_nl   : statements NEWLINE_CHAR
                        | NEWLINE_CHAR
        """
        if len(p) == 2:
            p[0] = None
        elif len(p) == 3 and p[1]:
            p[0] = p[1]

    def p_statements(self, p):
        """
        statements  : statements COLON if_statement
                    | statements COLON loop_statement
                    | statements COLON statement
                    | if_statement
                    | loop_statement
                    | statement
        """
        if (len(p) == 2) and p[1]:
            p[0] = []
            if isinstance(p[1], list):
                p[0] += p[1]
            else:
                p[0].append(p[1])
        elif len(p) == 4:
            p[0] = p[1]
            if not p[0]:
                p[0] = []
            if p[3]:
                if isinstance(p[3], list):
                    p[0] += p[3]
                else:
                    p[0].append(p[3])

    def p_loop_statement(self, p):
        """
        loop_statement : WHILE LPAREN boolexpression RPAREN loop_statement WEND
                       | WHILE LPAREN boolexpression RPAREN loop_subprogram WEND
                       | WHILE LPAREN RPAREN loop_statement WEND
                       | WHILE LPAREN RPAREN loop_subprogram WEND
        """
        if len(p) == 7 and p[3]:
            label_loop = self._get_hidden_label()
            label_end = self._get_hidden_label()

            p[0] = [("LABEL", label_loop)]
            if isinstance(p[3], list):
                p[0] += p[3]
                p[0] += [("IF_N_GOTO", label_end, 0, 0)]
            else:
                p[0] += [p[3], ("IF_N_GOTO", label_end, 0, 0)]

            if p[5]:
                if isinstance(p[5], list):
                    p[0] += p[5]
                else:
                    p[0].append(p[5])

            p[0] += [("GOTO", label_loop, 0, 0), ("LABEL", label_end)]
        elif len(p) == 6:
            label_loop = self._get_hidden_label()
            p[0] = [("LABEL", label_loop)]
            if p[4]:
                if isinstance(p[4], list):
                    p[0] += p[4]
                else:
                    p[0].append(p[4])
            p[0] += [("GOTO", label_loop, 0, 0)]

    def p_loop_subprogram(self, p):
        """
        loop_subprogram : loop_subprogram statements_nl
                        | loop_subprogram statements
                        | statements_nl
                        | statements
                        | loop_empty
        """
        if len(p) == 2:
            p[0] = []
            if p[1]:
                print(p[1])
                if isinstance(p[1], list):
                    p[0] += p[1]
                else:
                    p[0].append(p[1])
        elif len(p) == 3:
            p[0] = p[1]
            if not p[0]:
                p[0] = []
            if p[2]:
                if isinstance(p[2], list):
                    p[0] += p[2]
                else:
                    p[0].append(p[2])

    def p_loop_empty(self, p):
        """
        loop_empty : loop_empty NEWLINE_CHAR
                    | empty
        """
        pass

    def p_if_statement(self, p):
        """
        if_statement :  IF boolexpression then_statement else_statement ENDIF
        """
        if len(p) == 6 and p[2] and p[3]:
            label = self._get_hidden_label()
            p[0] = []
            if isinstance(p[2], list):
                p[0] += p[2]
                p[0] += [("IF_N_GOTO", label, 0, 0)]
            else:
                p[0] += [p[2], ("IF_N_GOTO", label, 0, 0)]

            if p[4]:
                label2 = self._get_hidden_label()
                p[0] += p[3]
                p[0] += [("GOTO", label2, 0, 0), ("LABEL", label)]
                p[0] += p[4]
                p[0] += [("LABEL", label2)]
            else:
                p[0] += p[3]
                p[0] += [("LABEL", label)]

    def p_then_statement(self, p):
        """
        then_statement :   THEN if_statement
                       |   THEN if_subprogram
        """
        if len(p) == 3 and p[2]:
            p[0] = []
            if isinstance(p[2], list):
                p[0] += p[2]
            else:
                p[0].append(p[2])

    def p_else_statement(self, p):
        """
        else_statement :   ELSEIF boolexpression then_statement else_statement
                       |   ELSE if_subprogram
                       |   ELSE if_statement
                       |   empty
        """
        p[0] = []
        if len(p) == 5 and p[1] == "ELSEIF" and p[2] and p[3]:
            label = self._get_hidden_label()
            if isinstance(p[2], list):
                p[0] += p[2]
                p[0] += [("IF_N_GOTO", label, 0, 0)]
            else:
                p[0] += [p[2], ("IF_N_GOTO", label, 0, 0)]
            if p[4]:
                label2 = self._get_hidden_label()
                p[0] += p[3]
                p[0] += [("GOTO", label2, 0, 0), ("LABEL", label)]
                p[0] += p[4]
                p[0] += [("LABEL", label2)]
            else:
                p[0] += p[3]
                p[0] += [("LABEL", label)]
        elif len(p) == 3 and p[2]:
            if isinstance(p[2], list):
                p[0] += p[2]
            else:
                p[0].append(p[2])

    def p_if_subprogram(self, p):
        """
        if_subprogram : if_subprogram statements_nl
                        | if_subprogram statements
                        | statements_nl
                        | statements
        """
        if len(p) == 2 and p[1]:
            p[0] = []
            if isinstance(p[1], list):
                p[0] += p[1]
            else:
                p[0].append(p[1])
        elif len(p) == 3:
            p[0] = p[1]
            if not p[0]:
                p[0] = []
            if p[2]:
                if isinstance(p[2], list):
                    p[0] += p[2]
                else:
                    p[0].append(p[2])

    def p_statement_close_error(self, p):
        "statement : ERROR_CLOSE_TEXT"
        self.errors.append(f"Invalid opening code token in line {p[1]}")
        p[0] = None

    def p_statement_text_error(self, p):
        "statement : ERROR_TEXT"
        for err in p[1]:
            self.errors.append(
                f"Invalid character '{err[2]}' ({ord(err[2])}) in line {err[0]} and position {err[1]}"
            )
        p[0] = None

    def p_statement_text(self, p):
        "statement : TEXT"
        p[0] = p[1]

    def p_statement_short_label(self, p):
        "statement : SHORT_LABEL"
        if self._declare_symbol(p[1], SymbolType.LABEL, p.lexer.lexer.lineno):
            p[0] = ("LABEL", p[1])
        else:
            p[0] = None

    def p_statement_end(self, p):
        "statement : END"
        p[0] = ("END",)

    def p_statement_return(self, p):
        "statement : RETURN"
        p[0] = ("RETURN",)

    def p_statement_center(self, p):
        "statement : CENTER"
        p[0] = ("CENTER",)

    def p_statement_waitkey(self, p):
        "statement : WAITKEY"
        p[0] = ("WAITKEY",)

    def p_statement_clear(self, p):
        "statement : CLEAR"
        p[0] = ("CLEAR",)

    def p_statement_clearoptions(self, p):
        "statement : CLEAROPTIONS"
        p[0] = ("CLEAR_OPTIONS",)

    def p_statement_randomize(self, p):
        "statement : RANDOMIZE"
        p[0] = ("RANDOMIZE",)

    def p_statement_goto(self, p):
        "statement : GOTO ID"
        if self._symbol_usage(p[2], SymbolType.LABEL, p.lexer.lexer.lineno):
            p[0] = ("GOTO", p[2], 0, 0)
        else:
            p[0] = None

    def p_statement_gosub(self, p):
        "statement : GOSUB ID"
        if self._symbol_usage(p[2], SymbolType.LABEL, p.lexer.lexer.lineno):
            p[0] = ("GOSUB", p[2], 0, 0)
        else:
            p[0] = None

    def p_statement_label(self, p):
        "statement : LABEL ID"
        if self._declare_symbol(p[2], SymbolType.LABEL, p.lexer.lexer.lineno):
            p[0] = ("LABEL", p[2])
        else:
            p[0] = None

    def p_statement_backspace(self, p):
        """
        statement : BACKSPACE expression
                  | BACKSPACE
        """
        if len(p) == 3 and p[2]:
            if self._check_byte_value(p[2], p.lexer.lexer.lineno):
                p[0] = ("BACKSPACE", p[2])
            else:
                p[0] = None
        elif len(p) == 2:
            p[0] = ("BACKSPACE", 1)

    def p_statement_newline(self, p):
        """
        statement : NEWLINE expression
                  | NEWLINE
        """
        if len(p) == 3 and p[2]:
            if self._check_byte_value(p[2], p.lexer.lexer.lineno):
                p[0] = ("NEWLINE", p[2])
            else:
                p[0] = None
        elif len(p) == 2:
            p[0] = ("NEWLINE", 1)

    def p_statement_tab(self, p):
        "statement : TAB expression"
        if self._check_byte_value(p[2], p.lexer.lexer.lineno):
            p[0] = ("TAB", p[2])
        else:
            p[0] = None

    def p_statement_page_pause(self, p):
        "statement : PAGEPAUSE expression"
        if self._check_byte_value(p[2], p.lexer.lexer.lineno):
            p[0] = ("PAGEPAUSE", p[2])
        else:
            p[0] = None

    def p_statement_char(self, p):
        "statement : CHAR numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_CHAR",))

    def p_statement_print(self, p):
        "statement : PRINT numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_PRINT",))

    def p_statement_ink(self, p):
        "statement : INK numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_INK",))

    def p_statement_paper(self, p):
        "statement : PAPER numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_PAPER",))

    def p_statement_border(self, p):
        "statement : BORDER numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_BORDER",))

    def p_statement_bright(self, p):
        "statement : BRIGHT numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_BRIGHT",))

    def p_statement_flash(self, p):
        "statement : FLASH numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_FLASH",))

    def p_statement_sfx(self, p):
        "statement : SFX numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_SFX",))

    def p_statement_display(self, p):
        "statement : DISPLAY numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_DISPLAY",))

    def p_statement_picture(self, p):
        "statement : PICTURE numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_PICTURE",))

    def p_statement_track(self, p):
        "statement : TRACK numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_TRACK",))

    def p_statement_play(self, p):
        "statement : PLAY numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_PLAY",))

    def p_statement_loop(self, p):
        "statement : LOOP numexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_LOOP",))

    def p_statement_load(self, p):
        "statement : LOAD numexpression"
        if len(p) == 3 and p[2]:
            if isinstance(p[2], list):
                p[0] = p[2]
            else:
                p[0] = [p[2]]
            p[0].append(("POP_SLOT_LOAD",))
        else:
            p[0] = None

    def p_statement_wait(self, p):
        "statement : WAIT expression"
        if self._check_word_value(p[2], p.lexer.lexer.lineno):
            p[0] = ("WAIT", p[2] & 0xFF, (p[2] >> 8) & 0xFF)
        else:
            p[0] = None

    def p_statement_pause(self, p):
        "statement : PAUSE expression"
        if self._check_word_value(p[2], p.lexer.lexer.lineno):
            p[0] = ("PAUSE", p[2] & 0xFF, (p[2] >> 8) & 0xFF)
        else:
            p[0] = None

    def p_statement_typerate(self, p):
        "statement : TYPERATE expression"
        if self._check_word_value(p[2], p.lexer.lexer.lineno):
            p[0] = ("TYPERATE", p[2] & 0xFF, (p[2] >> 8) & 0xFF)
        else:
            p[0] = None

    def p_statement_window(self, p):
        "statement : WINDOW expression"
        if len(p) == 3 and self._check_byte_value(p[2], p.lexer.lexer.lineno):
            p[0] = ("WINDOW", p[2] & 0x07)
        else:
            p[0] = None

    def p_statement_blit(self, p):
        "statement : BLIT numexpression COMMA numexpression COMMA numexpression COMMA numexpression AT numexpression COMMA numexpression"
        if len(p) == 13:
            if (
                isinstance(p[2], tuple)
                and isinstance(p[4], tuple)
                and isinstance(p[6], tuple)
                and isinstance(p[8], tuple)
            ):
                t1 = p[2]
                t2 = p[4]
                t3 = p[6]
                t4 = p[8]
                if (
                    (t1[0] == "PUSH_D")
                    and (t2[0] == "PUSH_D")
                    and (t3[0] == "PUSH_D")
                    and (t4[0] == "PUSH_D")
                    and isinstance(t1[1], int)
                    and isinstance(t2[1], int)
                    and isinstance(t3[1], int)
                    and isinstance(t4[1], int)
                ):
                    (row, col, width, height) = self._fix_borders(
                        t2[1], t1[1], t3[1], t4[1]
                    )
                    if isinstance(p[10], tuple) and isinstance(p[12], tuple):
                        t1 = p[10]
                        t2 = p[12]
                        if (
                            (t1[0] == "PUSH_D")
                            and (t2[0] == "PUSH_D")
                            and isinstance(t1[1], int)
                            and isinstance(t2[1], int)
                        ):
                            row_d = t2[1]
                            col_d = t1[1]
                            if row_d >= 24:
                                row_d = 23
                            if col_d >= 32:
                                col_d = 31
                            if row_d < 0:
                                row_d = 0
                            if col_d < 0:
                                col_d = 0
                            p[0] = ("BLIT", col, row, width, height, col_d, row_d)
                        else:
                            p[0] = [t1, t2, ("POP_BLIT", col, row, width, height)]
                    else:
                        if isinstance(p[10], list):
                            p[0] = p[10]
                        else:
                            p[0] = [p[10]]
                        if isinstance(p[12], list):
                            p[0] += p[12]
                        else:
                            p[0] += [p[12]]
                        p[0] += [("POP_BLIT", col, row, width, height)]
                else:
                    if isinstance(p[2], list):
                        p[0] = p[2]
                    else:
                        p[0] = [p[2]]
                    if isinstance(p[4], list):
                        p[0] += p[4]
                    else:
                        p[0] += [p[4]]
                    if isinstance(p[6], list):
                        p[0] += p[6]
                    else:
                        p[0] += [p[6]]
                    if isinstance(p[8], list):
                        p[0] += p[8]
                    else:
                        p[0] += [p[8]]
                    if isinstance(p[10], list):
                        p[0] += p[10]
                    else:
                        p[0] += [p[10]]
                    if isinstance(p[12], list):
                        p[0] += p[12]
                    else:
                        p[0] += [p[12]]
                    p[0] += [("POP_ALL_BLIT",)]
            else:
                if isinstance(p[2], list):
                    p[0] = p[2]
                else:
                    p[0] = [p[2]]
                if isinstance(p[4], list):
                    p[0] += p[4]
                else:
                    p[0] += [p[4]]
                if isinstance(p[6], list):
                    p[0] += p[6]
                else:
                    p[0] += [p[6]]
                if isinstance(p[8], list):
                    p[0] += p[8]
                else:
                    p[0] += [p[8]]
                if isinstance(p[10], list):
                    p[0] += p[10]
                else:
                    p[0] += [p[10]]
                if isinstance(p[12], list):
                    p[0] += p[12]
                else:
                    p[0] += [p[12]]
                p[0] += [("POP_ALL_BLIT",)]

    def p_statement_fillattr(self, p):
        "statement : FILLATTR numexpression COMMA numexpression COMMA numexpression COMMA numexpression COMMA numexpression"
        if len(p) == 11:
            col = None
            row = None
            width = None
            height = None
            attr = None
            if isinstance(p[2], tuple):
                t1 = p[2]
                if (t1[0] == "PUSH_D") and isinstance(t1[1], int):
                    col = t1[1]
            if isinstance(p[4], tuple):
                t1 = p[4]
                if (t1[1] == "PUSH_D") and isinstance(t1[1], int):
                    row = t1[1]
            if isinstance(p[6], tuple):
                t1 = p[6]
                if (t1[0] == "PUSH_D") and isinstance(t1[1], int):
                    width = t1[1]
            if isinstance(p[8], tuple):
                t1 = p[8]
                if (t1[0] == "PUSH_D") and isinstance(t1[1], int):
                    height = t1[1]
            if isinstance(p[10], tuple):
                t1 = p[10]
                if (t1[0] == "PUSH_D") and isinstance(t1[1], int):
                    attr = t1[1]
            if (
                col is not None
                and row is not None
                and width is not None
                and height is not None
                and attr is not None
            ):
                p[0] = ("FILLATTR", col, row, width, height, attr)
            else:
                if isinstance(p[2], list):
                    p[0] = p[2]
                else:
                    p[0] = [p[2]]
                if isinstance(p[4], list):
                    p[0] += p[4]
                else:
                    p[0] += [p[4]]
                if isinstance(p[6], list):
                    p[0] += p[6]
                else:
                    p[0] += [p[6]]
                if isinstance(p[8], list):
                    p[0] += p[8]
                else:
                    p[0] += [p[8]]
                if isinstance(p[10], list):
                    p[0] += p[10]
                else:
                    p[0] += [p[10]]
                p[0] += [("POP_FILLATTR",)]

    def p_statement_fadeout(self, p):
        """
        statement : FADEOUT expression COMMA expression COMMA expression COMMA expression
        """
        if len(p) == 9:
            if (
                self._check_byte_value(p[2], p.lexer.lexer.lineno)
                and self._check_byte_value(p[4], p.lexer.lexer.lineno)
                and self._check_byte_value(p[6], p.lexer.lexer.lineno)
                and self._check_byte_value(p[8], p.lexer.lexer.lineno)
            ):
                (row, col, width, height) = self._fix_borders(p[4], p[2], p[6], p[8])
                p[0] = ("FADEOUT", col, row, width, height)
            else:
                p[0] = None

    def p_statement_margins(self, p):
        "statement : MARGINS expression COMMA expression COMMA expression COMMA expression"
        if len(p) == 9:
            if (
                self._check_byte_value(p[2], p.lexer.lexer.lineno)
                and self._check_byte_value(p[4], p.lexer.lexer.lineno)
                and self._check_byte_value(p[6], p.lexer.lexer.lineno)
                and self._check_byte_value(p[8], p.lexer.lexer.lineno)
            ):
                (row, col, width, height) = self._fix_borders(p[4], p[2], p[6], p[8])
                p[0] = ("MARGINS", col, row, width, height)
            else:
                p[0] = None

    def p_statement_putattr(self, p):
        """
        statement : PUTATTR numexpression COMMA numexpression AT numexpression COMMA numexpression
                  | PUTATTR numexpression AT numexpression COMMA numexpression
        """
        if len(p) == 9:
            attr = None
            mask = None
            row = None
            col = None
            if isinstance(p[2], tuple):
                t1 = p[2]
                if (t1[0] == "PUSH_D") and isinstance(t1[1], int):
                    attr = t1[1]
            if isinstance(p[4], tuple):
                t2 = p[4]
                if (t2[0] == "PUSH_D") and isinstance(t2[1], int):
                    mask = t2[1]
            if isinstance(p[6], tuple):
                t3 = p[6]
                if (t3[0] == "PUSH_D") and isinstance(t3[1], int):
                    col = t3[1]
            if isinstance(p[8], tuple):
                t4 = p[8]
                if (t4[0] == "PUSH_D") and isinstance(t4[1], int):
                    row = t4[1]
            if attr is not None and mask is not None:
                if row is not None and col is not None:
                    p[0] = ("PUTATTR", col, row, mask, attr)
                else:
                    if isinstance(p[6], list):
                        p[0] = p[6]
                    else:
                        p[0] = [p[6]]
                    if isinstance(p[8], list):
                        p[0] += p[8]
                    else:
                        p[0] += [p[8]]
                    p[0] += [("POP_PUTATTR", mask, attr)]
            else:
                if isinstance(p[2], list):
                    p[0] = p[2]
                else:
                    p[0] = [p[2]]
                if isinstance(p[4], list):
                    p[0] += p[4]
                else:
                    p[0] += [p[4]]
                if isinstance(p[6], list):
                    p[0] += p[6]
                else:
                    p[0] = [p[6]]
                if isinstance(p[8], list):
                    p[0] += p[8]
                else:
                    p[0] += [p[8]]
                p[0] += [("POP_ALL_PUTATTR",)]
        elif len(p) == 7:
            attr = None
            row = None
            col = None
            if isinstance(p[2], tuple):
                t1 = p[2]
                if (t1[0] == "PUSH_D") and isinstance(t1[1], int):
                    attr = t1[1]
            if isinstance(p[4], tuple):
                t2 = p[4]
                if (t2[0] == "PUSH_D") and isinstance(t2[1], int):
                    col = t2[1]
            if isinstance(p[6], tuple):
                t3 = p[6]
                if (t3[0] == "PUSH_D") and isinstance(t3[1], int):
                    row = t3[1]
            if attr is not None:
                if row is not None and col is not None:
                    p[0] = ("PUTATTR", col, row, 0xFF, attr)
                else:
                    if isinstance(p[4], list):
                        p[0] = p[4]
                    else:
                        p[0] = [p[4]]
                    if isinstance(p[6], list):
                        p[0] += p[6]
                    else:
                        p[0] += [p[6]]
                    p[0] += [("POP_PUTATTR", 0xFF, attr)]
            else:
                if isinstance(p[2], list):
                    p[0] = p[2]
                else:
                    p[0] = [p[2]]
                p[0] += [("PUSH_D", 0xFF)]
                if isinstance(p[4], list):
                    p[0] += p[4]
                else:
                    p[0] = [p[4]]
                if isinstance(p[6], list):
                    p[0] += p[6]
                else:
                    p[0] += [p[6]]
                p[0] += [("POP_ALL_PUTATTR",)]

    def p_statement_at(self, p):
        "statement : AT numexpression COMMA numexpression"
        if len(p) == 5:
            col_d = None
            row_d = None
            if isinstance(p[2], tuple):
                t1 = p[2]
                if (t1[0] == "PUSH_D") and isinstance(t1[1], int):
                    col_d = t1[1]
                    if col_d >= 32:
                        col_d = 31
                    if col_d < 0:
                        col_d = 0
            if isinstance(p[4], tuple):
                t2 = p[4]
                if (t2[0] == "PUSH_D") and isinstance(t2[1], int):
                    row_d = t2[1]
                    if row_d >= 24:
                        row_d = 23
                    if row_d < 0:
                        row_d = 0
            if col_d is not None and row_d is not None:
                p[0] = ("AT", col_d, row_d)
            else:
                if isinstance(p[2], list):
                    p[0] = p[2]
                else:
                    p[0] = [p[2]]
                if isinstance(p[4], list):
                    p[0] += p[4]
                else:
                    p[0] += [p[4]]
                p[0] += [("POP_AT",)]

    def p_statement_menuconfig(self, p):
        """
        statement : MENUCONFIG numexpression COMMA numexpression COMMA numexpression
                  | MENUCONFIG numexpression COMMA numexpression
        """
        if len(p) in [7, 5]:
            col_d = None
            row_d = None
            init_d = None
            if isinstance(p[2], tuple):
                t1 = p[2]
                if (t1[0] == "PUSH_D") and isinstance(t1[1], int):
                    col_d = t1[1]
                    if col_d >= 32:
                        col_d = 31
                    if col_d < 0:
                        col_d = 0
            if isinstance(p[4], tuple):
                t2 = p[4]
                if (t2[0] == "PUSH_D") and isinstance(t2[1], int):
                    row_d = t2[1]
                    if row_d >= 32:
                        row_d = 31
                    if row_d < 0:
                        row_d = 0
            if len(p) == 5:
                init_d = 0
            elif isinstance(p[6], tuple):
                t3 = p[6]
                if (t3[0] == "PUSH_D") and isinstance(t3[1], int):
                    init_d = t3[1]
                    if init_d >= 32:
                        init_d = 0
            if col_d is not None and row_d is not None and init_d is not None:
                p[0] = ("MENUCONFIG", col_d, row_d, init_d)
            else:
                if isinstance(p[2], list):
                    p[0] = p[2]
                else:
                    p[0] = [p[2]]
                if isinstance(p[4], list):
                    p[0] += p[4]
                else:
                    p[0] += [p[4]]
                if init_d is not None and isinstance(init_d, int):
                    p[0] += [("PUSH_D", init_d)]
                elif isinstance(p[6], list):
                    p[0] += p[6]
                else:
                    p[0] += [p[6]]
                p[0] += [("POP_MENUCONFIG",)]

    def p_statement_save(self, p):
        """
        statement : SAVE numexpression COMMA variableID COMMA expression
                  | SAVE numexpression COMMA variableID
                  | SAVE numexpression
        """
        if len(p) == 7 and p[2] and self._is_valid_var(p[4]):
            if self._check_byte_value(p[6], p.lexer.lexer.lineno):
                if isinstance(p[2], list):
                    p[0] = p[2]
                else:
                    p[0] = [p[2]]
                p[0].append(("POP_SLOT_SAVE", (p[4], 0), p[6]))
            else:
                p[0] = None
        elif len(p) == 5 and p[2] and self._is_valid_var(p[4]):
            if isinstance(p[2], list):
                p[0] = p[2]
            else:
                p[0] = [p[2]]
            p[0].append(("POP_SLOT_SAVE", (p[4], 0), 0))
        elif len(p) == 3 and p[2]:
            if isinstance(p[2], list):
                p[0] = p[2]
            else:
                p[0] = [p[2]]
            p[0].append(("POP_SLOT_SAVE", 0, 0))

    def p_statement_ramload(self, p):
        """
        statement : RAMLOAD variableID COMMA expression
                  | RAMLOAD variableID
                  | RAMLOAD
        """
        if len(p) == 5 and self._is_valid_var(p[2]):
            if self._check_byte_value(p[4], p.lexer.lexer.lineno):
                p[0] = ("RAMLOAD", (p[2], 0), p[4])
            else:
                p[0] = None
        elif len(p) == 3 and self._is_valid_var(p[2]):
            p[0] = ("RAMLOAD", (p[2], 0), 0)
        elif len(p) == 2:
            p[0] = ("RAMLOAD", 0, 0)

    def p_statement_ramsave(self, p):
        """
        statement : RAMSAVE variableID COMMA expression
                  | RAMSAVE variableID
                  | RAMSAVE
        """
        if len(p) == 5 and self._is_valid_var(p[2]):
            if self._check_byte_value(p[4], p.lexer.lexer.lineno):
                p[0] = ("RAMSAVE", (p[2], 0), p[4])
            else:
                p[0] = None
        elif len(p) == 3 and self._is_valid_var(p[2]):
            p[0] = ("RAMSAVE", (p[2], 0), 0)
        elif len(p) == 2:
            p[0] = ("RAMSAVE", 0, 0)

    def p_statement_repchar(self, p):
        "statement : REPCHAR expression COMMA expression"
        if self._check_byte_value(
            p[2], p.lexer.lexer.lineno
        ) and self._check_byte_value(p[4], p.lexer.lexer.lineno):
            p[0] = ("REPCHAR", p[2], p[4])
        else:
            p[0] = None

    def p_statement_declare(self, p):
        "statement : DECLARE expression AS ID"
        if self._check_byte_value(p[2], p.lexer.lexer.lineno):
            if self._declare_symbol(p[4], SymbolType.VARIABLE, p.lexer.lexer.lineno):
                p[0] = ("DECLARE", p[2], p[4])
            else:
                p[0] = None
        else:
            p[0] = None

    def p_statement_set_ind_array(self, p):
        """
        statement : SET LCARET variableID RCARET TO LCURLY numexpressions_list RCURLY
                  | LET LCARET variableID RCARET EQUALS LCURLY numexpressions_list RCURLY
        """
        if len(p) == 9 and self._is_valid_var(p[3]) and isinstance(p[7], list):
            p[0] = []
            for i, c in enumerate(p[7]):
                if isinstance(c, list):
                    p[0] += c
                    p[0].append(("POP_SET_DI", (p[3], i)))
                else:
                    p[0] = None
                    break
        else:
            p[0] = None

    def p_statement_set_dir_array(self, p):
        """
        statement : SET variableID TO LCURLY numexpressions_list RCURLY
                  | LET variableID EQUALS LCURLY numexpressions_list RCURLY
        """
        if len(p) == 7 and self._is_valid_var(p[2]) and isinstance(p[5], list):
            p[0] = []
            for i, c in enumerate(p[5]):
                if isinstance(c, list):
                    p[0] += c
                    p[0].append(("POP_SET", (p[2], i)))
                else:
                    p[0] = None
                    break
        else:
            p[0] = None

    def p_statement_set_ind(self, p):
        """
        statement : SET LCARET variableID RCARET TO numexpression
                  | LET LCARET variableID RCARET EQUALS numexpression
        """
        if len(p) == 7 and self._is_valid_var(p[3]):
            if isinstance(p[6], list):
                p[0] = p[6]
            else:
                p[0] = [p[6]]
            p[0].append(("POP_SET_DI", (p[3], 0)))

    def p_statement_set_dir(self, p):
        """
        statement : SET variableID TO numexpression
                  | LET variableID EQUALS numexpression
        """
        if len(p) == 5 and self._is_valid_var(p[2]):
            if isinstance(p[4], list):
                p[0] = p[4]
            else:
                p[0] = [p[4]]
            p[0].append(("POP_SET", (p[2], 0)))

    def p_statement_choose(self, p):
        """
        statement : CHOOSE IF WAIT expression THEN GOTO ID
                  | CHOOSE IF WAIT expression THEN GOSUB ID
                  | CHOOSE IF CHANGED THEN GOSUB ID
                  | CHOOSE
        """
        if len(p) == 8 and p[3] == "WAIT":
            if self._check_word_value(
                p[4], p.lexer.lexer.lineno
            ) and self._symbol_usage(p[7], SymbolType.LABEL, p.lexer.lexer.lineno):
                if p[6] == "GOTO":
                    p[0] = (
                        "CHOOSE_W",
                        p[4] & 0xFF,
                        (p[4] >> 8) & 0xFF,
                        0x00,
                        p[7],
                        0,
                        0,
                    )
                elif p[6] == "GOSUB":
                    p[0] = (
                        "CHOOSE_W",
                        p[4] & 0xFF,
                        (p[4] >> 8) & 0xFF,
                        0xFF,
                        p[7],
                        0,
                        0,
                    )
                else:
                    p[0] = None
            else:
                p[0] = None
        elif len(p) == 7 and p[3] == "CHANGED":
            if self._symbol_usage(p[6], SymbolType.LABEL, p.lexer.lexer.lineno):
                p[0] = ("CHOOSE_CH", p[6], 0, 0)
            else:
                p[0] = None
        elif len(p) == 2:
            p[0] = ("CHOOSE",)

    def p_statement_option_goto(self, p):
        """
        statement : OPTION VALUE LPAREN numexpression RPAREN GOTO ID
                  | OPTION GOTO ID
        """
        if len(p) == 8 and self._symbol_usage(
            p[7], SymbolType.LABEL, p.lexer.lexer.lineno
        ):
            if isinstance(p[4], list):
                p[0] = p[4]
            else:
                p[0] = [p[4]]
            p[0] += [("POP_VAL_OPTION", 0, p[7], 0, 0)]
        elif len(p) == 4 and self._symbol_usage(
            p[3], SymbolType.LABEL, p.lexer.lexer.lineno
        ):
            p[0] = ("OPTION", 0, p[3], 0, 0)
        else:
            p[0] = None

    def p_statement_option_gosub(self, p):
        """
        statement : OPTION VALUE LPAREN numexpression RPAREN GOSUB ID
                  | OPTION GOSUB ID
        """
        if len(p) == 8 and self._symbol_usage(
            p[7], SymbolType.LABEL, p.lexer.lexer.lineno
        ):
            if isinstance(p[4], list):
                p[0] = p[4]
            else:
                p[0] = [p[4]]
            p[0] += [("POP_VAL_OPTION", 0xFF, p[7], 0, 0)]
        elif len(p) == 4 and self._symbol_usage(
            p[3], SymbolType.LABEL, p.lexer.lexer.lineno
        ):
            p[0] = ("OPTION", 0xFF, p[3], 0, 0)
        else:
            p[0] = None

    def p_numexpressions_list(self, p):
        """
        numexpressions_list : numexpressions_list COMMA numexpression
                            | numexpression
        """
        if len(p) == 2 and p[1]:
            p[0] = []
            if isinstance(p[1], list):
                p[0].append(p[1])
            else:
                p[0].append([p[1]])
        elif len(p) == 4:
            p[0] = p[1]
            if not p[0]:
                p[0] = []
            if p[3]:
                if isinstance(p[3], list):
                    p[0].append(p[3])
                else:
                    p[0].append([p[3]])

    def p_boolexpression_binop(self, p):
        """
        boolexpression  : boolexpression AND boolexpression
                        | boolexpression OR boolexpression
        """
        if isinstance(p[1], list):
            p[0] = p[1]
        else:
            p[0] = [p[1]]

        if isinstance(p[3], list):
            p[0] += p[3]
        else:
            p[0].append(p[3])

        if p[2].upper() == "AND":
            p[0].append(("AND",))
        elif p[2].upper() == "OR":
            p[0].append(("OR",))
        else:
            p[0] = None

    def p_boolexpression_unop(self, p):
        "boolexpression : NOT boolexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
            p[0].append(("NOT",))
        else:
            p[0] = [p[2], ("NOT",)]

    def p_boolexpression_group(self, p):
        "boolexpression : LPAREN boolexpression RPAREN"
        p[0] = p[2]

    def p_boolexpression_cmp_op(self, p):
        """
        boolexpression : numexpression NOT_EQUALS numexpression
                  | numexpression LESS_EQUALS numexpression
                  | numexpression MORE_EQUALS numexpression
                  | numexpression EQUALS numexpression
                  | numexpression LESS_THAN numexpression
                  | numexpression MORE_THAN numexpression
        """
        if isinstance(p[1], list):
            p[0] = p[1]
        else:
            p[0] = [p[1]]

        if isinstance(p[3], list):
            p[0] += p[3]
        else:
            p[0].append(p[3])

        if p[2] == "<>":
            p[0].append(("CP_NE",))
        elif p[2] == "<=":
            p[0].append(("CP_LE",))
        elif p[2] == ">=":
            p[0].append(("CP_ME",))
        elif p[2] == "=":
            p[0].append(("CP_EQ",))
        elif p[2] == "<":
            p[0].append(("CP_LT",))
        elif p[2] == ">":
            p[0].append(("CP_MT",))

    def p_numexpression_binop(self, p):
        """
        numexpression : numexpression PLUS numexpression
                  | numexpression MINUS numexpression
                  | numexpression AND_B numexpression
                  | numexpression OR_B numexpression
                  | numexpression SHIFT_L numexpression
                  | numexpression SHIFT_R numexpression
        """
        if len(p) == 4 and p[1] and p[3]:
            p[0] = []
            if isinstance(p[1], list):
                p[0] += p[1]
            else:
                p[0].append(p[1])

            if isinstance(p[3], list):
                p[0] += p[3]
            else:
                p[0].append(p[3])

            if p[2] == "+":
                p[0].append(("ADD",))
            elif p[2] == "-":
                p[0].append(("SUB",))
            elif p[2] == "&":
                p[0].append(("AND",))
            elif p[2] == "|":
                p[0].append(("OR",))
            elif p[2] == "<<":
                p[0].append(("SHIFT_L",))
            elif p[2] == ">>":
                p[0].append(("SHIFT_R",))

    def p_numexpression_min(self, p):
        """
        numexpression : MIN LPAREN numexpression COMMA numexpression RPAREN
        """
        if len(p) == 4 and p[3] and p[5]:
            p[0] = []
            if isinstance(p[3], list):
                p[0] += p[3]
            else:
                p[0].append(p[3])

            if isinstance(p[5], list):
                p[0] += p[5]
            else:
                p[0].append(p[5])

            p[0].append(("MIN",))

    def p_numexpression_max(self, p):
        """
        numexpression : MAX LPAREN numexpression COMMA numexpression RPAREN
        """
        if len(p) == 4 and p[3] and p[5]:
            p[0] = []
            if isinstance(p[3], list):
                p[0] += p[3]
            else:
                p[0].append(p[3])

            if isinstance(p[5], list):
                p[0] += p[5]
            else:
                p[0].append(p[5])

            p[0].append(("MAX",))

    def p_numexpression_unop(self, p):
        "numexpression : NOT_B numexpression %prec UNOT_B"
        if isinstance(p[2], list):
            p[0] = p[2].append(("NOT_B",))
        else:
            p[0] = [p[2], ("NOT_B",)]

    def p_numexpression_group(self, p):
        "numexpression : LPAREN numexpression RPAREN"
        p[0] = p[2]

    def p_numexpression_variable_ind(self, p):
        "numexpression : LCARET numexpression RCARET"
        if len(p) == 4 and p[2]:
            if isinstance(p[2], list):
                p[0] = p[2]
            else:
                p[0] = [p[2]]
            p[0].append(("POP_PUSH_I",))

    def p_numexpression_get_attr(self, p):
        "numexpression : GETATTR LPAREN numexpression COMMA numexpression RPAREN"
        if len(p) == 7 and p[3] and p[5]:
            if isinstance(p[3], list):
                p[0] = p[3]
            else:
                p[0] = [p[3]]
            if isinstance(p[5], list):
                p[0] += p[5]
            else:
                p[0] += [p[5]]
            p[0].append(("PUSH_GET_ATTR",))
        else:
            p[0] = None

    def p_numexpression_variable_addr(self, p):
        "numexpression : AT_CHAR AT_CHAR variableID"
        if self._is_valid_var(p[3]):
            p[0] = ("PUSH_D", (p[3], 0))
        else:
            p[0] = None

    def p_numexpression_variable(self, p):
        "numexpression : AT_CHAR variableID"
        if self._is_valid_var(p[2]):
            p[0] = ("PUSH_I", (p[2], 0))
        else:
            p[0] = None

    def p_numexpression_saveresult_expression(self, p):
        "numexpression : SAVERESULT LPAREN RPAREN"
        p[0] = ("PUSH_SAVE_RESULT",)

    def p_numexpression_optionval(self, p):
        "numexpression : OPTIONVAL LPAREN RPAREN"
        if len(p) == 4:
            p[0] = ("PUSH_OPTION_ST", 2)

    def p_numexpression_optionsel(self, p):
        "numexpression : OPTIONSEL LPAREN RPAREN"
        if len(p) == 4:
            p[0] = ("PUSH_OPTION_ST", 1)

    def p_numexpression_numoptions(self, p):
        "numexpression : NUMOPTIONS LPAREN RPAREN"
        if len(p) == 4:
            p[0] = ("PUSH_OPTION_ST", 0)

    def p_numexpression_attrval_expression(self, p):
        "numexpression : ATTRVAL LPAREN expression COMMA expression COMMA expression COMMA expression RPAREN"
        if len(p) == 11:
            if (
                self._check_byte_value(p[3], p.lexer.lexer.lineno)
                and self._check_byte_value(p[5], p.lexer.lexer.lineno)
                and self._check_byte_value(p[7], p.lexer.lexer.lineno)
                and self._check_byte_value(p[9], p.lexer.lexer.lineno)
            ):
                attr = self._check_attr_values(
                    p[3], p[5], p[7], p[9], p.lexer.lexer.lineno
                )
                if attr is not None:
                    p[0] = ("PUSH_D", attr)
                else:
                    p[0] = None

    def p_numexpression_attrmask_expression(self, p):
        "numexpression : ATTRMASK LPAREN expression COMMA expression COMMA expression COMMA expression RPAREN"
        if len(p) == 11:
            if (
                self._check_byte_value(p[3], p.lexer.lexer.lineno)
                and self._check_byte_value(p[5], p.lexer.lexer.lineno)
                and self._check_byte_value(p[7], p.lexer.lexer.lineno)
                and self._check_byte_value(p[9], p.lexer.lexer.lineno)
            ):
                mask = self._get_attr_mask(p[3], p[5], p[7], p[9], p.lexer.lexer.lineno)
                if mask is not None:
                    p[0] = ("PUSH_D", mask)
                else:
                    p[0] = None

    def p_numexpression_random_expression_limit(self, p):
        "numexpression : RANDOM LPAREN expression COMMA expression RPAREN"
        if self._check_byte_value(
            p[3], p.lexer.lexer.lineno
        ) and self._check_byte_value(p[5], p.lexer.lexer.lineno):
            limit = p[5] - p[3]
            if limit <= 0 or limit > 255:
                self.errors.append(f"Invalid values on RANDOM({p[3]}, {p[5]})")
                p[0] = None
            else:
                p[0] = [
                    ("PUSH_RANDOM", limit),
                    ("PUSH_D", p[3]),
                    ("ADD",),
                ]
        else:
            p[0] = None

    def p_numexpression_random_expression(self, p):
        """
        numexpression : RANDOM LPAREN expression RPAREN
                      | RANDOM LPAREN RPAREN
        """
        if len(p) == 5:
            if self._check_byte_value(p[3], p.lexer.lexer.lineno):
                p[0] = ("PUSH_RANDOM", p[3])
            else:
                p[0] = None
        elif len(p) == 4:
            p[0] = ("PUSH_RANDOM", 0)

    def p_numexpression_inkey_expression(self, p):
        "numexpression : INKEY LPAREN expression RPAREN"
        if self._check_byte_value(p[3], p.lexer.lexer.lineno):
            p[0] = ("PUSH_INKEY", p[3])
        else:
            p[0] = None

    def p_numexpression_inkey(self, p):
        "numexpression : INKEY LPAREN RPAREN"
        p[0] = ("PUSH_INKEY", 0)

    def p_numexpression_xpos(self, p):
        "numexpression : XPOS LPAREN RPAREN"
        p[0] = ("PUSH_XPOS",)

    def p_numexpression_ypos(self, p):
        "numexpression : YPOS LPAREN RPAREN"
        p[0] = ("PUSH_YPOS",)

    def p_numexpression_isdisk(self, p):
        "numexpression : ISDISK LPAREN RPAREN"
        p[0] = ("PUSH_IS_DISK",)

    def p_numexpression_expression(self, p):
        "numexpression : expression"
        if self._check_byte_value(p[1], p.lexer.lexer.lineno):
            p[0] = ("PUSH_D", p[1])
        else:
            p[0] = None

    def p_variable_ID(self, p):
        """
        variableID  : number
                    | ID
        """
        if isinstance(p[1], int):
            if self._check_byte_value(p[1], p.lexer.lexer.lineno):
                p[0] = p[1]
            else:
                p[0] = None
        elif isinstance(p[1], str):
            if self._symbol_usage(p[1], SymbolType.VARIABLE, p.lexer.lexer.lineno):
                p[0] = p[1]
            else:
                p[0] = None
        else:
            p[0] = None

    def p_expression_binop(self, p):
        """
        expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression AND_B expression
                  | expression OR_B expression
                  | expression SHIFT_L expression
                  | expression SHIFT_R expression
        """
        if p[2] == "+":
            p[0] = p[1] + p[3]
        elif p[2] == "-":
            p[0] = p[1] - p[3]
        elif p[2] == "*":
            p[0] = p[1] * p[3]
        elif p[2] == "/":
            p[0] = p[1] / p[3]
        elif p[2] == "&":
            p[0] = p[1] & p[3]
        elif p[2] == "|":
            p[0] = p[1] | p[3]
        elif p[2] == "<<":
            p[0] = p[1] << p[3]
        elif p[2] == ">>":
            p[0] = p[1] >> p[3]

    def p_expression_group(self, p):
        "expression : LPAREN expression RPAREN"
        p[0] = p[2]

    def p_expression_number(self, p):
        "expression : number"
        p[0] = p[1]

    def p_expression_bin_number(self, p):
        "number : BIN_NUMBER"
        p[0] = p[1]

    def p_expression_hex_number(self, p):
        "number : HEX_NUMBER"
        p[0] = p[1]

    def p_expression_dec_number(self, p):
        "number : DEC_NUMBER"
        p[0] = p[1]

    def p_empty(self, p):
        "empty :"
        pass

    def p_error(self, p):
        if p:
            msg = f"Syntax error at line {p.lineno}: {p.value}"
        else:
            msg = "Syntax error"
        self.errors.append(msg)

    def build(self):
        self.lexer.build()
        self.parser = yacc.yacc(module=self)

    def parse(self, input):
        if self.parser is None:
            self.errors.append("Parser not build.")
            return None
        else:
            self.symbols.clear()
            self.symbols_used.clear()
            self.errors.clear()
            self.hidden_label_counter = 0
            cinput, cerrors = self._code_text_reversal(input)
            self.errors += cerrors
            if len(self.errors) > 0:
                return []
            parse_result = self.parser.parse(cinput, lexer=self.lexer)
            if not self._check_symbols():
                return []
            return parse_result

    def debug_p(self, p):
        s = ""
        for t in p:
            s += str(t) + ";"
        print(s)

    def _check_byte_value(self, val, lineno):
        if not isinstance(val, int) or val not in range(256):
            self.errors.append(f"Invalid byte value {val} on line {lineno}")
            return False
        return True

    def _check_word_value(self, val, lineno):
        if not isinstance(val, int) or val not in range(64 * 1024):
            self.errors.append(f"Invalid word value {val} on line {lineno}")
            return False
        return True

    def _is_valid_var(self, val):
        return isinstance(val, str) or isinstance(val, int)

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

    def _check_attr_values(self, ink, paper, bright, flash, lineno):
        error = False
        if ink < 0 or ink > 7:
            self.errors.append(f"Invalid Ink value on line {lineno}")
            error = True
        if paper < 0 or paper > 7:
            self.errors.append(f"Invalid Paper value on line {lineno}")
            error = True
        if bright < 0 or bright > 1:
            self.errors.append(f"Invalid Bright value on line {lineno}")
            error = True
        if flash < 0 or flash > 1:
            self.errors.append(f"Invalid Flash value on line {lineno}")
            error = True
        if error:
            return None
        return (flash << 7) | (bright << 6) | (paper << 3) | ink

    def _get_attr_mask(self, ink, paper, bright, flash, lineno):
        error = False
        if ink not in range(2):
            self.errors.append(f"Invalid Ink value on line {lineno}")
            error = True
        if paper not in range(2):
            self.errors.append(f"Invalid Paper value on line {lineno}")
            error = True
        if bright not in range(2):
            self.errors.append(f"Invalid Bright value on line {lineno}")
            error = True
        if flash not in range(2):
            self.errors.append(f"Invalid Flash value on line {lineno}")
            error = True
        if error:
            return None
        if paper != 0:
            paper = 7
        if ink != 0:
            ink |= 7
        return (flash << 7) | (bright << 6) | (paper << 3) | ink

    def _get_hidden_label(self):
        l = f"__LABEL_{self.hidden_label_counter}"
        self.hidden_label_counter += 1
        return l

    def _code_text_reversal(self, text):
        code = ""
        skip = False
        is_text = True
        errors = []
        curr_text = ""
        curr_code = ""
        curr_line = 0
        curr_pos = 0
        last_c_line = 0
        last_c_pos = 0
        for i, c in enumerate(text):
            if skip:
                curr_pos += 1
                skip = False
            elif (i + 1) < len(text):
                if text[i] == "[" and text[i + 1] == "[":
                    if not is_text:
                        errors.append(
                            f"Invalid code opening on line {curr_line} at {curr_pos}"
                        )
                        break
                    skip = True
                    is_text = False
                    last_c_line = curr_line
                    last_c_pos = curr_pos
                    if len(curr_text) > 0:
                        curr_code += "[[" + curr_text + "]]"
                    curr_text = ""
                elif text[i] == "]" and text[i + 1] == "]":
                    if is_text:
                        errors.append(
                            f"Invalid code closure on line {curr_line} at {curr_pos}"
                        )
                        break
                    skip = True
                    is_text = True
                    if len(curr_code) > 0:
                        code += curr_code
                    curr_code = ""
                elif is_text:
                    curr_text += c
                else:
                    curr_code += c
                if c == "\n":
                    curr_line += 1
                    curr_pos = 0
                else:
                    curr_pos += 1
        if not is_text and len(errors) == 0:
            errors.append(f"Invalid code closure on line {last_c_line} at {last_c_pos}")

        return (code, errors)

    # def _check_symbol(self, symbol, expected_type, lineno):
    #     if symbol in self.symbols.keys():
    #         s = self.symbols[symbol]
    #         if s[0] == expected_type:
    #             return True
    #         else:
    #             if s[0] == SymbolType.LABEL:
    #                 self.errors.append(
    #                     f"The variable '{symbol}' on line {lineno} is not valid. Already declared as a label."
    #                 )
    #             elif s[0] == SymbolType.VARIABLE:
    #                 self.errors.append(
    #                     f"The label '{symbol}' on line {lineno} is not valid. Already declared as a variable."
    #                 )
    #             else:
    #                 self.errors.append(
    #                     f"The symbol '{symbol}' on line {lineno} is not valid."
    #                 )
    #             return False
    #     else:
    #         self.errors.append(
    #             f"The symbol '{symbol}' on line {lineno} does not exists."
    #         )
    #         return False

    def _declare_symbol(self, symbol, symbol_type, lineno):
        if symbol in self.symbols.keys():
            if symbol_type == SymbolType.LABEL:
                self.errors.append(
                    f"Label '{symbol}' on line {lineno} was already declared before."
                )
            elif symbol_type == SymbolType.VARIABLE:
                self.errors.append(
                    f"Variable '{symbol}' on line {lineno} was already declared before."
                )
            else:
                self.errors.append(
                    f"Symbol '{symbol}' on line {lineno} was already declared before."
                )
            return False
        else:
            self.symbols[symbol] = (symbol_type, lineno)
            return True

    def _symbol_usage(self, symbol, symbol_type, lineno):
        if symbol in self.symbols_used.keys():
            s = self.symbols_used[symbol]
            if s[0] == symbol_type:
                s[1].append(lineno)
                self.symbols_used[symbol] = s
                return True
            else:
                if symbol_type == SymbolType.LABEL:
                    self.errors.append(
                        f"Label '{symbol}' on line {lineno} was already used as variable."
                    )
                elif symbol_type == SymbolType.VARIABLE:
                    self.errors.append(
                        f"Variable '{symbol}' on line {lineno} was already used as label."
                    )
                else:
                    self.errors.append(
                        f"Symbol '{symbol}' on line {lineno} was already used in other context."
                    )
                return False
        else:
            self.symbols_used[symbol] = (symbol_type, [lineno])
            return True

    def _check_symbols(self):
        res = True
        for symbol in self.symbols_used.keys():
            symbol_type, lines = self.symbols_used[symbol]
            lines_str = ", ".join([str(i) for i in lines])
            if symbol not in self.symbols.keys():
                if symbol_type == SymbolType.LABEL:
                    self.errors.append(
                        f"Label '{symbol}' on lines {lines_str} is not declared."
                    )
                elif symbol_type == SymbolType.VARIABLE:
                    self.errors.append(
                        f"Variable '{symbol}' on lines {lines_str} is not declared."
                    )
                else:
                    self.errors.append(
                        f"Symbol '{symbol}' on lines {lines_str} is not declared."
                    )
                res = False
            else:
                s = self.symbols[symbol]
                if s[0] != symbol_type:
                    if symbol_type == SymbolType.LABEL:
                        self.errors.append(
                            f"Label '{symbol}' on lines {lines_str} was already declared as variable on {s[1]}."
                        )
                    elif symbol_type == SymbolType.VARIABLE:
                        self.errors.append(
                            f"Variable '{symbol}' on lines {lines_str} was already declared as label on {s[1]}."
                        )
                    else:
                        self.errors.append(
                            f"Symbol '{symbol}' on lines {lines_str} was already declared with another type on {s[1]}."
                        )
                    res = False
        return res

    def print_symbols(self):
        for symbol in self.symbols.keys():
            s = self.symbols[symbol]
            if s[0] == SymbolType.LABEL:
                print(f"- Label '{symbol}' declared on line {s[1]}.")
            elif s[0] == SymbolType.VARIABLE:
                print(f"- Variable '{symbol}' declared on line {s[1]}.")
            else:
                print(f"- Symbol '{symbol}' declared on line {s[1]}.")
