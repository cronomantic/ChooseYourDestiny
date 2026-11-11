"""Pygments lexer for Choose Your Destiny (.cyd), for the documentation site.

It follows the VS Code highlighter (external/chooseyourdestiny-highlighter,
syntaxes/cyd.tmLanguage.json): the code goes inside [[ ]] and everything
outside is the game's text. A snippet with no [[ at all (the manuals'
one-line examples) is taken as code.
"""

import re

from pygments.lexer import RegexLexer, bygroups, words
from pygments.token import (Comment, Keyword, Name, Number, Operator,
                            Punctuation, String, Text, Whitespace)

ID = r"[A-Za-z_][A-Za-z0-9_]*"

FLOW = ("GOTO", "GOSUB", "CALL", "RETURN", "END", "LABEL", "READ", "RESTORE",
        "IF", "THEN", "ELSE", "ELSEIF", "ENDIF", "SELECT", "CASE", "ENDSELECT",
        "WHILE", "WEND", "DO", "UNTIL", "FOR", "NEXT", "STEP")
DECLARATION = ("DECLARE", "AS", "CONST", "DIM", "DATA", "IMPORT", "FROM",
               "WORD", "DWORD", "ENUM", "REPEAT", "INCLUDE", "LIB",
               "SET", "TO", "LET", "SWAP")
COMMANDS = ("OPTION", "CHOOSE", "MENUCONFIG", "MENUKEY", "MENUJOY", "CLEAROPTIONS",
            "PRINT", "CLEAR", "CENTER", "NEWLINE", "BACKSPACE", "CHAR", "REPCHAR",
            "TAB", "MARGINS", "AT", "PAGEPAUSE", "TYPERATE", "WAITKEY", "WAIT",
            "PAUSE", "WINDOW", "BLIT", "PICTURE", "DISPLAY",
            "INK", "PAPER", "BORDER", "BRIGHT", "FLASH", "FADEOUT", "FILLATTR",
            "PUTATTR", "CHARSET", "SFX", "TRACK", "PLAY", "LOOP",
            "LOAD", "SAVE", "RAMLOAD", "RAMSAVE", "RANDOMIZE", "VALUE", "CHANGED")
FUNCTIONS = ("INKEY", "RANDOM", "XPOS", "YPOS", "ISDISK", "KEMPSTON", "MIN", "MAX",
             "ATTRVAL", "ATTRMASK", "GETATTR", "OPTIONVAL", "OPTIONSEL",
             "NUMOPTIONS", "SAVERESULT", "LASTPOS", "DATAEND")
ASM_NAMES = r"\b(CYD_PEEK|CYD_POKE|CYD_ARR_MAP|CYD_ARR_FLUSH|CYD_CALL|CYD_SYSCALL|" \
            r"SET_RAM_BANK|FLAGS|SCREEN_BUFFER_PXL|SCREEN_BUFFER_ATT|VIDEO_PXL|" \
            r"VIDEO_ATT|SVC_[A-Z0-9_]+|ARR_\w+|RT_\w+)\b"


class CydLexer(RegexLexer):
    name = "Choose Your Destiny"
    aliases = ["cyd"]
    filenames = ["*.cyd"]
    flags = re.IGNORECASE | re.MULTILINE

    tokens = {
        "root": [
            (r"\[\[", Comment.Preproc, "code"),
            (r"[^\[]+", Text),
            (r"\[", Text),
        ],
        "code": [
            (r"\]\]", Comment.Preproc, "#pop"),
            (r"\s+", Whitespace),
            (r"/\*", Comment.Multiline, "comment"),
            (r'"(?:[^"\n\]]|\](?!\]))*"', String.Double),
            (r"'[^'\n]'", String.Char),
            (r"\b(ASM)(\s+)(" + ID + ")", bygroups(Keyword.Declaration, Whitespace, Name.Function), "asm"),
            (r"\b(LABEL|GOTO|GOSUB)(\s+)(" + ID + ")", bygroups(Keyword, Whitespace, Name.Function)),
            (r"\b(CALL)(\s+)(" + ID + ")", bygroups(Keyword, Whitespace, Name.Function)),
            (r"(#)(" + ID + ")", bygroups(Punctuation, Name.Function)),
            (words(FUNCTIONS, prefix=r"\b", suffix=r"(?=\s*\()"), Name.Builtin),
            (words(FLOW, prefix=r"\b", suffix=r"\b"), Keyword),
            (words(DECLARATION, prefix=r"\b", suffix=r"\b"), Keyword.Declaration),
            (words(COMMANDS, prefix=r"\b", suffix=r"\b"), Name.Builtin),
            (r"\b(AND|OR|NOT)\b", Operator.Word),
            (r"\b0b[01]+\b", Number.Bin),
            (r"\b0x[0-9a-f]+\b", Number.Hex),
            (r"\b[0-9]+\b", Number.Integer),
            (r"(@@?)(" + ID + r"|[0-9]+)", Name.Variable),
            (ID, Name),
            (r"\.\.|\+=|-=|<>|<=|>=|<<|>>|[<>+\-*/=!&|]", Operator),
            (r"[\[\](){},:]", Punctuation),
            (r".", Text),
        ],
        "comment": [
            (r"[^*]+", Comment.Multiline),
            (r"\*/", Comment.Multiline, "#pop"),
            (r"\*", Comment.Multiline),
        ],
        "asm": [
            (r"^(\s*)(ENDASM)\b", bygroups(Whitespace, Keyword.Declaration), "#pop"),
            (r";.*$", Comment.Single),
            (r"\b(EXPORTS|USES)\b", Keyword.Declaration),
            (ASM_NAMES, Name.Builtin),
            (r"(\$|0x)[0-9a-f]+\b|(%|0b)[01]+\b|\b[0-9]+\b", Number),
            (r"\b\w+\b", Name),
            (r"\s+", Whitespace),
            (r".", Text),
        ],
    }

    def get_tokens_unprocessed(self, text, stack=("root",)):
        if "[[" not in text:
            stack = ("root", "code")
        yield from super().get_tokens_unprocessed(text, stack)
