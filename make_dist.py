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
import zipfile

currentPath = os.path.dirname(__file__)

DST_PATH = "dist/"
SRC_PATH = "src/cydc"
SRC_FILES = [
    "cydc_cli.py",
    "cyd_chr_conv.py",
    "cydc/cydc.py",
    "cydc/cydc_codegen.py",
    "cydc/cydc_font.py",
    "cydc/cydc_lexer.py",
    "cydc/cydc_parser.py",
    "cydc/cydc_txt_compress.py",
    "cydc/cyd.py",
    "cydc/cydc_utils.py",
    "cydc/cydc_music.py",
    "cydc/cydc_csc.py",
    "cydc/plus3fs.py",
    "cydc/mkp3fs.py",
    "cydc/ply/lex.py",
    "cydc/ply/yacc.py",
    "cydc/pyZX0/compress.py",
    "cydc/pyZX0/optimize.py",
    "cydc/pyZX0/pyzx0.py",
    "cydc/pyZX0/README.md",
    "cydc/pyZX0/LICENSE",
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
    "cydc/cyd/savegame_plus3.asm",
    "cydc/cyd/savegame_tape.asm",
    "cydc/cyd/wyz_player.asm",
]

for file in SRC_FILES:
    srcPath = os.path.join(currentPath, SRC_PATH, file)
    dstPath = os.path.join(currentPath, DST_PATH, file)
    os.makedirs(os.path.dirname(dstPath), exist_ok=True)
    shutil.copy(srcPath, dstPath)


DIST_DIRS = ["assets", "examples", "dist/cydc"]
DIST_DIRS_WIN32 = ["dist/python"] + DIST_DIRS
DIST_DIRS_LINUX = [] + DIST_DIRS

DIST_FILES = [
    "make_adventure.py",
    "LICENSE",
    "version.txt",
    "test.cyd",
    "MANUAL_es.md",
    "MANUAL_en.md",
    "README.md",
    "dist/cyd_chr_conv.py",
    "dist/cydc_cli.py",
    "IMAGES/readme.txt",
    "TRACKS/readme.txt",
    "documentation/es/MANUAL_es.pdf",
    "documentation/en/MANUAL_en.pdf",
    "documentation/es/TUTORIAL_es.pdf",
    "documentation/en/TUTORIAL_en.pdf",
    "make_adventure_gui.py",
]
DIST_FILES_WIN32 = [
    "make_adv.cmd",
    "tools/mkp3fs.exe",
    "tools/sjasmplus.exe",
    "tools/zx0.exe",
    "dist/csc.exe",
    "dist/cyd_chr_conv.cmd",
    "dist/cydc.cmd",
    "make_adventure_gui.cmd",
] + DIST_FILES
DIST_FILES_LINUX = [
    "make_adv.sh",
    "make_adventure_gui.sh",
    "dist/csc",
] + DIST_FILES

for d in DIST_DIRS_WIN32:
    result = [os.path.join(x[0], t) for x in os.walk(os.path.normpath(d)) for t in x[2]]
    result = [x for x in result if "__pycache__" not in x]
    DIST_FILES_WIN32 += result

for d in DIST_DIRS_LINUX:
    result = [os.path.join(x[0], t) for x in os.walk(os.path.normpath(d)) for t in x[2]]
    result = [x for x in result if "__pycache__" not in x]
    DIST_FILES_LINUX += result

ver_file_path = os.path.join(currentPath, "version.txt")
version = ""
if os.path.exists(ver_file_path):
    with open(ver_file_path, "r") as f:
        version = f.read()
    version = "_" + version
    version = version.replace("\n", "")
    version = version.replace("\r", "")

with zipfile.ZipFile(
    os.path.join(currentPath, "ChooseYourDestiny_Win_x64" + version + ".zip"),
    mode="w",
    compression=zipfile.ZIP_DEFLATED,
    compresslevel=9,
) as zFile:
    for f in DIST_FILES_WIN32:
        f_path = os.path.join(currentPath, os.path.normpath(f))
        zFile.write(f_path, arcname=f)
    zFile.close()

# with zipfile.ZipFile(
#    os.path.join(currentPath, "ChooseYourDestiny_Linux_x64.zip"),
#    mode="w",
#    compression=zipfile.ZIP_DEFLATED,
#    compresslevel=9,
# ) as zFile:
#    for f in DIST_FILES_LINUX:
#        f_path = os.path.join(currentPath, os.path.normpath(f))
#        zFile.write(f_path, arcname=f)
#    zFile.close()
