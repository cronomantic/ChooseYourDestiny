#!/usr/bin/python3

import shutil
import os

cPath= os.path.dirname(__file__)

DST_PATH = "../../dist/cydc/"
SRC_PATH = "./"
SRC_FILES = [
    "cydc_cli.py",
    "cydc/cydc.py",
    "cydc/cydc_codegen.py",
    "cydc/cydc_font.py",
    "cydc/cydc_lexer.py",
    "cydc/cydc_parser.py",
    "cydc/cydc_txt_compress.py",
    "cydc/ply/lex.py",
    "cydc/ply/yacc.py",
#    "cydc/__init__.py",
#    "cydc/ply/__init__.py",
]

for file in SRC_FILES:
    srcPath = os.path.join(cPath, SRC_PATH, file)
    dstPath = os.path.join(cPath, DST_PATH, file)
    os.makedirs(os.path.dirname(dstPath), exist_ok=True)
    shutil.copy(srcPath, dstPath)
