#!/usr/bin/python3

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

from __future__ import print_function
from operator import itemgetter, attrgetter

import sys
import os
import gettext
import argparse
import subprocess


def run_exec(exec_path, parameter_list=[], capture_output=False):
    """_summary_

    Args:
        zx0_path (_type_): _description_
        chunk (_type_): _description_
    """
    exec_path = os.path.abspath(exec_path)  # Get the absolute path of the executable
    command_line = [exec_path] + parameter_list
    try:
        stdout = None
        # stdout = subprocess.DEVNULL
        # stdout = subprocess.STDOUT
        stderr = None
        # stderr=subprocess.DEVNULL
        result = subprocess.run(
            args=command_line,
            check=False,
            stdout=stdout,
            stderr=stderr,
            text=capture_output,
            capture_output=capture_output,
            universal_newlines=capture_output,
        )
    except subprocess.CalledProcessError as exc:
        raise OSError from exc
    if result.returncode != 0:
        raise OSError(result.stderr)
    return result


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
    return value


def main():
    version = "1.0.0"
    program = "Make Adventure " + version
    exec = "make_adventure"

    if sys.version_info[0] < 3:  # Python 2
        sys.exit(_("ERROR: Invalid python version"))

    gettext.bindtextdomain(
        exec, os.path.join(os.path.abspath(os.path.dirname(__file__)), "locale")
    )
    gettext.textdomain(exec)
    _ = gettext.gettext

    # setting paths
    curr_path = os.path.abspath(os.path.dirname(__file__))
    dist_path = os.path.join(curr_path, "dist")
    tools_path = os.path.join(curr_path, "tools")
    external_path = os.path.join(curr_path, "external")
    if os.name == "nt":
        # csc_path = os.path.join(dist_path, "csc.exe")
        python_path = os.path.join(dist_path, "python", "python.exe")
        sjasmplus_path = os.path.join(tools_path, "sjasmplus.exe")
        # mkp3fs_path = os.path.join(tools_path, "mkp3fs.exe")
    else:
        # csc_path = os.path.join(dist_path, "csc")
        python_path = "/usr/bin/python"
        sjasmplus_path = os.path.join(external_path, "sjasmplus")
        sjasmplus_path = os.path.join(sjasmplus_path, "sjasmplus")
        # mkp3fs_path = os.path.join(external_path, "taptools-1.1.1")
        # mkp3fs_path = os.path.join(mkp3fs_path, "mkp3fs")
    cydc_path = os.path.join(dist_path, "cydc_cli.py")

    #########################################################

    arg_parser = argparse.ArgumentParser(sys.argv[0], description=program)

    arg_parser.add_argument(
        "-n",
        "--name",
        metavar=_("NAME"),
        help=_("Name of the adventure"),
        default="test",
    )
    arg_parser.add_argument(
        "-o",
        "--output-path",
        type=dir_path,
        metavar=_("OUTPUT_PATH"),
        help=_("Output path to files"),
        default=curr_path,
    )
    arg_parser.add_argument(
        "-img",
        "--images-path",
        type=dir_path,
        help=_("path to the directory with the SCR files"),
        default=os.path.join(curr_path, "IMAGES"),
    )
    arg_parser.add_argument(
        "-trk",
        "--tracks-path",
        type=dir_path,
        help=_("path to the directory with the music tracks"),
        default=os.path.join(curr_path, "TRACKS"),
    )
    arg_parser.add_argument(
        "-sfx",
        "--sfx-asm-file",
        help=_("path to the asm file generated by beepfx"),
        default=os.path.join(curr_path, "SFX.ASM"),
    )
    arg_parser.add_argument(
        "-scr",
        "--load-scr-file",
        help=_("path to the SCR file used as Loading screen"),
        default=os.path.join(curr_path, "IMAGES/000.SCR"),
    )
    arg_parser.add_argument(
        "-tok",
        "--tokens-file",
        help=_("path to the token json file"),
        default=os.path.join(curr_path, "tokens.json"),
    )
    arg_parser.add_argument(
        "-chr",
        "--charset-file",
        help=_("path to the charset json file"),
        default=os.path.join(curr_path, "charset.json"),
    )
    arg_parser.add_argument(
        "-wyz",
        "--use-wyz-tracker",
        action="store_true",
        default=False,
        help=_("Use WYZ tracker instead of Vortex tracker"),
    )
    ###
    arg_parser.add_argument(
        "-il",
        "--image-lines",
        metavar=_("NUM_IMAGE_LINES"),
        type=int,
        help=_("Number of lines of the image to use (default: %(default)d)"),
        default=192,
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
        "-V",
        "--version",
        action="version",
        version=program,
        help=_("show program's version number and exit"),
    )
    ##
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
        "-720",
        "--disk-720",
        action="store_true",
        default=False,
        help=_("Use 720 Kb disk images"),
    )
    ##
    arg_parser.add_argument(
        "model",
        choices=["48k", "128k", "plus3"],
        help=_("Model of spectrum to target"),
        type=str.lower,
        default="plus3",
    )

    arg_parser.add_argument(
        "sjasmplus_path",
        nargs="?",
        metavar=_("SJASMPLUS_PATH"),
        type=file_path,
        help=_("path to sjasmplus executable"),
        default=sjasmplus_path,
    )

    try:
        args = arg_parser.parse_args()
    except FileNotFoundError as f1:
        sys.exit(_("ERROR: File not found:") + f"{f1}")
    except NotADirectoryError as f2:
        sys.exit(_("ERROR: Not a valid path:") + f"{f2}")

    input_file = os.path.join(curr_path, f"{args.name}.cyd")
    if not os.path.isfile(input_file):
        sys.exit(_("ERROR: Input file does not exists."))

    # Setting parameters
    cydc_params = ["-img", f"{args.images_path}", "-trk", f"{args.tracks_path}"]

    if not os.path.isfile(args.tokens_file):
        cydc_params = ["-T", f"{args.tokens_file}"] + cydc_params
    else:
        cydc_params = ["-t", f"{args.tokens_file}"] + cydc_params

    if os.path.isfile(args.charset_file):
        cydc_params = ["-c", f"{args.charset_file}"] + cydc_params

    if os.path.isfile(args.sfx_asm_file):
        cydc_params = ["-sfx", f"{args.sfx_asm_file}"] + cydc_params

    if os.path.isfile(args.load_scr_file):
        cydc_params = ["-scr", f"{args.load_scr_file}"] + cydc_params

    if args.min_length:
        cydc_params = ["-l", f"{args.min_length}"] + cydc_params

    if args.max_length:
        cydc_params = ["-L", f"{args.max_length}"] + cydc_params

    if args.superset_limit:
        cydc_params = ["-s", f"{args.superset_limit}"] + cydc_params

    if args.verbose:
        cydc_params = ["-v"] + cydc_params

    if args.slice_texts:
        cydc_params = ["-S"] + cydc_params

    if args.trim_interpreter:
        cydc_params = ["-trim"] + cydc_params

    if args.show_bytecode:
        cydc_params = ["-code"] + cydc_params

    if args.pause_after_load:
        cydc_params = ["-pause", f"{args.pause_after_load}"] + cydc_params

    if args.disk_720:
        cydc_params = ["-720"] + cydc_params

    if args.use_wyz_tracker:
        cydc_params = ["-wyz"] + cydc_params

    if args.image_lines:
        cydc_params = ["-il", f"{args.image_lines}"] + cydc_params

    cydc_params = [cydc_path] + cydc_params
    cydc_params += [
        args.model,
        input_file,
        args.sjasmplus_path,
        # args.mkp3fs_path,
        args.output_path,
    ]

    try:
        print("Compiling the script...")
        #print(cydc_params)
        run_exec(python_path, cydc_params)
    except OSError as os1:
        err = _("ERROR: Error running CYDC.") + str(os1)
        sys.exit(err)

    if args.model == "plus3":
        print("Cleaning...")
        files_to_clean = ["SCRIPT.DAT", "DISK", "CYD.BIN"]
        for f in files_to_clean:
            p = os.path.join(args.output_path, f)
            if os.path.isfile(p):
                os.remove(p)

    sys.exit(0)


if __name__ == "__main__":
    main()
