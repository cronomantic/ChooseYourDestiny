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

"""
Make Adventure GUI - A cross-platform graphical interface for the
Choose Your Destiny (CYD) adventure compiler.

Replicates the functionality of make_adventure.py, make_adv.cmd, and make_adv.sh
using tkinter for cross-platform compatibility.
"""

from __future__ import print_function

import sys
import os
import json
import re
import shutil
import subprocess
import threading
import datetime

# Hide console window on Windows after successful initialization
def hide_console_window():
    """Hide the console window on Windows after GUI starts successfully."""
    if os.name == "nt":
        try:
            import ctypes
            import ctypes.wintypes
            
            # Get console window handle
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            user32 = ctypes.WinDLL('user32', use_last_error=True)
            
            hwnd = kernel32.GetConsoleWindow()
            if hwnd:
                # SW_HIDE = 0
                user32.ShowWindow(hwnd, 0)
        except Exception:
            # Silently fail - not critical if we can't hide console
            pass

if os.name == "nt":
    _embed_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), "dist", "python")
    if os.path.isdir(_embed_dir):
        os.add_dll_directory(_embed_dir)
        # Also set TCL_LIBRARY / TK_LIBRARY so Tcl/Tk finds its init scripts
        _tcl_lib = os.path.join(_embed_dir, "tcl", "tcl8.6")
        _tk_lib = os.path.join(_embed_dir, "tcl", "tk8.6")
        if os.path.isdir(_tcl_lib):
            os.environ["TCL_LIBRARY"] = _tcl_lib
        if os.path.isdir(_tk_lib):
            os.environ["TK_LIBRARY"] = _tk_lib

# Now it is safe to import tkinter
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox, scrolledtext, colorchooser

# Import i18n from dist/cydc or src/cydc/cydc depending on location
try:
    from cydc.cyd_i18n import setup_i18n, get_available_languages, set_language, get_language, _
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dist'))
    from cydc.cyd_i18n import setup_i18n, get_available_languages, set_language, get_language, _


# ── Internationalisation ──────────────────────────────────────────────────────
_LOCALE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "locale")
setup_i18n("make_adventure_gui", locale_dir=_LOCALE_DIR)


# ── Version ────────────────────────────────────────────────────────────────────
VERSION = "1.0.0"
PROGRAM_TITLE = f"Choose Your Destiny GUI {VERSION}"

# Logo file to use in the header (relative to the project root).
# Primary: cydlogo_2_gui.png (94×80), pre-sized to LOGO_MAX_HEIGHT so it fits the
# fixed-height header crisply without runtime subsampling or clipping. The taller
# cydlogo_2_small.png (156 px) is for the README/manual, where it is not clipped.
LOGO_CANDIDATES = [
    os.path.join("assets", "cydlogo_2_gui.png"),     # 94×80 – preferred (fits header)
    os.path.join("assets", "cydlogo_2_small.png"),    # 183×156 – fallback
    os.path.join("assets", "cyddeluxe_small.png"),    # previous logo – fallback
    os.path.join("assets", "logo_cyd.png"),           # 162 KB – last resort
]

# Maximum logo height in pixels for the header
LOGO_MAX_HEIGHT = 80

# Settings file name (saved next to the script)
SETTINGS_FILE = "cyd_gui_settings.json"

# Current settings format version – bump when adding/removing keys
SETTINGS_VERSION = 2


# ── Settings persistence ──────────────────────────────────────────────────────

def _settings_path(curr_path):
    """Return the full path to the settings JSON file."""
    return os.path.join(curr_path, SETTINGS_FILE)


def load_settings(curr_path):
    """Load settings from the JSON file.  Returns a dict or None."""
    path = _settings_path(curr_path)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def save_settings(curr_path, data):
    """Save the settings dict to the JSON file."""
    path = _settings_path(curr_path)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError:
        pass  # Non‑critical – fail silently


# Keys used for serialisation.  The order here defines the JSON layout.
# Each entry: (json_key, attribute_name, type)
#   type is "str", "int", "bool"
_SETTINGS_KEYS = [
    # Project
    ("game_name",          "var_game_name",          "str"),
    ("target",             "var_target",             "str"),
    # Paths
    ("output_path",        "var_output_path",        "str"),
    ("images_path",        "var_images_path",        "str"),
    ("tracks_path",        "var_tracks_path",        "str"),
    ("sfx_file",           "var_sfx_file",           "str"),
    ("load_scr",           "var_load_scr",           "str"),
    ("tokens_file",        "var_tokens_file",        "str"),
    ("charset_file",       "var_charset_file",       "str"),
    ("sjasmplus",          "var_sjasmplus",          "str"),
    # Compiler
    ("image_lines",        "var_image_lines",        "int"),
    ("min_length",         "var_min_length",         "int"),
    ("max_length",         "var_max_length",         "int"),
    ("superset_limit",     "var_superset_limit",     "int"),
    ("verbose",            "var_verbose",            "bool"),
    ("slice_texts",        "var_slice_texts",        "bool"),
    ("trim_interpreter",   "var_trim_interpreter",   "bool"),
    ("dead_code_elimination", "var_dead_code_elimination", "bool"),
    ("show_bytecode",      "var_show_bytecode",      "bool"),
    ("no_strict_colons",   "var_no_strict_colons",   "bool"),
    ("use_wyz",            "var_use_wyz",            "bool"),
    ("disk_720",           "var_disk_720",           "bool"),
    ("autoboot",           "var_autoboot",           "bool"),
    ("max_errors",         "var_max_errors",         "int"),
    ("token_format",       "var_token_format",       "str"),
    ("warn_unused",        "var_warn_unused",        "bool"),
    ("warn_gosub",         "var_warn_gosub",         "bool"),
    ("warn_shared_vars",   "var_warn_shared_vars",   "bool"),
    ("debug_stack",        "var_debug_stack",        "bool"),
    ("debug_errors",       "var_debug_errors",       "bool"),
    ("pause_after_load",   "var_pause_after_load",   "str"),
    # Post-build
    ("run_emulator",       "var_run_emulator",       "str"),
    ("backup_cyd",         "var_backup_cyd",         "bool"),
    # Appearance
    ("app_font_size",      "var_app_font_size",      "int"),
    ("log_font_family",    "var_log_font_family",    "str"),
    ("log_font_size",      "var_log_font_size",      "int"),
    ("log_fg_color",       "var_log_fg_color",       "str"),
    ("log_bg_color",       "var_log_bg_color",       "str"),
]


def _collect_settings(app):
    """Read all tk variables into a plain dict for JSON serialisation."""
    data = {"_version": SETTINGS_VERSION}
    for json_key, attr_name, _ in _SETTINGS_KEYS:
        var = getattr(app, attr_name, None)
        if var is not None:
            data[json_key] = var.get()
    return data


def _apply_settings(app, data):
    """Write values from a loaded dict into the tk variables."""
    if not isinstance(data, dict):
        return
    for json_key, attr_name, typ in _SETTINGS_KEYS:
        if json_key not in data:
            continue
        var = getattr(app, attr_name, None)
        if var is None:
            continue
        value = data[json_key]
        try:
            if typ == "int":
                var.set(int(value))
            elif typ == "bool":
                var.set(bool(value))
            else:
                var.set(str(value))
        except (ValueError, tk.TclError):
            pass  # Skip invalid values silently


# ── Helpers (from make_adventure.py) ───────────────────────────────────────────

def _child_env(language=None):
    """Environment for the compiler: UTF-8 output, not buffered (so the log
    shows it as it comes), and the GUI's language for its messages."""
    # Force UTF-8 encoding to avoid UnicodeEncodeError on Windows
    # when the child process outputs Unicode characters (e.g. asciibars
    # uses ▓ and ░ which are not representable in cp1252).
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    if language:
        env["LANGUAGE"] = language  # gettext, used by cydc
        env["CYD_LANG"] = language
    return env


def stream_exec(exec_path, parameter_list, on_line, language=None):
    """Run an external executable, passing each line it prints (stdout and
    stderr) to on_line as it comes. Returns the exit code."""
    command_line = [os.path.abspath(exec_path)] + list(parameter_list)
    try:
        proc = subprocess.Popen(
            command_line,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=_child_env(language),
        )
    except Exception as exc:
        raise OSError(str(exc)) from exc
    with proc:
        for line in proc.stdout:
            on_line(line.rstrip("\r\n"))
    return proc.returncode


# "game.cyd:12" in a compiler message: a place in the script.
SOURCE_LOCATION_RE = re.compile(r"([^\s:()'\"]+\.cyd):(\d+)", re.IGNORECASE)


def classify_log_line(line):
    """'error', 'warning' or None, for colouring a line of the log."""
    if re.search(r"\bERROR\b", line):
        return "error"
    if re.search(r"\bWARNING\b", line):
        return "warning"
    return None


def lookup_debug_map(map_path, text):
    """The statement a system error belongs to, from the .map that
    --debug-errors writes: (location, opcode, column), or None if the chunk is
    not in the map. The column is where the statement starts on its line (1 =
    first character), or None in maps without it. text is "0:42582" or the whole
    message ("SYSTEM ERROR No:7 at 0:42582"). Raises FileNotFoundError if there
    is no map and ValueError if text has no chunk:address."""
    found = re.findall(r"(\d+)\s*:\s*(\d+)", text)
    if not found:
        raise ValueError(text)
    chunk, address = (int(v) for v in found[-1])
    best = None
    with open(map_path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            where, loc, opcode, *rest = line.rstrip("\n").split("\t")
            c, a = (int(v) for v in where.split(":"))
            if c == chunk and a <= address:  # the map is in memory order
                col = rest[0] if rest else ""
                best = (loc, opcode, int(col) if col.isdigit() else None)
    return best


def system_error_number(text):
    """The number in a pasted "SYSTEM ERROR No:7 ..." message, or None."""
    match = re.search(r"ERROR\D{0,6}?(\d+)", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def system_error_meaning(number):
    """What a system error means, in the author's terms (MANUAL: Error codes)."""
    return {
        1: _("The game asked for a picture or a music track that it doesn't "
             "have (PICTURE or TRACK with a number that wasn't included when "
             "compiling). It can also be a RETURN with no GOSUB."),
        2: _("Too many options (OPTION) at the same time."),
        3: _("CHOOSE with no OPTION to choose from."),
        4: _("A character of the character set is more than 8 pixels wide."),
        5: _("PLAY or LOOP with no music loaded."),
        6: _("The game is damaged: compile it again."),
        7: _("A position outside an array (DIM) was read or written: the "
             "position is bigger than the array."),
        8: _("An option scrolled off the top of the window before it could be "
             "chosen."),
        9: _("RETURN with no GOSUB to go back to."),
        10: _("Too many GOSUB one inside another: a subroutine probably leaves "
              "with GOTO instead of RETURN."),
    }.get(number)


def statement_span(line, col, is_text=False):
    """(start, end) of the statement that starts at col (1-based) on line, as
    0-based indices, or None if col isn't on the line. A statement ends at the
    next ':' outside quotes, at ']]' or at the end of the line; a text, at
    '[['."""
    if not col or col > len(line.rstrip()):
        return None
    start = end = col - 1
    quoted = False
    while end < len(line):
        rest = line[end:]
        if is_text:
            if rest.startswith("[["):
                break
        elif rest[0] == '"':
            quoted = not quoted
        elif not quoted and (rest[0] == ":" or rest.startswith("]]")):
            break
        end += 1
    while end > start and line[end - 1].isspace():
        end -= 1
    return (start, end) if end > start else None


def find_compiled_file(model, game_name, output_path):
    """The file the compiler wrote for game_name, or None. Its name may be cut
    (10 characters on tape, 8 on disk) and its extension lower- or uppercase."""
    if model == "plus3":
        ext = ".dsk"
    elif model in ("mld", "mld128"):
        ext = ".mld"
    else:
        ext = ".tap"
    wanted = {n.lower() + ext for n in (game_name, game_name[:10], game_name[:8])}
    try:
        names = os.listdir(output_path)
    except OSError:
        return None
    for name in sorted(names):
        if name.lower() in wanted:
            return os.path.join(output_path, name)
    return None


def find_source(name, root):
    """A script file named in a compiler message: name as given (from root) or
    else the first file with that name under root. None if there is none."""
    direct = os.path.join(root, name)
    if os.path.isfile(direct):
        return direct
    base = os.path.basename(name).lower()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in ("dist", "external", ".git"))
        for f in sorted(filenames):
            if f.lower() == base:
                return os.path.join(dirpath, f)
    return None


def find_zesarux(tools_path):
    """The ZEsarUX to run the game with, or None: tools/zesarux/, else the
    newest tools/ZEsarUX*/ (tools/build_emu_tools.sh leaves it in
    tools/ZEsarUX-<version>/), else the one on the PATH."""
    exe = "zesarux.exe" if os.name == "nt" else "zesarux"
    try:
        dirs = [d for d in os.listdir(tools_path) if d.lower().startswith("zesarux")]
    except OSError:
        dirs = []
    plain = [d for d in dirs if d.lower() == "zesarux"]
    versions = sorted(  # the highest version first, 13.0 before 9.0
        (d for d in dirs if d.lower() != "zesarux"), reverse=True,
        key=lambda d: [int(n) for n in re.findall(r"\d+", d)])
    for d in plain + versions:
        path = os.path.join(tools_path, d, exe)
        if os.path.isfile(path):
            return os.path.abspath(path)  # it runs from its own folder
    return shutil.which("zesarux")


# ZEsarUX machine per target (esxdos: divMMC on a 128K).
ZESARUX_MACHINES = {"plus3": "P341", "128k": "128k", "48k": "48k", "esxdos": "128k"}


def zesarux_arguments(model, compiled_file, output_path):
    """ZEsarUX's arguments to run compiled_file for model (not mld/mld128)."""
    args = [
        "--noconfigfile", "--quickexit", "--zoom", "2", "--realvideo", "--nosplash",
        "--forcevisiblehotkeys", "--forceconfirmyes", "--nowelcomemessage",
        "--cpuspeed", "100", "--machine", ZESARUX_MACHINES[model],
    ]
    if model == "esxdos":
        # The .TAP bootstrap loads the .DAT from the SD: the output folder.
        args += ["--enable-divmmc", "--enable-esxdos-handler",
                 "--esxdos-root-dir", os.path.abspath(output_path)]
    return args + [os.path.abspath(compiled_file)]


def open_with_system(path):
    """Open a file or a folder with the system's default application."""
    if os.name == "nt":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def run_exec(exec_path, parameter_list=None, capture_output=False):
    """Run an external executable and return the result."""
    if parameter_list is None:
        parameter_list = []
    exec_path = os.path.abspath(exec_path)
    command_line = [exec_path] + parameter_list

    env = _child_env()

    try:
        result = subprocess.run(
            args=command_line,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
        )
    except Exception as exc:
        raise OSError(str(exc)) from exc
    return result


def resolve_paths():
    """Resolve tool paths based on the current OS, mirroring make_adventure.py."""
    curr_path = os.path.abspath(os.path.dirname(__file__))
    dist_path = os.path.join(curr_path, "dist")
    tools_path = os.path.join(curr_path, "tools")
    external_path = os.path.join(curr_path, "external")

    if os.name == "nt":
        python_path = os.path.join(dist_path, "python", "python.exe")
        sjasmplus_path = os.path.join(tools_path, "sjasmplus.exe")
    else:
        python_path = (
            shutil.which("python3") or shutil.which("python") or "/usr/bin/python"
        )
        sjasmplus_path = os.path.join(external_path, "sjasmplus", "sjasmplus")

    cydc_path = os.path.join(dist_path, "cydc_cli.py")

    return {
        "curr_path": curr_path,
        "dist_path": dist_path,
        "tools_path": tools_path,
        "external_path": external_path,
        "python_path": python_path,
        "sjasmplus_path": sjasmplus_path,
        "cydc_path": cydc_path,
    }


def load_logo_image(curr_path, max_height=LOGO_MAX_HEIGHT):
    """Try to load the project logo, returning a PhotoImage or None.

    Tries each candidate in LOGO_CANDIDATES order.
    Uses tk.PhotoImage which supports PNG natively on Tk 8.6+.
    Applies subsample to reduce the size if needed.
    """
    for candidate in LOGO_CANDIDATES:
        logo_path = os.path.join(curr_path, candidate)
        if not os.path.isfile(logo_path):
            continue
        try:
            photo = tk.PhotoImage(file=logo_path)
            if photo.height() > max_height and photo.height() > 0:
                factor = photo.height() // max_height
                if factor >= 2:
                    photo = photo.subsample(factor, factor)
            return photo
        except Exception:
            continue
    return None


# ── Tooltips and source viewer ─────────────────────────────────────────────────

class Tooltip:
    """A help text shown while the pointer rests on a widget."""

    def __init__(self, widget, text, delay=500):
        self.widget, self.text, self.delay = widget, text, delay
        self._after = None
        self._tip = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None):
        self._hide()
        self._after = self.widget.after(self.delay, self._show)

    def _show(self):
        self._after = None
        if self._tip is not None:
            return
        x = self.widget.winfo_rootx() + 16
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self._tip = tk.Toplevel(self.widget)
        self._tip.wm_overrideredirect(True)
        self._tip.wm_geometry(f"+{x}+{y}")
        tk.Label(
            self._tip, text=self.text, justify=tk.LEFT, wraplength=380,
            background="#ffffe0", relief=tk.SOLID, borderwidth=1, padx=6, pady=4,
        ).pack()

    def _hide(self, _event=None):
        if self._after is not None:
            self.widget.after_cancel(self._after)
            self._after = None
        if self._tip is not None:
            self._tip.destroy()
            self._tip = None


class SourceViewer(tk.Toplevel):
    """A script opened at a line, from the log: read-only, the line
    highlighted, and a button to open it in the system's editor."""

    def __init__(self, parent, path, line, span=None):
        super().__init__(parent)
        self.title(f"{os.path.basename(path)}:{line}")
        self.geometry("760x520")
        self.path = path

        bar = ttk.Frame(self)
        bar.pack(fill=tk.X, padx=6, pady=(6, 0))
        # The button first: a long path is cut, not the button.
        ttk.Button(bar, text=_("Open in editor"), command=self._open).pack(side=tk.RIGHT)
        ttk.Label(bar, text=path, foreground="gray").pack(side=tk.LEFT)

        text = scrolledtext.ScrolledText(self, wrap=tk.NONE, font=("Courier", 10))
        text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.read().split("\n")
        width = len(str(len(lines)))
        text.insert("1.0", "\n".join(f"{n:>{width}}  {l}" for n, l in enumerate(lines, 1)))
        text.tag_configure("current", background="#ffe08a")
        text.tag_add("current", f"{line}.0", f"{line}.end")
        if span:  # the statement itself, within the line
            text.tag_configure("statement", background="#ff9f40")
            text.tag_add("statement", f"{line}.{width + 2 + span[0]}",
                         f"{line}.{width + 2 + span[1]}")
        text.see(f"{max(line - 5, 1)}.0")
        text.see(f"{line}.0")
        text.configure(state=tk.DISABLED)

    def _open(self):
        try:
            open_with_system(self.path)
        except Exception as exc:
            messagebox.showerror(_("Error"), str(exc), parent=self)


# ── Settings Dialog ────────────────────────────────────────────────────────────

class SettingsDialog(tk.Toplevel):
    """Modal dialog opened by the '⚙ Configure…' button.

    Contains paths, compiler options, post-build actions, and all the
    advanced settings.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.title("⚙  Settings")
        self.resizable(True, True)
        self.minsize(600, 540)
        self.transient(parent)
        self.grab_set()

        self._build_ui()

        # Centre on parent
        self.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        py = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{max(px, 0)}+{max(py, 0)}")

    def _build_ui(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))

        # ── Tab 1: Paths ───────────────────────────────────────────────────
        tab_paths = ttk.Frame(notebook)
        notebook.add(tab_paths, text=_("  Paths  "))
        self._build_paths_tab(tab_paths)

        # ── Tab 2: Compiler ────────────────────────────────────────────────
        tab_compiler = ttk.Frame(notebook)
        notebook.add(tab_compiler, text=_("  Compiler  "))
        self._build_compiler_tab(tab_compiler)

        # ── Tab 3: Post‑build ──────────────────────────────────────────────
        tab_post = ttk.Frame(notebook)
        notebook.add(tab_post, text=_("  Post‑build  "))
        self._build_post_tab(tab_post)

        # ── Tab 4: Appearance ──────────────────────────────────────────────
        tab_appearance = ttk.Frame(notebook)
        notebook.add(tab_appearance, text=_("  Appearance  "))
        self._build_appearance_tab(tab_appearance)

        # ── Bottom buttons ─────────────────────────────────────────────────
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=8, pady=8)

        ttk.Button(
            btn_frame, text=_("Reset to Defaults"), command=self._reset_defaults
        ).pack(side=tk.LEFT)

        ttk.Button(btn_frame, text=_("Close"), command=self.destroy).pack(side=tk.RIGHT)

    # ── Paths tab ──────────────────────────────────────────────────────────

    def _build_paths_tab(self, parent):
        pad = {"padx": 6, "pady": 3}
        frame = ttk.LabelFrame(parent, text=_("File & Directory Paths"))
        frame.pack(fill=tk.BOTH, expand=True, **pad)
        frame.columnconfigure(1, weight=1)

        path_rows = [
            (_("Output path:"), self.app.var_output_path, "dir"),
            (_("Images path:"), self.app.var_images_path, "dir"),
            (_("Tracks path:"), self.app.var_tracks_path, "dir"),
            (_("SFX ASM file:"), self.app.var_sfx_file, "file"),
            (_("Loading screen (.scr):"), self.app.var_load_scr, "file"),
            (_("Tokens file:"), self.app.var_tokens_file, "file"),
            (_("Charset file:"), self.app.var_charset_file, "file"),
            (_("SjASMPlus executable:"), self.app.var_sjasmplus, "file"),
        ]

        for i, (label, var, kind) in enumerate(path_rows):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky=tk.W, **pad)
            entry = ttk.Entry(frame, textvariable=var)
            entry.grid(row=i, column=1, sticky=tk.EW, **pad)
            if kind == "dir":
                cmd = lambda v=var: self._browse_dir(v)
            else:
                cmd = lambda v=var: self._browse_file(v)
            ttk.Button(frame, text=_("Browse…"), command=cmd).grid(
                row=i, column=2, **pad
            )

    # ── Compiler tab ───────────────────────────────────────────────────────

    def _build_compiler_tab(self, parent):
        pad = {"padx": 6, "pady": 3}

        # Image settings
        img_frame = ttk.LabelFrame(parent, text=_("Image Settings"))
        img_frame.pack(fill=tk.X, **pad)

        ttk.Label(img_frame, text=_("Image lines (1–192):")).grid(
            row=0, column=0, sticky=tk.W, **pad
        )
        ttk.Spinbox(
            img_frame,
            textvariable=self.app.var_image_lines,
            from_=1,
            to=192,
            width=6,
        ).grid(row=0, column=1, sticky=tk.W, **pad)
        ttk.Label(
            img_frame,
            text=_("Number of horizontal lines used in SCR files"),
            foreground="gray",
        ).grid(row=0, column=2, sticky=tk.W, **pad)

        # Abbreviation search
        abbr = ttk.LabelFrame(parent, text=_("Abbreviation Search"))
        abbr.pack(fill=tk.X, **pad)

        ttk.Label(abbr, text=_("Min length:")).grid(row=0, column=0, sticky=tk.W, **pad)
        ttk.Spinbox(
            abbr, textvariable=self.app.var_min_length, from_=1, to=100, width=6
        ).grid(row=0, column=1, sticky=tk.W, **pad)

        ttk.Label(abbr, text=_("Max length:")).grid(row=0, column=2, sticky=tk.W, **pad)
        ttk.Spinbox(
            abbr, textvariable=self.app.var_max_length, from_=1, to=100, width=6
        ).grid(row=0, column=3, sticky=tk.W, **pad)

        ttk.Label(abbr, text=_("Superset limit:")).grid(
            row=1, column=0, sticky=tk.W, **pad
        )
        ttk.Spinbox(
            abbr, textvariable=self.app.var_superset_limit, from_=1, to=10000, width=6
        ).grid(row=1, column=1, sticky=tk.W, **pad)

        ttk.Label(abbr, text=_("Max parser errors:")).grid(
            row=1, column=2, sticky=tk.W, **pad
        )
        ttk.Spinbox(
            abbr, textvariable=self.app.var_max_errors, from_=1, to=1000, width=6
        ).grid(row=1, column=3, sticky=tk.W, **pad)

        ttk.Label(abbr, text=_("Abbreviation format:")).grid(
            row=2, column=0, sticky=tk.W, **pad
        )
        ttk.Combobox(
            abbr,
            textvariable=self.app.var_token_format,
            values=("auto", "flat", "nested"),
            state="readonly",
            width=8,
        ).grid(row=2, column=1, sticky=tk.W, **pad)
        ttk.Label(
            abbr,
            text=_("auto: nested or flat, whichever takes less memory"),
            foreground="gray",
        ).grid(row=2, column=2, columnspan=2, sticky=tk.W, **pad)

        # Options, in groups, each with its help text on hover.
        groups_frame = ttk.Frame(parent)
        groups_frame.pack(fill=tk.X, **pad)
        groups_frame.columnconfigure(0, weight=1)
        groups_frame.columnconfigure(1, weight=1)
        app = self.app
        groups = [
            (_("Optimization"), [
                ("Trim unused interpreter code", app.var_trim_interpreter,
                 _("Leave out of the interpreter the code of the commands the "
                   "game doesn't use. Saves memory.")),
                ("Dead code elimination", app.var_dead_code_elimination,
                 _("Remove the code that can never be reached, such as the "
                   "routines of an included library that the game doesn't call.")),
                ("Slice texts between banks", app.var_slice_texts,
                 _("If a compressed text doesn't fit in a bank, split it between "
                   "that bank and the next one instead of moving it whole.")),
            ]),
            (_("Warnings"), [
                ("Warn about unused symbols", app.var_warn_unused,
                 _("Warn about labels, variables and data arrays that are "
                   "declared but never used.")),
                ("Warn about GOSUB/RETURN problems", app.var_warn_gosub,
                 _("Warn about RETURNs that can run with no GOSUB pending and "
                   "subroutines that can end without RETURN.")),
                ("Warn about variables shared between files", app.var_warn_shared_vars,
                 _("Warn when a variable declared in one file, such as a "
                   "library's, is used from another file under another name or "
                   "by its number.")),
            ]),
            (_("Debugging"), [
                ("Check the GOSUB stack at runtime (debug)", app.var_debug_stack,
                 _("The interpreter checks the GOSUB stack while the game runs "
                   "and stops with system error 9 or 10 instead of hanging. Adds "
                   "about 30 bytes: leave it out of the final version.")),
                ("Show where system errors happen (debug)", app.var_debug_errors,
                 _("System errors also say where they happened, and a .map file "
                   "next to the game turns that into a file and a line: use "
                   "'Game error' in the main window. Leave it out of the final "
                   "version.")),
                ("Show generated bytecode", app.var_show_bytecode,
                 _("Show the generated bytecode in the log.")),
                ("Verbose output", app.var_verbose,
                 _("Show more detail about each step of the compilation.")),
            ]),
            (_("Compatibility"), [
                ("Allow statements without colons", app.var_no_strict_colons,
                 _("Accept several statements on a line without ':' between "
                   "them, as old scripts did.")),
                ("Use WYZ Tracker (instead of Vortex)", app.var_use_wyz,
                 _("Play the music with WYZ Tracker instead of Vortex Tracker.")),
                ("Use 720 KB disk images (+3 only)", app.var_disk_720,
                 _("Make 720 KB disk images instead of the standard 180 KB "
                   "ones (+3 only).")),
                ("Autoboot from SD (esxdos only)", app.var_autoboot,
                 _("Also write AUTOBOOT.BAS and ESXDOS.CFG so the game starts on "
                   "its own when the Spectrum is switched on (esxdos 0.8.7 or "
                   "later).")),
            ]),
        ]
        autoboot_chk = None
        for g, (title, options) in enumerate(groups):
            frame = ttk.LabelFrame(groups_frame, text=title)
            frame.grid(row=g // 2, column=g % 2, sticky=tk.NSEW, padx=3, pady=3)
            for text, var, help_text in options:
                chk = ttk.Checkbutton(frame, text=_(text), variable=var)
                chk.pack(anchor=tk.W, padx=6, pady=2)
                Tooltip(chk, help_text)
                if var is app.var_autoboot:
                    autoboot_chk = chk

        # Autoboot is ESXDOS-only: the checkbox is enabled only while the ESXDOS
        # target is selected, and cleared otherwise.
        def _sync_autoboot(*_):
            if self.app.var_target.get() == "esxdos":
                autoboot_chk.config(state=tk.NORMAL)
            else:
                autoboot_chk.config(state=tk.DISABLED)
                self.app.var_autoboot.set(False)

        trace = self.app.var_target.trace_add("write", _sync_autoboot)
        # The dialog goes away but the variable stays: drop the trace with it,
        # or changing the target later calls a checkbox that no longer exists.
        autoboot_chk.bind(
            "<Destroy>", lambda _e: self.app.var_target.trace_remove("write", trace)
        )
        _sync_autoboot()

        # Pause after load
        pause_frame = ttk.LabelFrame(parent, text=_("Pause After Load"))
        pause_frame.pack(fill=tk.X, **pad)
        ttk.Label(pause_frame, text=_("Seconds (empty = no pause):")).grid(
            row=0, column=0, sticky=tk.W, **pad
        )
        ttk.Entry(
            pause_frame, textvariable=self.app.var_pause_after_load, width=8
        ).grid(row=0, column=1, sticky=tk.W, **pad)

    # ── Post‑build tab ────────────────────────────────────────────────────

    def _build_post_tab(self, parent):
        pad = {"padx": 6, "pady": 3}

        emu_frame = ttk.LabelFrame(parent, text=_("Run Emulator After Compilation"))
        emu_frame.pack(fill=tk.X, **pad)
        for val, label in [
            ("none", _("Do nothing")),
            ("internal", _("Internal (Zesarux in ./tools/zesarux/)")),
            ("default", _("System default application")),
        ]:
            ttk.Radiobutton(
                emu_frame,
                text=label,
                variable=self.app.var_run_emulator,
                value=val,
            ).pack(anchor=tk.W, **pad)

        bkp_frame = ttk.LabelFrame(parent, text=_("Backup"))
        bkp_frame.pack(fill=tk.X, **pad)
        ttk.Checkbutton(
            bkp_frame,
            text=_("Backup .cyd file after successful compilation (to ./BACKUP/)"),
            variable=self.app.var_backup_cyd,
        ).pack(anchor=tk.W, **pad)

    # ── Appearance tab ──────────────────────────────────────────────────

    def _build_appearance_tab(self, parent):
        pad = {"padx": 6, "pady": 3}

        # ── Application font size ──────────────────────────────────────────
        app_frame = ttk.LabelFrame(parent, text=_("Application Font"))
        app_frame.pack(fill=tk.X, **pad)

        ttk.Label(app_frame, text=_("Font size:")).grid(
            row=0, column=0, sticky=tk.W, **pad
        )
        ttk.Spinbox(
            app_frame,
            textvariable=self.app.var_app_font_size,
            from_=7,
            to=24,
            width=6,
        ).grid(row=0, column=1, sticky=tk.W, **pad)
        ttk.Label(
            app_frame,
            text=_("Size of the general UI font (requires restart)"),
            foreground="gray",
        ).grid(row=0, column=2, sticky=tk.W, **pad)

        # ── Log window settings ────────────────────────────────────────────
        log_frame = ttk.LabelFrame(parent, text=_("Log Window"))
        log_frame.pack(fill=tk.X, **pad)
        log_frame.columnconfigure(1, weight=1)

        # Font family
        available_fonts = sorted(set(tkfont.families()))
        ttk.Label(log_frame, text=_("Font:")).grid(
            row=0, column=0, sticky=tk.W, **pad
        )
        font_combo = ttk.Combobox(
            log_frame,
            textvariable=self.app.var_log_font_family,
            values=available_fonts,
            width=28,
        )
        font_combo.grid(row=0, column=1, sticky=tk.W, **pad)

        # Font size
        ttk.Label(log_frame, text=_("Font size:")).grid(
            row=1, column=0, sticky=tk.W, **pad
        )
        ttk.Spinbox(
            log_frame,
            textvariable=self.app.var_log_font_size,
            from_=6,
            to=32,
            width=6,
        ).grid(row=1, column=1, sticky=tk.W, **pad)

        # Foreground colour
        ttk.Label(log_frame, text=_("Text colour:")).grid(
            row=2, column=0, sticky=tk.W, **pad
        )
        self._fg_swatch = tk.Label(
            log_frame, width=4, relief=tk.SUNKEN,
            bg=self.app.var_log_fg_color.get(),
        )
        self._fg_swatch.grid(row=2, column=1, sticky=tk.W, **pad)
        ttk.Button(
            log_frame, text=_("Choose…"),
            command=lambda: self._pick_color(self.app.var_log_fg_color, self._fg_swatch),
        ).grid(row=2, column=2, sticky=tk.W, **pad)

        # Background colour
        ttk.Label(log_frame, text=_("Background colour:")).grid(
            row=3, column=0, sticky=tk.W, **pad
        )
        self._bg_swatch = tk.Label(
            log_frame, width=4, relief=tk.SUNKEN,
            bg=self.app.var_log_bg_color.get(),
        )
        self._bg_swatch.grid(row=3, column=1, sticky=tk.W, **pad)
        ttk.Button(
            log_frame, text=_("Choose…"),
            command=lambda: self._pick_color(self.app.var_log_bg_color, self._bg_swatch),
        ).grid(row=3, column=2, sticky=tk.W, **pad)

        # ── Preview ────────────────────────────────────────────────────────
        preview_frame = ttk.LabelFrame(parent, text=_("Log Preview"))
        preview_frame.pack(fill=tk.BOTH, expand=True, **pad)

        self._preview_text = tk.Text(
            preview_frame, height=4, wrap=tk.WORD,
            font=(self.app.var_log_font_family.get(), self.app.var_log_font_size.get()),
            fg=self.app.var_log_fg_color.get(),
            bg=self.app.var_log_bg_color.get(),
        )
        self._preview_text.insert(tk.END, _("This is a preview of the log window.") + "\n")
        self._preview_text.insert(tk.END, "ABCDEFghijklmn 0123456789 !@#$%\n")
        self._preview_text.insert(tk.END, _("Compilation finished successfully!"))
        self._preview_text.configure(state=tk.DISABLED)
        self._preview_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # Apply button
        ttk.Button(
            parent, text=_("Apply Appearance"),
            command=self._apply_and_refresh,
        ).pack(pady=(0, 6))

    def _pick_color(self, var, swatch):
        """Open colour picker and update the variable and swatch."""
        colour = colorchooser.askcolor(
            initialcolor=var.get(), parent=self, title=_("Choose colour"),
        )
        if colour and colour[1]:
            var.set(colour[1])
            swatch.configure(bg=colour[1])
            self._refresh_preview()

    def _refresh_preview(self):
        """Update the preview text widget with current settings."""
        if not hasattr(self, "_preview_text"):
            return
        self._preview_text.configure(
            font=(self.app.var_log_font_family.get(), self.app.var_log_font_size.get()),
            fg=self.app.var_log_fg_color.get(),
            bg=self.app.var_log_bg_color.get(),
        )

    def _apply_and_refresh(self):
        """Apply appearance settings to the main app and refresh preview."""
        self._refresh_preview()
        self.app._apply_appearance()
        self.app._save_settings()

    # ── Browse helpers ─────────────────────────────────────────────────────────

    def _browse_dir(self, var):
        path = filedialog.askdirectory(
            parent=self,
            initialdir=var.get() or self.app.paths["curr_path"],
        )
        if path:
            var.set(path)

    def _browse_file(self, var):
        path = filedialog.askopenfilename(
            parent=self,
            initialdir=os.path.dirname(var.get()) or self.app.paths["curr_path"],
        )
        if path:
            var.set(path)

    # ── Reset to defaults ──────────────────────────────────────────────────

    def _reset_defaults(self):
        """Reset all settings to their default values."""
        if not messagebox.askyesno(
            _("Reset to Defaults"),
            _("Are you sure you want to reset all settings to their default values?"),
            parent=self,
        ):
            return
        self.app._set_defaults()
        # Also delete the saved settings file
        path = _settings_path(self.app.paths["curr_path"])
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass


# ── Main Application ──────────────────────────────────────────────────────────

class MakeAdventureGUI:
    """Main GUI application class."""

    def __init__(self, root):
        self.root = root
        self.root.title(PROGRAM_TITLE)
        self.root.minsize(700, 550)
        self.root.resizable(True, True)

        self.paths = resolve_paths()
        self.compiling = False
        self._logo_photo = None  # prevent GC of PhotoImage
        self.available_languages = get_available_languages(_LOCALE_DIR)
        
        # Detect current language (from environment or system locale)
        self.current_language = get_language()

        # ── Create tk variables ────────────────────────────────────────────
        self.var_game_name = tk.StringVar()
        self.var_target = tk.StringVar()
        self.var_image_lines = tk.IntVar()
        self.var_output_path = tk.StringVar()
        self.var_images_path = tk.StringVar()
        self.var_tracks_path = tk.StringVar()
        self.var_sfx_file = tk.StringVar()
        self.var_load_scr = tk.StringVar()
        self.var_tokens_file = tk.StringVar()
        self.var_charset_file = tk.StringVar()
        self.var_sjasmplus = tk.StringVar()
        self.var_min_length = tk.IntVar()
        self.var_max_length = tk.IntVar()
        self.var_superset_limit = tk.IntVar()
        self.var_verbose = tk.BooleanVar()
        self.var_slice_texts = tk.BooleanVar()
        self.var_trim_interpreter = tk.BooleanVar()
        self.var_dead_code_elimination = tk.BooleanVar()
        self.var_show_bytecode = tk.BooleanVar()
        self.var_no_strict_colons = tk.BooleanVar()
        self.var_use_wyz = tk.BooleanVar()
        self.var_disk_720 = tk.BooleanVar()
        self.var_autoboot = tk.BooleanVar()
        self.var_max_errors = tk.IntVar()
        self.var_token_format = tk.StringVar()
        self.var_warn_unused = tk.BooleanVar()
        self.var_warn_gosub = tk.BooleanVar()
        self.var_warn_shared_vars = tk.BooleanVar()
        self.var_debug_stack = tk.BooleanVar()
        self.var_debug_errors = tk.BooleanVar()
        self.var_pause_after_load = tk.StringVar()
        self.var_run_emulator = tk.StringVar()
        self.var_backup_cyd = tk.BooleanVar()
        # Appearance
        self.var_app_font_size = tk.IntVar()
        self.var_log_font_family = tk.StringVar()
        self.var_log_font_size = tk.IntVar()
        self.var_log_fg_color = tk.StringVar()
        self.var_log_bg_color = tk.StringVar()

        # Set defaults first, then override with saved settings
        self._set_defaults()
        self._load_settings()

        self._build_ui()
        self._apply_appearance()
        self._set_window_icon()
        for var in (self.var_target, self.var_game_name, self.var_output_path):
            var.trace_add("write", lambda *_a: self._update_run_button())
        
        # Hide console window on Windows after successful GUI initialization
        hide_console_window()

        # Save settings on close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Defaults ───────────────────────────────────────────────────────────

    def _set_defaults(self):
        """Set all variables to their default values."""
        curr = self.paths["curr_path"]
        self.var_game_name.set("test")
        self.var_target.set("128k")
        self.var_image_lines.set(192)
        self.var_output_path.set(curr)
        self.var_images_path.set(os.path.join(curr, "IMAGES"))
        self.var_tracks_path.set(os.path.join(curr, "TRACKS"))
        self.var_sfx_file.set(os.path.join(curr, "SFX.ASM"))
        self.var_load_scr.set(os.path.join(curr, "IMAGES", "LOAD.scr"))
        self.var_tokens_file.set(os.path.join(curr, "tokens.json"))
        self.var_charset_file.set(os.path.join(curr, "charset.json"))
        self.var_sjasmplus.set(self.paths["sjasmplus_path"])
        self.var_min_length.set(3)
        self.var_max_length.set(30)
        self.var_superset_limit.set(100)
        self.var_verbose.set(False)
        self.var_slice_texts.set(False)
        self.var_trim_interpreter.set(False)
        self.var_dead_code_elimination.set(False)
        self.var_show_bytecode.set(False)
        self.var_no_strict_colons.set(False)
        self.var_use_wyz.set(False)
        self.var_disk_720.set(False)
        self.var_autoboot.set(False)
        self.var_max_errors.set(20)
        self.var_token_format.set("auto")
        self.var_warn_unused.set(True)
        self.var_warn_gosub.set(True)
        self.var_warn_shared_vars.set(True)
        self.var_debug_stack.set(False)
        self.var_debug_errors.set(False)
        self.var_pause_after_load.set("")
        self.var_run_emulator.set("none")
        self.var_backup_cyd.set(False)
        # Appearance defaults
        self.var_app_font_size.set(9)
        self.var_log_font_family.set("Courier")
        self.var_log_font_size.set(9)
        self.var_log_fg_color.set("#000000")
        self.var_log_bg_color.set("#ffffff")

    # ── Settings persistence ───────────────────────────────────────────────

    def _load_settings(self):
        """Load saved settings from disk and apply them."""
        data = load_settings(self.paths["curr_path"])
        if data is not None:
            _apply_settings(self, data)

    def _save_settings(self):
        """Collect current settings and write them to disk."""
        data = _collect_settings(self)
        save_settings(self.paths["curr_path"], data)

    def _on_close(self):
        """Called when the window is closed – save settings and exit."""
        self._save_settings()
        self.root.destroy()

    def _on_language_change(self, event=None):
        """Handle language change from dropdown."""
        new_lang = self.lang_var.get()
        if new_lang == self.current_language:
            return
        
        self.current_language = new_lang
        set_language(new_lang)
        
        # Refresh UI with new language
        self._refresh_ui_text()

    def _refresh_ui_text(self):
        """Rebuild the window in the new language. The log is kept, and so is
        the busy state if a compilation is running."""
        log_text = self.log.get("1.0", "end-1c")
        log_tags = {tag: self.log.tag_ranges(tag) for tag in ("error", "warning", "summary")}
        for widget in self.root.winfo_children():
            widget.destroy()  # the settings dialog too, if open
        self._build_ui()
        self._apply_appearance()
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, log_text)
        for tag, ranges in log_tags.items():  # its colours too
            if ranges:
                self.log.tag_add(tag, *ranges)
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)
        if self.compiling:
            self.btn_compile.configure(state=tk.DISABLED)
            self.btn_check.configure(state=tk.DISABLED)
            self.progress.start(15)

    # ── UI Construction ────────────────────────────────────────────────────

    def _build_ui(self):
        """Build the entire user interface."""

        # ── Header with logo ───────────────────────────────────────────────
        header = tk.Frame(self.root, bg="#1a1a2e", height=LOGO_MAX_HEIGHT + 20)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        header_inner = tk.Frame(header, bg="#1a1a2e")
        header_inner.pack(expand=True)

        self._logo_photo = load_logo_image(self.paths["curr_path"])
        if self._logo_photo:
            logo_label = tk.Label(header_inner, image=self._logo_photo, bg="#1a1a2e")
            logo_label.pack(side=tk.LEFT, padx=(12, 10), pady=6)

        title_frame = tk.Frame(header_inner, bg="#1a1a2e")
        title_frame.pack(side=tk.LEFT, padx=(0, 12), pady=6)

        self.title_main = tk.Label(
            title_frame,
            text=_("Choose Your Destiny"),
            font=("Helvetica", 16, "bold"),
            fg="#e0e0e0",
            bg="#1a1a2e",
        )
        self.title_main.pack(anchor=tk.W)
        
        self.title_sub = tk.Label(
            title_frame,
            text=f"Adventure Compiler — {PROGRAM_TITLE}",
            font=("Helvetica", 9),
            fg="#8888aa",
            bg="#1a1a2e",
        )
        self.title_sub.pack(anchor=tk.W)

        # ── Language selector (top right) ───────────────────────────────────
        if len(self.available_languages) > 1:
            lang_frame = tk.Frame(header_inner, bg="#1a1a2e")
            lang_frame.pack(side=tk.RIGHT, padx=12, pady=6)

            lang_label = tk.Label(
                lang_frame,
                text=_("Language:"),
                font=("Helvetica", 9),
                fg="#8888aa",
                bg="#1a1a2e",
            )
            lang_label.pack(side=tk.LEFT, padx=(0, 6))

            self.lang_var = tk.StringVar(value=self.current_language)
            lang_dropdown = ttk.Combobox(
                lang_frame,
                textvariable=self.lang_var,
                values=self.available_languages,
                state="readonly",
                width=4,
                font=("Helvetica", 9),
            )
            lang_dropdown.pack(side=tk.LEFT)
            lang_dropdown.bind("<<ComboboxSelected>>", self._on_language_change)

        # ── Main settings area ─────────────────────────────────────────────
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        pad = {"padx": 6, "pady": 4}
        project_frame = ttk.LabelFrame(main_frame, text=_("Project"))
        project_frame.pack(fill=tk.X, **pad)

        # Game name
        r = 0
        ttk.Label(project_frame, text=_("Game name:")).grid(
            row=r, column=0, sticky=tk.W, **pad
        )
        ttk.Entry(project_frame, textvariable=self.var_game_name, width=25).grid(
            row=r, column=1, sticky=tk.W, **pad
        )
        ttk.Label(
            project_frame,
            text=_("(the .cyd file must match this name)"),
            foreground="gray",
        ).grid(row=r, column=2, sticky=tk.W, **pad)

        # Target
        r += 1
        ttk.Label(project_frame, text=_("Target:")).grid(
            row=r, column=0, sticky=tk.W, **pad
        )
        target_frame = ttk.Frame(project_frame)
        target_frame.grid(row=r, column=1, columnspan=2, sticky=tk.W, **pad)
        # Two rows of three, so they fit in the window's minimum width.
        for i, (val, label) in enumerate([
            ("48k", "48K (TAP)"),
            ("128k", "128K (TAP)"),
            ("plus3", "+3 (DSK)"),
            ("mld", "Dandanator (MLD) ⚠ exp."),
            ("mld128", "Dandanator 128K (MLD) ⚠ exp."),
            ("esxdos", "ESXDOS/divMMC (SD)"),
        ]):
            ttk.Radiobutton(
                target_frame, text=label, variable=self.var_target, value=val
            ).grid(row=i // 3, column=i % 3, sticky=tk.W, padx=(0, 14))

        # ── Buttons row: Configure + Compile ───────────────────────────────
        btn_area = ttk.Frame(self.root)
        btn_area.pack(fill=tk.X, padx=8, pady=(0, 4))

        ttk.Button(
            btn_area,
            text=_("⚙  Configure…"),
            command=self._open_settings,
        ).pack(side=tk.LEFT, padx=(6, 4))

        self.btn_compile = ttk.Button(
            btn_area, text=_("▶  Compile"), command=self._on_compile
        )
        self.btn_compile.pack(side=tk.LEFT, padx=(0, 4))

        # --check: parser + code generator only, no assembler, no files.
        self.btn_check = ttk.Button(
            btn_area, text=_("✔  Check"), command=lambda: self._on_compile(check=True)
        )
        self.btn_check.pack(side=tk.LEFT, padx=(0, 4))

        # Run the last build in the emulator, without compiling again.
        self.btn_run = ttk.Button(btn_area, text=_("▷  Run"), command=self._on_run)
        self.btn_run.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(self.btn_run, _("Load the compiled game in the emulator chosen in "
                                "Configure (the internal one if none is chosen)."))

        btn_folder = ttk.Button(btn_area, text=_("Open folder"), command=self._on_open_folder)
        btn_folder.pack(side=tk.LEFT, padx=(0, 4))
        Tooltip(btn_folder, _("Open the output folder."))

        self.btn_clear_log = ttk.Button(
            btn_area, text=_("Clear Log"), command=self._clear_log
        )
        self.btn_clear_log.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(btn_area, mode="indeterminate", length=200)
        self.progress.pack(side=tk.RIGHT, padx=(4, 6))

        # ── Find a system error (--debug-errors) ───────────────────────────
        find_area = ttk.Frame(self.root)
        find_area.pack(fill=tk.X, padx=8, pady=(0, 4))
        ttk.Label(find_area, text=_("Game error:")).pack(side=tk.LEFT, padx=(6, 4))
        self.var_find_error = tk.StringVar()
        find_entry = ttk.Entry(find_area, textvariable=self.var_find_error, width=34)
        find_entry.pack(side=tk.LEFT, padx=(0, 4))
        find_entry.bind("<Return>", lambda _e: self._on_find_error())
        Tooltip(find_entry, _("Paste the error message shown on the Spectrum screen "
                              "(for example «SYSTEM ERROR No:7 at 0:42582») to see "
                              "the line of the script where it happened. The game "
                              "must be compiled with 'Show where system errors "
                              "happen'."))
        ttk.Button(find_area, text=_("Find"), command=self._on_find_error).pack(side=tk.LEFT)

        # ── Build output log ───────────────────────────────────────────────
        log_frame = ttk.LabelFrame(self.root, text=_("Build Output"))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.log = scrolledtext.ScrolledText(
            log_frame,
            height=14,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Courier", 9),
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.log.tag_configure("error", foreground="#c00000")
        self.log.tag_configure("warning", foreground="#a05a00")
        # Double-click on a "game.cyd:12" opens the script at that line.
        self.log.bind("<Double-Button-1>", self._on_log_double_click)
        self._update_run_button()

    # ── Window icon ────────────────────────────────────────────────────────

    def _set_window_icon(self):
        """Set the window/taskbar icon to the CYD Deluxe logo."""
        icon_path = os.path.join(
            self.paths["curr_path"], "assets", "cyddeluxe_small.png"
        )
        if not os.path.isfile(icon_path):
            return
        try:
            self._icon_photo = tk.PhotoImage(file=icon_path)
            self.root.iconphoto(True, self._icon_photo)
        except Exception:
            pass  # Non‑critical – skip silently

    # ── Settings dialog ────────────────────────────────────────────────────

    def _open_settings(self):
        """Open the settings/configuration dialog."""
        SettingsDialog(self.root, self)

    # ── Appearance ─────────────────────────────────────────────────────────

    def _apply_appearance(self):
        """Apply appearance settings to the application and the log widget."""
        # ── Application font size ──────────────────────────────────────────
        app_size = self.var_app_font_size.get()
        if app_size < 7:
            app_size = 9
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.configure(size=app_size)
        text_font = tkfont.nametofont("TkTextFont")
        text_font.configure(size=app_size)

        # ── Log widget ─────────────────────────────────────────────────────
        log_family = self.var_log_font_family.get() or "Courier"
        log_size = self.var_log_font_size.get()
        if log_size < 6:
            log_size = 9
        log_fg = self.var_log_fg_color.get() or "#000000"
        log_bg = self.var_log_bg_color.get() or "#ffffff"

        self.log.configure(
            font=(log_family, log_size),
            fg=log_fg,
            bg=log_bg,
        )
        self.log.tag_configure("summary", font=(log_family, log_size, "bold"))

    # ── Logging ────────────────────────────────────────────────────────────

    def _log(self, text, tag=None):
        """Thread‑safe log append. Each line that is an error or a warning is
        coloured as one, unless tag says otherwise."""

        def _append():
            self.log.configure(state=tk.NORMAL)
            for line in text.split("\n"):
                self.log.insert(tk.END, line + "\n", tag or classify_log_line(line) or ())
            self.log.see(tk.END)
            self.log.configure(state=tk.DISABLED)

        self.root.after(0, _append)

    def _on_log_double_click(self, event):
        """Open the script at the "game.cyd:12" under the pointer."""
        index = self.log.index(f"@{event.x},{event.y}")
        column = int(index.split(".")[1])
        line = self.log.get(f"{index} linestart", f"{index} lineend")
        matches = list(SOURCE_LOCATION_RE.finditer(line))
        if not matches:
            return None
        match = next((m for m in matches if m.start() <= column <= m.end()), matches[0])
        self._open_source(match.group(1), int(match.group(2)))
        return "break"  # don't select the word

    def _open_source(self, name, line, span=None):
        path = find_source(name, self.paths["curr_path"])
        if path is None:
            self._log(_("Can't find {name} in {root}.").format(
                name=name, root=self.paths["curr_path"]), "warning")
            return
        SourceViewer(self.root, path, line, span)

    # ── Run, output folder and system errors ───────────────────────────────

    def _update_run_button(self):
        """Run is available when there is a compiled game to run."""
        built = find_compiled_file(
            self.var_target.get(), self.var_game_name.get().strip(),
            self.var_output_path.get().strip())
        self.btn_run.configure(
            state=tk.NORMAL if built and not self.compiling else tk.DISABLED)

    def _on_run(self):
        mode = self.var_run_emulator.get()
        if mode == "none":  # nothing chosen: the internal one if it is there
            mode = "internal" if find_zesarux(self.paths["tools_path"]) else "default"
        self._run_emulator(self.var_target.get(), self.var_game_name.get().strip(),
                           self.var_output_path.get().strip(), mode)

    def _on_open_folder(self):
        folder = self.var_output_path.get().strip()
        try:
            open_with_system(folder)
        except Exception as exc:
            self._log(_("Failed to open {path}: {error}").format(path=folder, error=exc),
                      "error")

    def _on_find_error(self):
        """Show where in the script a system error happened: what the error
        means, the line of the script with the statement marked, and the file
        opened at it. Uses the .map a --debug-errors build writes."""
        text = self.var_find_error.get().strip()
        if not text:
            return
        game = self.var_game_name.get().strip()
        map_path = os.path.join(self.var_output_path.get().strip(), f"{game}.map")
        try:
            found = lookup_debug_map(map_path, text)
        except FileNotFoundError:
            self._log(_("To find where errors happen, compile the game with 'Show "
                        "where system errors happen (debug)' (Configure, Compiler "
                        "tab), run it until the error appears and paste its "
                        "message here."), "warning")
            return
        except ValueError:
            self._log(_("Paste the error message shown on the Spectrum screen, for "
                        "example «SYSTEM ERROR No:7 at 0:42582»."), "warning")
            return
        if found is None:
            self._log(_("That error doesn't belong to the last compilation of {game}. "
                        "If you have compiled it again since, run it until the error "
                        "appears and paste the new message.").format(game=game),
                      "warning")
            return
        loc, opcode, col = found
        number = system_error_number(text)
        meaning = system_error_meaning(number)
        if meaning:
            self._log(_("Error {number}: {meaning}").format(number=number, meaning=meaning),
                      "summary")
        match = SOURCE_LOCATION_RE.search(loc)
        if not match:  # past the last statement
            self._log(_("It happened when the program ended, after its last line."))
            return
        name, line_no = match.group(1), int(match.group(2))
        path = find_source(name, self.paths["curr_path"])
        line, span = "", None
        if path:
            try:
                with open(path, encoding="utf-8", errors="replace") as f:
                    lines = f.read().split("\n")
                line = lines[line_no - 1] if 0 < line_no <= len(lines) else ""
            except OSError:
                pass
            span = statement_span(line, col, opcode == "TEXT")
        self._log(_("{file}, line {line}:").format(file=name, line=line_no), "summary")
        if line.strip():
            self._log("    " + line)
            if span:  # ^^^ under the statement (tabs kept so it lines up)
                pad = "".join(c if c == "\t" else " " for c in line[:span[0]])
                self._log("    " + pad + "^" * (span[1] - span[0]), "error")
        self._open_source(name, line_no, span)

    def _clear_log(self):
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    # ── Compile logic ──────────────────────────────────────────────────────

    def _on_compile(self, check=False):
        """Validate inputs and start compilation in a background thread. With
        check, only look for errors (cydc --check): no assembler, no output."""
        if self.compiling:
            return

        # Save settings before compiling (in case of crash)
        self._save_settings()

        # ── Validation ─────────────────────────────────────────────────────
        curr_path = self.paths["curr_path"]
        game_name = self.var_game_name.get().strip()
        if not game_name:
            messagebox.showerror(_("Error"), _("Game name cannot be empty."))
            return

        input_file = os.path.join(curr_path, f"{game_name}.cyd")
        if not os.path.isfile(input_file):
            messagebox.showerror(
                _("Error"), _("Input file does not exist:\n") + input_file
            )
            return

        sjasmplus = self.var_sjasmplus.get().strip()
        if not check and not os.path.isfile(sjasmplus):
            messagebox.showerror(
                _("Error"), _("SjASMPlus executable not found:\n") + sjasmplus
            )
            return

        output_path = self.var_output_path.get().strip()
        if not check and not os.path.isdir(output_path):
            messagebox.showerror(
                _("Error"), _("Output path does not exist:\n") + output_path
            )
            return

        # Pause validation
        pause_val = self.var_pause_after_load.get().strip()
        if pause_val:
            try:
                pv = int(pause_val)
                if pv < 0 or (pv * 50) >= (64 * 1024):
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    _("Error"),
                    _("Pause value must be a non‑negative integer (seconds) "
                    "such that value × 50 < 65536."),
                )
                return

        # ── Build parameter list (mirrors make_adventure.py logic) ─────────
        cydc_params = [
            "-img",
            self.var_images_path.get(),
            "-trk",
            self.var_tracks_path.get(),
        ]

        tokens_file = self.var_tokens_file.get()
        if not os.path.isfile(tokens_file):
            cydc_params = ["-T", tokens_file] + cydc_params
        else:
            cydc_params = ["-t", tokens_file] + cydc_params

        charset_file = self.var_charset_file.get()
        if os.path.isfile(charset_file):
            cydc_params = ["-c", charset_file] + cydc_params

        sfx_file = self.var_sfx_file.get()
        if os.path.isfile(sfx_file):
            cydc_params = ["-sfx", sfx_file] + cydc_params

        load_scr = self.var_load_scr.get()
        if os.path.isfile(load_scr):
            cydc_params = ["-scr", load_scr] + cydc_params

        cydc_params = ["-l", str(self.var_min_length.get())] + cydc_params
        cydc_params = ["-L", str(self.var_max_length.get())] + cydc_params
        cydc_params = ["-s", str(self.var_superset_limit.get())] + cydc_params
        if self.var_max_errors.get():
            cydc_params = ["--max-errors", str(self.var_max_errors.get())] + cydc_params

        if self.var_verbose.get():
            cydc_params = ["-v"] + cydc_params
        if self.var_slice_texts.get():
            cydc_params = ["-S"] + cydc_params
        if self.var_trim_interpreter.get():
            cydc_params = ["-trim"] + cydc_params
        if self.var_dead_code_elimination.get():
            cydc_params = ["-dce"] + cydc_params
        if self.var_show_bytecode.get():
            cydc_params = ["-code"] + cydc_params
        if self.var_no_strict_colons.get():
            cydc_params = ["--no-strict-colons"] + cydc_params
        if pause_val:
            cydc_params = ["-pause", pause_val] + cydc_params
        if self.var_disk_720.get():
            cydc_params = ["-720"] + cydc_params

        if self.var_autoboot.get():
            cydc_params = ["-autoboot"] + cydc_params
        if self.var_use_wyz.get():
            cydc_params = ["-wyz"] + cydc_params
        if self.var_image_lines.get():
            cydc_params = ["-il", str(self.var_image_lines.get())] + cydc_params
        token_format = self.var_token_format.get()
        if token_format in ("flat", "nested"):
            cydc_params = ["--token-format", token_format] + cydc_params
        if not self.var_warn_unused.get():
            cydc_params = ["--no-warn-unused"] + cydc_params
        if not self.var_warn_gosub.get():
            cydc_params = ["--no-warn-gosub"] + cydc_params
        if not self.var_warn_shared_vars.get():
            cydc_params = ["--no-warn-shared-vars"] + cydc_params
        if self.var_debug_stack.get():
            cydc_params = ["--debug-stack"] + cydc_params
        if self.var_debug_errors.get():
            cydc_params = ["--debug-errors"] + cydc_params
        if check:
            cydc_params = ["--check"] + cydc_params

        cydc_path = self.paths["cydc_path"]
        python_path = self.paths["python_path"]
        model = self.var_target.get()

        cydc_params = [cydc_path] + cydc_params
        cydc_params += [model, input_file]
        if not check:
            cydc_params += [sjasmplus, output_path]

        # ── Launch ─────────────────────────────────────────────────────────
        self.compiling = True
        self.btn_compile.configure(state=tk.DISABLED)
        self.btn_check.configure(state=tk.DISABLED)
        self.btn_run.configure(state=tk.DISABLED)
        self.progress.start(15)
        self._log(f"{'─' * 60}")
        if check:
            self._log(_("Checking '{}' for {}…").format(game_name, model))
        else:
            self._log(_("Compiling '{}' for {}…").format(game_name, model))
        self._log(f"Command: {python_path} {' '.join(cydc_params)}")

        thread = threading.Thread(
            target=self._compile_thread,
            args=(
                python_path,
                cydc_params,
                model,
                game_name,
                output_path,
                input_file,
                check,
            ),
            daemon=True,
        )
        thread.start()

    def _compile_thread(
        self, python_path, cydc_params, model, game_name, output_path, input_file,
        check=False,
    ):
        """Run the compiler in a background thread."""
        success = False
        counts = {"error": 0, "warning": 0}

        def on_line(line):
            kind = classify_log_line(line)
            if kind:
                counts[kind] += 1
            self._log(line)

        try:
            returncode = stream_exec(
                python_path, cydc_params, on_line, language=self.current_language
            )
            self._log(_("Errors: {errors}   Warnings: {warnings}").format(
                errors=counts["error"], warnings=counts["warning"]), "summary")
            if returncode != 0:
                self._log(_("ERROR: Compiler exited with code {}.").format(returncode))
            else:
                success = True
                self._log("─────────────────────")
                if check:
                    self._log(_("No errors found."))
                else:
                    self._log(_("Compilation finished successfully!"))
        except OSError as exc:
            self._log(_("ERROR running CYDC: {}").format(exc))

        if check:  # nothing was built: no cleanup, backup or emulator
            self.root.after(0, self._compile_finished)
            return

        # Plus3 cleanup (mirrors make_adventure.py)
        if success and model == "plus3":
            self._log(_("Cleaning temporary files…"))
            for fname in ["SCRIPT.DAT", "DISK", "CYD.BIN"]:
                p = os.path.join(output_path, fname)
                if os.path.isfile(p):
                    os.remove(p)
                    self._log(_("  Removed {}").format(fname))

        # Backup (mirrors make_adv.cmd)
        if success and self.var_backup_cyd.get():
            self._do_backup(input_file, game_name)

        # Emulator launch
        if success:
            self._run_emulator(model, game_name, output_path)

        # UI reset
        self.root.after(0, self._compile_finished)

    def _compile_finished(self):
        self.progress.stop()
        self.btn_compile.configure(state=tk.NORMAL)
        self.btn_check.configure(state=tk.NORMAL)
        self.compiling = False
        self._update_run_button()

    # ── Backup ─────────────────────────────────────────────────────────────

    def _do_backup(self, input_file, game_name):
        """Backup the .cyd file, mirroring make_adv.cmd logic."""
        backup_dir = os.path.join(self.paths["curr_path"], "BACKUP")
        os.makedirs(backup_dir, exist_ok=True)
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dst = os.path.join(backup_dir, f"{game_name}_{now}.cyd")
        try:
            shutil.copy2(input_file, dst)
            self._log(_("Backup saved to {}").format(dst))
        except Exception as exc:
            self._log(_("Backup failed: {}").format(exc))

    # ── Emulator launch ───────────────────────────────────────────────────

    def _run_emulator(self, model, game_name, output_path, run_mode=None):
        """Launch the compiled file in an emulator, mirroring make_adv.cmd.
        run_mode defaults to the one chosen in Configure."""
        run_mode = run_mode or self.var_run_emulator.get()
        if run_mode == "none":
            return

        # Its name may be cut (tape: 10 characters) and its extension lowercase.
        compiled_file = find_compiled_file(model, game_name, output_path)
        if compiled_file is None:
            self._log(_("Cannot run emulator – file not found: {}").format(
                os.path.join(output_path, game_name)))
            return

        if run_mode == "default":
            self._log(_("Opening {} with default application…").format(compiled_file))
            try:
                open_with_system(compiled_file)
            except Exception as exc:
                self._log(_("Failed to open file: {}").format(exc))

        elif run_mode == "internal":
            zesarux = find_zesarux(self.paths["tools_path"])
            if zesarux is None:
                self._log(_("ZEsarUX not found in {} (a zesarux or ZEsarUX-* folder) "
                            "or on the PATH.").format(self.paths["tools_path"]))
                return

            if model == "mld" or model == "mld128":
                self._log(
                    _(
                        "Internal ZEsarUX launch is not configured for MLD "
                        "cartridges. Use the default application or load the MLD "
                        "manually (as a Dandanator ROM)."
                    )
                )
                return

            zparams = zesarux_arguments(model, compiled_file, output_path)
            self._log(_("Launching Zesarux: {} {}").format(zesarux, ' '.join(zparams)))
            try:
                # Its ROMs are next to it.
                subprocess.Popen([zesarux] + zparams, cwd=os.path.dirname(zesarux))
            except Exception as exc:
                self._log(_("Failed to launch Zesarux: {}").format(exc))


# ── Entry point ────────────────────────────────────────────────────────────────


def main():
    if sys.version_info[0] < 3:
        print(_("ERROR: Python 3 is required."))
        sys.exit(1)

    root = tk.Tk()

    # Attempt a native look on each platform
    try:
        if os.name == "nt":
            root.tk.call("tk", "scaling", 1.25)
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
    except tk.TclError:
        pass

    MakeAdventureGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()