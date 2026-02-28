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

from ply import yacc as yacc
from ply import lex as lex
from cydc_lexer import CydcLexer
from enum import Enum


class SymbolType(Enum):
    LABEL = 1
    VARIABLE = 2
    CONSTANT = 3
    ARRAY = 4


class CydcParser(object):

    def __init__(self, gettext=None, strict_colon_mode=True):
        self.lexer = CydcLexer()
        self.tokens = self.lexer.get_tokens()
        self.parser = None
        self.errors = list()
        self.symbols = dict()
        self.symbols_used = dict()
        self.hidden_label_counter = 0
        self.debug = False
        # Backwards compatibility: require colons between code statements
        # When True: statements like "PRINT x GOTO Label" require "PRINT x : GOTO Label"
        # When False: allows "PRINT x GOTO Label" (old behavior)
        self.strict_colon_mode = strict_colon_mode
        import builtins
        self._ = gettext.gettext if gettext is not None else builtins.__dict__.get('_', lambda x: x)

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
        statements_nl   : statements newline_seq
                        | newline_seq
        """
        if len(p) == 2:
            p[0] = None
        elif len(p) == 3 and p[1]:
            p[0] = p[1]

    def p_statements_text_statement(self, p):
        """
        statements  : statements text_statement
                    | text_statement
        """
        if (len(p) == 2) and p[1]:
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

    def p_statements_text_transitions(self, p):
        """
        statements  : text_statement if_statement
                    | text_statement loop_while_statement
                    | text_statement loop_do_until_statement
                    | text_statement statement
        """
        # Text naturally separates code blocks - no colon required
        p[0] = []
        if p[1]:
            if isinstance(p[1], list):
                p[0] += p[1]
            else:
                p[0].append(p[1])
        if p[2]:
            if isinstance(p[2], list):
                p[0] += p[2]
            else:
                p[0].append(p[2])

    def p_statements_no_colon(self, p):
        """
        statements  : statements if_statement
                    | statements loop_while_statement
                    | statements loop_do_until_statement
                    | statements statement
        """
        if len(p) == 3 and p[1] and p[2]:
            if self.strict_colon_mode:
                # In strict mode, report error but continue parsing
                self.errors.append(self._(f"Colon required between statements on same line (line {p.lineno(2)})"))
        
        p[0] = p[1]
        if not p[0]:
            p[0] = []
        if p[2]:
            if isinstance(p[2], list):
                p[0] += p[2]
            else:
                p[0].append(p[2])

    def p_statements(self, p):
        """
        statements  : statements COLON if_statement
                    | statements COLON loop_while_statement
                    | statements COLON loop_do_until_statement
                    | statements COLON statement
                    | if_statement
                    | loop_do_until_statement
                    | loop_while_statement
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

    def p_loop_while_statement(self, p):
        """
        loop_while_statement    : WHILE LPAREN boolexpression RPAREN loop_while_statement WEND
                                | WHILE LPAREN boolexpression RPAREN loop_while_subprogram WEND
                                | WHILE LPAREN RPAREN loop_while_statement WEND
                                | WHILE LPAREN RPAREN loop_while_subprogram WEND
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

    def p_loop_while_subprogram(self, p):
        """
        loop_while_subprogram   : loop_while_subprogram statements_nl
                                | loop_while_subprogram statements
                                | statements_nl
                                | statements
                                | loop_empty
        """
        if len(p) == 2:
            p[0] = []
            if p[1]:
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

    def p_loop_do_until_statement(self, p):
        """
        loop_do_until_statement : DO loop_do_until_statement UNTIL LPAREN boolexpression RPAREN
                                | DO loop_do_until_subprogram UNTIL LPAREN boolexpression RPAREN
                                | DO loop_do_until_statement UNTIL LPAREN RPAREN
                                | DO loop_do_until_subprogram UNTIL LPAREN RPAREN
        """
        if len(p) == 7 and p[5]:
            label_loop = self._get_hidden_label()
            p[0] = [("LABEL", label_loop)]
            if p[2]:
                if isinstance(p[2], list):
                    p[0] += p[2]
                else:
                    p[0].append(p[2])
            if isinstance(p[5], list):
                p[0] += p[5]
                p[0] += [("IF_N_GOTO", label_loop, 0, 0)]
            else:
                p[0] += [p[5], ("IF_N_GOTO", label_loop, 0, 0)]

        elif len(p) == 6:
            label_loop = self._get_hidden_label()
            p[0] = [("LABEL", label_loop)]
            if p[2]:
                if isinstance(p[2], list):
                    p[0] += p[2]
                else:
                    p[0].append(p[2])
            p[0] += [("GOTO", label_loop, 0, 0)]

    def p_loop_do_until_subprogram(self, p):
        """
        loop_do_until_subprogram    : loop_do_until_subprogram statements_nl
                                    | loop_do_until_subprogram statements
                                    | statements_nl
                                    | statements
                                    | loop_empty
        """
        if len(p) == 2:
            p[0] = []
            if p[1]:
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
        then_statement :   THEN if_subprogram
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

    def p_text_statement_close_error(self, p):
        "text_statement : ERROR_CLOSE_TEXT"
        self.errors.append(self._(f"Invalid opening code token in line {p[1]}"))
        p[0] = None

    def p_text_statement_text_error(self, p):
        "text_statement : ERROR_TEXT"
        if isinstance(p[1], tuple):
            t = p[1]
            if isinstance(t[1], list):
                for err in t[1]:
                    print(err)
                    self.errors.append(self._(
                        f"Invalid character '{err[2]}' (\\u{ord(err[2]):04x}) in line {err[0]} and position {err[1]}"
                    ))
            else:
                self.errors.append(self._(f"Undefined codification error"))
        else:
            self.errors.append(self._(f"Undefined codification error"))
        p[0] = None

    def p_text_statement_text(self, p):
        "text_statement : TEXT"
        p[0] = p[1]

    def p_statement_short_label(self, p):
        "statement : SHORT_LABEL"
        if self._declare_symbol(p[1], SymbolType.LABEL, p.lineno(1)):
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
        if self._symbol_usage(p[2], SymbolType.LABEL, p.lineno(2)):
            p[0] = ("GOTO", p[2], 0, 0)
        else:
            p[0] = None

    def p_statement_goto_error(self, p):
        """
        statement : GOTO error
                | GOTO
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on GOTO at line {p.lineno(1)}, missing identifier."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on GOTO at line {p.lineno(1)}, invalid identifier."
            ))

    def p_statement_gosub(self, p):
        "statement : GOSUB ID"
        if self._symbol_usage(p[2], SymbolType.LABEL, p.lineno(2)):
            p[0] = ("GOSUB", p[2], 0, 0)
        else:
            p[0] = None

    def p_statement_gosub_error(self, p):
        """
        statement : GOSUB error
                | GOSUB
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on GOSUB at line {p.lineno(1)}, missing identifier."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on GOSUB at line {p.lineno(1)}, invalid identifier."
            ))

    def p_statement_label(self, p):
        "statement : LABEL ID"
        if self._declare_symbol(p[2], SymbolType.LABEL, p.lineno(2)):
            p[0] = ("LABEL", p[2])
        else:
            p[0] = None

    def p_statement_label_error(self, p):
        """
        statement : LABEL error
                | LABEL
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on LABEL at line {p.lineno(1)}, missing identifier."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on LABEL at line {p.lineno(1)}, invalid identifier."
            ))

    def p_statement_backspace(self, p):
        """
        statement : BACKSPACE constexpression
                  | BACKSPACE
        """
        if len(p) == 3 and self._is_valid_constexpression(p[2]):
            if isinstance(p[2], list):
                p[0] = ("BACKSPACE", ("CONSTANT", p[2]))
            else:
                p[0] = ("BACKSPACE", ("CONSTANT", [p[2]]))
        elif len(p) == 2:
            p[0] = ("BACKSPACE", 1)
        else:
            p[0] = None

    def p_statement_backspace_error(self, p):
        "statement : BACKSPACE error"
        self.errors.append(self._(
            f"Syntax error on BACKSPACE command at line {p.lineno(1)}, invalid expression."
        ))

    def p_statement_newline(self, p):
        """
        statement : NEWLINE constexpression
                  | NEWLINE
        """
        if len(p) == 3 and self._is_valid_constexpression(p[2]):
            if isinstance(p[2], list):
                p[0] = ("NEWLINE", ("CONSTANT", p[2]))
            else:
                p[0] = ("NEWLINE", ("CONSTANT", [p[2]]))
        elif len(p) == 2:
            p[0] = ("NEWLINE", 1)
        else:
            p[0] = None

    def p_statement_newline_error(self, p):
        "statement : NEWLINE error"
        self.errors.append(self._(
            f"Syntax error on NEWLINE command at line {p.lineno(1)}, invalid expression."
        ))

    def p_statement_tab(self, p):
        "statement : TAB constexpression"
        if len(p) == 3 and self._is_valid_constexpression(p[2]):
            if isinstance(p[2], list):
                p[0] = ("TAB", ("CONSTANT", p[2]))
            else:
                p[0] = ("TAB", ("CONSTANT", [p[2]]))
        else:
            p[0] = None

    def p_statement_tab_error(self, p):
        """
        statement : TAB error
                | TAB
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on TAB command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on TAB command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_page_pause(self, p):
        "statement : PAGEPAUSE constexpression"
        if len(p) == 3 and self._is_valid_constexpression(p[2]):
            if isinstance(p[2], list):
                p[0] = ("PAGEPAUSE", ("CONSTANT", p[2]))
            else:
                p[0] = ("PAGEPAUSE", ("CONSTANT", [p[2]]))
        else:
            p[0] = None

    def p_statement_page_pause_error(self, p):
        """
        statement : PAGEPAUSE error
                | PAGEPAUSE
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on PAGEPAUSE command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on PAGEPAUSE command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_char(self, p):
        "statement : CHAR varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_CHAR",))

    def p_statement_char_error(self, p):
        """
        statement : CHAR error
                | CHAR
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on CHAR command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on CHAR command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_print(self, p):
        "statement : PRINT varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_PRINT",))

    def p_statement_print_string(self, p):
        "statement : PRINT STRING"
        encoded = self.lexer.replace_chars(p[2])
        p[0] = ("TEXT", encoded)

    def p_statement_print_error(self, p):
        """
        statement : PRINT error
                | PRINT
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on PRINT command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on PRINT command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_ink(self, p):
        "statement : INK varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_INK",))

    def p_statement_ink_error(self, p):
        """
        statement : INK error
                | INK
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on INK command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on INK command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_paper(self, p):
        "statement : PAPER varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_PAPER",))

    def p_statement_paper_error(self, p):
        """
        statement : PAPER error
                | PAPER
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on PAPER command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on PAPER command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_border(self, p):
        "statement : BORDER varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_BORDER",))

    def p_statement_border_error(self, p):
        """
        statement : BORDER error
                | BORDER
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on BORDER command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on BORDER command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_bright(self, p):
        "statement : BRIGHT varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_BRIGHT",))

    def p_statement_bright_error(self, p):
        """
        statement : BRIGHT error
                | BRIGHT
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on BRIGHT command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on BRIGHT command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_flash(self, p):
        "statement : FLASH varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_FLASH",))

    def p_statement_flash_error(self, p):
        """
        statement : FLASH error
                | FLASH
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on FLASH command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on FLASH command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_sfx(self, p):
        "statement : SFX varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_SFX",))

    def p_statement_sfx_error(self, p):
        """
        statement : SFX error
                | SFX
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on SFX command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on SFX command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_display(self, p):
        "statement : DISPLAY varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_DISPLAY",))

    def p_statement_display_error(self, p):
        """
        statement : DISPLAY error
                | DISPLAY
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on DISPLAY command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on DISPLAY command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_picture(self, p):
        "statement : PICTURE varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_PICTURE",))

    def p_statement_picture_error(self, p):
        """
        statement : PICTURE error
                | PICTURE
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on PICTURE command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on PICTURE command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_track(self, p):
        "statement : TRACK varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_TRACK",))

    def p_statement_track_error(self, p):
        """
        statement : TRACK error
                | TRACK
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on TRACK command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on TRACK command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_play(self, p):
        "statement : PLAY varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_PLAY",))

    def p_statement_play_error(self, p):
        """
        statement : PLAY error
                | PLAY
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on PLAY command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on PLAY command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_loop(self, p):
        "statement : LOOP varexpression"
        if isinstance(p[2], list):
            p[0] = p[2]
        else:
            p[0] = [p[2]]
        p[0].append(("POP_LOOP",))

    def p_statement_loop_error(self, p):
        """
        statement : LOOP error
                | LOOP
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on LOOP command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on LOOP command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_load(self, p):
        "statement : LOAD varexpression"
        if len(p) == 3 and p[2]:
            if isinstance(p[2], list):
                p[0] = p[2]
            else:
                p[0] = [p[2]]
            p[0].append(("POP_SLOT_LOAD",))
        else:
            p[0] = None

    def p_statement_load_error(self, p):
        """
        statement : LOAD error
                | LOAD
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on LOAD command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on LOAD command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_wait(self, p):
        "statement : WAIT constexpression"
        if len(p) == 3 and self._is_valid_constexpression(p[2]):
            if isinstance(p[2], list):
                p[0] = ("WAIT", ("CONSTANT_L", p[2]), ("CONSTANT_H", p[2]))
            else:
                p[0] = ("WAIT", ("CONSTANT_L", [p[2]]), ("CONSTANT_H", [p[2]]))
        else:
            p[0] = None

    def p_statement_wait_error(self, p):
        """
        statement : WAIT error
                | WAIT
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on WAIT command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on WAIT command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_pause(self, p):
        "statement : PAUSE constexpression"
        if len(p) == 3 and self._is_valid_constexpression(p[2]):
            if isinstance(p[2], list):
                p[0] = ("PAUSE", ("CONSTANT_L", p[2]), ("CONSTANT_H", p[2]))
            else:
                p[0] = ("PAUSE", ("CONSTANT_L", [p[2]]), ("CONSTANT_H", [p[2]]))
        else:
            p[0] = None

    def p_statement_pause_error(self, p):
        """statement : PAUSE error
        | PAUSE
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on PAUSE command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on PAUSE command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_typerate(self, p):
        "statement : TYPERATE constexpression"
        if len(p) == 3 and self._is_valid_constexpression(p[2]):
            if isinstance(p[2], list):
                p[0] = ("TYPERATE", ("CONSTANT_L", p[2]), ("CONSTANT_H", p[2]))
            else:
                p[0] = ("TYPERATE", ("CONSTANT_L", [p[2]]), ("CONSTANT_H", [p[2]]))
        else:
            p[0] = None

    def p_statement_typerate_error(self, p):
        """
        statement : TYPERATE error
                | TYPERATE
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on TYPERATE command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on TYPERATE command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_window(self, p):
        "statement : WINDOW constexpression"
        if len(p) == 3 and self._is_valid_constexpression(p[2]):
            if isinstance(p[2], list):
                p[0] = ("WINDOW", ("CONSTANT", p[2] + [("C_VAL", 7), ("C_&",)]))
            else:
                p[0] = ("WINDOW", ("CONSTANT", [p[2]] + [("C_VAL", 7), ("C_&",)]))
        else:
            p[0] = None

    def p_statement_window_error(self, p):
        """
        statement : WINDOW error
                | WINDOW
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on WINDOW command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on WINDOW command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_charset(self, p):
        "statement : CHARSET constexpression"
        if len(p) == 3 and self._is_valid_constexpression(p[2]):
            if isinstance(p[2], list):
                p[0] = ("CHARSET", ("CONSTANT", p[2] + [("C_VAL", 7), ("C_&",)]))
            else:
                p[0] = ("CHARSET", ("CONSTANT", [p[2]] + [("C_VAL", 7), ("C_&",)]))
        else:
            p[0] = None

    def p_statement_charset_error(self, p):
        """
        statement : CHARSET error
                | CHARSET
        """
        if len(p) != 3:
            self.errors.append(self._(
                f"Syntax error on CHARSET command at line {p.lineno(1)}, it has no argument."
            ))
        else:
            self.errors.append(self._(
                f"Syntax error on CHARSET command at line {p.lineno(1)}, invalid expression."
            ))

    def p_statement_blit(self, p):
        "statement : BLIT varexpression COMMA varexpression COMMA varexpression COMMA varexpression AT varexpression COMMA varexpression"
        if len(p) == 13:
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
        "statement : FILLATTR varexpression COMMA varexpression COMMA varexpression COMMA varexpression COMMA varexpression"
        if len(p) == 11:
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
        statement : FADEOUT constexpression COMMA constexpression COMMA constexpression COMMA constexpression
        """
        if len(p) == 9:
            if (
                self._is_valid_constexpression(p[2])
                and self._is_valid_constexpression(p[4])
                and self._is_valid_constexpression(p[6])
                and self._is_valid_constexpression(p[8])
            ):
                if isinstance(p[2], list):
                    p1 = ("CONSTANT", p[2])
                else:
                    p1 = ("CONSTANT", [p[2]])
                if isinstance(p[4], list):
                    p2 = ("CONSTANT", p[4])
                else:
                    p2 = ("CONSTANT", [p[4]])
                if isinstance(p[6], list):
                    p3 = ("CONSTANT", p[6])
                else:
                    p3 = ("CONSTANT", [p[6]])
                if isinstance(p[8], list):
                    p4 = ("CONSTANT", p[8])
                else:
                    p4 = ("CONSTANT", [p[8]])
                p[0] = ("FADEOUT", p1, p2, p3, p4)
            else:
                p[0] = None

    def p_statement_margins(self, p):
        "statement : MARGINS constexpression COMMA constexpression COMMA constexpression COMMA constexpression"
        if len(p) == 9:
            if (
                self._is_valid_constexpression(p[2])
                and self._is_valid_constexpression(p[4])
                and self._is_valid_constexpression(p[6])
                and self._is_valid_constexpression(p[8])
            ):
                if isinstance(p[2], list):
                    p1 = ("CONSTANT", p[2])
                else:
                    p1 = ("CONSTANT", [p[2]])
                if isinstance(p[4], list):
                    p2 = ("CONSTANT", p[4])
                else:
                    p2 = ("CONSTANT", [p[4]])
                if isinstance(p[6], list):
                    p3 = ("CONSTANT", p[6])
                else:
                    p3 = ("CONSTANT", [p[6]])
                if isinstance(p[8], list):
                    p4 = ("CONSTANT", p[8])
                else:
                    p4 = ("CONSTANT", [p[8]])
                p[0] = ("MARGINS", p1, p2, p3, p4)
            else:
                p[0] = None

    def p_statement_putattr(self, p):
        """
        statement : PUTATTR varexpression COMMA varexpression AT varexpression COMMA varexpression
                  | PUTATTR varexpression AT varexpression COMMA varexpression
        """
        if len(p) == 9:
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
            p[0] += [("POP_ALL_PUTATTR",)]
        elif len(p) == 7:
            if isinstance(p[2], list):
                p[0] = p[2]
            else:
                p[0] = [p[2]]
            p[0] += [("PUSH_D", 0xFF)]
            if isinstance(p[4], list):
                p[0] += p[4]
            else:
                p[0] += [p[4]]
            if isinstance(p[6], list):
                p[0] += p[6]
            else:
                p[0] += [p[6]]
            p[0] += [("POP_ALL_PUTATTR",)]
        else:
            p[0] = None

    def p_statement_at(self, p):
        "statement : AT varexpression COMMA varexpression"
        if len(p) == 5:
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
        statement : MENUCONFIG varexpression COMMA varexpression COMMA varexpression COMMA varexpression
                  | MENUCONFIG varexpression COMMA varexpression COMMA varexpression
                  | MENUCONFIG varexpression COMMA varexpression
        """
        if len(p) == 9:
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
            p[0] += [("POP_MENUCONFIG",)]
        elif len(p) == 7:
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
            p[0] += [("PUSH_D", 1)]  # show
            p[0] += [("POP_MENUCONFIG",)]
        elif len(p) == 5:
            if isinstance(p[2], list):
                p[0] = p[2]
            else:
                p[0] = [p[2]]
            if isinstance(p[4], list):
                p[0] += p[4]
            else:
                p[0] += [p[4]]
            p[0] += [("PUSH_D", 0)]  # init
            p[0] += [("PUSH_D", 1)]  # show
            p[0] += [("POP_MENUCONFIG",)]
        else:
            p[0] = None

    def p_statement_save(self, p):
        """
        statement : SAVE varexpression COMMA variableID COMMA constexpression
                  | SAVE varexpression COMMA variableID
                  | SAVE varexpression
        """
        if len(p) == 7 and p[2] and self._is_valid_var(p[4]):
            if self._is_valid_constexpression(p[6]):
                if isinstance(p[6], list):
                    p3 = ("CONSTANT", p[6])
                else:
                    p3 = ("CONSTANT", [p[6]])
                if isinstance(p[2], list):
                    p[0] = p[2]
                else:
                    p[0] = [p[2]]
                p[0].append(("POP_SLOT_SAVE", ("VARIABLE", p[4], 0), p3))
            else:
                p[0] = None
        elif len(p) == 5 and p[2] and self._is_valid_var(p[4]):
            if isinstance(p[2], list):
                p[0] = p[2]
            else:
                p[0] = [p[2]]
            p[0].append(("POP_SLOT_SAVE", ("VARIABLE", p[4], 0), 0))
        elif len(p) == 3 and p[2]:
            if isinstance(p[2], list):
                p[0] = p[2]
            else:
                p[0] = [p[2]]
            p[0].append(("POP_SLOT_SAVE", 0, 0))

    def p_statement_ramload(self, p):
        """
        statement : RAMLOAD variableID COMMA constexpression
                  | RAMLOAD variableID
                  | RAMLOAD
        """
        if len(p) == 5 and self._is_valid_var(p[2]):
            if self._is_valid_constexpression(p[4]):
                if isinstance(p[4], list):
                    p[0] = ("RAMLOAD", ("VARIABLE", p[2], 0), ("CONSTANT", p[4]))
                else:
                    p[0] = ("RAMLOAD", ("VARIABLE", p[2], 0), ("CONSTANT", [p[4]]))
            else:
                p[0] = None
        elif len(p) == 3 and self._is_valid_var(p[2]):
            p[0] = ("RAMLOAD", ("VARIABLE", p[2], 0), 0)
        elif len(p) == 2:
            p[0] = ("RAMLOAD", 0, 0)

    def p_statement_ramsave(self, p):
        """
        statement : RAMSAVE variableID COMMA constexpression
                  | RAMSAVE variableID
                  | RAMSAVE
        """
        if len(p) == 5 and self._is_valid_var(p[2]):
            if self._is_valid_constexpression(p[4]):
                if isinstance(p[4], list):
                    p[0] = ("RAMSAVE", ("VARIABLE", p[2], 0), ("CONSTANT", p[4]))
                else:
                    p[0] = ("RAMSAVE", ("VARIABLE", p[2], 0), ("CONSTANT", [p[4]]))
            else:
                p[0] = None
        elif len(p) == 3 and self._is_valid_var(p[2]):
            p[0] = ("RAMSAVE", ("VARIABLE", p[2], 0), 0)
        elif len(p) == 2:
            p[0] = ("RAMSAVE", 0, 0)

    def p_statement_repchar(self, p):
        "statement : REPCHAR constexpression COMMA constexpression"
        if (
            len(p) == 5
            and self._is_valid_constexpression(p[2])
            and self._is_valid_constexpression(p[4])
        ):
            if isinstance(p[2], list):
                p1 = ("CONSTANT", p[2])
            else:
                p1 = ("CONSTANT", [p[2]])
            if isinstance(p[4], list):
                p2 = ("CONSTANT", p[4])
            else:
                p2 = ("CONSTANT", [p[4]])
            p[0] = ("REPCHAR", p1, p2)
        else:
            p[0] = None

    def p_statement_declare(self, p):
        "statement : DECLARE expression AS ID"
        if self._check_byte_value(p[2], p.lineno(2)):
            if self._declare_symbol(p[4], SymbolType.VARIABLE, p.lineno(4)):
                p[0] = ("DECLARE", p[2], p[4])
            else:
                p[0] = None
        else:
            p[0] = None

    def p_constant_ID(self, p):
        """
        statement : CONST ID EQUALS constexpression
        """
        if len(p) == 5 and self._declare_symbol(p[2], SymbolType.CONSTANT, p.lineno(2)):
            if isinstance(p[4], list):
                p[0] = ("CONST", p[2], p[4])
            else:
                p[0] = ("CONST", p[2], [p[4]])
        else:
            p[0] = None

    def p_array_constexpressions_list(self, p):
        """
        statement : DIM ID LPAREN constexpression RPAREN EQUALS LCURLY constexpressions_list RCURLY
                  | DIM ID LPAREN RPAREN EQUALS LCURLY constexpressions_list RCURLY
                  | DIM ID LPAREN constexpression RPAREN
                  | DIM ID LPAREN RPAREN

        """
        if (
            len(p) == 10
            and self._check_array(p[8], p.lineno(8))
            and (isinstance(p[4], tuple) or isinstance(p[4], list))
            and self._declare_symbol(p[2], SymbolType.ARRAY, p.lineno(2))
        ):
            if isinstance(p[4], list):
                size = ("CONSTANT", p[4])
            else:
                size = ("CONSTANT", [p[4]])
            p[0] = ("ARRAY", p[2], size, [("CONSTANT", c) for c in p[8]])
        elif (
            len(p) == 9
            and self._check_array(p[7], p.lineno(7))
            and self._declare_symbol(p[2], SymbolType.ARRAY, p.lineno(2))
        ):
            p[0] = ("ARRAY", p[2], None, [("CONSTANT", c) for c in p[7]])
        elif (
            len(p) == 6
            and (isinstance(p[4], tuple) or isinstance(p[4], list))
            and self._declare_symbol(p[2], SymbolType.ARRAY, p.lineno(2))
        ):
            if isinstance(p[4], list):
                size = ("CONSTANT", p[4])
            else:
                size = ("CONSTANT", [p[4]])
            p[0] = ("ARRAY", p[2], size, [])
        elif len(p) == 5 and self._declare_symbol(p[2], SymbolType.ARRAY, p.lineno(2)):
            self.errors.append(self._(
                f"Data array '{p[2]}' on line {p.lineno(2)} must have defined a size or have initialization data."
            ))
            p[0] = None
        else:
            p[0] = None

    def p_statement_inc_dec_array_value(self, p):
        """
        statement : LET ID LPAREN varexpression RPAREN INCREMENT varexpression
                  | LET ID LPAREN varexpression RPAREN DECREMENT varexpression
        """
        if len(p) == 8 and self._symbol_usage(p[2], SymbolType.ARRAY, p.lineno(2)):

            array_index = []
            if isinstance(p[4], list):
                array_index += p[4]
            else:
                array_index += [p[4]]

            p[0] = array_index.copy()
            p[0].append(("PUSH_VAL_ARRAY", p[2], 0, 0))

            if isinstance(p[7], list):
                p[0] += p[7]
            else:
                p[0] += [p[7]]

            if p[6] == "+=":
                p[0].append(("ADD",))
            elif p[6] == "-=":
                p[0].append(("SUB",))
            else:
                self.errors.append(self._(f"Symbol on line {p.lineno(6)} invalid"))
            p[0] += array_index
            p[0].append(("POP_VAL_ARRAY", p[2], 0, 0))
        else:
            p[0] = None

    def p_statement_set_array_value(self, p):
        """
        statement : SET ID LPAREN varexpression RPAREN TO varexpression
                  | LET ID LPAREN varexpression RPAREN EQUALS varexpression
        """
        if len(p) == 8 and self._symbol_usage(p[2], SymbolType.ARRAY, p.lineno(2)):
            if isinstance(p[7], list):
                p[0] = p[7]
            else:
                p[0] = [p[7]]
            if isinstance(p[4], list):
                p[0] += p[4]
            else:
                p[0] += [p[4]]
            p[0].append(("POP_VAL_ARRAY", p[2], 0, 0))
        else:
            p[0] = None

    def p_statement_set_ind_array_var(self, p):
        """
        statement : SET LCARET variableID RCARET TO LCURLY varexpressions_list RCURLY
                  | LET LCARET variableID RCARET EQUALS LCURLY varexpressions_list RCURLY
        """
        if len(p) == 9 and self._is_valid_var(p[3]) and isinstance(p[7], list):
            p[0] = []
            for i, c in enumerate(p[7]):
                if isinstance(c, list):
                    p[0] += c
                    p[0].append(("POP_SET_DI", ("VARIABLE", p[3], i)))
                else:
                    p[0] = None
                    break
        else:
            p[0] = None

    def p_statement_set_dir_array_var(self, p):
        """
        statement : SET variableID TO LCURLY varexpressions_list RCURLY
                  | LET variableID EQUALS LCURLY varexpressions_list RCURLY
        """
        if len(p) == 7 and self._is_valid_var(p[2]) and isinstance(p[5], list):
            p[0] = []
            for i, c in enumerate(p[5]):
                if isinstance(c, list):
                    p[0] += c
                    p[0].append(("POP_SET", ("VARIABLE", p[2], i)))
                else:
                    p[0] = None
                    break
        else:
            p[0] = None

    def p_statement_inc_dec_ind(self, p):
        """
        statement : LET LCARET variableID RCARET INCREMENT varexpression
                  | LET LCARET variableID RCARET DECREMENT varexpression
        """
        if len(p) == 7 and self._is_valid_var(p[3]):

            p[0] = []
            p[0].append(("PUSH_DI", ("VARIABLE", p[3], 0)))

            if isinstance(p[6], list):
                p[0] += p[6]
            else:
                p[0] += [p[6]]

            if p[5] == "+=":
                p[0].append(("ADD",))
            elif p[5] == "-=":
                p[0].append(("SUB",))
            else:
                self.errors.append(self._(f"Symbol on line {p.lineno(5)} invalid"))
            p[0].append(("POP_SET_DI", ("VARIABLE", p[3], 0)))

    def p_statement_inc_dec_dir(self, p):
        """
        statement : LET variableID INCREMENT varexpression
                  | LET variableID DECREMENT varexpression
        """
        if len(p) == 5 and self._is_valid_var(p[2]):

            p[0] = []
            p[0].append(("PUSH_I", ("VARIABLE", p[2], 0)))

            if isinstance(p[4], list):
                p[0] += p[4]
            else:
                p[0] += [p[4]]

            if p[3] == "+=":
                p[0].append(("ADD",))
            elif p[3] == "-=":
                p[0].append(("SUB",))
            else:
                self.errors.append(self._(f"Symbol on line {p.lineno(3)} invalid"))
            p[0].append(("POP_SET", ("VARIABLE", p[2], 0)))

    def p_statement_set_ind(self, p):
        """
        statement : SET LCARET variableID RCARET TO varexpression
                  | LET LCARET variableID RCARET EQUALS varexpression
        """
        if len(p) == 7 and self._is_valid_var(p[3]):
            if isinstance(p[6], list):
                p[0] = p[6]
            else:
                p[0] = [p[6]]
            p[0].append(("POP_SET_DI", ("VARIABLE", p[3], 0)))

    def p_statement_set_dir(self, p):
        """
        statement : SET variableID TO varexpression
                  | LET variableID EQUALS varexpression
        """
        if len(p) == 5 and self._is_valid_var(p[2]):
            if isinstance(p[4], list):
                p[0] = p[4]
            else:
                p[0] = [p[4]]
            p[0].append(("POP_SET", ("VARIABLE", p[2], 0)))

    def p_statement_set_at_dir(self, p):
        "statement : SET AT_CHAR variableID TO varexpression"
        if len(p) == 6 and self._is_valid_var(p[3]):
            if isinstance(p[5], list):
                p[0] = p[5]
            else:
                p[0] = [p[5]]
            p[0].append(("POP_SET", ("VARIABLE", p[3], 0)))

    def p_statement_choose(self, p):
        """
        statement : CHOOSE IF WAIT constexpression THEN GOTO ID
                  | CHOOSE IF WAIT constexpression THEN GOSUB ID
                  | CHOOSE IF CHANGED THEN GOSUB ID
                  | CHOOSE
        """
        if len(p) == 8 and p[3] == "WAIT":
            if self._is_valid_constexpression(p[4]) and self._symbol_usage(
                p[7], SymbolType.LABEL, p.lineno(7)
            ):
                if isinstance(p[4], list):
                    tm = p[4]
                else:
                    tm = [p[4]]

                if p[6] == "GOTO":
                    p[0] = (
                        "CHOOSE_W",
                        ("CONSTANT_L", tm),
                        ("CONSTANT_H", tm),
                        0x00,
                        p[7],
                        0,
                        0,
                    )
                elif p[6] == "GOSUB":
                    p[0] = (
                        "CHOOSE_W",
                        ("CONSTANT_L", tm),
                        ("CONSTANT_H", tm),
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
            if self._symbol_usage(p[6], SymbolType.LABEL, p.lineno(6)):
                p[0] = ("CHOOSE_CH", p[6], 0, 0)
            else:
                p[0] = None
        elif len(p) == 2:
            p[0] = ("CHOOSE",)

    def p_statement_option_goto(self, p):
        """
        statement : OPTION VALUE LPAREN varexpression RPAREN GOTO ID
                  | OPTION GOTO ID
        """
        if len(p) == 8 and self._symbol_usage(p[7], SymbolType.LABEL, p.lineno(7)):
            if isinstance(p[4], list):
                p[0] = p[4]
            else:
                p[0] = [p[4]]
            p[0] += [("POP_VAL_OPTION", 0, p[7], 0, 0)]
        elif len(p) == 4 and self._symbol_usage(p[3], SymbolType.LABEL, p.lineno(3)):
            p[0] = ("OPTION", 0, p[3], 0, 0)
        else:
            p[0] = None

    def p_statement_option_gosub(self, p):
        """
        statement : OPTION VALUE LPAREN varexpression RPAREN GOSUB ID
                  | OPTION GOSUB ID
        """
        if len(p) == 8 and self._symbol_usage(p[7], SymbolType.LABEL, p.lineno(7)):
            if isinstance(p[4], list):
                p[0] = p[4]
            else:
                p[0] = [p[4]]
            p[0] += [("POP_VAL_OPTION", 0xFF, p[7], 0, 0)]
        elif len(p) == 4 and self._symbol_usage(p[3], SymbolType.LABEL, p.lineno(3)):
            p[0] = ("OPTION", 0xFF, p[3], 0, 0)
        else:
            p[0] = None

    def p_varexpressions_list(self, p):
        """
        varexpressions_list : varexpressions_list COMMA nl_varexpression
                            | varexpressions_list COMMA varexpression_nl
                            | varexpressions_list COMMA varexpression
                            | nl_varexpression
                            | varexpression_nl
                            | varexpression
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

    def p_nl_varexpression(self, p):
        """
        nl_varexpression    : newline_seq varexpression_nl
                            | newline_seq varexpression
                            | newline_seq
        """
        if len(p) == 2:
            p[0] = None
        elif len(p) == 3 and p[2]:
            p[0] = p[2]

    def p_varexpression_nl(self, p):
        """
        varexpression_nl    : varexpression newline_seq
        """
        if len(p) == 3 and p[1]:
            p[0] = p[1]
        else:
            p[0] = None

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
        boolexpression : varexpression NOT_EQUALS varexpression
                  | varexpression LESS_EQUALS varexpression
                  | varexpression MORE_EQUALS varexpression
                  | varexpression EQUALS varexpression
                  | varexpression LESS_THAN varexpression
                  | varexpression MORE_THAN varexpression
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
        else:
            self.errors.append(self._(f"Symbol on line {p.lineno(2)} invalid"))

    def p_varexpression_binop(self, p):
        """
        varexpression : varexpression PLUS varexpression
                  | varexpression MINUS varexpression
                  | varexpression AND_B varexpression
                  | varexpression OR_B varexpression
                  | varexpression SHIFT_L varexpression
                  | varexpression SHIFT_R varexpression
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
            else:
                self.errors.append(self._(f"Symbol on line {p.lineno(2)} invalid"))

    def p_varexpression_min(self, p):
        """
        varexpression : MIN LPAREN varexpression COMMA varexpression RPAREN
        """
        if len(p) == 7 and p[3] and p[5]:
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

    def p_varexpression_max(self, p):
        """
        varexpression : MAX LPAREN varexpression COMMA varexpression RPAREN
        """
        if len(p) == 7 and p[3] and p[5]:
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

    def p_varexpression_unop(self, p):
        "varexpression : NOT_B varexpression %prec UNOT_B"
        if isinstance(p[2], list):
            p[0] = p[2] + [("NOT_B",)]
        else:
            p[0] = [p[2], ("NOT_B",)]

    def p_varexpression_group(self, p):
        "varexpression : LPAREN varexpression RPAREN"
        p[0] = p[2]

    def p_varexpression_variable_ind(self, p):
        "varexpression : LCARET varexpression RCARET"
        if len(p) == 4 and p[2]:
            if isinstance(p[2], list):
                p[0] = p[2]
            else:
                p[0] = [p[2]]
            p[0].append(("POP_PUSH_I",))

    def p_varexpression_get_attr(self, p):
        "varexpression : GETATTR LPAREN varexpression COMMA varexpression RPAREN"
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

    def p_varexpression_variable_addr(self, p):
        "varexpression : AT_CHAR AT_CHAR variableID"
        if self._is_valid_var(p[3]):
            p[0] = ("PUSH_D", ("VARIABLE", p[3], 0))
        else:
            p[0] = None

    def p_varexpression_variable(self, p):
        "varexpression : AT_CHAR variableID"
        if self._is_valid_var(p[2]):
            p[0] = ("PUSH_I", ("VARIABLE", p[2], 0))
        else:
            p[0] = None

    def p_varexpression_saveresult_expression(self, p):
        "varexpression : SAVERESULT LPAREN RPAREN"
        p[0] = ("PUSH_SAVE_RESULT",)

    def p_varexpression_optionval(self, p):
        "varexpression : OPTIONVAL LPAREN RPAREN"
        if len(p) == 4:
            p[0] = ("PUSH_OPTION_ST", 2)

    def p_varexpression_optionsel(self, p):
        "varexpression : OPTIONSEL LPAREN RPAREN"
        if len(p) == 4:
            p[0] = ("PUSH_OPTION_ST", 1)

    def p_varexpression_numoptions(self, p):
        "varexpression : NUMOPTIONS LPAREN RPAREN"
        if len(p) == 4:
            p[0] = ("PUSH_OPTION_ST", 0)

    def p_varexpression_attrval_constexpression(self, p):
        "varexpression : ATTRVAL LPAREN constexpression COMMA constexpression COMMA constexpression COMMA constexpression RPAREN"
        if (
            len(p) == 11
            and self._is_valid_constexpression(p[3])
            and self._is_valid_constexpression(p[5])
            and self._is_valid_constexpression(p[7])
            and self._is_valid_constexpression(p[9])
        ):
            ink = []
            if isinstance(p[3], list):
                ink += p[3]
            else:
                ink += [p[3]]
            ink += [("C_VAL", 7), ("C_&",)]

            paper = []
            if isinstance(p[5], list):
                paper += p[5]
            else:
                paper += [p[5]]
            paper += [("C_VAL", 7), ("C_&",), ("C_VAL", 3), ("C_<<",)]

            bright = []
            if isinstance(p[7], list):
                bright += p[7]
            else:
                bright += [p[7]]
            bright += [("C_VAL", 1), ("C_&",), ("C_VAL", 6), ("C_<<",)]

            flash = []
            if isinstance(p[9], list):
                flash += p[9]
            else:
                flash += [p[9]]

            flash += [("C_VAL", 1), ("C_&",), ("C_VAL", 7), ("C_<<",)]
            c_seq = ink + paper + [("C_|",)] + bright + [("C_|",)] + flash + [("C_|",)]
            p[0] = ("PUSH_D", ("CONSTANT", c_seq))

    def p_varexpression_attrmask_constexpression(self, p):
        "varexpression : ATTRMASK LPAREN constexpression COMMA constexpression COMMA constexpression COMMA constexpression RPAREN"
        if (
            len(p) == 11
            and self._is_valid_constexpression(p[3])
            and self._is_valid_constexpression(p[5])
            and self._is_valid_constexpression(p[7])
            and self._is_valid_constexpression(p[9])
        ):
            ink = []
            if isinstance(p[3], list):
                ink += p[3]
            else:
                ink += [p[3]]
            ink = (
                ink
                + [("C_VAL", 1), ("C_&",), ("C_VAL", 2), ("C_<<",)]
                + ink
                + [("C_VAL", 1), ("C_&",), ("C_VAL", 1), ("C_<<",)]
                + ink
                + [("C_VAL", 1), ("C_&",), ("C_|",), ("C_|",)]
            )

            paper = []
            if isinstance(p[5], list):
                paper += p[5]
            else:
                paper += [p[5]]
            paper = (
                paper
                + [("C_VAL", 1), ("C_&",), ("C_VAL", 5), ("C_<<",)]
                + paper
                + [("C_VAL", 1), ("C_&",), ("C_VAL", 4), ("C_<<",)]
                + paper
                + [("C_VAL", 1), ("C_&",), ("C_VAL", 3), ("C_<<",), ("C_|",), ("C_|",)]
            )

            bright = []
            if isinstance(p[7], list):
                bright += p[7]
            else:
                bright += [p[7]]
            bright += [("C_VAL", 1), ("C_&",), ("C_VAL", 6), ("C_<<",)]

            flash = []
            if isinstance(p[9], list):
                flash += p[9]
            else:
                flash += [p[9]]

            flash += [("C_VAL", 1), ("C_&",), ("C_VAL", 7), ("C_<<",)]
            c_seq = ink + paper + [("C_|",)] + bright + [("C_|",)] + flash + [("C_|",)]
            p[0] = ("PUSH_D", ("CONSTANT", c_seq))

    def p_varexpression_random_expression_limit(self, p):
        "varexpression : RANDOM LPAREN constexpression COMMA constexpression RPAREN"
        if (
            len(p) == 7
            and self._is_valid_constexpression(p[3])
            and self._is_valid_constexpression(p[5])
        ):
            if isinstance(p[3], list):
                p1 = p[3]
            else:
                p1 = [p[3]]
            if isinstance(p[5], list):
                p2 = p[5]
            else:
                p2 = [p[5]]

            p[0] = [
                ("PUSH_RANDOM", ("CONSTANT", p2 + p1 + [("C_-",)])),
                ("PUSH_D", ("CONSTANT", p1)),
                ("ADD",),
            ]
        else:
            p[0] = None

    def p_varexpression_random_constexpression(self, p):
        """
        varexpression : RANDOM LPAREN constexpression RPAREN
                      | RANDOM LPAREN RPAREN
        """
        if len(p) == 5 and self._is_valid_constexpression(p[3]):
            if isinstance(p[3], list):
                p[0] = ("PUSH_RANDOM", ("CONSTANT", p[3]))
            else:
                p[0] = ("PUSH_RANDOM", ("CONSTANT", [p[3]]))
        elif len(p) == 4:
            p[0] = ("PUSH_RANDOM", 255)
        else:
            p[0] = None

    def p_varexpression_inkey_constexpression(self, p):
        "varexpression : INKEY LPAREN constexpression RPAREN"
        if len(p) == 5 and self._is_valid_constexpression(p[3]):
            if isinstance(p[3], list):
                p[0] = ("PUSH_INKEY", ("CONSTANT", p[3]))
            else:
                p[0] = ("PUSH_INKEY", ("CONSTANT", [p[3]]))
        else:
            p[0] = None

    def p_varexpression_lastpos_array(self, p):
        "varexpression : LASTPOS LPAREN ID RPAREN"
        if len(p) == 5 and self._symbol_usage(p[3], SymbolType.ARRAY, p.lineno(3)):
            p[0] = ("PUSH_LEN_ARRAY", p[3], 0, 0)
        else:
            p[0] = [p[3]]

    def p_varexpression_get_array_value(self, p):
        "varexpression : ID LPAREN varexpression RPAREN"
        if (
            len(p) == 5
            and p[3]
            and self._symbol_usage(p[1], SymbolType.ARRAY, p.lineno(1))
        ):
            if isinstance(p[3], list):
                p[0] = p[3]
            else:
                p[0] = [p[3]]
            p[0].append(("PUSH_VAL_ARRAY", p[1], 0, 0))
        else:
            p[0] = None

    def p_varexpression_inkey(self, p):
        "varexpression : INKEY LPAREN RPAREN"
        p[0] = ("PUSH_INKEY", 0)

    def p_varexpression_kempston(self, p):
        "varexpression : KEMPSTON LPAREN RPAREN"
        p[0] = ("PUSH_KEMPSTON",)

    def p_varexpression_xpos(self, p):
        "varexpression : XPOS LPAREN RPAREN"
        p[0] = ("PUSH_XPOS",)

    def p_varexpression_ypos(self, p):
        "varexpression : YPOS LPAREN RPAREN"
        p[0] = ("PUSH_YPOS",)

    def p_varexpression_isdisk(self, p):
        "varexpression : ISDISK LPAREN RPAREN"
        p[0] = ("PUSH_IS_DISK",)

    def p_varexpression_expression(self, p):
        """
        varexpression  : constexpression
        """
        if isinstance(p[1], list):
            p[0] = ("PUSH_D", ("CONSTANT", p[1]))
        elif isinstance(p[1], tuple):
            p[0] = ("PUSH_D", ("CONSTANT", [p[1]]))
        else:
            p[0] = None

    def p_variable_ID(self, p):
        """
        variableID  : number
                    | ID
        """
        if isinstance(p[1], int):
            if self._check_byte_value(p[1], p.lineno(1)):
                p[0] = p[1]
            else:
                p[0] = None
        elif isinstance(p[1], str):
            if self._symbol_usage(p[1], SymbolType.VARIABLE, p.lineno(1)):
                p[0] = p[1]
            else:
                p[0] = None
        else:
            p[0] = None

    def p_constexpressions_list(self, p):
        """
        constexpressions_list   : constexpressions_list COMMA nl_constexpression
                                | constexpressions_list COMMA constexpression_nl
                                | constexpressions_list COMMA constexpression
                                | nl_constexpression
                                | constexpression_nl
                                | constexpression
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

    def p_nl_constexpression(self, p):
        """
        nl_constexpression  : newline_seq constexpression_nl
                            | newline_seq constexpression
                            | newline_seq
        """
        if len(p) == 2:
            p[0] = None
        elif len(p) == 3 and p[2]:
            p[0] = p[2]

    def p_constexpression_nl(self, p):
        """
        constexpression_nl  : constexpression newline_seq
        """
        if len(p) == 3 and p[1]:
            p[0] = p[1]
        else:
            p[0] = None

    def p_constexpression_binop(self, p):
        """
        constexpression : constexpression PLUS constexpression
                        | constexpression MINUS constexpression
                        | constexpression AND_B constexpression
                        | constexpression OR_B constexpression
                        | constexpression SHIFT_L constexpression
                        | constexpression SHIFT_R constexpression
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
            p[0].append(("C_" + p[2],))

    def p_constexpression_group(self, p):
        "constexpression : LPAREN constexpression RPAREN"
        p[0] = p[2]

    def p_constexpression_expression(self, p):
        "constexpression : expression"
        # if self._check_byte_value(p[1], p.lexer.lexer.lineno):
        if isinstance(p[1], int):
            p[0] = ("C_VAL", p[1])
        else:
            p[0] = None

    def p_constexpression_constant(self, p):
        "constexpression : ID"
        if self._is_valid_const(p[1]) and self._symbol_usage(
            p[1], SymbolType.CONSTANT, p.lineno(1)
        ):
            p[0] = ("C_REPL", p[1])
        else:
            p[0] = None

    def p_expression_binop(self, p):
        """
        expression : expression PLUS expression
                  | expression MINUS expression
                  | expression AND_B expression
                  | expression OR_B expression
                  | expression SHIFT_L expression
                  | expression SHIFT_R expression
        """
        if p[2] == "+":
            p[0] = p[1] + p[3]
        elif p[2] == "-":
            p[0] = p[1] - p[3]
        elif p[2] == "&":
            p[0] = p[1] & p[3]
        elif p[2] == "|":
            p[0] = p[1] | p[3]
        elif p[2] == "<<":
            p[0] = p[1] << p[3]
        elif p[2] == ">>":
            p[0] = p[1] >> p[3]
        else:
            self.errors.append(self._(f"Symbol on line {p.lineno(2)} invalid"))

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

    def p_newline_seq(self, p):
        """
        newline_seq : newline_seq NEWLINE_CHAR
                    | NEWLINE_CHAR
        """
        p[0] = None

    def p_loop_empty(self, p):
        """
        loop_empty : loop_empty NEWLINE_CHAR
                   | empty
        """
        pass

    def p_empty(self, p):
        "empty :"
        pass

    def p_error(self, p):
        if isinstance(p, lex.LexToken) or isinstance(p, yacc.YaccSymbol):
            msg = self._("Syntax error at line {}").format(p.lineno)
        elif isinstance(p, yacc.YaccProduction):
            msg = self._("Syntax error at line {}").format(p.lineno(0))
        else:
            tok_type_stack = [xx.type for xx in self.parser.symstack][1:]
            if self.debug:
                print(f"Last symbol stack: {tok_type_stack}")
            if tok_type_stack.count("IF") != tok_type_stack.count("ENDIF"):
                pos_if = tok_type_stack.index("IF") + 1
                msg = self._("Syntax error at line {}: Missing ENDIF for IF").format(self.parser.symstack[pos_if].lineno)
            elif tok_type_stack.count("WHILE") != tok_type_stack.count("WEND"):
                pos_while = tok_type_stack.index("WHILE") + 1
                msg = self._("Syntax error at line {}: Missing WEND for WHILE").format(self.parser.symstack[pos_while].lineno)
            elif tok_type_stack.count("DO") != tok_type_stack.count("UNTIL"):
                pos_while = tok_type_stack.index("DO") + 1
                msg = self._("Syntax error at line {}: Missing UNTIL for DO").format(self.parser.symstack[pos_while].lineno)
            else:
                msg = self._("Syntax error")
        self.errors.append(msg)

    def build(self):
        self.lexer.build()
        self.parser = yacc.yacc(module=self)

    def parse(self, input, verbose=False):
        if self.parser is None:
            self.errors.append(self._("Parser not build."))
            return None
        else:
            self.debug = verbose
            self.symbols.clear()
            self.symbols_used.clear()
            self.errors.clear()
            self.hidden_label_counter = 0
            # No need for code_text_reversal with refactored lexer (JSP/PHP style)
            # Text outside [[ ]], code inside [[ ]]
            parse_result = self.parser.parse(
                input, lexer=self.lexer, debug=self.debug, tracking=True
            )
            if not self._check_symbols():
                return []
            return parse_result

    def debug_p(self, p):
        s = ""
        for t in p:
            s += str(t) + ";"
        print(s)

    def _check_array(self, val, lineno):
        if not isinstance(val, list) or len(val) not in range(1, 256 + 1):
            self.errors.append(self._(f"Invalid array size on line {lineno}"))
            return False
        return True

    def _check_byte_value(self, val, lineno):
        if not isinstance(val, int) or val not in range(256):
            self.errors.append(self._(f"Invalid byte value {val} on line {lineno}"))
            return False
        return True

    def _check_word_value(self, val, lineno):
        if not isinstance(val, int) or val not in range(64 * 1024):
            self.errors.append(self._(f"Invalid word value {val} on line {lineno}"))
            return False
        return True

    def _is_valid_var(self, val):
        return isinstance(val, str) or isinstance(val, int)

    def _is_valid_const(self, val):
        return isinstance(val, str)

    def _is_valid_constexpression(self, val):
        return isinstance(val, list) or isinstance(val, tuple)

    def _is_valid_array(self, val):
        return isinstance(val, str)

    # def _fix_borders(self, row, col, width, height):
    #     (row, height) = self._fix_rows(row, height)
    #     (col, width) = self._fix_cols(col, width)
    #     return (row, col, width, height)

    # def _fix_rows(self, row, height):
    #     if row >= 24:
    #         row = 23
    #     if row < 0:
    #         row = 0
    #     if height <= 0:
    #         height = 1
    #     if (height + row) > 24:
    #         height = 24 - row
    #     return (row, height)

    # def _fix_cols(self, col, width):
    #     if col >= 32:
    #         col = 31
    #     if col < 0:
    #         col = 0
    #     if width <= 0:
    #         width = 1
    #     if (width + col) > 32:
    #         width = 32 - col
    #     return (col, width)

    # def _check_attr_values(self, ink, paper, bright, flash, lineno):
    #     error = False
    #     if ink < 0 or ink > 7:
    #         self.errors.append(self._(f"Invalid Ink value on line {lineno}"))
    #         error = True
    #     if paper < 0 or paper > 7:
    #         self.errors.append(self._(f"Invalid Paper value on line {lineno}"))
    #         error = True
    #     if bright < 0 or bright > 1:
    #         self.errors.append(self._(f"Invalid Bright value on line {lineno}"))
    #         error = True
    #     if flash < 0 or flash > 1:
    #         self.errors.append(self._(f"Invalid Flash value on line {lineno}"))
    #         error = True
    #     if error:
    #         return None
    #     return (flash << 7) | (bright << 6) | (paper << 3) | ink

    # def _get_attr_mask(self, ink, paper, bright, flash, lineno):
    #     error = False
    #     if ink not in range(2):
    #         self.errors.append(self._(f"Invalid Ink value on line {lineno}"))
    #         error = True
    #     if paper not in range(2):
    #         self.errors.append(self._(f"Invalid Paper value on line {lineno}"))
    #         error = True
    #     if bright not in range(2):
    #         self.errors.append(self._(f"Invalid Bright value on line {lineno}"))
    #         error = True
    #     if flash not in range(2):
    #         self.errors.append(self._(f"Invalid Flash value on line {lineno}"))
    #         error = True
    #     if error:
    #         return None
    #     if paper != 0:
    #         paper = 7
    #     if ink != 0:
    #         ink |= 7
    #     return (flash << 7) | (bright << 6) | (paper << 3) | ink

    def _get_hidden_label(self):
        l = f"__LABEL_{self.hidden_label_counter}"
        self.hidden_label_counter += 1
        return l

    # LEGACY: _code_text_reversal is no longer needed with refactored lexer
    # The refactored lexer (JSP/PHP style) handles text/code boundaries correctly:
    # - Text outside [[ ]] is tokenized as TEXT
    # - Code inside [[ ]] is tokenized as statements
    # This function was used with the old backwards lexer semantics
    #
    # def _code_text_reversal(self, text):
    #     code = ""
    #     skip = False
    #     is_text = True
    #     errors = []
    #     curr_text = ""
    #     curr_code = ""
    #     curr_line = 0
    #     curr_pos = 0
    #     last_c_line = 0
    #     last_c_pos = 0
    #     for i, c in enumerate(text):
    #         if skip:
    #             curr_pos += 1
    #             skip = False
    #         elif (i + 1) < len(text):
    #             if text[i] == "[" and text[i + 1] == "[":
    #                 if not is_text:
    #                     errors.append(
    #                         f"Invalid code opening on line {curr_line} at {curr_pos}"
    #                     )
    #                     break
    #                 skip = True
    #                 is_text = False
    #                 last_c_line = curr_line
    #                 last_c_pos = curr_pos
    #                 if len(curr_text) > 0:
    #                     curr_code += "[[" + curr_text + "]]"
    #                 else:  # with no text, adding a space to act as a separator
    #                     curr_code += " "
    #                 curr_text = ""
    #             elif text[i] == "]" and text[i + 1] == "]":
    #                 if is_text:
    #                     errors.append(
    #                         f"Invalid code closure on line {curr_line} at {curr_pos}"
    #                     )
    #                     break
    #                 skip = True
    #                 is_text = True
    #                 if len(curr_code) > 0:
    #                     code += curr_code
    #                 curr_code = ""
    #             elif is_text:
    #                 curr_text += c
    #             else:
    #                 curr_code += c
    #             if c == "\n":
    #                 curr_line += 1
    #                 curr_pos = 0
    #             else:
    #                 curr_pos += 1
    #     if not is_text and len(errors) == 0:
    #         errors.append(f"Invalid code closure on line {last_c_line} at {last_c_pos}")
    #     # Adding trailing text if exists
    #     if len(curr_text) > 0:
    #         code += "[[" + curr_text + "]]"
    #
    #     return (code, errors)

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
                self.errors.append(self._(
                    f"Label '{symbol}' on line {lineno} was already declared before."
                ))
            elif symbol_type == SymbolType.VARIABLE:
                self.errors.append(self._(
                    f"Variable '{symbol}' on line {lineno} was already declared before."
                ))
            elif symbol_type == SymbolType.CONSTANT:
                self.errors.append(self._(
                    f"Constant '{symbol}' on line {lineno} was already declared before."
                ))
            elif symbol_type == SymbolType.ARRAY:
                self.errors.append(self._(
                    f"Data array '{symbol}' on line {lineno} was already declared before."
                ))
            else:
                self.errors.append(self._(
                    f"Symbol '{symbol}' on line {lineno} was already declared before."
                ))
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
                    self.errors.append(self._(
                        f"Label '{symbol}' on line {lineno} was already used as variable."
                    ))
                elif symbol_type == SymbolType.VARIABLE:
                    self.errors.append(self._(
                        f"Variable '{symbol}' on line {lineno} was already used as label."
                    ))
                elif symbol_type == SymbolType.CONSTANT:
                    self.errors.append(self._(
                        f"Constant '{symbol}' on line {lineno} was already used as label."
                    ))
                elif symbol_type == SymbolType.ARRAY:
                    self.errors.append(self._(
                        f"Data array '{symbol}' on line {lineno} was already used as label."
                    ))
                else:
                    self.errors.append(self._(
                        f"Symbol '{symbol}' on line {lineno} was already used in other context."
                    ))
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
                    self.errors.append(self._(
                        f"Label '{symbol}' on lines {lines_str} is not declared."
                    ))
                elif symbol_type == SymbolType.VARIABLE:
                    self.errors.append(self._(
                        f"Variable '{symbol}' on lines {lines_str} is not declared."
                    ))
                elif symbol_type == SymbolType.CONSTANT:
                    self.errors.append(self._(
                        f"Constant '{symbol}' on lines {lines_str} is not declared."
                    ))
                elif symbol_type == SymbolType.ARRAY:
                    self.errors.append(self._(
                        f"Data array '{symbol}' on lines {lines_str} is not declared."
                    ))
                else:
                    self.errors.append(self._(
                        f"Symbol '{symbol}' on lines {lines_str} is not declared."
                    ))
                res = False
            else:
                s = self.symbols[symbol]
                if s[0] != symbol_type:
                    if symbol_type == SymbolType.LABEL:
                        self.errors.append(self._(
                            f"Label '{symbol}' on lines {lines_str} was already declared as variable on {s[1]}."
                        ))
                    elif symbol_type == SymbolType.VARIABLE:
                        self.errors.append(self._(
                            f"Variable '{symbol}' on lines {lines_str} was already declared as label on {s[1]}."
                        ))
                    elif symbol_type == SymbolType.CONSTANT:
                        self.errors.append(self._(
                            f"Constant '{symbol}' on lines {lines_str} was already declared as label on {s[1]}."
                        ))
                    elif symbol_type == SymbolType.ARRAY:
                        self.errors.append(self._(
                            f"Data array '{symbol}' on lines {lines_str} was already declared as label on {s[1]}."
                        ))
                    else:
                        self.errors.append(self._(
                            f"Symbol '{symbol}' on lines {lines_str} was already declared with another type on {s[1]}."
                        ))
                    res = False
        return res

    def print_symbols(self):
        for symbol in self.symbols.keys():
            s = self.symbols[symbol]
            if s[0] == SymbolType.LABEL:
                print(f"- Label '{symbol}' declared on line {s[1]}.")
            elif s[0] == SymbolType.VARIABLE:
                print(f"- Variable '{symbol}' declared on line {s[1]}.")
            elif s[0] == SymbolType.CONSTANT:
                print(f"- Constant '{symbol}' declared on line {s[1]}.")
            elif s[0] == SymbolType.ARRAY:
                print(f"- Data Array '{symbol}' declared on line {s[1]}.")
            else:
                print(f"- Symbol '{symbol}' declared on line {s[1]}.")
