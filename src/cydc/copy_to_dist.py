#!/usr/bin/python3

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

import shutil
import os

cPath= os.path.dirname(__file__)

DST_PATH = "../../dist/"
SRC_PATH = "./"
SRC_FILES = [
    "cydc_cli.py",
    "cyd_font_conv.py",
    "cydc/cydc.py",
    "cydc/cydc_codegen.py",
    "cydc/cydc_font.py",
    "cydc/cydc_lexer.py",
    "cydc/cydc_parser.py",
    "cydc/cydc_txt_compress.py",
    "cydc/cyd.py",
    "cydc/cydc_utils.py",
    "cydc/ply/lex.py",
    "cydc/ply/yacc.py",
    "cydc/cyd/bank_zx128.asm",
    "cydc/cyd/cyd_plus3.asm",
    "cydc/cyd/cyd_tape.asm",
    "cydc/cyd/dzx0_turbo.asm",
    "cydc/cyd/dzx0_turbo_plus3.asm",
    "cydc/cyd/interpreter.asm",
    "cydc/cyd/loaderplus3.asm",
    "cydc/cyd/loadertape.asm",
    "cydc/cyd/music_manager.asm",
    "cydc/cyd/music_manager_tape.asm",
    "cydc/cyd/plus3dos.asm",
    "cydc/cyd/screen_manager.asm",
    "cydc/cyd/screen_manager_tape.asm",
    "cydc/cyd/sysvars.asm",
    "cydc/cyd/text_manager.asm",
    "cydc/cyd/inkey.asm",
    "cydc/cyd/vars.asm",
    "cydc/cyd/VTII10bG.asm",
    "cydc/cyd/VTII10bG_vars.asm",
]

for file in SRC_FILES:
    srcPath = os.path.join(cPath, SRC_PATH, file)
    dstPath = os.path.join(cPath, DST_PATH, file)
    os.makedirs(os.path.dirname(dstPath), exist_ok=True)
    shutil.copy(srcPath, dstPath)
