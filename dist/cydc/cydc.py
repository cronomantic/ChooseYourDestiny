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
import re
import copy

from cydc_txt_compress import CydcTextCompressor, NUM_TOKENS
from cydc_parser import CydcParser
from cydc_codegen import CydcCodegen
from cydc_font import CydcFont

from cyd import (
    get_asm_plus3_size,
    get_asm_48_size,
    get_asm_128_size,
    do_asm_128,
    do_asm_48,
    do_asm_plus3,
)
from cydc_utils import make_plus3_dsk


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


def pause_value(value):
    val = (int(value))
    val *= 50
    if (val < 0) or (val >= (64 * 1024)):
        raise argparse.ArgumentTypeError("%s is an invalid value" % value)
    return val


def main():
    """Main function"""

    version = "1.0.0"
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
        "-n",
        "--name",
        metavar=_("NAME"),
        help=_("Name of the output file"),
    )

    #####################################
    arg_parser.add_argument(
        "-csc",
        "--csc-images-path",
        type=dir_path,
        help=_("path to the directory with the CSC compressed Spectrum screens"),
    )
    arg_parser.add_argument(
        "-pt3",
        "--pt3-tracks-path",
        type=dir_path,
        help=_("path to the directory with the PT3 tracks"),
    )
    arg_parser.add_argument(
        "-sfx",
        "--sfx-asm-file",
        type=file_path,
        help=_("path to the asm file generated by beepfx"),
    )
    arg_parser.add_argument(
        "-scr",
        "--load-scr-file",
        type=file_path,
        help=_("path to the SCR file used as Loading screen"),
    )
    ###
    arg_parser.add_argument(
        "-v", "--verbose", action="store_true", help=_("show additional information")
    )
    arg_parser.add_argument(
        "-trim",
        "--trim-interpreter",
        action="store_true",
        help=_("exclude code of unused commands"),
    )
    arg_parser.add_argument(
        "-code",
        "--show-bytecode",
        action="store_true",
        help=_("show the generated bytecode"),
    )
    arg_parser.add_argument(
        "-pause",
        "--pause-after-load",
        type=pause_value,
        help=_(
            "Number of seconds of pause after finishing the loading process, can be aborted with any keypress."
        ),
    )
    arg_parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=program,
        help=_("show program's version number and exit"),
    )
    #####################################################
    arg_parser.add_argument(
        "model",
        default="plus3",
        choices=["48k", "128k", "plus3"],
        help=_("Model of spectrum to target"),
        type=str.lower,
    )
    arg_parser.add_argument(
        "input",
        metavar=_("input.cyd"),
        type=file_path,
        help=_("input filename, the script for the adventure"),
    )
    arg_parser.add_argument(
        "sjasmplus_path",
        default="sjasmplus",
        metavar=_("SJASMPLUS_PATH"),
        type=file_path,
        help=_("path to sjasmplus executable"),
    )
    # arg_parser.add_argument(
    #     "zx0_path",
    #     default="zx0",
    #     metavar=_("ZX0_PATH"),
    #     type=file_path,
    #     help=_("path to zx0 executable"),
    # )
    arg_parser.add_argument(
        "mkp3fs_path",
        default="mkp3fs",
        type=file_path,
        metavar=_("MKP3FS_PATH"),
        help=_("path to mkp3fs executable"),
    )
    arg_parser.add_argument(
        "output_path",
        default=".",
        type=dir_path,
        metavar=_("OUTPUT_PATH"),
        help=_("Output path to files"),
    )

    try:
        args = arg_parser.parse_args()
    except FileNotFoundError as f1:
        sys.exit(_("ERROR: File not found:") + f"{f1}")
    except NotADirectoryError as f2:
        sys.exit(_("ERROR: Not a valid path:") + f"{f2}")

    verbose = args.verbose
    model = args.model
    output_name = args.name

    if sys.version_info[0] < 3:  # Python 2
        sys.exit(_("ERROR: Invalid python version"))

    if not os.path.isfile(args.input):
        sys.exit(_("ERROR: Path to input file does not exist."))

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    if output_name is None:
        output_name = os.path.splitext(os.path.basename(args.input))
        output_name = output_name[0]

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
                if set(c.keys()) != set(["Character", "Width", "Id"]):
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
                i = c["Id"]
                if not isinstance(w, int):
                    sys.exit(
                        _("ERROR: The charset import file has not a valid format.")
                    )
                if w < 0 or w > 255:
                    sys.exit(
                        _("ERROR: The charset import file has not a valid format.")
                    )
        font.loadCharset(jsonCharset)

    ######################################################################

    if verbose:
        print(_("Parsing code..."))

    parser = CydcParser()
    parser.build()
    code = parser.parse(text)
    if verbose:
        print(_("Symbols:"))
        parser.print_symbols()
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

    if args.min_length > args.max_length:
        sys.exit(_("ERROR: min-length can't be greather than max-length."))

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
        print(_("Reading external files..."))

    sfx = None
    if args.sfx_asm_file is not None:
        with open(args.sfx_asm_file, "r", encoding="utf-8") as f:
            sfx = f.read()
            sfx = re.sub(r"org\s+\d{1,6}", "", sfx, flags=re.IGNORECASE)

    blocks = []
    if args.csc_images_path is not None:
        for i in range(256):
            fpath = os.path.join(args.csc_images_path, f"{i:03d}.CSC")
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    b = list(f.read())
                    t = ("SCR", i, len(b), b, fpath)
                    blocks.append(t)
                    if (model == "plus3") and (len(b) > (7 * 1024)):
                        sys.exit(_("ERROR: Invalid SCR file, it is too big"))

    has_tracks = False
    if args.pt3_tracks_path is not None and model != "48k":
        for i in range(256):
            fpath = os.path.join(args.pt3_tracks_path, f"{i:03d}.PT3")
            if os.path.isfile(fpath):
                with open(fpath, "rb") as f:
                    b = list(f.read())
                    t = ("TRK", i, len(b), b, fpath)
                    blocks.append(t)
                    has_tracks = True
                    if (model == "plus3") and (len(b) > (8 * 1024)):
                        sys.exit(_("ERROR: Invalid PT3 file, it is too big"))

    loading_scr = None
    if args.load_scr_file is not None:
        if os.path.isfile(args.load_scr_file):
            with open(args.load_scr_file, "rb") as f:
                loading_scr = list(f.read())
            if len(loading_scr) != 32 * (192 + 24):
                sys.exit(_("ERROR: Invalid SCR file"))
        else:
            sys.exit(_("ERROR: Can't open load SCR file."))
    ######################################################################
    codegen = CydcCodegen(gettext)
    chunks = []
    l_tokens = []
    l_chars = []
    l_charw = []

    # TODO: experimental for now...
    if args.trim_interpreter:
        unused_opcodes = codegen.get_unused_opcodes(code)
    else:
        unused_opcodes = set()

    if font is None:
        font = CydcFont()
    l_chars = font.font_chars
    l_charw = font.font_sizes
    l_tokens = tokenBytes

    ######################################################################

    asm_size = 0
    try:
        if model == "plus3":
            if verbose:
                print(_("Assembling interpreter for size..."))
            asm_size = get_asm_plus3_size(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=verbose,
                sfx_asm=sfx,
                tokens=l_tokens,
                chars=l_chars,
                charw=l_charw,
                has_tracks=has_tracks,
                unused_opcodes=unused_opcodes,
                pause_start_value=args.pause_after_load,
            )
        elif model == "128k":
            if verbose:
                print(_("Assembling interpreter for size..."))
            asm_size = get_asm_128_size(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=verbose,
                sfx_asm=sfx,
                tokens=l_tokens,
                chars=l_chars,
                charw=l_charw,
                has_tracks=has_tracks,
                unused_opcodes=unused_opcodes,
                pause_start_value=args.pause_after_load,
            )
        else:
            if verbose:
                print(_("Assembling interpreter for size..."))
            asm_size = get_asm_48_size(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=verbose,
                sfx_asm=sfx,
                tokens=l_tokens,
                chars=l_chars,
                charw=l_charw,
                unused_opcodes=unused_opcodes,
                pause_start_value=args.pause_after_load,
            )

    except ValueError as e1:
        sys.exit(_("ERROR: Error assembling interpreter."), e1)
    except OSError as e2:
        sys.exit(_("ERROR: Error assembling interpreter."), e2)
        
    if verbose:
        print(f"Interpreter size: {asm_size}")

    if model == "48k" and (asm_size > 32 * 1024):
        sys.exit(_("ERROR: Interpreter too big!") + f" {asm_size} bytes.")
    elif model != "48k" and asm_size > 16 * 1024:
        sys.exit(_("ERROR: Interpreter too big!") + f" {asm_size} bytes.")

    ######################################################################

    if model == "plus3" and verbose:
        print(_("Memory organization for disk version..."))
    elif verbose:
        print(_("Memory organization for tape version..."))

    # We do this to get an rounded-up approximation of the number of blocks
    codegen.set_bank_offset_list([0xC000])
    codegen.set_bank_size_list([16 * 1024])
    chunks = codegen.generate_code(
        code=code, slice_text=args.slice_texts, show_debug=False
    )

    # To calculate the offset
    if model == "plus3":
        num_blocks = len(chunks)
    else:
        num_blocks = len(blocks) + len(chunks)
    bank0_offset = (5 * num_blocks) + asm_size + 0x8000
    bank0_size_available = (16 * 1024) + (0xC000 - bank0_offset)

    # generate block again
    codegen.set_bank_offset_list([bank0_offset, 0xC000])
    codegen.set_bank_size_list([bank0_size_available, 16 * 1024])
    chunks = codegen.generate_code(
        code=code, slice_text=args.slice_texts, show_debug=args.show_bytecode
    )

    if model == "128k":
        spectrum_banks = [0, 1, 3, 4, 6, 7]
    elif model == "plus3":
        spectrum_banks = [0, 1, 3, 4]
    else:
        spectrum_banks = [0]

    tmp_blocks = []
    tmp_index = []
    tmp_available_bank_size = []
    # Make sure that the TXT blocks are first!
    for i, chunk in enumerate(chunks):
        # tmp_blocks.insert(i, ("TXT", i, len(chunk), chunk, ""))
        if i == 0:
            offset = bank0_offset
            size = bank0_size_available
        else:
            offset = 0xC000
            size = 16 * 1024
        if size < len(chunk):
            sys.exit(_("ERROR: Block too big."))
        tmp_blocks.insert(i, chunk)
        tmp_index.insert(i, (0, i, i, offset))
        tmp_available_bank_size.insert(i, size - len(chunk))

    max_banks = len(spectrum_banks)
    num_banks = len(tmp_blocks)

    if num_banks > max_banks:
        sys.exit(_("ERROR: Not enough memory available"))

    fits = False
    while not fits:
        index = copy.deepcopy(tmp_index)
        available_banks = copy.deepcopy(tmp_blocks)
        available_banks.extend([[] for x in range(num_banks - len(tmp_blocks))])
        available_bank_size = copy.deepcopy(tmp_available_bank_size)
        available_bank_size.extend(
            [16 * 1024 for x in range(num_banks - len(tmp_available_bank_size))]
        )
        fits = True
        if model != "plus3":
            for i, block in enumerate(blocks):
                btype, bidx, bsize, bdata, bpath = block
                best_fit_index = -1
                min_leftover = sys.maxsize
                for j, b in enumerate(available_banks):
                    available = available_bank_size[j]
                    if available >= bsize:
                        leftover = available - bsize
                        if min_leftover > leftover:
                            min_leftover = leftover
                            best_fit_index = j
                if best_fit_index != -1:
                    offset = len(available_banks[best_fit_index])
                    if best_fit_index == 0:
                        offset += bank0_offset
                    else:
                        offset += 0xC000
                    if btype == "TRK":
                        b = 2
                    elif btype == "SCR":
                        b = 1
                    else:  # btype == "TXT"
                        sys.exit(_("ERROR: Unexpected data"))
                    index.append((b, bidx, best_fit_index, offset))
                    available_banks[best_fit_index] += bdata
                    available_bank_size[best_fit_index] -= bsize
                else:
                    del available_bank_size
                    del available_banks
                    del index
                    num_banks += 1
                    fits = False
                    break
            if num_banks > max_banks:
                sys.exit(_("ERROR: Not enough memory available"))

    index = [
        (b, bidx, spectrum_banks[bank], offset) for (b, bidx, bank, offset) in index
    ]

    print("\nRAM usage:\n-----------------")
    total_bytes = 0
    for i, v in enumerate(available_banks):
        total_bytes += len(v)
        print(
            f"Bank [{spectrum_banks[i]}]: {len(v)} Bytes / Free: {available_bank_size[i]} bytes."
        )

    available_bytes = 0
    for v in spectrum_banks:
        if v == 0:
            available_bytes += bank0_size_available
        else:
            available_bytes += 16 * 1024

    print("\nSummary:")
    print(f"- {available_bytes} bytes available.")
    print(f"- {total_bytes} bytes used.")
    print(f"- {available_bytes-total_bytes} bytes free.")

    if verbose:
        print("\nIndex:\n-----------------")
        for i, v in enumerate(index):
            print(f"Type={v[0]} Index={v[1]} Bank={v[2]} Start Address=${v[3]:04X}")
        print("\n")
    try:
        if model == "128k":
            if verbose:
                print(_("Assembling Spectrum 128k TAP..."))
            output_name = output_name[:10]
            do_asm_128(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=verbose,
                tap_name=output_name,
                index=index,
                blocks=available_banks,
                banks=spectrum_banks,
                size_interpreter=asm_size,
                bank0_offset=bank0_offset,
                sfx_asm=sfx,
                tokens=l_tokens,
                chars=l_chars,
                charw=l_charw,
                loading_scr=loading_scr,
                has_tracks=has_tracks,
                unused_opcodes=unused_opcodes,
                pause_start_value=args.pause_after_load,
                name=output_name,
            )
        elif model == "plus3":
            if verbose:
                print(_("Assembling Spectrum PLUS3 binary files..."))
            output_name = output_name[:8]
            do_asm_plus3(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=verbose,
                dsk_name=output_name,
                index=index,
                blocks=available_banks,
                banks=spectrum_banks,
                size_interpreter=asm_size,
                bank0_offset=bank0_offset,
                sfx_asm=sfx,
                tokens=l_tokens,
                chars=l_chars,
                charw=l_charw,
                loading_scr=loading_scr,
                has_tracks=has_tracks,
                unused_opcodes=unused_opcodes,
                pause_start_value=args.pause_after_load,
                name=output_name,
            )
        else:
            if verbose:
                print(_("Assembling Spectrum 48k TAP..."))
            output_name = output_name[:10]
            do_asm_48(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=verbose,
                tap_name=output_name,
                index=index,
                blocks=available_banks,
                banks=spectrum_banks,
                size_interpreter=asm_size,
                bank0_offset=bank0_offset,
                sfx_asm=sfx,
                tokens=l_tokens,
                chars=l_chars,
                charw=l_charw,
                loading_scr=loading_scr,
                unused_opcodes=unused_opcodes,
                pause_start_value=args.pause_after_load,
                name=output_name,
            )
    except ValueError as e1:
        sys.exit(_("ERROR: Error assembling source."), e1)
    except OSError as e2:
        sys.exit(_("ERROR: Error assembling source."), e2)

    ######################################################################
    if model == "plus3":
        if verbose:
            print(_("Assembling PLUS3 disk..."))
        files = [
            os.path.join(args.output_path, "DISK"),
            os.path.join(args.output_path, f"{output_name}.BIN"),
        ]
        for b in blocks:
            btype = b[0]
            bpath = b[4]
            if btype == "SCR" or btype == "TRK":
                files.append(bpath)
        try:
            make_plus3_dsk(
                args.mkp3fs_path,
                os.path.join(args.output_path, output_name + ".DSK"),
                output_name,
                files,
            )
        except OSError:
            sys.exit("ERROR: could not create DSK file")

    ######################################################################
    sys.exit(0)


if __name__ == "__main__":
    main()
