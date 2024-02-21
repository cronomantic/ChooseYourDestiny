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

from ply import lex as lex


class CydcLexer(object):
    def __init__(self):
        self.lexer = None
        self.txt_pos = 0
        self.special_chars = [
            c.decode("iso-8859-15")
            for c in (
                b"\xAA",
                b"\xA1",
                b"\xBF",
                b"\xAB",
                b"\xBB",
                b"\xE1",
                b"\xE9",
                b"\xED",
                b"\xF3",
                b"\xFA",
                b"\xF1",
                b"\xD1",
                b"\xFC",
                b"\xDC",
            )
        ]

    states = (
        ("code", "exclusive"),
        #        ("comment", "exclusive"),
    )

    reserved = {
        "END": "END",
        "GOTO": "GOTO",
        "GOSUB": "GOSUB",
        "RETURN": "RETURN",
        "LABEL": "LABEL",
        "IF": "IF",
        "THEN": "THEN",
        "SET": "SET",
        "TO": "TO",
        "ADD": "ADD",
        "SUB": "SUB",
        "AND": "AND",
        "OR": "OR",
        "NOT": "NOT",
        "INK": "INK",
        "PAPER": "PAPER",
        "BORDER": "BORDER",
        "AT": "AT",
        "PRINT": "PRINT",
        "MARGINS": "MARGINS",
        "PICTURE": "PICTURE",
        "DISPLAY": "DISPLAY",
        "RANDOM": "RANDOM",
        "CENTER": "CENTER",
        "OPTION": "OPTION",
        "WAITKEY": "WAITKEY",
        "INKEY": "INKEY",
        "WAIT": "WAIT",
        "PAUSE": "PAUSE",
        "CHOOSE": "CHOOSE",
        "TYPERATE": "TYPERATE",
        "CLEAR": "CLEAR",
        "PAGEPAUSE": "PAGEPAUSE",
        "CHAR": "CHAR",
        "TAB": "TAB",
        "BRIGHT": "BRIGHT",
        "FLASH": "FLASH",
        "SFX": "SFX",
        "TRACK": "TRACK",
        "PLAY": "PLAY",
        "LOOP": "LOOP",
    }

    # token_list
    tokens = [
        "OPEN_CODE",
        "CLOSE_CODE",
        "TEXT",
        "COLON",
        "ERROR_OPEN_CODE",
        "NEWLINE",
        "ERROR_TEXT",
    ]
    tokens += ["SHORT_LABEL", "DEC_NUMBER", "HEX_NUMBER", "ID", "INDIRECTION", "COMMA"]
    tokens += ["PLUS", "MINUS", "TIMES", "DIVIDE", "EQUALS", "LPAREN", "RPAREN"]
    tokens += ["NOT_EQUALS", "LESS_EQUALS", "MORE_EQUALS", "LESS_THAN", "MORE_THAN"]
    tokens += list(reserved.values())

    def t_INITIAL_OPEN_CODE(self, t):
        r"\[\["
        string = t.lexer.lexdata[self.txt_pos : t.lexer.lexpos - 2]
        if len(string) > 0:
            t.type, t.value = self._parse_string(string, t.lexer.lineno)
            t.lexer.begin("code")  # Enter 'ccode' state
            return t
        else:
            t.lexer.begin("code")
            return None

    def t_code_comment(self, t):
        r"/\*(.|\n|\r|\r\n)*?\*/"
        t.lexer.lineno += self._count_newlines(t.value.count("\r"), t.value.count("\n"))
        return None

    def t_code_OPEN_CODE(self, t):
        r"\[\["
        t.type = "ERROR_OPEN_CODE"
        t.value = t.lexer.lineno
        return t

    def t_code_CLOSE_CODE(self, t):
        r"\]\]"
        # t.lexer.lineno += t.value.count("\n")
        self.txt_pos = t.lexer.lexpos
        t.lexer.begin("INITIAL")
        return t

    # Ignored characters
    t_code_ignore = " \t"

    def t_code_NEWLINE(self, t):
        r"(\n|\r|\r\n)+"
        t.lexer.lineno += self._count_newlines(t.value.count("\r"), t.value.count("\n"))
        return t

    def t_INITIAL_NEWLINE(self, t):
        r"(\n|\r|\r\n)+"
        t.lexer.lineno += self._count_newlines(t.value.count("\r"), t.value.count("\n"))
        return None

    t_code_COLON = r":"
    t_code_INDIRECTION = r"@"
    t_code_NOT_EQUALS = r"<>"
    t_code_LESS_EQUALS = r"<="
    t_code_MORE_EQUALS = r">="
    t_code_LESS_THAN = r"<"
    t_code_MORE_THAN = r">"
    t_code_PLUS = r"\+"
    t_code_MINUS = r"-"
    t_code_TIMES = r"\*"
    t_code_DIVIDE = r"/"
    t_code_EQUALS = r"="
    t_code_LPAREN = r"\("
    t_code_RPAREN = r"\)"
    t_code_COMMA = r","

    def t_code_SHORT_LABEL(self, t):
        r"\#[a-zA-Z_][a-zA-Z0-9_]*"
        t.value = t.value[1:]
        t.type = self.reserved.get(t.value.upper(), "SHORT_LABEL")  # Check for reserved words
        return t

    def t_code_HEX_NUMBER(self, t):
        r"0[xX][0-9a-fA-F]+|$[0-9a-fA-F]+"
        try:
            t.value = int(t.value, 0)
        except ValueError:
            print("Integer value too large %d", t.value)
            t.value = 0
        return t

    def t_code_DEC_NUMBER(self, t):
        r"\d+"
        try:
            t.value = int(t.value)
        except ValueError:
            print("Integer value too large %d", t.value)
            t.value = 0
        return t

    def t_code_ID(self, t):
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        t.type = self.reserved.get(t.value.upper(), "ID")  # Check for reserved words
        return t

    def t_code_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # EOF handling rule
    def t_INITIAL_eof(self, t):
        string = t.lexer.lexdata[self.txt_pos : t.lexer.lexpos]
        if len(string) > 0:
            t.type, t.value = self._parse_string(string, t.lexer.lineno)
            self.txt_pos = t.lexer.lexpos
            return t
        else:
            return None

    def t_INITIAL_error(self, t):
        t.lexer.skip(1)  # just skip chars

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def input(self, data):
        self.txt_pos = 0
        self.texts = []
        self.lexer.input(data)

    def token(self):
        return self.lexer.token()

    def get_tokens(self):
        return [i for i in self.tokens if i not in ("OPEN_CODE", "COMMENT")]

    def test(self, data):
        # Test it output
        self.input(data)
        while True:
            tok = self.token()
            if not tok:
                break
            print(tok)

    def _replace_chars(self, old_string):
        """Replace carriage returns and special characters"""
        new_string = ""
        for char in old_string:
            if ord(char) > 127:
                try:
                    char = self.special_chars.index(char) + 16
                except ValueError:
                    char = ord(char)
            elif char == "\n":
                char = ord("\r")
            else:
                char = ord(char)
            new_string += chr(char)
        return new_string

    def _parse_string(self, old_string, current_line):
        """parse to check if string is correct"""
        new_string = self._replace_chars(old_string)
        pos = 0
        line = current_line
        errors = []
        for char in new_string:
            if ord(char) == ord("\r"):
                pos = 0
                line += 1
            elif ord(char) > 127:
                errors.append((line, pos, char))
                pos += 1
            else:
                pos += 1
        if len(errors) > 0:
            token_type = "ERROR_TEXT"
            token_value = ("ERROR_TEXT", errors)
        else:
            token_type = "TEXT"
            token_value = ("TEXT", new_string)
        return token_type, token_value

    def _count_newlines(self, num_r, num_n):
        if num_n == 0 and num_r == 0:
            return 0
        elif num_n == 0 and num_r > 0:
            return num_r
        return num_n
