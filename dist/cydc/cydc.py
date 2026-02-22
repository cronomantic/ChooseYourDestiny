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

from __future__ import print_function
from operator import itemgetter, attrgetter

import sys, os, gettext, argparse, json, re, copy, math

from cydc_txt_compress import CydcTextCompressor, NUM_TOKENS
from cydc_parser import CydcParser
from cydc_codegen import CydcCodegen
from cydc_font import CydcFont
from cydc_music import compress_track_data, create_wyz_player_bank, add_size_header
from cydc_preprocessor import CydcPreprocessor, PreprocessorError

from cyd import *
from cydc_utils import *

try:
    import asciibars

    abarAvailable = True
except ImportError:
    abarAvailable = False


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
    val = int(value)
    val *= 50
    if (val < 0) or (val >= (64 * 1024)):
        raise argparse.ArgumentTypeError("%s is an invalid value" % value)
    return val


def main():
    """Main function"""

    if sys.version_info[0] < 3:  # Python 2
        sys.exit(_("ERROR: Invalid python version"))

    version = "1.0.6"
    program = "Choose Your Destiny Compiler " + version
    exec = "cydc"

    gettext.bindtextdomain(
        exec, os.path.join(os.path.abspath(os.path.dirname(__file__)), "locale")
    )
    gettext.textdomain(exec)
    _ = gettext.gettext

    timer = Timer()
    tmp_timer = Timer()

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
    arg_parser.add_argument(
        "-720",
        "--disk-720",
        action="store_true",
        default=False,
        help=_("Use 720 Kb disk images"),
    )
    arg_parser.add_argument(
        "-il",
        "--image-lines",
        metavar=_("NUM_IMAGE_LINES"),
        type=int,
        help=_("Number of lines of the image to use (default: %(default)d)"),
        default=192,
    )
    #####################################
    arg_parser.add_argument(
        "-wyz",
        "--use-wyz-tracker",
        action="store_true",
        default=False,
        help=_("Use WYZ tracker instead of Vortex tracker"),
    )
    arg_parser.add_argument(
        "-img",
        "--images-path",
        type=dir_path,
        help=_("path to the directory with the Spectrum screens"),
    )
    arg_parser.add_argument(
        "-trk",
        "--tracks-path",
        type=dir_path,
        help=_("path to the directory with the music tracks"),
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
        "-v",
        "--verbose",
        action="count",
        default=0,
        help=_("show additional information (-v for level 1, -vv for level 2, etc.)"),
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
        "--no-strict-colons",
        action="store_true",
        default=False,
        help=_("allow statements without colon separator (backwards compatibility mode)"),
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
    #     "mkp3fs_path",
    #     default="mkp3fs",
    #     type=file_path,
    #     metavar=_("MKP3FS_PATH"),
    #     help=_("path to mkp3fs executable"),
    # )
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

    verbose = 3 if args.verbose > 3 else args.verbose
    model = args.model
    output_name = args.name

    if model != "plus3" and args.disk_720:
        sys.exit(_("ERROR: Invalid parameter this model."))

    if not os.path.isfile(args.input):
        sys.exit(_("ERROR: Path to input file does not exist."))

    # Preprocess the input file to handle #include directives
    if verbose > 0:
        print(_("Preprocessing includes..."))
    tmp_timer.reset()
    
    try:
        preprocessor = CydcPreprocessor(
            max_depth=20, 
            base_path=os.path.dirname(os.path.abspath(args.input))
        )
        text = preprocessor.preprocess(args.input)
        
        if verbose >= 1:
            included_count = len(preprocessor.included_files) - 1  # -1 for main file
            if included_count > 0:
                print(_(f"Preprocessed {included_count} include file(s) in {tmp_timer}"))
            else:
                print(_(f"Preprocessing completed in {tmp_timer}"))
    except PreprocessorError as e:
        sys.exit(_("ERROR: ") + str(e))

    if output_name is None:
        output_name = os.path.splitext(os.path.basename(args.input))
        output_name = output_name[0]

    if verbose >= 1:
        print(_(f"Parameters parsed in {tmp_timer}"))

    ######################################################################

    tokens = None
    if args.import_tokens_file is not None:
        tmp_timer.reset()
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
        if verbose >= 1:
            print(_(f"Tokens imported in {tmp_timer}"))

    ######################################################################
    # Importing Font
    font = CydcFont()
    if args.import_charset is not None:
        tmp_timer.reset()
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
        if verbose >= 1:
            print(_(f"Character set loaded in {tmp_timer}"))

    ######################################################################

    if verbose > 0:
        print(_("Parsing code..."))

    tmp_timer.reset()
    parser = CydcParser(gettext, strict_colon_mode=not args.no_strict_colons)
    parser.build()
    code = parser.parse(input=text, verbose=(verbose >= 3))
    if verbose >= 2:
        print(_("Symbols:"))
        parser.print_symbols()
    if len(parser.errors) > 0:
        for e in parser.errors:
            print("ERROR:" + e)
        sys.exit(1)
    print(_(f"Code parsing completed ({tmp_timer})"))

    ######################################################################

    if verbose > 0:
        print(_("Compressing texts..."))
    tmp_timer.reset()

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

    txtComp = CydcTextCompressor(gettext, args.superset_limit, verbose=(verbose >= 1))
    (textBytes, tokenBytes, tokens) = txtComp.compress(
        strings, args.min_length, args.max_length, tokens
    )

    # Exporting tokens
    if args.export_tokens_file is not None:
        output_token_file = args.export_tokens_file
        with open(output_token_file, "w", encoding="utf-8") as fto:
            fto.write(json.dumps(tokens))

    # Set text to compressed bytes format
    force_slice_texts = args.slice_texts
    for posT, posC in enumerate(positions):
        code[posC] = ("TEXT", textBytes[posT])
        # If any of the texts are bigger than 16Kb (size of bank), we enforce text slicing
        if not force_slice_texts and ((len(textBytes[posT]) + 1) >= (16 * 1024)):
            force_slice_texts = True

    del txtComp

    print(_(f"Text compression completed ({tmp_timer})"))

    ######################################################################

    # Exporting current font
    if args.export_charset is not None:
        output_charset_file = args.export_charset
        with open(output_charset_file, "w", encoding="utf-8") as fco:
            fco.write(font.getJson())

    ######################################################################
    if verbose > 0:
        print(_("Reading external files..."))

    if args.image_lines not in range(1, 193):
        sys.exit(_(f"ERROR: Invalid number of image lines {args.image_lines}."))

    sfx = None
    if args.sfx_asm_file is not None:
        with open(args.sfx_asm_file, "r", encoding="utf-8") as f:
            sfx = f.read()
            sfx = re.sub(r"org\s+\d{1,6}", "", sfx, flags=re.IGNORECASE)

    blocks = []
    if args.images_path is not None:
        images_json_path = os.path.join(args.images_path, f"images.json")
        result, images_json, error_txt = get_image_config(images_json_path)
        if not result:
            sys.exit(_(error_txt))
        tmp_timer.reset()
        for i in range(256):
            fpath = os.path.join(args.images_path, f"{i:03d}.scr")
            dpath = os.path.join(args.images_path, f"{i:03d}.csc")
            if os.path.isfile(fpath) and file_must_be_generated(fpath, dpath):
                scr_num_lines = args.image_lines
                scr_force_mirror = False
                if images_json is not None:
                    for image_json in images_json:
                        if image_json["id"] == i:
                            scr_num_lines = image_json["num_lines"]
                            scr_force_mirror = image_json["force_mirror"]
                            if verbose >= 1:
                                print(_(f"{fpath} is set with {scr_num_lines} lines."))
                                if scr_force_mirror:
                                    print(_(f"{fpath} has forced simmetry."))
                b = compress_screen_file(
                    fpath,
                    num_lines=scr_num_lines,
                    force_mirror=scr_force_mirror,
                    verbose=(verbose >= 1),
                )
                if (model == "plus3") and (len(b) > (7 * 1024)):
                    sys.exit(_("ERROR: Invalid SCR file, it is too big"))
                with open(dpath, "wb") as f:
                    f.write(bytearray(b))
                t = ("SCR", i, len(b), b, dpath)
                blocks.append(t)
            elif os.path.isfile(dpath):
                with open(dpath, "rb") as f:
                    b = list(f.read())
                    t = ("SCR", i, len(b), b, dpath)
                    blocks.append(t)
                    if (model == "plus3") and (len(b) > (7 * 1024)):
                        sys.exit(_("ERROR: Invalid SCR file, it is too big"))
        print(_(f"Images processing completed ({tmp_timer})"))

    has_tracks = False
    wyz_instruments = ""
    wyz_tracks = dict()
    wyz_tracks_sizes = dict()
    if args.tracks_path is not None and model != "48k":
        tmp_timer.reset()
        if args.use_wyz_tracker:
            # Using WYZ tracker
            if verbose > 0:
                print(_("Reading WyzTracker files..."))
            fpath1 = os.path.join(args.tracks_path, f"instruments.asm")
            if os.path.isfile(fpath1):
                with open(fpath1, "r") as f:  # Load instruments data
                    wyz_instruments += f.read()
            for i in range(256):
                fpath = os.path.join(args.tracks_path, f"{i:03d}.mus")
                if os.path.isfile(fpath):
                    b = None
                    with open(fpath, "rb") as f:  # Load track data
                        b = list(f.read())
                    if b is not None:
                        b2, delta = compress_track_data(b)
                        wyz_tracks[i] = b2
                        wyz_tracks_sizes[i] = len(b)
                        if verbose >= 1:
                            print(
                                _(
                                    f"Track {i:03d} compressed: {len(b)} bytes to {len(b2)} bytes (delta={delta})."
                                )
                            )
                        # test
                        t = ("WYZ", i, 0, [], fpath)
                        blocks.append(t)
            if len(wyz_instruments) == 0 and len(wyz_tracks.keys()) > 0:
                sys.exit(_(f"ERROR: File {fpath1} not found."))
            has_tracks = len(wyz_instruments) > 0 and len(wyz_tracks.keys()) > 0
        else:
            # PT3 tracks
            if verbose > 0:
                print(_("Reading PT3 files..."))
            for i in range(256):
                fpath = os.path.join(args.tracks_path, f"{i:03d}.PT3")
                if os.path.isfile(fpath):
                    with open(fpath, "rb") as f:
                        b = list(f.read())
                        if (model == "plus3") and (len(b) > (8 * 1024)):
                            sys.exit(
                                _(f"ERROR: Invalid PT3 file {fpath}, it is too big")
                            )
                        t = ("TRK", i, len(b), b, fpath)
                        blocks.append(t)
                        if not has_tracks:
                            has_tracks = True
        print(_(f"Tracks processing completed ({tmp_timer})"))

    loading_scr = None
    if args.load_scr_file is not None:
        if verbose > 0:
            print(_("Reading loading screen..."))
        if os.path.isfile(args.load_scr_file):
            with open(args.load_scr_file, "rb") as f:
                loading_scr = list(f.read())
            if len(loading_scr) != 32 * (192 + 24):
                sys.exit(_("ERROR: Invalid SCR file"))
        else:
            sys.exit(_("ERROR: Can't open load SCR file."))

    ######################################################################
    tmp_timer.reset()
    ######################################################################
    use_wyz_tracker = has_tracks and args.use_wyz_tracker

    wyz_player_bin = None
    if use_wyz_tracker:
        if verbose > 0:
            print(_("Assembling WyzTracker bank..."))
        res, wyz_player_bin = create_wyz_player_bank(
            track_path=args.tracks_path,
            sjasmplus_path=args.sjasmplus_path,
            tracks=wyz_tracks,
            instruments=wyz_instruments,
            verbose=(verbose >= 1),
        )
        if not res:
            sys.exit(_("ERROR: Invalid WyzTracker code generation."))
        else:
            for k in wyz_tracks_sizes.keys():
                if wyz_tracks_sizes[k] > (16 * 1024 - len(wyz_player_bin)):
                    sys.exit(
                        _(f"ERROR: Track {k} doens't fit on available space in bank 1!")
                    )

    ######################################################################

    codegen = CydcCodegen(gettext)
    chunks = []
    l_tokens = []
    l_chars = []
    l_charw = []

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
            if verbose > 0:
                print(_("Assembling interpreter for size..."))
            asm_size = get_asm_plus3_size(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=(verbose >= 1),
                sfx_asm=sfx,
                tokens=l_tokens,
                chars=l_chars,
                charw=l_charw,
                has_tracks=has_tracks,
                unused_opcodes=unused_opcodes,
                pause_start_value=args.pause_after_load,
                use_wyz_tracker=use_wyz_tracker,
            )
        elif model == "128k":
            if verbose > 0:
                print(_("Assembling interpreter for size..."))
            asm_size = get_asm_128_size(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=(verbose >= 1),
                sfx_asm=sfx,
                tokens=l_tokens,
                chars=l_chars,
                charw=l_charw,
                has_tracks=has_tracks,
                unused_opcodes=unused_opcodes,
                pause_start_value=args.pause_after_load,
                use_wyz_tracker=use_wyz_tracker,
            )
        else:
            if verbose > 0:
                print(_("Assembling interpreter for size..."))
            asm_size = get_asm_48_size(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=(verbose >= 1),
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

    if model == "plus3" and verbose > 0:
        print(_("Memory organization for disk version..."))
    elif verbose > 0:
        print(_("Memory organization for tape version..."))

    # We do this to get an rounded-up approximation of the number of blocks
    codegen.set_bank_offset_list([0xC000])
    codegen.set_bank_size_list([16 * 1024])
    chunks = codegen.generate_code(
        code=code, slice_text=force_slice_texts, show_debug=False
    )

    # To calculate the offset
    if model == "plus3":
        num_blocks = len(chunks)
    else:
        num_blocks = len(blocks) + len(chunks)
    bank0_offset = (5 * num_blocks) + asm_size + 0x8000
    bank0_size_available = (16 * 1024) + (0xC000 - bank0_offset)

    # generate block again
    if model == "plus3" and use_wyz_tracker:
        codegen.set_bank_offset_list([bank0_offset, 0xC000])
        codegen.set_bank_size_list(
            [bank0_size_available, 16 * 1024, 16 * 1024, 8 * 1024]
        )
    else:
        codegen.set_bank_offset_list([bank0_offset, 0xC000])
        codegen.set_bank_size_list([bank0_size_available, 16 * 1024])
    chunks = codegen.generate_code(
        code=code, slice_text=force_slice_texts, show_debug=args.show_bytecode
    )

    if model == "128k":
        if use_wyz_tracker:
            spectrum_banks = [0, 3, 4, 6, 7]
        else:
            spectrum_banks = [0, 1, 3, 4, 6, 7]
    elif model == "plus3":
        if use_wyz_tracker:
            spectrum_banks = [0, 3, 4, 6]
        else:
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
        elif i == 3 and model == "plus3" and use_wyz_tracker:
            offset = 0xC000
            size = 8 * 1024
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
                    elif btype == "WYZ":
                        b = 3
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
        (b, bidx, spectrum_banks[bank], (offset & 0xFFFF))
        for (b, bidx, bank, offset) in index
    ]

    print("\nRAM usage:\n-----------------")
    total_bytes = 0
    bars_data = []
    for i, v in enumerate(available_banks):
        total_bytes += len(v)
        if abarAvailable:
            bars_data.append(
                (
                    f"Bank [{spectrum_banks[i]}]: {len(v)} / {available_bank_size[i]} bytes",
                    math.ceil(
                        (len(v) * 100.0) / (len(v) + available_bank_size[i]) * 100.0
                    )
                    / 100.0,
                )
            )
        else:
            print(
                f"Bank [{spectrum_banks[i]}]: {len(v)} Bytes / Free: {available_bank_size[i]} bytes."
            )
    if abarAvailable:
        asciibars.plot(
            bars_data,
            sep_lc=" -> ",
            count_pf="%",
            max_length=20,
            unit="▓",
            neg_unit="░",
            neg_max=100,
        )

    if use_wyz_tracker:
        print(_("Bank [1]: Reserved for WyzTracker."))

    available_bytes = 0
    for v in spectrum_banks:
        if v == 0:
            available_bytes += bank0_size_available
        elif v == 6 and model == "plus3" and use_wyz_tracker:
            available_bytes += 8 * 1024
        else:
            available_bytes += 16 * 1024

    print("\nSummary:")
    print(f"- {available_bytes} bytes available.")
    print(f"- {total_bytes} bytes used.")
    print(f"- {available_bytes-total_bytes} bytes free.")
    if abarAvailable:
        bars_data = [
            (
                "- RAM usage",
                math.ceil(((total_bytes * 100.0) / available_bytes) * 100.0) / 100.0,
            )
        ]
        asciibars.plot(
            bars_data,
            sep_lc=": ",
            count_pf="%",
            max_length=40,
            unit="▓",
            neg_unit="░",
            neg_max=100,
        )

    if verbose >= 1:
        print("\nIndex:\n-----------------")
        for i, v in enumerate(index):
            print(f"Type={v[0]} Index={v[1]} Bank={v[2]} Start Address=${v[3]:04X}")

    print()

    # Cutting the spectrum banks not used from the list
    spectrum_banks = spectrum_banks[0 : len(available_banks)]

    # In case we use WyzTracker, add bank 1
    if use_wyz_tracker:
        spectrum_banks.append(1)
        available_banks.append(wyz_player_bin)

    try:
        if model == "128k":
            if verbose > 0:
                print(_("Assembling Spectrum 128k TAP..."))
            output_name = output_name[:10]
            do_asm_128(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=(verbose >= 1),
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
                use_wyz_tracker=use_wyz_tracker,
                name=output_name,
            )
        elif model == "plus3":
            if verbose > 0:
                print(_("Assembling Spectrum PLUS3 binary files..."))
            output_name = output_name[:8]
            do_asm_plus3(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=(verbose >= 1),
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
                use_wyz_tracker=use_wyz_tracker,
                name=output_name,
            )
        else:
            if verbose > 0:
                print(_("Assembling Spectrum 48k TAP..."))
            output_name = output_name[:10]
            do_asm_48(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=(verbose >= 1),
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
        if verbose > 0:
            print(_("Assembling PLUS3 disk..."))
        files = [
            os.path.join(args.output_path, "DISK"),
            os.path.join(args.output_path, f"{output_name}.BIN"),
        ]
        track_list = []
        for b in blocks:
            btype = b[0]
            bpath = b[4]
            if btype == "SCR":
                files.append(bpath)
            elif btype == "TRK":
                track_list.append(bpath)

        track_list_aux = []
        res = True
        try:
            for t in track_list:
                tb, _ = os.path.splitext(t)
                tb += ".BIN"
                add_size_header(t, tb)
                track_list_aux.append(tb)

            files += track_list_aux

            make_plus3_dsk(
                filename=os.path.join(args.output_path, output_name + ".DSK"),
                filelist=files,
                label=output_name,
                disk_720=args.disk_720,
                verbose=(verbose >= 1),
            )
        except OSError:
            res = False

        try:
            for t in track_list_aux:
                if os.path.exists(t):
                    os.remove(tb)
        except OSError:
            sys.exit("ERROR: could not create DSK file")
        finally:
            if not res:
                sys.exit("ERROR: could not create DSK file")

    ######################################################################
    print(_(f"TAP/DSK generation completed ({tmp_timer})"))
    print(_(f"Compilation successful in {timer}"))
    sys.exit(0)


if __name__ == "__main__":
    main()
