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

from string import Template


class AsmTemplate(Template):
    delimiter = "@"


def get_asm_template(filename):
    filepath = os.path.join(os.path.dirname(__file__), "cyd", filename + ".asm")
    filepath = os.path.abspath(filepath)
    if not os.path.isfile(filepath):
        raise ValueError(f"{filename} file not found")
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    return AsmTemplate(text)


def run_assembler(asm_path, asm, filename, listing=True, capture_output=False):
    """_summary_

    Args:
        zx0_path (_type_): _description_
        chunk (_type_): _description_
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(asm)
    except OSError:
        sys.exit("ERROR: Can't write temp file.")
    asm_path = os.path.abspath(asm_path)  # Get the absolute path of the executable
    command_line = [asm_path, "--nologo", "-Wno-all"]
    if listing:
        command_line += ["--lst=" + (os.path.splitext(filename)[0] + ".lst")]
    command_line += [filename]
    try:
        stdout = None
        # stdout = subprocess.DEVNULL
        # stdout = subprocess.STDOUT
        stderr = None
        # stderr=subprocess.DEVNULL
        result = subprocess.run(
            args=command_line,
            check=False,
            stdout=subprocess.PIPE if capture_output else stdout,
            stderr=subprocess.PIPE if capture_output else stderr,
            universal_newlines=capture_output,
        )
    except subprocess.CalledProcessError as exc:
        raise OSError from exc
    finally:
        if os.path.isfile(filename):
            os.remove(filename)
    if result.returncode != 0:
        raise OSError(result.stderr)
    return result
    # try:
    #    with open(filename + ".zx0", "rb") as f:
    #        chunk = list(f.read())
    # except OSError:
    #    sys.exit("ERROR: Can't read temp file.")
    # finally:
    #    if os.path.isfile(filename + ".zx0"):
    #        os.remove(filename + ".zx0")
    # return chunk


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


def file_must_be_generated(src_file_path, prod_file_path):
    if not os.path.exists(src_file_path):
        return False

    if not os.path.exists(prod_file_path):
        return True

    src_mtime = os.path.getmtime(src_file_path)
    prod_mtime = os.path.getmtime(prod_file_path)

    return prod_mtime <= src_mtime
