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

import sys
import os

from plus3fs import *

################################################################################

class QueuedFile:

    def __init__(self, path="", data=None, uid=0):
        self.path = path
        self.data = data
        self.fcbname = bytearray(12)
        self.uid = uid
        p3fs_83name(os.path.basename(path), self.fcbname)

    def load_file_data(self):
        try:
            with open(self.path, "rb") as f:
                self.data = f.read()
        except IOError:
            return False
        return True

################################################################################

class Plus3DosFilesystem(object):

    BOOT_180 = [
        0x00,  # Disc type
        0x00,  # Disc geometry
        0x28,  # Tracks
        0x09,  # Sectors
        0x02,  # Sector size
        0x01,  # Reserved tracks
        0x03,  # ?Sectors per block
        0x02,  # ?Directory blocks
        0x2A,  # Gap length (R/W)
        0x52,  # Gap length (format)
    ]

    BOOT_720 = [
        0x03,  # Disc type
        0x81,  # Disc geometry
        0x50,  # Tracks
        0x09,  # Sectors
        0x02,  # Sector size
        0x02,  # Reserved tracks
        0x04,  # ?Sectors per block
        0x04,  # ?Directory blocks
        0x2A,  # Gap length (R/W)
        0x52,  # Gap length (format)
    ]

    def __init__(self):
        self.gl_fs = PLUS3FS(self.report)
        self.files = []
        self.fcbname = bytearray(12)

    def add_file_data(self, name, data):
        file = QueuedFile(path=name, data=data)
        self.files.append(file)

    def add_file_path(self, path):
        file = QueuedFile(path=path)
        self.files.append(file)

    def make_plus3_disk(
        self,
        dsk_file,
        size720=False,
        label=None,
        timestamp=True,
        cpmonly=True,
        dosonly=False,
    ):
        if cpmonly and dosonly:
            self.report(
                "cpmonly and dosonly options both present; cpmonly option takes priority\n"
            )
        boot_spec = self.BOOT_720 if size720 else self.BOOT_180
        dsk_format = 720 if size720 else 180
        err = self.gl_fs.p3fs_mkfs(
            name=dsk_file,
            type="dsk",
            dsk_format=dsk_format,
            timestamped=timestamp,
            boot_spec=boot_spec,
        )
        if p3fs_error_check(err) and timestamp and label is not None:
            fcbname = bytearray(12)
            p3fs_label(label, fcbname)
            err = self.gl_fs.p3fs_setlabel(fcbname)
        if not p3fs_error_check(err):
            self.report_error(f"Can't create {dsk_file}: {p3fs_strerror(err)}\n")
            return False
        for file in self.files:
            if file.data is None:
                res = file.load_file_data()
                if not res:
                    self.report_error(f"Could not load file {file.path}\n")
                    return False
            filename = file.fcbname.decode("ascii")
            self.report(f"Writing {filename[:8]:<8}.{filename[8:11]:<3}")
            err, fpo = self.gl_fs.p3fs_creat(file.uid, file.fcbname)
            if not p3fs_error_check(err):
                self.diewith(file, err)
                return False
            for c in file.data:
                err = fpo.p3fs_putc(c)
                if not p3fs_error_check(err):
                    self.diewith(file, err)
                    return False

            err = fpo.p3fs_close()
            if not p3fs_error_check(err):
                self.diewith(file, err)
                return False

        if not cpmonly:
            err = self.gl_fs.p3fs_dossync(format=dsk_format, dosonly=dosonly)
            if not p3fs_error_check(err):
                self.report_error(
                    f"Cannot do DOS sync on {dsk_file}: {p3fs_strerror(err)}\n"
                )
                return False

        err = self.gl_fs.p3fs_umount()
        if not p3fs_error_check(err):
            self.report_error(f"Cannot close {dsk_file}: {p3fs_strerror(err)}\n")
            return False

        return True

    def report(self, s):
        print(f"{s}\n", end="")
        sys.stdout.flush()

    def report_error(self, s):
        sys.stderr.write(f"{s}\n")
        sys.stderr.flush()

    def diewith(self, file, err):
        self.report_error(
            "Cannot write {0:<8.8s}.{1:<3.3s}: {2}\n".format(
                file.fcbname[0:8], file.fcbname[8:11], p3fs_strerror(err)
            )
        )
        if self.gl_fs is not None:
            self.gl_fs.p3fs_umount()

################################################################################

import argparse


def mlp3fs_cli():
    parser = argparse.ArgumentParser(description="MK3PFS +3Dos disk creator")
    parser.add_argument(
        "-720",
        "--size-720",
        action="store_true",
        default=False,
        help="Write a 720k image. If not set, it will write a 180k image",
    )
    parser.add_argument(
        "-cpm",
        "--cpm-only",
        action="store_true",
        default=False,
        help="Write a disc only usable by +3DOS",
    )
    parser.add_argument(
        "-dos",
        "--dos-only",
        action="store_true",
        default=False,
        help="Write a disc only usable by PCDOS",
    )
    parser.add_argument(
        "-s",
        "--no-stamps",
        action="store_false",
        default=True,
        help="Do not include file date stamps",
    )
    parser.add_argument(
        "-l", "--label", default="", help="Set disk label (default=none)"
    )
    parser.add_argument("dskfile", help="Disk image file path")
    parser.add_argument("file", help="File to add to disk", nargs="+")
    args = parser.parse_args()

    p3fs = Plus3DosFilesystem()

    for filepath in args.file:
        p3fs.add_file_path(filepath)

    label = None if args.label == "" else args.label

    if not p3fs.make_plus3_disk(
        dsk_file=args.dskfile,
        label=label,
        size720=args.size_720,
        timestamp=args.no_stamps,
        cpmonly=args.cpm_only,
        dosonly=args.dos_only,
    ):
        sys.exit(1)


# def test():
#     fcbname = bytearray(12)
#     p3fs_83name("ABCDEDFG.BIN", fcbname)
#     print(fcbname)
#     p3fs_83name("SCRIPT.BIN", fcbname)
#     print(fcbname)
#     p3fs_83name("CYD.BIN", fcbname)
#     print(fcbname)
#     p3fs_83name("DISC", fcbname)
#     print(fcbname)

#     p3fs = Plus3DosFilesystem()
#     if not p3fs.make_plus3_disk(
#         dsk_file="test1_A.dsk",
#         label="THIS_IS_A_TEST",
#         size720=False,
#         timestamp=True,
#         cpmonly=True,
#         dosonly=False,
#     ):
#         print("ERROR")

#     p3fs = Plus3DosFilesystem()
#     if not p3fs.make_plus3_disk(
#         dsk_file="test2_A.dsk",
#         label="THIS_IS_A_TEST",
#         size720=True,
#         timestamp=True,
#         cpmonly=True,
#         dosonly=False,
#     ):
#         print("ERROR")


if __name__ == "__main__":
    mlp3fs_cli()
    # test()
