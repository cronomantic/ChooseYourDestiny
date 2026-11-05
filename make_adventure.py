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
import argparse
import subprocess

# Import i18n from dist/cydc or src/cydc/cydc depending on location
try:
    from cydc.cyd_i18n import setup_i18n, _
    from cydc import cyd_project
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dist'))
    from cydc.cyd_i18n import setup_i18n, _
    from cydc import cyd_project


def run_exec(exec_path, parameter_list=[], capture_output=False, cwd=None):
    """_summary_

    Args:
        zx0_path (_type_): _description_
        chunk (_type_): _description_
    """
    exec_path = os.path.abspath(exec_path)  # Get the absolute path of the executable
    command_line = [exec_path] + parameter_list
    # Force UTF-8 encoding to avoid UnicodeEncodeError on Windows (the compiler
    # prints RAM-usage bars and accented messages that a cp1252 console cannot
    # encode). The GUI wrapper does the same.
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
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
            env=env,
            cwd=cwd,
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


class _TrackedStore(argparse._StoreAction):
    """A store action that notes the option was given: those win over the
    project's cyd_project.ini, the defaults don't."""

    def __call__(self, parser, namespace, values, option_string=None):
        super().__call__(parser, namespace, values, option_string)
        namespace.__dict__.setdefault("_given", set()).add(self.dest)


class _TrackedStoreTrue(argparse._StoreTrueAction):
    def __call__(self, parser, namespace, values, option_string=None):
        super().__call__(parser, namespace, values, option_string)
        namespace.__dict__.setdefault("_given", set()).add(self.dest)


# Options that set a key of the project (dest -> key).
_PATH_OPTIONS = {
    "output_path": "output", "images_path": "images", "tracks_path": "tracks",
    "sfx_asm_file": "sfx", "load_scr_file": "load_scr", "tokens_file": "tokens",
    "charset_file": "charset",
}
_VALUE_OPTIONS = {
    "image_lines": "image_lines", "min_length": "min_length", "max_length": "max_length",
    "superset_limit": "superset_limit", "max_errors": "max_errors",
    "token_format": "token_format", "pause_after_load": "pause_after_load",
}
_FLAG_OPTIONS = {
    "use_wyz_tracker": "use_wyz", "slice_texts": "slice_texts",
    "trim_interpreter": "trim_interpreter", "dead_code_elimination": "dead_code_elimination",
    "show_bytecode": "show_bytecode", "no_strict_colons": "no_strict_colons",
    "disk_720": "disk_720", "autoboot": "autoboot", "debug_stack": "debug_stack",
    "debug_errors": "debug_errors", "keep_temp": "keep_temp",
}
_NO_WARN_OPTIONS = {
    "no_warn_unused": "warn_unused", "no_warn_gosub": "warn_gosub",
    "no_warn_shared_vars": "warn_shared_vars",
}


def project_error_message(e):
    """The message for a cyd_project.ProjectError."""
    messages = {
        "not_a_folder": _("ERROR: Not a valid path:"),
        "not_a_project": _("ERROR: Not a project folder or a .cyd file:"),
        "no_main": _("ERROR: The project doesn't say its main .cyd file (main in cyd_project.ini) and there isn't exactly one in its folder:"),
        "bad_target": _("ERROR: Unknown target:"),
        "bad_number": _("ERROR: Invalid number in cyd_project.ini:"),
        "already_a_project": _("ERROR: There is already a project in"),
        "file_exists": _("ERROR: The file already exists:"),
    }
    return f"{messages.get(e.code, 'ERROR:')} {e.detail}"


def main():
    version = "2.0.0"
    program = "Make Adventure " + version
    exec = "make_adventure"

    if sys.version_info[0] < 3:  # Python 2
        print("ERROR: Invalid python version")
        sys.exit(1)

    # Initialize internationalization
    setup_i18n(exec, locale_dir="locale")

    # setting paths
    curr_path = os.path.abspath(os.path.dirname(__file__))
    dist_path = os.path.join(curr_path, "dist")
    tools_path = os.path.join(curr_path, "tools")
    external_path = os.path.join(curr_path, "external")
    if os.name == "nt":
        python_path = os.path.join(dist_path, "python", "python.exe")
        sjasmplus_path = os.path.join(tools_path, "sjasmplus.exe")
    else:
        python_path = "/usr/bin/python"
        sjasmplus_path = os.path.join(external_path, "sjasmplus")
        sjasmplus_path = os.path.join(sjasmplus_path, "sjasmplus")
    cydc_path = os.path.join(dist_path, "cydc_cli.py")

    #########################################################

    arg_parser = argparse.ArgumentParser(
        sys.argv[0],
        description=program,
        epilog=_(
            "The project is a folder with the game (and its cyd_project.ini, if it "
            "has one), or the game's main .cyd file. The target, if not given, is "
            "the project's."
        ),
    )
    # Options given win over the project's settings; their defaults don't.
    arg_parser.register("action", None, _TrackedStore)
    arg_parser.register("action", "store", _TrackedStore)
    arg_parser.register("action", "store_true", _TrackedStoreTrue)

    arg_parser.add_argument(
        "--lang",
        choices=["en", "es"],
        help=_("Language for output (English or Spanish)"),
        default=None,
    )
    arg_parser.add_argument(
        "--new",
        metavar=_("FOLDER"),
        help=_("make a new project in FOLDER (a short game, IMAGES, TRACKS and its cyd_project.ini) and exit"),
    )
    arg_parser.add_argument(
        "--describe",
        action="store_true",
        default=False,
        help=_("print the project's root, main file, name, target and output folder as KEY=value lines, and exit (for the make_adv scripts)"),
    )
    arg_parser.add_argument(
        "-n",
        "--name",
        metavar=_("NAME"),
        help=_("Name of the adventure"),
    )
    arg_parser.add_argument(
        "-o",
        "--output-path",
        metavar=_("OUTPUT_PATH"),
        help=_("Output path to files"),
    )
    arg_parser.add_argument(
        "-img",
        "--images-path",
        type=dir_path,
        help=_("path to the directory with the SCR files"),
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
        help=_("path to the asm file generated by beepfx"),
    )
    arg_parser.add_argument(
        "-scr",
        "--load-scr-file",
        help=_("path to the SCR file used as Loading screen"),
    )
    arg_parser.add_argument(
        "-tok",
        "--tokens-file",
        help=_("path to the token json file"),
    )
    arg_parser.add_argument(
        "-chr",
        "--charset-file",
        help=_("path to the charset json file"),
    )
    arg_parser.add_argument(
        "-I",
        "--include-path",
        action="append",
        default=[],
        metavar=_("FOLDER"),
        help=_("another folder for INCLUDE, after the project root (can be repeated)"),
    )
    arg_parser.add_argument(
        "--lib-path",
        action="append",
        default=[],
        metavar=_("FOLDER"),
        help=_("a folder for INCLUDE LIB, before the bundled lib/ (can be repeated)"),
    )
    arg_parser.add_argument(
        "--import-path",
        action="append",
        default=[],
        metavar=_("FOLDER"),
        help=_("another folder for IMPORT, after the script's folder (can be repeated)"),
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
        "-dce",
        "--dead-code-elimination",
        action="store_true",
        help=_("remove code that can never be reached"),
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
        help=_("allow statements without colon separator (backwards compatibility mode)"),
    )
    arg_parser.add_argument(
        "--max-errors",
        type=int,
        default=20,
        help=_("maximum number of parser errors to report before stopping"),
    )
    arg_parser.add_argument(
        "--token-format",
        choices=["auto", "flat", "nested"],
        default="auto",
        help=_(
            "abbreviation format: nested ones can contain other abbreviations; "
            "auto uses whichever takes less memory (default: %(default)s)"
        ),
    )
    arg_parser.add_argument(
        "--check",
        action="store_true",
        default=False,
        help=_("only check the script for errors, without building it"),
    )
    arg_parser.add_argument(
        "--no-warn-unused",
        action="store_true",
        default=False,
        help=_("don't warn about labels, variables and data arrays that are never used"),
    )
    arg_parser.add_argument(
        "--no-warn-gosub",
        action="store_true",
        default=False,
        help=_("don't warn about RETURNs reached without a GOSUB and subroutines left without RETURN"),
    )
    arg_parser.add_argument(
        "--no-warn-shared-vars",
        action="store_true",
        default=False,
        help=_(
            "don't warn when a variable declared in one file (such as a library's) "
            "is used from another file under another name or by its number"
        ),
    )
    arg_parser.add_argument(
        "--debug-errors",
        action="store_true",
        default=False,
        help=_(
            "make system errors show where they happened, and write a .map file "
            "that turns that into a file and a line (for debugging, adds some bytes)"
        ),
    )
    arg_parser.add_argument(
        "--debug-stack",
        action="store_true",
        default=False,
        help=_("make GOSUB and RETURN check the call stack at runtime (for debugging)"),
    )
    arg_parser.add_argument(
        "--keep-temp",
        action="store_true",
        default=False,
        help=_(
            "keep the intermediate files (cyd.asm, cyd.sym, the listing...) in the "
            "cyd_tmp folder of the output folder; without it they are removed "
            "when the build ends well"
        ),
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
    arg_parser.add_argument(
        "-autoboot",
        "--autoboot",
        action="store_true",
        default=False,
        help=_("[esxdos] also emit AUTOBOOT.BAS + ESXDOS.CFG for SD autoboot"),
    )
    arg_parser.add_argument(
        "--compiler",
        metavar=_("CYDC_PATH"),
        type=file_path,
        help=_("the compiler to run instead of dist/cydc_cli.py (for development: src/cydc/cydc/cydc.py)"),
    )
    arg_parser.add_argument(
        "--sjasmplus",
        metavar=_("SJASMPLUS_PATH"),
        type=file_path,
        help=_("path to sjasmplus executable"),
        default=None,  # the bundled one; checked below, --check doesn't need it
    )
    ##
    arg_parser.add_argument(
        "items",
        nargs="*",
        metavar=_("TARGET / PROJECT"),
        help=_(
            "the target ({targets}; mld/mld128 are EXPERIMENTAL) and the project "
            "(its folder or its main .cyd file), in any order"
        ).format(targets=", ".join(cyd_project.TARGETS)),
    )

    try:
        args = arg_parser.parse_args()
    except FileNotFoundError as f1:
        sys.exit(_("ERROR: File not found:") + f"{f1}")
    except NotADirectoryError as f2:
        sys.exit(_("ERROR: Not a valid path:") + f"{f2}")
    given = getattr(args, "_given", set())

    # --new: a project to start with
    if args.new:
        target = next((i.lower() for i in args.items if i.lower() in cyd_project.TARGETS), "128k")
        try:
            project = cyd_project.new_project(args.new, args.name, target)
        except cyd_project.ProjectError as e:
            sys.exit(project_error_message(e))
        print(_("New project in {root}: {main}").format(root=project.root, main=project.main))
        sys.exit(0)

    # The target and the project, in any order
    target = None
    project_arg = None
    for item in args.items:
        if item.lower() in cyd_project.TARGETS and target is None:
            target = item.lower()
        elif project_arg is None:
            project_arg = item
        else:
            arg_parser.error(_("too many arguments: {item}").format(item=item))
    if project_arg is None:
        sys.exit(_(
            "ERROR: No project given. Give the folder of your game (or its main "
            ".cyd file); to start one, use --new FOLDER. A game made with an older "
            "version, in CYD's own folder, has to be moved to a folder of its own "
            "(see the manual, \"Migrating a game from an older version\")."
        ))
    try:
        project = cyd_project.find(project_arg)
        if cyd_project.is_install_root(project.root, curr_path):
            sys.exit(_(
                "ERROR: CYD's own folder can't be a project: move the game to a "
                "folder of its own (see the manual, \"Migrating a game from an "
                "older version\")."
            ))

        # What was given here wins over the project's settings.
        if "name" in given:
            project.values["name"] = args.name
        for dest, key in _PATH_OPTIONS.items():
            if dest in given:
                project.values[key] = os.path.abspath(getattr(args, dest))
        for dest, key in _VALUE_OPTIONS.items():
            if dest in given:
                project.values[key] = str(getattr(args, dest))
        for dest, key in _FLAG_OPTIONS.items():
            if dest in given:
                project.values[key] = "yes"
        for dest, key in _NO_WARN_OPTIONS.items():
            if dest in given:
                project.values[key] = "no"
        for dest, key in (("include_path", "include_paths"), ("lib_path", "lib_paths"),
                          ("import_path", "import_paths")):
            extra = [os.path.abspath(p) for p in getattr(args, dest)]
            if extra:
                project.values[key] = ";".join([project.get(key)] + extra).strip(";")
        if target is None:
            target = project.target

        if args.describe:
            for key, value in (("ROOT", project.root), ("MAIN", project.main_path),
                               ("NAME", project.name), ("TARGET", target),
                               ("OUTPUT", project.path("output")),
                               ("BACKUP", project.get("backup"))):
                print(f"{key}={value}")
            sys.exit(0)

        if not os.path.isfile(project.main_path):
            sys.exit(_("ERROR: Input file does not exists.") + f" {project.main_path}")

        # Tokens and character set given here, instead of the project's.
        extra_params = []
        if args.import_tokens_file or args.export_tokens_file:
            project.values["tokens"] = ""
            if args.import_tokens_file:
                extra_params += ["-t", os.path.abspath(args.import_tokens_file)]
            if args.export_tokens_file:
                extra_params += ["-T", os.path.abspath(args.export_tokens_file)]
        if args.import_charset:
            project.values["charset"] = os.path.abspath(args.import_charset)
        if args.export_charset:
            extra_params += ["-C", os.path.abspath(args.export_charset)]
        extra_params += ["-v"] * args.verbose

        cydc_params = cyd_project.compiler_args(project, target, check=args.check)
    except cyd_project.ProjectError as e:
        sys.exit(project_error_message(e))

    if args.compiler:
        # Run with this Python: the embedded one in dist/ doesn't put the
        # script's folder on the path, as src/cydc/cydc/cydc.py needs.
        cydc_path = os.path.abspath(args.compiler)
        python_path = sys.executable
    cydc_params = [cydc_path] + cydc_params + extra_params + [target, project.main_path]
    if not args.check:  # --check assembles nothing and writes no files
        if args.sjasmplus is None:
            try:
                args.sjasmplus = file_path(sjasmplus_path)
            except FileNotFoundError as f1:
                sys.exit(_("ERROR: File not found:") + f"{f1}")
        output_path = project.path("output")
        os.makedirs(output_path, exist_ok=True)
        cydc_params += [os.path.abspath(args.sjasmplus), output_path]

    try:
        print(_("Compiling the script..."))
        run_exec(python_path, cydc_params, cwd=project.root)
    except OSError as os1:
        err = _("ERROR: Error running CYDC.") + str(os1)
        sys.exit(err)

    # Nothing to clean: the compiler keeps its intermediate files (the +3
    # DISK and .BIN among them) in cyd_tmp and removes them itself.
    sys.exit(0)


if __name__ == "__main__":
    main()
