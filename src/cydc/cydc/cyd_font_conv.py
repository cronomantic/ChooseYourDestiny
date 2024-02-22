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

from __future__ import print_function
from operator import itemgetter, attrgetter

import sys
import os
import gettext
import argparse

from cydc_font import CydcFont


def dir_path(string):
    """_summary_

    Args:
        string (_type_): _description_

    Raises:
        NotADirectoryError: _description_

    Returns:
        _type_: _description_
    """
    if os.path.isdir(string):
        return string
    else:
        raise NotADirectoryError(string)


def file_path(string):
    """_summary_

    Args:
        string (_type_): _description_

    Raises:
        FileNotFoundError: _description_

    Returns:
        _type_: _description_
    """
    if os.path.isfile(string):
        return string
    else:
        raise FileNotFoundError(string)


def check_width(value):
    width = int(value)
    if width <= 0 or width > 8:
        raise argparse.ArgumentTypeError("%s is an invalid value" % value)
    return width


def main():
    version = "0.1.0"
    program = "Choose Your Destiny Font Conversion " + version
    exec = "cyd_font_conv"

    gettext.bindtextdomain(
        exec, os.path.join(os.path.abspath(os.path.dirname(__file__)), "locale")
    )
    gettext.textdomain(exec)
    _ = gettext.gettext

    arg_parser = argparse.ArgumentParser(sys.argv[0], description=program)

    arg_parser.add_argument(
        "-w",
        "--width",
        metavar=_("WIDTH"),
        type=check_width,
        help=_("Width of the characters"),
    )

    arg_parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=program,
        help=_("show program's version number and exit"),
    )

    arg_parser.add_argument(
        "input",
        metavar=_("input.chr"),
        type=file_path,
        help=_("input filename, supports .chr, .ch8, .ch6 and .ch4 extensions"),
    )

    arg_parser.add_argument(
        "output",
        default="charset.json",
        metavar=_("output.json"),
        help=_("output JSON font file for CYDC"),
    )

    try:
        args = arg_parser.parse_args()
    except FileNotFoundError as f1:
        sys.exit(_("ERROR: File not found:") + f"{f1}")
    except NotADirectoryError as f2:
        sys.exit(_("ERROR: Not a valid path:") + f"{f2}")

    font = CydcFont()

    if sys.version_info[0] < 3:  # Python 2
        sys.exit(_("ERROR: Invalid python version"))

    if not os.path.isfile(args.input):
        sys.exit(_("ERROR: Path to input file does not exist."))

    font_file_chars = None
    with open(args.input, "rb") as f:
        font_file_chars = list(f.read())

    if (len(font_file_chars) % 8) != 0:
        sys.exit(_("ERROR: Invalid input file size"))

    num_chars = int(len(font_file_chars) / 8)

    if num_chars == 0 or num_chars > 256:
        sys.exit(_("ERROR: Invalid input file size"))

    valid_extensions = {".chr": 8, ".ch8": 8, ".ch6": 6, "ch4": 4}
    extension = os.path.splitext(os.path.basename(args.input))[1].lower()

    if extension not in valid_extensions.keys():
        sys.exit(_("ERROR: Invalid input file extension"))

    if args.width is None:
        chars_width = valid_extensions[extension]
    else:
        chars_width = args.width

    font_file_widths = [chars_width for x in range(num_chars)]

    if len(font_file_chars) < len(font.default_font) and len(font_file_widths) < len(
        font.default_font_sizes
    ):
        font_file_chars += font.default_font[len(font_file_chars) :]
        font_file_widths += font.default_font_sizes[len(font_file_widths) :]

    font.font = font_file_chars
    font.font_sizes = font_file_widths

    try:
        with open(args.output, "w") as f:
            f.write(font.getJson())
    except OSError as err:
        sys.exit(_("ERROR: creating output file ") + f"{err}")

    sys.exit(0)


if __name__ == "__main__":
    main()
