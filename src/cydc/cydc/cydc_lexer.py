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

        subtitute_chars_keys = [
            c.decode("iso-8859-15")
            for c in (
                b"\xC1",
                b"\xC9",
                b"\xCD",
                b"\xD3",
                b"\xDA",
                b"\xAB",
                b"\xBB",
            )
        ]
        subtitute_chars_values = [
            c.decode("iso-8859-15")
            for c in (
                b"\x41",
                b"\x45",
                b"\x49",
                b"\x4F",
                b"\x55",
                b"\x22",
                b"\x22",
            )
        ]
        self.subtitute_chars = {
            k: v for (k, v) in zip(subtitute_chars_keys, subtitute_chars_values)
        }
        subtitute_chars_keys = [8212, 8216, 8217, 0x02F5, 0x02F6, 0x030B, 0x030F]
        subtitute_chars_values = [
            c.decode("iso-8859-15")
            for c in (
                b"\x2D",
                b"\x27",
                b"\x27",
                b"\x22",
                b"\x22",
                b"\x22",
                b"\x22",
            )
        ]
        self.unicode_subtitute_chars = {
            k: v for (k, v) in zip(subtitute_chars_keys, subtitute_chars_values)
        }

    states = (
        ("text", "exclusive"),
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
        "ELSE": "ELSE",
        "ENDIF": "ENDIF",
        "SET": "SET",
        "TO": "TO",
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
        "RANDOMIZE": "RANDOMIZE",
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
        "REPCHAR": "REPCHAR",
        "DECLARE": "DECLARE",
        "AS": "AS",
        "NEWLINE": "NEWLINE",
        "WHILE": "WHILE",
        "WEND": "WEND",
        "XPOS": "XPOS",
        "YPOS": "YPOS",
        "MIN": "MIN",
        "MAX": "MAX",
    }

    # token_list
    tokens = [
        "TEXT",
        "COLON",
        "ERROR_CLOSE_TEXT",
        "NEWLINE_CHAR",
        "ERROR_TEXT",
    ]
    tokens += ["SHORT_LABEL", "DEC_NUMBER", "HEX_NUMBER", "ID", "AT_CHAR", "COMMA"]
    tokens += ["PLUS", "MINUS", "TIMES", "DIVIDE", "EQUALS"]
    tokens += ["NOT_EQUALS", "LESS_EQUALS", "MORE_EQUALS", "LESS_THAN", "MORE_THAN"]
    tokens += ["LPAREN", "RPAREN", "LCARET", "RCARET", "LCURLY", "RCURLY"]
    tokens += ["AND_B", "OR_B", "NOT_B"]
    tokens += list(reserved.values())

    def t_open_text(self, t):
        r"\[\["
        self.txt_pos = t.lexer.lexpos
        t.lexer.begin("text")
        return None

    def t_ERROR_CLOSE_TEXT(self, t):
        r"\]\]"
        t.type = "ERROR_CLOSE_TEXT"
        t.value = t.lexer.lineno
        return t

    def t_text_TEXT(self, t):
        r"\]\]"
        # t.lexer.lineno += t.value.count("\n")
        string = t.lexer.lexdata[self.txt_pos : t.lexer.lexpos - 2]
        if len(string) > 0:
            t.type, t.value = self._parse_string(string, t.lexer.lineno)
            t.lexer.begin("INITIAL")  # Enter 'ccode' state
            return t
        else:
            t.lexer.begin("INITIAL")
            return None

    def t_comment(self, t):
        r"/\*(.|\n|\r|\r\n)*?\*/"
        t.lexer.lineno += self._count_newlines(t.value.count("\r"), t.value.count("\n"))
        return None

    # Ignored characters
    t_ignore = " \t"
    t_text_ignore = ""

    def t_text_NEWLINE_CHAR(self, t):
        r"(\n|\r|\r\n)+"
        t.lexer.lineno += self._count_newlines(t.value.count("\r"), t.value.count("\n"))
        return None

    def t_NEWLINE_CHAR(self, t):
        r"(\n|\r|\r\n)+"
        t.lexer.lineno += self._count_newlines(t.value.count("\r"), t.value.count("\n"))
        return t

    t_COLON = r":"
    t_AT_CHAR = r"@"
    t_NOT_EQUALS = r"<>"
    t_LESS_EQUALS = r"<="
    t_MORE_EQUALS = r">="
    t_LESS_THAN = r"<"
    t_MORE_THAN = r">"
    t_NOT_B = r"!"
    t_AND_B = r"&"
    t_OR_B = r"\|"
    t_PLUS = r"\+"
    t_MINUS = r"-"
    t_TIMES = r"\*"
    t_DIVIDE = r"/"
    t_EQUALS = r"="
    t_LPAREN = r"\("
    t_RPAREN = r"\)"
    t_COMMA = r","
    t_LCARET = r"\["
    t_RCARET = r"\]"
    t_LCURLY = r"\{"
    t_RCURLY = r"\}"

    def t_SHORT_LABEL(self, t):
        r"\#[a-zA-Z_][a-zA-Z0-9_]*"
        t.value = t.value[1:]
        t.type = self.reserved.get(
            t.value.upper(), "SHORT_LABEL"
        )  # Check for reserved words
        return t

    def t_HEX_NUMBER(self, t):
        r"0[xX][0-9a-fA-F]+|$[0-9a-fA-F]+"
        try:
            t.value = int(t.value, 0)
        except ValueError:
            print("Integer value too large %d", t.value)
            t.value = 0
        return t

    def t_DEC_NUMBER(self, t):
        r"\d+"
        try:
            t.value = int(t.value)
        except ValueError:
            print("Integer value too large %d", t.value)
            t.value = 0
        return t

    def t_ID(self, t):
        r"[a-zA-Z_][a-zA-Z0-9_]*"
        t.type = self.reserved.get(t.value.upper(), "ID")  # Check for reserved words
        return t

    def t_text_error(self, t):
        t.lexer.skip(1)

    def t_INITIAL_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)

    # EOF handling rule
    def t_text_eof(self, t):
        string = t.lexer.lexdata[self.txt_pos : t.lexer.lexpos]
        if len(string) > 0:
            t.type, t.value = self._parse_string(string, t.lexer.lineno)
            self.txt_pos = t.lexer.lexpos
            return t
        else:
            return None

    def t_error(self, t):
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
        return [
            i for i in self.tokens if i not in ("OPEN_TEXT", "COMMENT", "CLOSE_TEXT")
        ]

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
                    if char in self.subtitute_chars:
                        char = self.subtitute_chars[char]
                    elif ord(char) in self.unicode_subtitute_chars:
                        char = self.unicode_subtitute_chars[ord(char)]
                    else:
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
