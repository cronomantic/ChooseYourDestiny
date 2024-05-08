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

from ply import yacc as yacc
from cydc_lexer import CydcLexer


class CydcParser(object):
    def __init__(self):
        self.lexer = CydcLexer()
        self.tokens = self.lexer.get_tokens()
        self.parser = None
        self.errors = []
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
                        |  THEN if_subprogram
        """
        if len(p) == 3 and p[2]:
            p[0] = []
            if isinstance(p[2], list):
                p[0] += p[2]
            else:
                p[0].append(p[2])

    def p_else_statement(self, p):
        """
        else_statement :    ELSE if_subprogram
                        |   ELSE if_statement
                        |   empty
        """
        p[0] = []
        if len(p) == 3 and p[2]:
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
        p[0] = ("LABEL", p[1])

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

    def p_statement_choose(self, p):
        "statement : CHOOSE"
        p[0] = ("CHOOSE",)

    def p_statement_clear(self, p):
        "statement : CLEAR"
        p[0] = ("CLEAR",)

    def p_statement_randomize(self, p):
        "statement : RANDOMIZE"
        p[0] = ("RANDOMIZE",)

    def p_statement_goto(self, p):
        "statement : GOTO ID"
        p[0] = ("GOTO", p[2], 0, 0)

    def p_statement_gosub(self, p):
        "statement : GOSUB ID"
        p[0] = ("GOSUB", p[2], 0, 0)

    def p_statement_label(self, p):
        "statement : LABEL ID"
        p[0] = ("LABEL", p[2])

    def p_statement_backspace(self, p):
        """
        statement : BACKSPACE expression
                  | BACKSPACE
        """
        if len(p) == 3 and p[2]:
            if self._check_byte_value(p[2]):
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
            if self._check_byte_value(p[2]):
                p[0] = ("NEWLINE", p[2])
            else:
                p[0] = None
        elif len(p) == 2:
            p[0] = ("NEWLINE", 1)

    def p_statement_tab(self, p):
        "statement : TAB expression"
        if self._check_byte_value(p[2]):
            p[0] = ("TAB", p[2])
        else:
            p[0] = None

    def p_statement_page_pause(self, p):
        "statement : PAGEPAUSE expression"
        if self._check_byte_value(p[2]):
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
        if self._check_word_value(p[2]):
            p[0] = ("WAIT", p[2] & 0xFF, (p[2] >> 8) & 0xFF)
        else:
            p[0] = None

    def p_statement_pause(self, p):
        "statement : PAUSE expression"
        if self._check_word_value(p[2]):
            p[0] = ("PAUSE", p[2] & 0xFF, (p[2] >> 8) & 0xFF)
        else:
            p[0] = None

    def p_statement_typerate(self, p):
        "statement : TYPERATE expression"
        if self._check_word_value(p[2]):
            p[0] = ("TYPERATE", p[2] & 0xFF, (p[2] >> 8) & 0xFF)
        else:
            p[0] = None

    def p_statement_blit(self, p):
        "statement : BLIT expression COMMA expression COMMA expression COMMA expression AT numexpression COMMA numexpression"
        if (
            self._check_byte_value(p[2])
            and self._check_byte_value(p[4])
            and self._check_byte_value(p[6])
            and self._check_byte_value(p[8])
        ):
            row = p[4]
            col = p[2]
            width = p[6]
            height = p[8]
            if row >= 24:
                row = 23
            if col >= 32:
                col = 31
            if row < 0:
                row = 0
            if col < 0:
                col = 0
            if width <= 0:
                width = 1
            if height <= 0:
                height = 1
            if (width + col) > 32:
                width = 32 - col
            if (height + row) > 24:
                height = 24 - row
            if isinstance(p[10], int) and isinstance(p[12], int):
                row_d = p[12]
                col_d = p[10]
                if self._check_byte_value(row_d) and self._check_byte_value(col_d):
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
                    p[0] = None
            elif isinstance(p[10], tuple) and isinstance(p[12], tuple):
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
                    if self._check_byte_value(row_d) and self._check_byte_value(col_d):
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
                        p[0] = None
                else:
                    p[0] = [t1, t2, ("POP_BLIT", col, row, width, height)]
            else:
                if isinstance(p[10], list):
                    p[0] = p[10]
                elif isinstance(p[10], int):
                    col_d = p[10]
                    if self._check_byte_value(col_d):
                        if col_d >= 32:
                            col_d = 31
                        if col_d < 0:
                            col_d = 0
                        p[0] = [("PUSH_D", col_d)]
                    else:
                        p[0] = None
                        return None
                else:
                    p[0] = [p[10]]
                if isinstance(p[12], list):
                    p[0] += p[12]
                elif isinstance(p[12], int):
                    row_d = p[12]
                    if self._check_byte_value(row_d):
                        if row_d >= 24:
                            row_d = 23
                        if row_d < 0:
                            row_d = 0
                        p[0].append(("PUSH_D", row_d))
                    else:
                        p[0] = None
                        return None
                else:
                    p[0].append(p[12])
                p[0].append(("POP_BLIT", col, row, width, height))
        else:
            p[0] = None

    def p_statement_fadeout(self, p):
        """
        statement : FADEOUT expression COMMA expression COMMA expression COMMA expression
        """
        if len(p) == 9:
            if (
                self._check_byte_value(p[2])
                and self._check_byte_value(p[4])
                and self._check_byte_value(p[6])
                and self._check_byte_value(p[8])
            ):
                row = p[4]
                col = p[2]
                width = p[6]
                height = p[8]
                if row >= 24:
                    row = 23
                if col >= 32:
                    col = 31
                if row < 0:
                    row = 0
                if col < 0:
                    col = 0
                if width <= 0:
                    width = 1
                if height <= 0:
                    height = 1
                if (width + col) > 32:
                    width = 32 - col
                if (height + row) > 24:
                    height = 24 - row
                p[0] = ("FADEOUT", col, row, width, height)
            else:
                p[0] = None

    def p_statement_margins(self, p):
        "statement : MARGINS expression COMMA expression COMMA expression COMMA expression"
        if len(p) == 9:
            if (
                self._check_byte_value(p[2])
                and self._check_byte_value(p[4])
                and self._check_byte_value(p[6])
                and self._check_byte_value(p[8])
            ):
                row = p[4]
                col = p[2]
                width = p[6]
                height = p[8]
                if row >= 24:
                    row = 23
                if col >= 32:
                    col = 31
                if row < 0:
                    row = 0
                if col < 0:
                    col = 0
                if width <= 0:
                    width = 1
                if height <= 0:
                    height = 1
                if (width + col) > 32:
                    width = 32 - col
                if (height + row) > 24:
                    height = 24 - row
                p[0] = ("MARGINS", col, row, width, height)
            else:
                p[0] = None

    def p_statement_at(self, p):
        "statement : AT numexpression COMMA numexpression"
        if isinstance(p[2], int) and isinstance(p[4], int):
            if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
                row = p[4]
                col = p[2]
                if row >= 24:
                    row = 23
                if col >= 32:
                    col = 31
                if row < 0:
                    row = 0
                if col < 0:
                    col = 0
                p[0] = ("AT", col, row)
            else:
                p[0] = None
        elif isinstance(p[2], tuple) and isinstance(p[4], tuple):
            t1 = p[2]
            t2 = p[4]
            if (
                (t1[0] == "PUSH_D")
                and (t2[0] == "PUSH_D")
                and isinstance(t1[1], int)
                and isinstance(t2[1], int)
            ):
                row = t2[1]
                col = t1[1]
                if self._check_byte_value(row) and self._check_byte_value(col):
                    if row >= 24:
                        row = 23
                    if col >= 32:
                        col = 31
                    if row < 0:
                        row = 0
                    if col < 0:
                        col = 0
                    p[0] = ("AT", col, row)
                else:
                    p[0] = None
            else:
                p[0] = [t1, t2, ("POP_AT",)]
        else:
            if isinstance(p[2], list):
                p[0] = p[2]
            elif isinstance(p[2], int):
                col = p[2]
                if self._check_byte_value(col):
                    if col >= 32:
                        col = 31
                    if col < 0:
                        col = 0
                    p[0] = [("PUSH_D", col)]
                else:
                    p[0] = None
                    return None
            else:
                p[0] = [p[2]]
            if isinstance(p[4], list):
                p[0] += p[4]
            elif isinstance(p[4], int):
                row = p[4]
                if self._check_byte_value(row):
                    if row >= 24:
                        row = 23
                    if row < 0:
                        row = 0
                    p[0].append(("PUSH_D", row))
                else:
                    p[0] = None
                    return None
            else:
                p[0].append(p[4])
            p[0].append(("POP_AT",))

    def p_statement_menuconfig(self, p):
        "statement : MENUCONFIG numexpression COMMA numexpression"
        if isinstance(p[2], int) and isinstance(p[4], int):
            if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
                row_d = p[4]
                col_d = p[2]
                if row_d >= 32:
                    row_d = 31
                if col_d >= 32:
                    col_d = 31
                if row_d < 0:
                    row_d = 0
                if col_d < 0:
                    col_d = 0
                p[0] = ("MENUCONFIG", col_d, row_d)
            else:
                p[0] = None
        elif isinstance(p[2], tuple) and isinstance(p[4], tuple):
            t1 = p[2]
            t2 = p[4]
            if (
                (t1[0] == "PUSH_D")
                and (t2[0] == "PUSH_D")
                and isinstance(t1[1], int)
                and isinstance(t2[1], int)
            ):
                row_d = t2[1]
                col_d = t1[1]
                if self._check_byte_value(row_d) and self._check_byte_value(col_d):
                    if row_d >= 32:
                        row_d = 31
                    if col_d >= 32:
                        col_d = 31
                    if row_d < 0:
                        row_d = 0
                    if col_d < 0:
                        col_d = 0
                    p[0] = ("MENUCONFIG", col_d, row_d)
                else:
                    p[0] = None
            else:
                p[0] = [t1, t2, ("POP_MENUCONFIG",)]
        else:
            if isinstance(p[2], list):
                p[0] = p[2]
            elif isinstance(p[2], int):
                col = p[2]
                if self._check_byte_value(col_d):
                    if col_d >= 32:
                        col_d = 31
                    if col_d < 0:
                        col_d = 0
                    p[0] = [("PUSH_D", col_d)]
                else:
                    p[0] = None
                    return None
            else:
                p[0] = [p[2]]
            if isinstance(p[4], list):
                p[0] += p[4]
            elif isinstance(p[4], int):
                row_d = p[4]
                if self._check_byte_value(row_d):
                    if row_d >= 32:
                        row_d = 31
                    if row_d < 0:
                        row_d = 0
                    p[0].append(("PUSH_D", row_d))
                else:
                    p[0] = None
                    return None
            else:
                p[0].append(p[4])
            p[0].append(("POP_MENUCONFIG",))

    def p_statement_save(self, p):
        """
        statement : SAVE numexpression COMMA variableID COMMA expression
                  | SAVE numexpression COMMA variableID
                  | SAVE numexpression
        """
        if len(p) == 7 and p[2] and self._is_valid_var(p[4]):
            if self._check_byte_value(p[6]):
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
            if self._check_byte_value(p[4]):
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
            if self._check_byte_value(p[4]):
                p[0] = ("RAMSAVE", (p[2], 0), p[4])
            else:
                p[0] = None
        elif len(p) == 3 and self._is_valid_var(p[2]):
            p[0] = ("RAMSAVE", (p[2], 0), 0)
        elif len(p) == 2:
            p[0] = ("RAMSAVE", 0, 0)

    def p_statement_repchar(self, p):
        "statement : REPCHAR expression COMMA expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("REPCHAR", p[2], p[4])
        else:
            p[0] = None

    def p_statement_declare(self, p):
        "statement : DECLARE expression AS ID"
        if self._check_byte_value(p[2]):
            p[0] = ("DECLARE", p[2], p[4])
        else:
            p[0] = None

    def p_statement_set_ind_array(self, p):
        "statement : SET LCARET variableID RCARET TO LCURLY numexpressions_list RCURLY"
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
        "statement : SET variableID TO LCURLY numexpressions_list RCURLY"
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
        "statement : SET LCARET variableID RCARET TO numexpression"
        if len(p) == 7 and self._is_valid_var(p[3]):
            if isinstance(p[6], list):
                p[0] = p[6]
            else:
                p[0] = [p[6]]
            p[0].append(("POP_SET_DI", (p[3], 0)))

    def p_statement_set_dir(self, p):
        "statement : SET variableID TO numexpression"
        if len(p) == 5 and self._is_valid_var(p[2]):
            if isinstance(p[4], list):
                p[0] = p[4]
            else:
                p[0] = [p[4]]
            p[0].append(("POP_SET", (p[2], 0)))

    def p_statement_choose_if_wait_goto(self, p):
        "statement : CHOOSE IF WAIT expression THEN GOTO ID"
        if self._check_word_value(p[4]):
            p[0] = ("CHOOSE_W", p[4] & 0xFF, (p[4] >> 8) & 0xFF, 0, p[7], 0, 0)
        else:
            p[0] = None

    def p_statement_choose_if_wait_gosub(self, p):
        "statement : CHOOSE IF WAIT expression THEN GOSUB ID"
        if self._check_word_value(p[4]):
            p[0] = ("CHOOSE_W", p[4] & 0xFF, (p[4] >> 8) & 0xFF, 0xFF, p[7], 0, 0)
        else:
            p[0] = None

    def p_statement_option_goto(self, p):
        "statement : OPTION GOTO ID"
        p[0] = ("OPTION", 0, p[3], 0, 0)

    def p_statement_option_gosub(self, p):
        "statement : OPTION GOSUB ID"
        p[0] = ("OPTION", 0xFF, p[3], 0, 0)

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

    def p_statement_saveresult_expression(self, p):
        "numexpression : SAVERESULT LPAREN RPAREN"
        p[0] = ("PUSH_SAVE_RESULT",)

    def p_statement_random_expression_limit(self, p):
        "numexpression : RANDOM LPAREN expression COMMA expression RPAREN"
        if self._check_byte_value(p[3]) and self._check_byte_value(p[5]):
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

    def p_statement_random_expression(self, p):
        "numexpression : RANDOM LPAREN expression RPAREN"
        if self._check_byte_value(p[3]):
            p[0] = ("PUSH_RANDOM", p[3])
        else:
            p[0] = None

    def p_statement_random(self, p):
        "numexpression : RANDOM LPAREN RPAREN"
        p[0] = ("PUSH_RANDOM", 0)

    def p_numexpression_inkey_expression(self, p):
        "numexpression : INKEY LPAREN expression RPAREN"
        if self._check_byte_value(p[3]):
            p[0] = ("PUSH_INKEY", p[3])
        else:
            p[0] = None

    def p_numexpression_inkey(self, p):
        "numexpression : INKEY LPAREN RPAREN"
        p[0] = ("PUSH_INKEY", 0)

    def p_numexpression_xpos(self, p):
        "numexpression : XPOS LPAREN RPAREN"
        p[0] = ("PUSH_YPOS",)

    def p_numexpression_ypos(self, p):
        "numexpression : YPOS LPAREN RPAREN"
        p[0] = ("PUSH_XPOS",)

    def p_numexpression_isdisk(self, p):
        "numexpression : ISDISK LPAREN RPAREN"
        p[0] = ("PUSH_IS_DISK",)

    def p_numexpression_expression(self, p):
        "numexpression : expression"
        if self._check_byte_value(p[1]):
            p[0] = ("PUSH_D", p[1])
        else:
            p[0] = None

    def p_variable_ID(self, p):
        """
        variableID  : number
                    | ID
        """
        if isinstance(p[1], int):
            if self._check_byte_value(p[1]):
                p[0] = p[1]
            else:
                p[0] = None
        else:
            p[0] = p[1]

    def p_expression_binop(self, p):
        """
        expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
        """
        if p[2] == "+":
            p[0] = p[1] + p[3]
        elif p[2] == "-":
            p[0] = p[1] - p[3]
        elif p[2] == "*":
            p[0] = p[1] * p[3]
        elif p[2] == "/":
            p[0] = p[1] / p[3]

    def p_expression_group(self, p):
        "expression : LPAREN expression RPAREN"
        p[0] = p[2]

    def p_expression_number(self, p):
        "expression : number"
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
            msg = "Syntax error at EOF"
        self.errors.append(msg)

    def build(self):
        self.lexer.build()
        self.parser = yacc.yacc(module=self)

    def parse(self, input):
        if self.parser is None:
            self.errors.append("Parser not build.")
            return None
        else:
            self.errors = []
            self.hidden_label_counter = 0
            cinput, cerrors = self._code_text_reversal(input)
            self.errors += cerrors
            if len(self.errors) > 0:
                return []
            return self.parser.parse(cinput, lexer=self.lexer)

    def debug_p(self, p):
        s = ""
        for t in p:
            s += str(t) + ";"
        print(s)

    def _check_byte_value(self, val):
        if val not in range(256):
            self.errors.append(f"Invalid byte value {val}")
            return False
        return True

    def _check_word_value(self, val):
        if val not in range(64 * 1024):
            self.errors.append(f"Invalid word value {val}")
            return False
        return True

    def _is_valid_var(self, val):
        return isinstance(val, str) or isinstance(val, int)

    def _get_hidden_label(self):
        l = f"*LABEL_{self.hidden_label_counter}*"
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
