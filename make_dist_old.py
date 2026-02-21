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
import struct
import zipfile


def compile_po_to_mo(po_path, mo_path):
    """Compile a gettext .po file into a binary .mo file (pure Python).

    Produces a little-endian MO file (magic 0xDE120495) compatible with the
    GNU gettext runtime and Python's ``gettext`` module.
    """

    def _unescape(s):
        out = []
        i = 0
        while i < len(s):
            if s[i] == "\\" and i + 1 < len(s):
                c = s[i + 1]
                if c == "n":
                    out.append("\n")
                elif c == "t":
                    out.append("\t")
                elif c == "r":
                    out.append("\r")
                elif c == '"':
                    out.append('"')
                elif c == "\\":
                    out.append("\\")
                else:
                    out.append(s[i])
                    i += 1
                    continue
                i += 2
            else:
                out.append(s[i])
                i += 1
        return "".join(out)

    catalog = {}        # msgid (str) → msgstr (str)
    msgid = msgstr = ""
    in_id = in_str = False

    def _save():
        if in_str:
            catalog[msgid] = msgstr

    with open(po_path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                _save()
                in_id = in_str = False
                continue
            if line.startswith("msgid "):
                _save()
                in_id, in_str = True, False
                msgid = _unescape(line[6:].strip()[1:-1])
                msgstr = ""
            elif line.startswith("msgstr "):
                in_id, in_str = False, True
                msgstr = _unescape(line[7:].strip()[1:-1])
            elif line.startswith('"') and line.endswith('"'):
                s = _unescape(line[1:-1])
                if in_id:
                    msgid += s
                elif in_str:
                    msgstr += s
    _save()

    # Keep header (msgid == "") and entries that have a non-empty translation.
    entries = sorted(
        [
            (k.encode("utf-8"), v.encode("utf-8"))
            for k, v in catalog.items()
            if v or k == ""
        ],
        key=lambda e: e[0],
    )
    N = len(entries)

    # MO layout (all uint32, little-endian):
    #   header         28 bytes  (7 × uint32)
    #   orig table     N × 8 bytes
    #   trans table    N × 8 bytes
    #   orig strings   (NUL-terminated, packed)
    #   trans strings  (NUL-terminated, packed)
    O = 28           # offset of original-strings table
    T = O + N * 8    # offset of translated-strings table
    S = T + N * 8    # first byte of string data

    orig_blob = b"\x00".join(k for k, _ in entries) + (b"\x00" if N else b"")
    tran_blob = b"\x00".join(v for _, v in entries) + (b"\x00" if N else b"")

    orig_table = b""
    tran_table = b""
    orig_pos = S
    tran_pos = S + len(orig_blob)
    for k, v in entries:
        orig_table += struct.pack("<II", len(k), orig_pos)
        tran_table += struct.pack("<II", len(v), tran_pos)
        orig_pos += len(k) + 1
        tran_pos += len(v) + 1

    os.makedirs(os.path.dirname(mo_path), exist_ok=True)
    with open(mo_path, "wb") as fh:
        fh.write(struct.pack("<7I", 0x950412DE, 0, N, O, T, 0, T + N * 8))
        fh.write(orig_table)
        fh.write(tran_table)
        fh.write(orig_blob)
        fh.write(tran_blob)
    print(f"  Compiled {os.path.relpath(po_path)} → {os.path.relpath(mo_path)}")


def compile_locale_dir(locale_dir):
    """Walk *locale_dir* and compile every .po file to its sibling .mo file."""
    for dirpath, _, filenames in os.walk(locale_dir):
        for fname in filenames:
            if fname.endswith(".po"):
                po = os.path.join(dirpath, fname)
                mo = os.path.splitext(po)[0] + ".mo"
                compile_po_to_mo(po, mo)

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

# Compile .po → .mo for all locale directories
LOCALE_DIRS = [
    os.path.join(currentPath, "locale"),
    os.path.join(currentPath, SRC_PATH, "cydc", "locale"),
    os.path.join(currentPath, SRC_PATH, "locale"),
]
print("Compiling translations...")
for locale_dir in LOCALE_DIRS:
    compile_locale_dir(locale_dir)

# Copy locale directories for the cydc and cyd_font_conv domains into dist/
shutil.copytree(
    os.path.join(currentPath, SRC_PATH, "cydc", "locale"),
    os.path.join(currentPath, DST_PATH, "cydc", "locale"),
    dirs_exist_ok=True,
)
shutil.copytree(
    os.path.join(currentPath, SRC_PATH, "locale"),
    os.path.join(currentPath, DST_PATH, "locale"),
    dirs_exist_ok=True,
)


DIST_DIRS = ["assets", "examples", "dist/cydc", "locale", "dist/locale"]
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
