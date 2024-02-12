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
import json
from cydc_txt_compress import CydcTextCompressor, NUM_TOKENS
from cydc_parser import CydcParser
from cydc_codegen import CydcCodegen
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

def main():
    """Main function"""

    version = "0.0.3"
    program = "Choose Your Destiny Compiler " + version
    exec = "cydc"

    gettext.bindtextdomain(
        exec, os.path.join(os.path.abspath(os.path.dirname(__file__)), "locale")
    )
    gettext.textdomain(exec)
    _ = gettext.gettext

    arg_parser = argparse.ArgumentParser(sys.argv[0], description=program)
    arg_parser.add_argument(
        "-l",
        "--min-length",
        metavar=_("MIN_LENGTH"),
        type=int,
        help=_("minimum abbreviation length (default: %(default)d)"),
        default=3,
    )
    arg_parser.add_argument(
        "-L",
        "--max-length",
        metavar=_("MAX_LENGTH"),
        type=int,
        help=_("maximum abbreviation length (default: %(default)d)"),
        default=30,
    )
    arg_parser.add_argument(
        "-s",
        "--superset-limit",
        metavar=_("SUPERSET_LIMIT"),
        type=int,
        help=_("limit for the superset search heuristic (default: %(default)d)"),
        default=100,
    )
    # token_group = arg_parser.add_mutually_exclusive_group()
    arg_parser.add_argument(
        "-T",
        "--export-tokens-file",
        metavar=_("EXPORT-TOKENS_FILE"),
        help=_("file to export the found tokens"),
    )
    arg_parser.add_argument(
        "-t",
        "--import-tokens-file",
        metavar=_("IMPORT-TOKENS-FILE"),
        help=_("file with the tokens to use"),
    )
    ###
    arg_parser.add_argument(
        "-C",
        "--export-charset",
        metavar=_("EXPORT-CHARSET"),
        help=_("file to export the current character set"),
    )
    arg_parser.add_argument(
        "-c",
        "--import-charset",
        metavar=_("IMPORT-CHARSET"),
        help=_("file with the character set to use"),
    )
    ###
    arg_parser.add_argument(
        "-S",
        "--slice-texts",
        action="store_true",
        default=False,
        help=_("The text string will be sliced between two banks"),
    )
    arg_parser.add_argument(
        "-x",
        "--export-json",
        action="store_true",
        help=_("The destination file is a JSON instead of a binary file"),
    )
    ###
    arg_parser.add_argument(
        "-v", "--verbose", action="store_true", help=_("show additional information")
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
        metavar=_("input.txt"),
        type=file_path,
        help=_("input filename, the script for the adventure"),
    )

    arg_parser.add_argument(
        "output",
        metavar=_("SCRIPT.DAT"),
        help=_("output filename, file with the compiled script if option -x is not enabled"),
    )

    args = arg_parser.parse_args()

    verbose = args.verbose

    if sys.version_info[0] < 3:  # Python 2
        sys.exit(_("ERROR: Invalid python version"))

    if not os.path.isfile(args.input):
        sys.exit(_("ERROR: Path to input file does not exist."))

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    ######################################################################
    tokens = None
    if args.import_tokens_file is not None:
        input_token_file = args.import_tokens_file
        if not os.path.isfile(input_token_file):
            sys.exit(_("Path to token file does not exist."))
        with open(input_token_file, "r", encoding="utf-8") as fti:
            try:
                jsonToken = json.load(fti)
            except json.JSONDecodeError:
                sys.exit(_("ERROR: The token import file has not a valid format."))
            if not isinstance(jsonToken, list):
                sys.exit(_("ERROR: The token import file has not a valid format."))
            if len(jsonToken) > NUM_TOKENS:
                sys.exit(
                    _(
                        "ERROR: Number of tokens must be equal o less to %(NUM_TOKENS)d."
                        % {"NUM_TOKENS": NUM_TOKENS}
                    )
                )
            for t in jsonToken:
                if not isinstance(t, str):
                    sys.exit(_("ERROR: The token import file has not a valid format."))
            tokens = jsonToken

    ######################################################################
    # Importing Font
    font = CydcFont()
    if args.import_charset is not None:
        input_charset_file = args.import_charset
        jsonCharset = None
        if not os.path.isfile(input_charset_file):
            sys.exit(_("Path to charset file does not exist."))
        with open(input_charset_file, "r", encoding="utf-8") as fci:
            try:
                jsonCharset = json.load(fci)
            except json.JSONDecodeError:
                sys.exit(_("ERROR: The charset import file has not a valid format."))
            if not isinstance(jsonCharset, list):
                sys.exit(_("ERROR: The charset import file has not a valid format."))
            if len(jsonCharset) > 256:
                sys.exit(_("ERROR: Too many characters!"))
            for c in jsonCharset:
                if not isinstance(c, dict):
                    sys.exit(
                        _("ERROR: The charset import file has not a valid format.")
                    )
                if set(c.keys()) != set(["Character", "Width"]):
                    sys.exit(
                        _("ERROR: The charset import file has not a valid format.")
                    )
                pxl = c["Character"]
                if len(pxl) != 8:
                    sys.exit(
                        _("ERROR: The charset import file has not a valid format.")
                    )
                for l in pxl:
                    if not isinstance(l, int):
                        sys.exit(
                            _("ERROR: The charset import file has not a valid format.")
                        )
                    if l < 0 or l > 255:
                        sys.exit(
                            _("ERROR: The charset import file has not a valid format.")
                        )
                w = c["Width"]
                if not isinstance(w, int):
                    sys.exit(
                        _("ERROR: The charset import file has not a valid format.")
                    )
                if w < 1 or w > 8:
                    sys.exit(
                        _("ERROR: The charset import file has not a valid format.")
                    )
        font.loadCharset(jsonCharset)

    ######################################################################
    if verbose:
        print(_("Parsing code..."))

    parser = CydcParser()
    parser.build()
    # parser.lexer.test(text)
    code = parser.parse(text)
    if len(parser.errors) > 0:
        for e in parser.errors:
            print("ERROR:" + e)
        sys.exit(1)

    ######################################################################

    if verbose:
        print(_("Compressing texts..."))

    # Recollecting strings for tokenization
    strings = []
    positions = []
    for pos, value in enumerate(code):
        opcode = value[0]
        if opcode == "TEXT":
            text = value[1]
            strings.append(text)
            positions.append(pos)

    txtComp = CydcTextCompressor(gettext, args.superset_limit, verbose)
    (textBytes, tokenBytes, tokens) = txtComp.compress(
        strings, args.min_length, args.max_length, tokens
    )

    # Exporting tokens
    if args.export_tokens_file is not None:
        output_token_file = args.export_tokens_file
        with open(output_token_file, "w", encoding="utf-8") as fto:
            fto.write(json.dumps(tokens))

    # Set text to compressed bytes format
    for posT, posC in enumerate(positions):
        code[posC] = ("TEXT", textBytes[posT])

    del txtComp
    ######################################################################

    # Exporting current font
    if args.export_charset is not None:
        output_charset_file = args.export_charset
        with open(output_charset_file, "w", encoding="utf-8") as fco:
            fco.write(font.getJson())

    ######################################################################

    if verbose:
        print(_("Generating final bytecode..."))

    codegen = CydcCodegen(gettext)

    if args.export_json:
        code_exp = codegen.generate_exportable_code(
            code=code, tokens=tokenBytes, font=font, slice_text=args.slice_texts
        )
        try:
            with open(args.output, "w", encoding="utf-8") as fe:
                fe.write(json.dumps(code_exp))
        except OSError:
            sys.exit(_("ERROR: Can't write destination file."))
    else:
        code_out = codegen.generate_code(
            code=code, tokens=tokenBytes, font=font, slice_text=args.slice_texts
        )
        for p, i in enumerate(code_out):
            if i > 255:
                sys.exit(_(f"ERROR: Invalid character.{i} - {chr(i)} at {p} byte."))

        try:
            with open(args.output, "wb") as f:
                fileBytes = bytes(code_out)
                f.write(fileBytes)
        except OSError:
            sys.exit(_("ERROR: Can't write destination file."))

    sys.exit(0)
    ######################################################################

if __name__ == '__main__':
    main()