import ply.lex as lex


class CydcLexer(object):
    def __init__(self):
        self.lexer = None
        self.txt_pos = 0

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
        "FLASH" : "FLASH" ,
        "SFX" : "SFX" ,
    }

    # token_list
    tokens = ["OPEN_CODE", "CLOSE_CODE", "TEXT", "COLON", "ERROR_OPEN_CODE", "NEWLINE"]
    tokens += ["DEC_NUMBER", "HEX_NUMBER", "ID", "INDIRECTION", "COMMA"]
    tokens += ["PLUS", "MINUS", "TIMES", "DIVIDE", "EQUALS", "LPAREN", "RPAREN"]
    tokens += ["NOT_EQUALS", "LESS_EQUALS", "MORE_EQUALS", "LESS_THAN", "MORE_THAN"]
    tokens += list(reserved.values())

    def t_INITIAL_OPEN_CODE(self, t):
        r"\[\["
        string = t.lexer.lexdata[self.txt_pos : t.lexer.lexpos - 2]
        if len(string) > 0:
            t.type = "TEXT"
            t.value = ("TEXT", string)
            t.lexer.begin("code")  # Enter 'ccode' state
            return t
        else:
            t.lexer.begin("code")
            return None

    def t_code_OPEN_CODE(self, t):
        r"\[\["
        t.type = "ERROR_OPEN_CODE"
        return t

    def t_code_CLOSE_CODE(self, t):
        r"\]\]"
        t.lexer.lineno += t.value.count("\n")
        self.txt_pos = t.lexer.lexpos
        t.lexer.begin("INITIAL")
        return t

    # Ignored characters
    t_code_ignore = " \t"

    def t_code_NEWLINE(self, t):
        r"(\n|\r|\r\n)+"
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_INITIAL_NEWLINE(self, t):
        r"\n+"
        t.lexer.lineno += t.value.count("\n")
        return None

    def t_code_COMMENT(self, t):
        r"--.*"
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
            t.type = "TEXT"
            t.value = ("TEXT", string)
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


if __name__ == "__main__":
    test = """[[Z 0x2f x>=(3+2)]] \[\]\n
    blablabla [[ Hola Label LABEL
    0x000 1234 @000 2-30 ]] xx
    [[
        --This is a comment
    ]] label
    [[ cccc:dddd ]] se acabo
    """
    l = CydcLexer()
    l.build()
    l.test(test)
