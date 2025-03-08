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

import sys
import os
import subprocess


def compress_zx0_list_bytes(zx0_path, chunk):
    """_summary_

    Args:
        zx0_path (_type_): _description_
        chunk (_type_): _description_
    """
    filename = "__TEMP__"
    try:
        with open(filename, "wb") as f:
            f.write(bytes(chunk))
    except OSError:
        sys.exit("ERROR: Can't write temp file.")
    zx0_path = os.path.abspath(zx0_path)  # Get the absolute path of the executable
    try:
        result = subprocess.run(
            [zx0_path, "-f", filename],
            check=True,
            # stdout=subprocess.DEVNULL,
            # stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as exc:
        raise OSError from exc
    finally:
        if os.path.isfile(filename):
            os.remove(filename)
    if result.returncode != 0:
        raise OSError
    try:
        with open(filename + ".zx0", "rb") as f:
            chunk = list(f.read())
    except OSError:
        sys.exit("ERROR: Can't read temp file.")
    finally:
        if os.path.isfile(filename + ".zx0"):
            os.remove(filename + ".zx0")
    return chunk


def bytes2str(list_bytes=[], b_str=""):
    """_summary_

    Args:
        list_bytes (list, optional): _description_. Defaults to [].
        b_str (str, optional): _description_. Defaults to "".

    Returns:
        _type_: _description_
    """
    cnt = 0
    for c in list_bytes:
        if cnt == 0:
            b_str += f"    DEFB ${c:02X}"
        else:
            b_str += f", ${c:02X}"
        cnt += 1
        if cnt == 16:
            cnt = 0
            b_str += "\n"
    if cnt != 0:
        b_str += "\n"
    return b_str


def make_plus3_dsk(mkp3fs_path, filename, label=None, filelist=[], disk_720=False):

    mkp3fs_path = os.path.abspath(
        mkp3fs_path
    )  # Get the absolute path of the executable
    if disk_720:
        command_line = [mkp3fs_path, "-720", "-cpmonly"]
    else:
        command_line = [mkp3fs_path, "-180"]
    if label is not None:
        command_line += ["-label", label]
    command_line += [filename] + filelist
    try:
        stdout = None
        # stdout=subprocess.DEVNULL
        stderr = None
        # stderr=subprocess.DEVNULL
        result = subprocess.run(
            command_line,
            check=True,
            stdout=stdout,
            stderr=stderr,
        )
    except subprocess.CalledProcessError as exc:
        raise OSError from exc
