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

import sys, os, argparse, json, re, copy, math, gettext, traceback

from cydc_txt_compress import CydcTextCompressor, NUM_TOKENS
from cydc_parser import CydcParser
from cydc_codegen import CydcCodegen
from cydc_font import CydcFont
from cydc_music import compress_track_data, create_wyz_player_bank, add_size_header
from cydc_preprocessor import CydcPreprocessor, PreprocessorError

from cyd import *
from cydc_utils import *
from cyd_i18n import setup_i18n

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


def max_errors_value(value):
    val = int(value)
    if val <= 0:
        raise argparse.ArgumentTypeError("%s is an invalid value" % value)
    return val


def emit_error(stage, message):
    print(f"ERROR [{stage}]: {message}")


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
        "-dce",
        "--dead-code-elimination",
        action="store_true",
        help=_(
            "remove bytecode that can never be reached (e.g. unused library "
            "routines), following jumps and sequential fall-through"
        ),
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
        "--max-errors",
        metavar=_("MAX_ERRORS"),
        type=max_errors_value,
        default=20,
        help=_("maximum number of parser errors to report before stopping (default: %(default)d)"),
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
        choices=["48k", "128k", "plus3", "mld", "mld128"],
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
            base_path=os.path.dirname(os.path.abspath(args.input)),
            max_errors=args.max_errors,
        )
        text, line_map = preprocessor.preprocess(args.input)
        
        if verbose >= 1:
            included_count = len(preprocessor.included_files) - 1  # -1 for main file
            if included_count > 0:
                print(_(f"Preprocessed {included_count} include file(s) in {tmp_timer}"))
            else:
                print(_(f"Preprocessing completed in {tmp_timer}"))
    except PreprocessorError as e:
        if len(preprocessor.errors) > 0:
            for prep_error in preprocessor.errors:
                emit_error("PREPROCESSOR", str(prep_error))
            if preprocessor.max_errors_reached:
                emit_error("COMPILER", _(f"Maximum error limit reached ({args.max_errors})."))
        else:
            emit_error("PREPROCESSOR", str(e))
        sys.exit(1)

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
    parser = CydcParser(
        gettext,
        strict_colon_mode=not args.no_strict_colons,
        max_errors=args.max_errors,
    )
    parser.set_line_map(line_map)  # Set line map for better error reporting
    parser.build()
    code = parser.parse(input=text, verbose=(verbose >= 3))
    if verbose >= 2:
        print(_("Symbols:"))
        parser.print_symbols()
    if len(parser.errors) > 0:
        for e in parser.errors:
            emit_error("PARSER", e)
        if parser.max_errors_reached:
            emit_error("COMPILER", _(f"Maximum error limit reached ({args.max_errors})."))
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
    if model == "mld" and args.tracks_path is not None:
        if verbose > 0:
            print(_("Ignoring tracks for strict MLD 48K target."))
    elif args.tracks_path is not None and model != "48k":
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
    codegen.eliminate_dead_code = args.dead_code_elimination
    chunks = []
    l_tokens = []
    l_chars = []
    l_charw = []

    if args.trim_interpreter:
        unused_opcodes = codegen.get_unused_opcodes(code)
    else:
        unused_opcodes = set()

    # Strip resident native-call machinery that no routine references, so a
    # program doesn't pay its cost: the array broker (CYD_PEEK/POKE/ARR_MAP/
    # ARR_FLUSH -> UNUSED_ARR_BROKER) and the cross-block call trampoline +
    # dispatch table (CYD_CALL -> UNUSED_CYD_CALL). Detection is an undefined-
    # symbol probe (assemble each block against a service-less ABI); it must be
    # decided before the size pass so the interpreter is measured at its stripped
    # size and the dispatch table is reserved only when used. Populate
    # codegen.externs first (generate_code re-does this harmlessly later).
    codegen.code_extract_declarations(code)
    unused_opcodes = set(unused_opcodes)
    # Stable RT_ index per callable (position in the dispatch table).
    route_names = sorted(codegen.extern_exports.keys())
    route_index = {n: i for i, n in enumerate(route_names)}
    used_services = extern_probe_used(
        codegen,
        code,
        args.sjasmplus_path,
        args.output_path,
        os.path.dirname(os.path.abspath(args.input)),
    )
    if len(codegen.externs) > 0 and not (used_services & set(BROKER_SERVICES)):
        unused_opcodes |= {"UNUSED_ARR_BROKER"}
    cyd_call_used = CYD_CALL_SERVICE in used_services
    if not cyd_call_used:
        unused_opcodes |= {"UNUSED_CYD_CALL"}
    # The dispatch table lives at the end of the resident image (like INDEX); its
    # size (3 bytes per callable) is accounted for in bank0_offset below.
    dispatch_size = 3 * len(route_names) if cyd_call_used else 0

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
        elif model == "mld" or model == "mld128":
            if verbose > 0:
                print(_("Assembling interpreter for size..."))
            asm_size = get_asm_mld_size(
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
                mld_is_128=(model == "mld128"),
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
        sys.exit(f"{_('ERROR: Error assembling interpreter.')}\n{e1}")
    except OSError as e2:
        sys.exit(f"{_('ERROR: Error assembling interpreter.')}\n{e2}")

    if verbose:
        print(f"Interpreter size: {asm_size}")

    if model == "48k" and (asm_size > 32 * 1024):
        sys.exit(_("ERROR: Interpreter too big!") + f" {asm_size} bytes.")
    elif model != "48k" and asm_size > 16 * 1024:
        sys.exit(_("ERROR: Interpreter too big!") + f" {asm_size} bytes.")

    ######################################################################

    if model == "plus3" and verbose > 0:
        print(_("Memory organization for disk version..."))
    elif (model == "mld" or model == "mld128") and verbose > 0:
        print(_("Memory organization for MLD version..."))
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
    # The resident image also carries the CYD_CALL dispatch table (dispatch_size
    # bytes) right after the block index, so reserve room for it too.
    bank0_offset = (5 * num_blocks) + dispatch_size + asm_size + 0x8000
    bank0_size_available = (16 * 1024) + (0xC000 - bank0_offset)

    # generate block again
    if model == "mld" or model == "mld128":
        # MLD (both strict mld and mld128): TXT/SCR/bytecode chunks are read from
        # Dandanator slots (IS_MLD_DAN); LOAD_CHUNK maps the chunk's slot at
        # $0000-$3FFF and HL is a 0-based offset inside it. So the jump addresses
        # embedded in the bytecode must be SLOT-RELATIVE (0-based), not resident,
        # and every slot is a full 16 KB (no resident $8000 sharing like the tape
        # 128k target). mld128 differs from strict mld only in having several
        # slots (spectrum_banks) and RAM-banked music, not in how bytecode is
        # addressed. (The RAM preload done by do_asm_mld for mld128 serves the
        # music managers, per cyd.py get_asm_mld128.)
        codegen.set_bank_offset_list([0, 0])
        codegen.set_bank_size_list([16 * 1024, 16 * 1024])
    elif model == "plus3" and use_wyz_tracker:
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

    if model == "mld128":
        # mld128 reads TXT/SCR/bytecode from Dandanator slots (IS_MLD_DAN), so
        # those chunks need only a slot, not a scarce 128K RAM bank. Only music
        # (TRK/WYZ) is preloaded to a RAM bank (played from $C000 by the ISR).
        # So keep the real RAM banks for music and append extra "slot-only" banks
        # (ids >= 8: not valid $7FFD banks, never preloaded) for everything else,
        # lifting the old ~96 KB / 6-bank cap up towards the 32-slot Dandanator.
        if use_wyz_tracker:
            ram_banks = [0, 3, 4, 6, 7]
        else:
            ram_banks = [0, 1, 3, 4, 6, 7]
        # loader (slot 0) + interpreter (slot 1) take two of the 32 Dandanator
        # banks; leave the rest as data slots.
        slot_only = list(range(8, 8 + (30 - len(ram_banks))))
        spectrum_banks = ram_banks + slot_only
    elif model == "128k":
        if use_wyz_tracker:
            spectrum_banks = [0, 3, 4, 6, 7]
        else:
            spectrum_banks = [0, 1, 3, 4, 6, 7]
    elif model == "plus3":
        if use_wyz_tracker:
            spectrum_banks = [0, 3, 4, 6]
        else:
            spectrum_banks = [0, 1, 3, 4]
    elif model == "mld":
        # Strict MLD (48K) reads data from Dandanator slots via SET_DAN_BANK (no
        # RAM banking, works in 48K mode), so it can span several slots — unlike a
        # real 48K machine it is not capped at one bank. The numbers are just
        # distinct slot indices; do_asm_mld maps them to slots 2..N and unused ones
        # are trimmed. 16 data slots (~256 KB) leaves room in the 32-bank
        # Dandanator Mini for the loader/interpreter and other games.
        spectrum_banks = list(range(0, 16))
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
            # MLD chunk 0 lives in its own full 16 KB slot (mapped at $0000-$3FFF),
            # not sharing the resident $8000 window, so it must be capped at 16 KB.
            # (offset stays bank0_offset: do_asm_mld remaps the index by
            # subtracting it, yielding the slot-relative 0.)
            size = (
                16 * 1024 if model in ("mld", "mld128") else bank0_size_available
            )
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
                # Music (TRK/WYZ) is played from a RAM bank at $C000, so on mld128
                # it can only live in a real 128K RAM bank (id < 8), never in a
                # slot-only Dandanator bank (id >= 8).
                music_ram_only = model == "mld128" and btype in ("TRK", "WYZ")
                best_fit_index = -1
                min_leftover = sys.maxsize
                for j, b in enumerate(available_banks):
                    if music_ram_only and spectrum_banks[j] >= 8:
                        continue
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

    ######################################################################
    # Native routines (IMPORT / CALL -> OP_EXTERN).
    #
    # A routine's final address depends on the memory layout, which is only
    # known here (the allocator runs after generate_code). So we assemble each
    # routine at its final ORG, place it, and late-patch the [bank, addr_lo,
    # addr_hi] operand of every CALL that references it.
    extern_dispatch_asm = ""  # CYD_CALL dispatch table (filled after placement)
    if len(codegen.externs) > 0:
        # 48k = resident; 128k/+3/mld128 = paged bank at $C000 ($7FFD). Strict
        # mld (single Dandanator-slot bank) is not supported yet.
        if model not in ("48k", "128k", "plus3", "mld128"):
            sys.exit(
                _(
                    "ERROR: IMPORT/CALL native routines are only supported on the "
                    "48k, 128k, +3 and mld128 targets for now."
                )
            )
        # USES declares the cross-block callees a routine reaches via CYD_CALL:
        # each name must be a known callable (an IMPORT/ASM export). The compiler
        # injects an RT_<name> index per USES entry (build_uses_inc).
        for n, d in codegen.externs.items():
            for u in d["uses"]:
                if u not in codegen.extern_exports:
                    sys.exit(
                        _(f"ERROR: Block {n} USES unknown native routine: {u}")
                    )

        # Deterministic placement order (one entry per ASM/IMPORT block).
        routine_names = sorted(codegen.externs.keys())

        # IMPORT "file.asm" paths are relative to the .cyd script's directory.
        extern_base_dir = os.path.dirname(os.path.abspath(args.input))

        # Resident ABI symbols (FLAGS, image buffer, video) a native routine may
        # reference by name, from the engine's --sym dump written by the size pass.
        extern_abi_inc = build_abi_inc(os.path.join(args.output_path, "cyd.sym"))
        # Plus the author's CYD arrays, reachable by name through the broker.
        extern_abi_inc += build_arrays_inc(codegen, spectrum_banks)

        def _assemble_block(r, org, with_syms):
            """Assemble block r at ORG; return (data, {export: addr}). Symbols are
            only resolved (via --sym) for EXPORTS blocks on the placement pass."""
            d = codegen.externs[r]
            exports = d["exports"] if (with_syms and d["explicit"]) else None
            # Shared ABI plus this block's RT_<name> indices (its USES callees).
            block_abi = extern_abi_inc + build_uses_inc(d["uses"], route_index)
            try:
                return assemble_extern_routine(
                    args.sjasmplus_path,
                    args.output_path,
                    r,
                    d["source"],
                    org,
                    exports=exports,
                    base_dir=extern_base_dir,
                    cyd_line=d.get("line"),
                    abi_inc=block_abi,
                    verbose=(verbose >= 1),
                )
            except OSError as e:
                sys.exit(f"{_('ERROR: Error assembling native routine.')}\n{e}")

        # extern_addr[callable] = (bank_byte, address). A block may expose several
        # callables (EXPORTS); a plain block/IMPORT exposes one, at its start. On
        # 48k the routine is resident and the bank byte is ignored; on 128k it is
        # the RAM bank the OP_EXTERN handler pages in before calling $C000+offset.
        extern_addr = {}

        def _place_block(r, org, bank_idx, bank_byte):
            """Re-assemble block r at its final ORG, append it to bank_idx (checking
            its size is stable vs. the measurement pass), and register the resolved
            address of every callable it exposes."""
            data, addrs = _assemble_block(r, org, True)
            if len(data) != sizes[r]:
                sys.exit(
                    _(
                        f"ERROR: Native routine {r} changed size between passes "
                        f"({sizes[r]} -> {len(data)}); its size must not depend "
                        f"on its load address."
                    )
                )
            available_banks[bank_idx] += data
            available_bank_size[bank_idx] -= len(data)
            d = codegen.externs[r]
            for callable_name in d["exports"]:
                # EXPORTS -> the label's own address; plain block -> the start.
                addr = addrs[callable_name] if d["explicit"] else org
                extern_addr[callable_name] = (bank_byte, addr)

        # Pass 1: measure every block at a provisional ORG (no symbols needed).
        sizes = {r: len(_assemble_block(r, 0xC000, False)[0]) for r in routine_names}
        for r in routine_names:
            if sizes[r] > 16 * 1024:
                sys.exit(
                    _(f"ERROR: Native routine {r} is too big for a bank.")
                    + f" ({sizes[r]} bytes)"
                )

        if model == "48k":
            total = sum(sizes.values())
            if total > available_bank_size[0]:
                sys.exit(
                    _("ERROR: Not enough memory for native routines.")
                    + f" ({total} > {available_bank_size[0]} bytes)"
                )
            # Place resident, at the end of bank 0.
            cursor = bank0_offset + len(available_banks[0])
            for r in routine_names:
                _place_block(r, cursor, 0, 0)
                cursor += sizes[r]
        else:  # 128k / +3 / mld128: place each block in a paged bank (>= 1).
            for r in routine_names:
                # Best-fit among the already-used paged banks; add a new bank
                # from spectrum_banks if none has room.
                best_j = -1
                min_leftover = sys.maxsize
                for j in range(1, len(available_banks)):
                    leftover = available_bank_size[j] - sizes[r]
                    if leftover >= 0 and leftover < min_leftover:
                        min_leftover = leftover
                        best_j = j
                if best_j == -1:
                    if len(available_banks) < len(spectrum_banks):
                        available_banks.append([])
                        available_bank_size.append(16 * 1024)
                        best_j = len(available_banks) - 1
                    else:
                        sys.exit(
                            _("ERROR: Not enough memory for native routines.")
                            + f" ({r})"
                        )
                addr = 0xC000 + len(available_banks[best_j])
                _place_block(r, addr, best_j, spectrum_banks[best_j])

        # Late-patch every CALL operand with the resolved [bank, addr_lo, addr_hi].
        for (rname, chunk_idx, pos) in codegen.extern_calls:
            bank_byte, addr = extern_addr[rname]
            available_banks[chunk_idx][pos] = bank_byte
            available_banks[chunk_idx][pos + 1] = addr & 0xFF
            available_banks[chunk_idx][pos + 2] = (addr >> 8) & 0xFF

        # Build the resident CYD_CALL dispatch table now that every callable's
        # (bank, address) is known. Emitted into the engine (see EXTERN_DISPATCH);
        # its size was reserved in bank0_offset. Only when CYD_CALL is used.
        if cyd_call_used:
            extern_dispatch_asm = build_dispatch_table(route_names, extern_addr)

    ######################################################################

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
                extern_dispatch=extern_dispatch_asm,
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
                extern_dispatch=extern_dispatch_asm,
            )
        elif model == "mld" or model == "mld128":
            if verbose > 0:
                print(_(f"Assembling Spectrum {model.upper()}..."))
            output_name = output_name[:8]
            do_asm_mld(
                sjasmplus_path=args.sjasmplus_path,
                output_path=args.output_path,
                verbose=(verbose >= 1),
                mld_name=output_name,
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
                mld_type="$88" if model == "mld128" else "$83",
                mld_is_128=(model == "mld128"),
                name=output_name,
                extern_dispatch=extern_dispatch_asm,
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
                extern_dispatch=extern_dispatch_asm,
            )
    except ValueError as e1:
        sys.exit(f"{_('ERROR: Error assembling source.')}\n{e1}")
    except OSError as e2:
        sys.exit(f"{_('ERROR: Error assembling source.')}\n{e2}")

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
                tb, _ext = os.path.splitext(t)
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
                    os.remove(t)
        except OSError:
            sys.exit("ERROR: could not create DSK file")
        finally:
            if not res:
                sys.exit("ERROR: could not create DSK file")

    ######################################################################
    if model == "mld" or model == "mld128":
        print(_(f"{model.upper()} generation completed ({tmp_timer})"))
    else:
        print(_(f"TAP/DSK generation completed ({tmp_timer})"))
    print(_(f"Compilation successful in {timer}"))
    sys.exit(0)


def cli():
    """Top-level entry point: turn any unexpected exception into a clean
    message instead of dumping a Python traceback on the author.

    Intentional ``sys.exit(...)`` calls raise ``SystemExit`` (a ``BaseException``),
    so they pass through untouched; only genuine bugs are caught here.
    """
    try:
        main()
    except Exception as e:
        sys.stderr.write(f"\nERROR [INTERNAL]: {type(e).__name__}: {e}\n")
        sys.stderr.write(
            "Unexpected compiler error. Re-run with -v for the full traceback "
            "and please report it together with your .cyd source.\n"
        )
        if "-v" in sys.argv:
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()
