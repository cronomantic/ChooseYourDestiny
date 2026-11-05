#
# MIT License
#
# Copyright (c) 2026 Sergio Chico
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
"""A CYD project: a folder with a game, configured by an optional
cyd_project.ini in it (see doc/dev/PROJECT_FOLDER_DESIGN.md).

Shared by make_adventure.py and the GUI. Paths in the file are relative to the
project's root folder. No key appears in two sections: the make_adv.cmd script
reads keys without looking at sections."""

import configparser
import os
import re

PROJECT_FILE = "cyd_project.ini"

TARGETS = ("48k", "128k", "plus3", "esxdos", "mld", "mld128")

# section -> [(key, default)]. A path default is relative to the project root.
SCHEMA = {
    "project": [
        ("name", ""),         # default: the main file's name without .cyd
        ("main", ""),         # default: <name>.cyd, or the only .cyd there is
        ("target", "128k"),
    ],
    "paths": [
        ("images", "IMAGES"),
        ("tracks", "TRACKS"),
        ("sfx", "SFX.ASM"),
        ("load_scr", "IMAGES/LOAD.scr"),
        ("tokens", "tokens.json"),
        ("charset", "charset.json"),
        ("output", "OUTPUT"),
        ("include_paths", ""),  # folders separated by ";"
        ("lib_paths", ""),
        ("import_paths", ""),
    ],
    "options": [
        ("image_lines", "192"),
        ("min_length", "3"),
        ("max_length", "30"),
        ("superset_limit", "100"),
        ("slice_texts", "no"),
        ("trim_interpreter", "no"),
        ("dead_code_elimination", "no"),
        ("show_bytecode", "no"),
        ("no_strict_colons", "no"),
        ("use_wyz", "no"),
        ("disk_720", "no"),
        ("autoboot", "no"),
        ("max_errors", "20"),
        ("token_format", "auto"),
        ("warn_unused", "yes"),
        ("warn_gosub", "yes"),
        ("warn_shared_vars", "yes"),
        ("debug_stack", "no"),
        ("debug_errors", "no"),
        ("pause_after_load", ""),
        ("keep_temp", "no"),
        ("backup", "no"),
    ],
}

SECTION_OF = {key: section for section, keys in SCHEMA.items() for key, _ in keys}
DEFAULTS = {key: default for keys in SCHEMA.values() for key, default in keys}
PATH_KEYS = ("images", "tracks", "sfx", "load_scr", "tokens", "charset", "output")
LIST_KEYS = ("include_paths", "lib_paths", "import_paths")
BOOL_KEYS = tuple(k for k, d in DEFAULTS.items() if d in ("yes", "no"))
INT_KEYS = ("image_lines", "min_length", "max_length", "superset_limit", "max_errors")


class ProjectError(Exception):
    """A project that can't be used. code says why (for a translated
    message), detail the file or value involved."""

    def __init__(self, code, detail=""):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def to_bool(value):
    return str(value).strip().lower() in ("yes", "true", "1", "on")


def from_bool(value):
    return "yes" if value else "no"


class Project:
    """A project's root folder and its settings (the file's, over the
    defaults)."""

    def __init__(self, root, values=None, has_file=False):
        self.root = os.path.abspath(root)
        self.values = dict(DEFAULTS)
        self.values.update(values or {})
        self.has_file = has_file

    @property
    def ini_path(self):
        return os.path.join(self.root, PROJECT_FILE)

    def get(self, key):
        return self.values.get(key, DEFAULTS.get(key, ""))

    def get_bool(self, key):
        return to_bool(self.get(key))

    def get_int(self, key):
        try:
            return int(str(self.get(key)).strip())
        except ValueError:
            raise ProjectError("bad_number", f"{key} = {self.get(key)}")

    def path(self, key):
        """A path setting, absolute (relative ones are from the root)."""
        value = self.get(key).strip()
        return os.path.normpath(os.path.join(self.root, value)) if value else ""

    def paths(self, key):
        """A list setting ("a;b"), as absolute folders."""
        return [os.path.normpath(os.path.join(self.root, p.strip()))
                for p in self.get(key).split(";") if p.strip()]

    @property
    def main(self):
        """The main .cyd's name (relative to the root)."""
        main = self.get("main").strip()
        if main:
            return main
        name = self.get("name").strip()
        if name:
            return name + ".cyd"
        found = sorted(f for f in os.listdir(self.root) if f.lower().endswith(".cyd"))
        if len(found) == 1:
            return found[0]
        raise ProjectError("no_main", self.root)

    @property
    def main_path(self):
        return os.path.normpath(os.path.join(self.root, self.main))

    @property
    def name(self):
        """The game's name: the setting, or the main file's without .cyd."""
        name = self.get("name").strip()
        return name or os.path.splitext(os.path.basename(self.main))[0]

    @property
    def target(self):
        target = self.get("target").strip().lower()
        if target not in TARGETS:
            raise ProjectError("bad_target", target)
        return target


def read_ini(path):
    """{key: value} of a cyd_project.ini (keys in any of its sections)."""
    parser = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=None)
    parser.optionxform = str  # keys as written
    with open(path, encoding="utf-8") as f:
        parser.read_file(f)
    values = {}
    for section in parser.sections():
        for key, value in parser.items(section):
            values[key.strip().lower()] = value.strip()
    return values


def load(root):
    """The project in root (its cyd_project.ini, if there is one)."""
    if not os.path.isdir(root):
        raise ProjectError("not_a_folder", root)
    ini = os.path.join(root, PROJECT_FILE)
    if os.path.isfile(ini):
        return Project(root, read_ini(ini), has_file=True)
    return Project(root)


def find(path):
    """The project of a path: a folder is the project's root; a .cyd file
    is the main file of the project in its folder."""
    if os.path.isdir(path):
        return load(path)
    if os.path.isfile(path) and path.lower().endswith(".cyd"):
        project = load(os.path.dirname(os.path.abspath(path)))
        project.values["main"] = os.path.basename(path)
        if not project.has_file or not project.get("name").strip():
            project.values["name"] = ""
        return project
    raise ProjectError("not_a_project", path)


def is_install_root(root, cyd_home):
    """A project can't be CYD's own folder (its subfolders, like examples/,
    can)."""
    if not cyd_home:
        return False
    a, b = os.path.normcase(os.path.realpath(root)), os.path.normcase(os.path.realpath(cyd_home))
    return a == b


# ---------------------------------------------------------------- writing

_KEY_LINE = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*[=:]\s*)(.*?)(\s*)$")
_SECTION_LINE = re.compile(r"^\s*\[([^\]]+)\]\s*$")


def update_ini_text(text, values):
    """text with values set: each key changed on its own line, so comments,
    order and unknown keys stay (configparser.write() would lose the
    comments); a key that isn't there is added at the end of its section,
    and a missing section at the end."""
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines()
    pending = {k: str(v) for k, v in values.items()}
    out = []
    section = None
    section_end = {}  # section -> index in out after its last line
    for line in lines:
        m = _SECTION_LINE.match(line)
        if m:
            section = m.group(1).strip().lower()
            out.append(line)
            section_end[section] = len(out)
            continue
        m = _KEY_LINE.match(line)
        if m and not line.lstrip().startswith((";", "#")):
            key = m.group(2).lower()
            if key in pending:
                line = f"{m.group(1)}{m.group(2)}{m.group(3)}{pending.pop(key)}"
        out.append(line)
        if section is not None and line.strip():
            section_end[section] = len(out)
    # keys still pending: at the end of their section (or a new one)
    by_section = {}
    for key, value in pending.items():
        by_section.setdefault(SECTION_OF.get(key, "options"), []).append(f"{key} = {value}")
    for sec in [s for s in SCHEMA if s in by_section] + [s for s in by_section if s not in SCHEMA]:
        new_lines = by_section[sec]
        if sec in section_end:
            at = section_end[sec]
            out[at:at] = new_lines
            for other, end in section_end.items():
                if end >= at and other != sec:
                    section_end[other] = end + len(new_lines)
            section_end[sec] = at + len(new_lines)
        else:
            if out and out[-1].strip():
                out.append("")
            out.append(f"[{sec}]")
            out += new_lines
            section_end[sec] = len(out)
    return newline.join(out) + newline


def save(project, values):
    """Set values in the project's cyd_project.ini (created if missing)."""
    path = project.ini_path
    text = ""
    if os.path.isfile(path):
        with open(path, encoding="utf-8", newline="") as f:
            text = f.read()
    else:
        text = "; Choose Your Destiny project. Paths are relative to this folder.\n"
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(update_ini_text(text, values))
    project.values.update({k: str(v) for k, v in values.items()})
    project.has_file = True


# -------------------------------------------------------------- new project

NEW_GAME = """[[
    /* {name}: your adventure starts here.

       - The code goes between [[ and ]]; what is outside is the text the
         player reads.
       - The settings of the project are in cyd_project.ini; the pictures go
         in IMAGES (000.scr, 001.scr...) and the music in TRACKS.
       - Libraries: INCLUDE LIB "strings.cyd" (see the manual). */
    CLEAR
]]Hello! This is {name}.

[[ OPTION GOTO Fin ]]Press a key to finish.
[[ CHOOSE ]]
[[ LABEL Fin ]]The end.[[ WAITKEY ]]
"""


def new_project(folder, name=None, target="128k"):
    """Make a project in folder (created if missing; it must not have a
    project already): a short commented game, IMAGES/, TRACKS/ and its
    cyd_project.ini. Returns the Project."""
    folder = os.path.abspath(folder)
    if os.path.isfile(os.path.join(folder, PROJECT_FILE)):
        raise ProjectError("already_a_project", folder)
    name = name or os.path.basename(folder.rstrip("\\/")) or "game"
    if target not in TARGETS:
        raise ProjectError("bad_target", target)
    main = f"{name}.cyd"
    os.makedirs(folder, exist_ok=True)
    if os.path.exists(os.path.join(folder, main)):
        raise ProjectError("file_exists", os.path.join(folder, main))
    for sub in ("IMAGES", "TRACKS"):
        os.makedirs(os.path.join(folder, sub), exist_ok=True)
    with open(os.path.join(folder, main), "w", encoding="utf-8") as f:
        f.write(NEW_GAME.format(name=name))
    project = Project(folder)
    text = (
        "; Choose Your Destiny project. Paths are relative to this folder.\n"
        "[project]\n"
        f"name = {name}\n"
        f"main = {main}\n"
        f"target = {target}\n"
        "\n"
        "[paths]\n"
        "images = IMAGES\n"
        "tracks = TRACKS\n"
        "output = OUTPUT\n"
        "\n"
        "[options]\n"
    )
    with open(project.ini_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return load(folder)


# ---------------------------------------------------------- compiler options

def compiler_args(project, target=None, check=False, cyd_home=None):
    """The cydc_cli.py arguments for building the project (or checking it,
    without the assembler and the output folder), before the model, input,
    sjasmplus and output path."""
    a = ["--project-root", project.root]
    for key, flag in (("include_paths", "-I"), ("lib_paths", "--lib-path"),
                      ("import_paths", "--import-path")):
        for folder in project.paths(key):
            a += [flag, folder]
    images, tracks = project.path("images"), project.path("tracks")
    if images and os.path.isdir(images):
        a += ["-img", images]
    if tracks and os.path.isdir(tracks):
        a += ["-trk", tracks]
    tokens = project.path("tokens")
    if tokens:
        a += ["-t", tokens] if os.path.isfile(tokens) else ["-T", tokens]
    for key, flag in (("charset", "-c"), ("sfx", "-sfx"), ("load_scr", "-scr")):
        p = project.path(key)
        if p and os.path.isfile(p):
            a += [flag, p]
    for key, flag in (("image_lines", "-il"), ("min_length", "-l"), ("max_length", "-L"),
                      ("superset_limit", "-s"), ("max_errors", "--max-errors")):
        a += [flag, str(project.get_int(key))]
    for key, flag in (("slice_texts", "-S"), ("trim_interpreter", "-trim"),
                      ("dead_code_elimination", "-dce"), ("show_bytecode", "-code"),
                      ("no_strict_colons", "--no-strict-colons"), ("use_wyz", "-wyz"),
                      ("disk_720", "-720"), ("autoboot", "-autoboot"),
                      ("debug_stack", "--debug-stack"), ("debug_errors", "--debug-errors"),
                      ("keep_temp", "--keep-temp")):
        if project.get_bool(key):
            a.append(flag)
    for key, flag in (("warn_unused", "--no-warn-unused"), ("warn_gosub", "--no-warn-gosub"),
                      ("warn_shared_vars", "--no-warn-shared-vars")):
        if not project.get_bool(key):
            a.append(flag)
    if project.get("token_format").strip() not in ("", "auto"):
        a += ["--token-format", project.get("token_format").strip()]
    if project.get("pause_after_load").strip():
        a += ["-pause", project.get("pause_after_load").strip()]
    if check:
        a.append("--check")
    return a
