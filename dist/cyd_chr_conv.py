#!/usr/bin/python3
#
# Choose Your Destiny.
#
# Copyright (C) 2024 Sergio Chico <cronomantic@gmail.com>
#
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
# 
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#  

from __future__ import print_function
from operator import itemgetter, attrgetter

import sys
import os
import gettext
import argparse

sys.path.append(os.path.join(os.path.dirname(__file__), "cydc"))

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
    version = "0.9.0"
    program = "Choose Your Destiny Font Conversion " + version
    exec = "cyd_font_conv"

    gettext.bindtextdomain(
        exec, os.path.join(os.path.abspath(os.path.dirname(__file__)), "locale")
    )
    gettext.textdomain(exec)
    _ = gettext.gettext

    if sys.version_info[0] < 3:  # Python 2
        sys.exit(_("ERROR: Invalid python version"))

    arg_parser = argparse.ArgumentParser(sys.argv[0], description=program)

    arg_parser.add_argument(
        "-w",
        "--width_low",
        metavar=_("WIDTH_LOW"),
        type=check_width,
        default=6,
        help=_("Width of the characters of the lower character set"),
    )

    arg_parser.add_argument(
        "-W",
        "--width_high",
        metavar=_("WIDTH_HIGH"),
        type=check_width,
        default=4,
        help=_("Width of the characters of the upper character set"),
    )

    arg_parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=program,
        help=_("show program's version number and exit"),
    )

    arg_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help=_("Verbose mode"),
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

    verbose = args.verbose

    if not os.path.isfile(args.input):
        sys.exit(_("ERROR: Path to input file does not exist."))

    font_file_chars = None
    with open(args.input, "rb") as f:
        font_file_chars = list(f.read())

    if (len(font_file_chars) % 8) != 0:
        sys.exit(_("ERROR: Invalid input file size"))

    num_chars = int(len(font_file_chars) / 8)

    if verbose:
        print(f"Num. chars {num_chars}")

    if num_chars == 0 or num_chars > 256:
        sys.exit(_("ERROR: Invalid input file size"))

    valid_extensions = {".chr", ".ch8", ".ch6", "ch4"}
    extension = os.path.splitext(os.path.basename(args.input))[1].lower()

    if extension not in valid_extensions:
        sys.exit(_("ERROR: Invalid input file extension"))

    chars_width_upper = args.width_high
    chars_width_lower = args.width_low

    if verbose:
        print(f"Chars. width upper set {chars_width_upper}")
        print(f"Chars. width lower set {chars_width_lower}")

    font_file_widths = [chars_width_lower for x in range(num_chars)]
    if num_chars >= 128:
        for x in range(128, num_chars):
            font_file_widths[x] = chars_width_upper

    if verbose:
        print(f"Character set with {len(font_file_widths)} characters")

    if len(font_file_chars) < len(font.default_font) and len(font_file_widths) < len(
        font.default_font_sizes
    ):
        font_file_chars += font.default_font[len(font_file_chars) :]
        font_file_widths += font.default_font_sizes[len(font_file_widths) :]

    for i in range(127, 144):
        if font_file_widths[i] != 8:
            font_file_widths[i] = 8

    font = CydcFont(font_chars=font_file_chars, font_sizes=font_file_widths)

    try:
        with open(args.output, "w") as f:
            f.write(font.getJson())
    except OSError as err:
        sys.exit(_("ERROR: creating output file ") + f"{err}")

    sys.exit(0)


if __name__ == "__main__":
    main()
