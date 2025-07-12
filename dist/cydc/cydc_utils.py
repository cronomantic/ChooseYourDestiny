# -- coding: utf-8 -*-
#
# Choose Your Destiny.
#
# Copyright (C) 2024 Sergio Chico <cronomantic@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys, os, subprocess, json, time

from string import Template
from mkp3fs import Plus3DosFilesystem
from cydc_csc import ScreenCompress


class Timer:
    MICROSECONDS = 1000
    MILLISECONDS = 1000 * MICROSECONDS
    SECONDS = 1000 * MILLISECONDS
    HOURS = 60 * 60 * SECONDS
    MINUTES = 60 * SECONDS

    def __init__(self):
        self.start_time_ns = time.time_ns()
        
    def reset(self):
        self.start_time_ns = time.time_ns()

    def elapsed_ns(self):
        return time.time_ns() - self.start_time_ns

    def __str__(self):
        elapsed = self.elapsed_ns()
        if elapsed >= self.HOURS:
            elapsed /= self.HOURS
            return f"{elapsed:.2f} hours"
        elif elapsed >= self.MINUTES:
            elapsed /= self.MINUTES
            return f"{elapsed:.2f} min."
        elif elapsed >= self.SECONDS:
            elapsed /= self.SECONDS
            return f"{elapsed:.2f} sec."
        elif elapsed >= self.MILLISECONDS:
            elapsed /= self.MILLISECONDS
            return f"{elapsed:.2f} ms."
        else:
            elapsed /= self.MICROSECONDS
            return f"{elapsed:.2f} us."


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


def get_image_config(fpath):
    txt = None
    file_data = None
    res = True
    try:
        if os.path.isfile(fpath):
            with open(fpath, "r") as f:
                file_data = json.load(f)
            res = isinstance(file_data, list)
            if res:
                for scr_cfg in file_data:
                    res = isinstance(scr_cfg, dict)
                    if not res:
                        break
                    else:
                        res = set(scr_cfg.keys()) == set(
                            ["id", "num_lines", "force_mirror"]
                        )
                        if res:
                            res = isinstance(scr_cfg["id"], int) and scr_cfg[
                                "id"
                            ] in range(256)
                            if not res:
                                break
                            res = isinstance(scr_cfg["num_lines"], int) and scr_cfg[
                                "num_lines"
                            ] in range(1, 193)
                            if not res:
                                break
                            res = isinstance(scr_cfg["force_mirror"], bool)
                            if not res:
                                break
            if not res:
                file_data = None
                txt = f"ERROR: Invalid JSON format for file {fpath}\n"
    except UnicodeDecodeError:
        txt = f"ERROR: Invalid encoding of file: {fpath}\n"
        res = False
    except json.JSONDecodeError:
        txt = f"ERROR: Invalid JSON file: {fpath}\n"
        res = False
    except OSError:
        txt = f"ERROR: Can't open file: {fpath}\n"
        res = False
    return (
        res,
        file_data,
        txt,
    )


def compress_screen_file(fpath, num_lines=192, force_mirror=False, verbose=False):
    if os.path.isfile(fpath):
        with open(fpath, "rb") as f:
            b = list(f.read())
            if verbose:
                print(f"Compressing file {fpath}...")
            csc = ScreenCompress(b)
            cb, txt = csc.convert_to_CSC(num_lines=num_lines, force_mirror=force_mirror)
            if verbose:
                txt = txt.splitlines()
                for line in txt:
                    print(line)
            return cb
    return None


def make_plus3_dsk(filename, label=None, filelist=[], disk_720=False, verbose=False):
    p3fs = Plus3DosDiskUtil(verbose=verbose)
    for filepath in filelist:
        p3fs.add_file_path(filepath)
    if not p3fs.make_plus3_disk(
        dsk_file=filename,
        label=label,
        size720=disk_720,
        timestamp=False,
        cpmonly=True,
        dosonly=False,
    ):
        raise OSError


def make_plus3_dsk_old(mkp3fs_path, filename, label=None, filelist=[], disk_720=False):

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


class Plus3DosDiskUtil(Plus3DosFilesystem):
    def __init__(self, verbose=False):
        self.verbose = verbose
        super().__init__()

    def report(self, s):
        if self.verbose:
            print(f"{s}\n", end="")
