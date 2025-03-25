#
# MIT License
#
# Copyright (c) 2025 Sergio Chico
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

import os

from cydc_utils import (
    bytes2str,
    run_assembler,
    get_asm_template,
    file_must_be_generated,
)
from pyZX0.compress import compress_data


def compress_track_data(data):
    cdata, delta = compress_data(bytearray(data), 0, False, False, False)
    return list(cdata), delta


def add_size_header(file_path_orig, file_path_dest):

    if file_must_be_generated(file_path_orig, file_path_dest):
        with open(file_path_orig, "rb") as fo:
            b = list(fo.read())
        size = len(b)
        b = [(size & 0xFF), ((size >> 8) & 0xFF)] + b
        with open(file_path_dest, "wb") as fb:
            fb.write(bytearray(b))


def create_wyz_player_bank(
    track_path, sjasmplus_path, tracks={}, instruments="", verbose=False
):

    bank_data = None

    tracks = dict(sorted(tracks.items()))

    path_dest = os.path.join(track_path, f"wyz_player_bank__.bin").replace(os.sep, "/")
    path_orig = os.path.join(track_path, f"wyz_player_bank__.asm").replace(os.sep, "/")

    tracks_asm = ""
    ttable = "TABLA_SONG:\n"
    for k in tracks.keys():
        ttable += f"    DW SONG_{k}\n"
        tracks_asm += f"SONG_{k}:\n" + bytes2str(tracks[k]) + "\n"
    ttable += "\n"
    tracks_asm += "\n"

    instruments = instruments.replace("DW ", "\tDW ").replace("DB ", "\tDB ")
    d = dict(
        TRACK_TABLE=ttable,
        TRACKS=tracks_asm,
        INSTRUMENTS=instruments,
    )
    t = get_asm_template("wyz_player")
    asm = t.substitute(d)

    asm += f"\nWYZ_LEN=($-$C000)"
    asm += f"\n    ASSERT WYZ_LEN < $4000, Player file is too big!\n"
    asm += f'    SAVEBIN "{path_dest}",WYZ_CALL,WYZ_LEN\n'
    asm += f"    END\n"

    res = run_assembler(
        asm_path=sjasmplus_path,
        asm=asm,
        filename=path_orig,
        listing=verbose,
        capture_output=False,
    )
    if os.path.exists(path_orig):
        os.remove(path_orig)

    if res and os.path.exists(path_dest):
        with open(path_dest, "rb") as f:
            bank_data = list(f.read())
        os.remove(path_dest)

    return res, bank_data
