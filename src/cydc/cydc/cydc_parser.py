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

import ply.yacc as yacc
from cydc_lexer import CydcLexer


class CydcParser(object):
    def __init__(self):
        self.lexer = CydcLexer()
        self.tokens = self.lexer.get_tokens()
        self.parser = None
        self.errors = []

    precedence = (
        ("left", "PLUS", "MINUS"),
        ("left", "TIMES", "DIVIDE"),
    )

    def p_script(self, p):
        """
        script : script TEXT
               | script code
               | TEXT
               | code
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

    def p_code(self, p):
        """
        code : program CLOSE_CODE
             | CLOSE_CODE
        """
        if len(p) == 2 and p[1]:
            p[0] = []
        elif len(p) == 3 and p[1]:
            p[0] = p[1]


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
        statements_nl   : statements NEWLINE
                        | NEWLINE
        """
        if len(p) == 2:
            p[0] = None
        elif len(p) == 3 and p[1]:
            p[0] = p[1]

    def p_statements(self, p):
        """
        statements  : statements COLON statement
                    | statement
        """
        if (len(p) == 2) and p[1]:
            p[0] = []
            p[0].append(p[1])
        elif len(p) == 4:
            p[0] = p[1]
            if not p[0]:
                p[0] = []
            if p[3]:
                p[0].append(p[3])

    def p_statement_open_error(self, p):
        "statement : ERROR_OPEN_CODE"
        self.errors.append(f"Invalid opening code token in line {p.lineno}")
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

    def p_statement_choose(self, p):
        "statement : CHOOSE"
        p[0] = ("CHOOSE",)

    def p_statement_clear(self, p):
        "statement : CLEAR"
        p[0] = ("CLEAR",)

    def p_statement_goto(self, p):
        "statement : GOTO ID"
        p[0] = ("GOTO", p[2], 0, 0)

    def p_statement_gosub(self, p):
        "statement : GOSUB ID"
        p[0] = ("GOSUB", p[2], 0, 0)

    def p_statement_option(self, p):
        "statement : OPTION GOTO ID"
        p[0] = ("OPTION", p[3], 0, 0)

    def p_statement_label(self, p):
        "statement : LABEL ID"
        p[0] = ("LABEL", p[2])

    def p_statement_inkey(self, p):
        "statement : INKEY expression"
        if self._check_byte_value(p[2]):
            p[0] = ("INKEY", p[2])
        else:
            p[0] = None

    def p_statement_char(self, p):
        "statement : CHAR expression"
        if self._check_byte_value(p[2]):
            p[0] = ("CHAR", p[2])
        else:
            p[0] = None

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

    def p_statement_set_random(self, p):
        "statement : SET expression TO RANDOM"
        if self._check_byte_value(p[2]):
            p[0] = ("SET_RANDOM", p[2])
        else:
            p[0] = None

    def p_statement_not(self, p):
        "statement : SET NOT expression"
        if self._check_byte_value(p[3]):
            p[0] = ("NOT", p[3])
        else:
            p[0] = None

    def p_statement_print_ind(self, p):
        "statement : PRINT INDIRECTION expression"
        if self._check_byte_value(p[3]):
            p[0] = ("PRINT_I", p[3])
        else:
            p[0] = None

    def p_statement_print_dir(self, p):
        "statement : PRINT expression"
        if self._check_byte_value(p[2]):
            p[0] = ("PRINT_D", p[2])
        else:
            p[0] = None

    def p_statement_ink_ind(self, p):
        "statement : INK INDIRECTION expression"
        if self._check_byte_value(p[3]):
            p[0] = ("INK_I", p[3])
        else:
            p[0] = None

    def p_statement_ink_dir(self, p):
        "statement : INK expression"
        if self._check_byte_value(p[2]):
            p[0] = ("INK_D", p[2])
        else:
            p[0] = None

    def p_statement_paper_ind(self, p):
        "statement : PAPER INDIRECTION expression"
        if self._check_byte_value(p[3]):
            p[0] = ("PAPER_I", p[3])
        else:
            p[0] = None

    def p_statement_paper_dir(self, p):
        "statement : PAPER expression"
        if self._check_byte_value(p[2]):
            p[0] = ("PAPER_D", p[2])
        else:
            p[0] = None

    def p_statement_border_ind(self, p):
        "statement : BORDER INDIRECTION expression"
        if self._check_byte_value(p[3]):
            p[0] = ("BORDER_I", p[3])
        else:
            p[0] = None

    def p_statement_border_dir(self, p):
        "statement : BORDER expression"
        if self._check_byte_value(p[2]):
            p[0] = ("BORDER_D", p[2])
        else:
            p[0] = None

    def p_statement_bright_ind(self, p):
        "statement : BRIGHT INDIRECTION expression"
        if self._check_byte_value(p[3]):
            p[0] = ("BRIGHT_I", p[3])
        else:
            p[0] = None

    def p_statement_bright_dir(self, p):
        "statement : BRIGHT expression"
        if self._check_byte_value(p[2]):
            p[0] = ("BRIGHT_D", p[2])
        else:
            p[0] = None

    def p_statement_flash_ind(self, p):
        "statement : FLASH INDIRECTION expression"
        if self._check_byte_value(p[3]):
            p[0] = ("FLASH_I", p[3])
        else:
            p[0] = None

    def p_statement_flash_dir(self, p):
        "statement : FLASH expression"
        if self._check_byte_value(p[2]):
            p[0] = ("FLASH_D", p[2])
        else:
            p[0] = None

    def p_statement_sfx_dir(self, p):
        "statement : SFX expression"
        if self._check_byte_value(p[2]):
            p[0] = ("SFX_D", p[2])
        else:
            p[0] = None

    def p_statement_sfx_ind(self, p):
        "statement : SFX INDIRECTION expression"
        if self._check_byte_value(p[3]):
            p[0] = ("SFX_I", p[3])
        else:
            p[0] = None

    def p_statement_display_ind(self, p):
        "statement : DISPLAY INDIRECTION expression"
        if self._check_byte_value(p[3]):
            p[0] = ("DISPLAY_I", p[3])
        else:
            p[0] = None

    def p_statement_picture_dir(self, p):
        "statement : PICTURE expression"
        if self._check_byte_value(p[2]):
            p[0] = ("PICTURE_D", p[2])
        else:
            p[0] = None

    def p_statement_display_dir(self, p):
        "statement : DISPLAY expression"
        if self._check_byte_value(p[2]):
            p[0] = ("DISPLAY_D", p[2])
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

    def p_statement_margins(self, p):
        "statement : MARGINS expression COMMA expression COMMA expression COMMA expression"
        if (
            self._check_byte_value(p[2])
            and self._check_byte_value(p[4])
            and self._check_byte_value(p[6])
            and self._check_byte_value(p[8])
        ):
            p[0] = ("MARGINS", p[2], p[4], p[6], p[8])
        else:
            p[0] = None

    def p_statement_at(self, p):
        "statement : AT expression COMMA expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("AT", p[2], p[4])
        else:
            p[0] = None

    def p_statement_set_ind(self, p):
        "statement : SET expression TO INDIRECTION expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("SET_I", p[2], p[5])
        else:
            p[0] = None

    def p_statement_set_dir(self, p):
        "statement : SET expression TO expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("SET_D", p[2], p[4])
        else:
            p[0] = None

    def p_statement_add_ind(self, p):
        "statement : SET expression ADD INDIRECTION expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("ADD_I", p[2], p[5])
        else:
            p[0] = None

    def p_statement_add_dir(self, p):
        "statement : SET expression ADD expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("ADD_D", p[2], p[4])
        else:
            p[0] = None

    def p_statement_sub_ind(self, p):
        "statement : SET expression SUB INDIRECTION expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("SUB_I", p[2], p[5])
        else:
            p[0] = None

    def p_statement_sub_dir(self, p):
        "statement : SET expression SUB expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("SUB_D", p[2], p[4])
        else:
            p[0] = None

    def p_statement_and_ind(self, p):
        "statement : SET expression AND INDIRECTION expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("AND_I", p[2], p[5])
        else:
            p[0] = None

    def p_statement_and_dir(self, p):
        "statement : SET expression AND expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("AND_D", p[2], p[4])
        else:
            p[0] = None

    def p_statement_or_ind(self, p):
        "statement : SET expression OR INDIRECTION expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("OR_I", p[2], p[5])
        else:
            p[0] = None

    def p_statement_or_dir(self, p):
        "statement : SET expression OR expression"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("OR_D", p[2], p[4])
        else:
            p[0] = None

    def p_statement_if_eq_goto_ind(self, p):
        "statement : IF expression EQUALS INDIRECTION expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("IF_EQ_I", p[2], p[5], p[8], 0, 0)
        else:
            p[0] = None

    def p_statement_if_eq_goto_dir(self, p):
        "statement : IF expression EQUALS expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("IF_EQ_D", p[2], p[4], p[7], 0, 0)
        else:
            p[0] = None

    def p_statement_if_ne_goto_ind(self, p):
        "statement : IF expression NOT_EQUALS INDIRECTION expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("IF_NE_I", p[2], p[5], p[8], 0, 0)
        else:
            p[0] = None

    def p_statement_if_ne_goto_dir(self, p):
        "statement : IF expression NOT_EQUALS expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("IF_NE_D", p[2], p[4], p[7], 0, 0)
        else:
            p[0] = None

    def p_statement_if_le_goto_ind(self, p):
        "statement : IF expression LESS_EQUALS INDIRECTION expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("IF_LE_I", p[2], p[5], p[8], 0, 0)
        else:
            p[0] = None

    def p_statement_if_le_goto_dir(self, p):
        "statement : IF expression LESS_EQUALS expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("IF_LE_D", p[2], p[4], p[7], 0, 0)
        else:
            p[0] = None

    def p_statement_if_me_goto_ind(self, p):
        "statement : IF expression MORE_EQUALS INDIRECTION expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("IF_ME_I", p[2], p[5], p[8], 0, 0)
        else:
            p[0] = None

    def p_statement_if_me_goto_dir(self, p):
        "statement : IF expression MORE_EQUALS expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("IF_ME_D", p[2], p[4], p[7], 0, 0)
        else:
            p[0] = None

    def p_statement_if_lt_goto_ind(self, p):
        "statement : IF expression LESS_THAN INDIRECTION expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("IF_LT_I", p[2], p[5], p[8], 0, 0)
        else:
            p[0] = None

    def p_statement_if_lt_goto_dir(self, p):
        "statement : IF expression LESS_THAN expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("IF_LT_D", p[2], p[4], p[7], 0, 0)
        else:
            p[0] = None

    def p_statement_if_mt_goto_ind(self, p):
        "statement : IF expression MORE_THAN INDIRECTION expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[5]):
            p[0] = ("IF_MT_I", p[2], p[5], p[8], 0, 0)
        else:
            p[0] = None

    def p_statement_if_mt_goto_dir(self, p):
        "statement : IF expression MORE_THAN expression THEN GOTO ID"
        if self._check_byte_value(p[2]) and self._check_byte_value(p[4]):
            p[0] = ("IF_MT_D", p[2], p[4], p[7], 0, 0)
        else:
            p[0] = None

    def p_statement_choose_if(self, p):
        "statement : CHOOSE IF WAIT expression THEN GOTO ID"
        if self._check_word_value(p[4]):
            p[0] = ("CHOOSE_W", p[4] & 0xFF, (p[4] >> 8) & 0xFF, p[7], 0, 0)
        else:
            p[0] = None

    def p_expression_binop(self, p):
        """
        expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
        """
        # print [repr(p[i]) for i in range(0,4)]
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
            return self.parser.parse(input, lexer=self.lexer)

    def debug_p(self, p):
        s = ""
        for t in p:
            s += str(t) + ";"
        print(s)

    def _check_byte_value(self, val):
        if val > 255:
            self.errors.append(f"Invalid byte value {val}")
            return False
        return True

    def _check_word_value(self, val):
        if val > ((64 * 1024) - 1):
            self.errors.append(f"Invalid word value {val}")
            return False
        return True


if __name__ == "__main__":
    test = """empiezo[[GOTO tag]][[
        IF 2 = 2+3 THEN GOTO tag
        LABEL tag
    -- Nada de nada
        label tag2
        END:
    ]]
    [[IF 3 < @5 THEN GOTO lalala]][[GOTO lalala]]acabo"""
    parser = CydcParser()
    parser.build()
    parser.lexer.test(test)
    res = parser.parse(test)
    print(parser.parser)
    print("Res=" + str(res) + "\n---------------------\n")
