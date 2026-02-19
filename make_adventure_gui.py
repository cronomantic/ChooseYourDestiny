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
import shutil
import subprocess
import threading
import datetime

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
from tkinter import ttk, filedialog, messagebox, scrolledtext


# ── Version ────────────────────────────────────────────────────────────────────
VERSION = "1.0.0"
PROGRAM_TITLE = f"Choose Your Destiny GUI {VERSION}"

# Logo file to use in the header (relative to the project root).
# Primary: cyddeluxe_small.png (39 KB, ideal size for GUI)
# Fallbacks in case the primary is missing.
LOGO_CANDIDATES = [
    os.path.join("assets", "cyddeluxe_small.png"),   # 39 KB – preferred
    os.path.join("assets", "logo_cyd_2small.png"),    # 11 KB – fallback
    os.path.join("assets", "logo_cyd_small.png"),     # 42 KB – fallback
    os.path.join("assets", "logo_cyd.png"),            # 162 KB – last resort
]

# Maximum logo height in pixels for the header
LOGO_MAX_HEIGHT = 80

# Settings file name (saved next to the script)
SETTINGS_FILE = "cyd_gui_settings.json"

# Current settings format version – bump when adding/removing keys
SETTINGS_VERSION = 1


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
    ("show_bytecode",      "var_show_bytecode",      "bool"),
    ("use_wyz",            "var_use_wyz",            "bool"),
    ("disk_720",           "var_disk_720",           "bool"),
    ("pause_after_load",   "var_pause_after_load",   "str"),
    # Post-build
    ("run_emulator",       "var_run_emulator",       "str"),
    ("backup_cyd",         "var_backup_cyd",         "bool"),
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

def run_exec(exec_path, parameter_list=None, capture_output=False):
    """Run an external executable and return the result."""
    if parameter_list is None:
        parameter_list = []
    exec_path = os.path.abspath(exec_path)
    command_line = [exec_path] + parameter_list

    # Force UTF-8 encoding to avoid UnicodeEncodeError on Windows
    # when the child process outputs Unicode characters (e.g. asciibars
    # uses ▓ and ░ which are not representable in cp1252).
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

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
        notebook.add(tab_paths, text="  Paths  ")
        self._build_paths_tab(tab_paths)

        # ── Tab 2: Compiler ────────────────────────────────────────────────
        tab_compiler = ttk.Frame(notebook)
        notebook.add(tab_compiler, text="  Compiler  ")
        self._build_compiler_tab(tab_compiler)

        # ── Tab 3: Post‑build ──────────────────────────────────────────────
        tab_post = ttk.Frame(notebook)
        notebook.add(tab_post, text="  Post‑build  ")
        self._build_post_tab(tab_post)

        # ── Bottom buttons ─────────────────────────────────────────────────
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=8, pady=8)

        ttk.Button(
            btn_frame, text="Reset to Defaults", command=self._reset_defaults
        ).pack(side=tk.LEFT)

        ttk.Button(btn_frame, text="Close", command=self.destroy).pack(side=tk.RIGHT)

    # ── Paths tab ──────────────────────────────────────────────────────────

    def _build_paths_tab(self, parent):
        pad = {"padx": 6, "pady": 3}
        frame = ttk.LabelFrame(parent, text="File & Directory Paths")
        frame.pack(fill=tk.BOTH, expand=True, **pad)
        frame.columnconfigure(1, weight=1)

        path_rows = [
            ("Output path:", self.app.var_output_path, "dir"),
            ("Images path:", self.app.var_images_path, "dir"),
            ("Tracks path:", self.app.var_tracks_path, "dir"),
            ("SFX ASM file:", self.app.var_sfx_file, "file"),
            ("Loading screen (.scr):", self.app.var_load_scr, "file"),
            ("Tokens file:", self.app.var_tokens_file, "file"),
            ("Charset file:", self.app.var_charset_file, "file"),
            ("SjASMPlus executable:", self.app.var_sjasmplus, "file"),
        ]

        for i, (label, var, kind) in enumerate(path_rows):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky=tk.W, **pad)
            entry = ttk.Entry(frame, textvariable=var)
            entry.grid(row=i, column=1, sticky=tk.EW, **pad)
            if kind == "dir":
                cmd = lambda v=var: self._browse_dir(v)
            else:
                cmd = lambda v=var: self._browse_file(v)
            ttk.Button(frame, text="Browse…", command=cmd).grid(
                row=i, column=2, **pad
            )

    # ── Compiler tab ───────────────────────────────────────────────────────

    def _build_compiler_tab(self, parent):
        pad = {"padx": 6, "pady": 3}

        # Image settings
        img_frame = ttk.LabelFrame(parent, text="Image Settings")
        img_frame.pack(fill=tk.X, **pad)

        ttk.Label(img_frame, text="Image lines (1–192):").grid(
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
            text="Number of horizontal lines used in SCR files",
            foreground="gray",
        ).grid(row=0, column=2, sticky=tk.W, **pad)

        # Abbreviation search
        abbr = ttk.LabelFrame(parent, text="Abbreviation Search")
        abbr.pack(fill=tk.X, **pad)

        ttk.Label(abbr, text="Min length:").grid(row=0, column=0, sticky=tk.W, **pad)
        ttk.Spinbox(
            abbr, textvariable=self.app.var_min_length, from_=1, to=100, width=6
        ).grid(row=0, column=1, sticky=tk.W, **pad)

        ttk.Label(abbr, text="Max length:").grid(row=0, column=2, sticky=tk.W, **pad)
        ttk.Spinbox(
            abbr, textvariable=self.app.var_max_length, from_=1, to=100, width=6
        ).grid(row=0, column=3, sticky=tk.W, **pad)

        ttk.Label(abbr, text="Superset limit:").grid(
            row=1, column=0, sticky=tk.W, **pad
        )
        ttk.Spinbox(
            abbr, textvariable=self.app.var_superset_limit, from_=1, to=10000, width=6
        ).grid(row=1, column=1, sticky=tk.W, **pad)

        # Flags
        flags = ttk.LabelFrame(parent, text="Flags")
        flags.pack(fill=tk.X, **pad)

        checks = [
            ("Verbose output", self.app.var_verbose),
            ("Slice texts between banks", self.app.var_slice_texts),
            ("Trim unused interpreter code", self.app.var_trim_interpreter),
            ("Show generated bytecode", self.app.var_show_bytecode),
            ("Use WYZ Tracker (instead of Vortex)", self.app.var_use_wyz),
            ("Use 720 KB disk images (+3 only)", self.app.var_disk_720),
        ]
        for i, (text, var) in enumerate(checks):
            ttk.Checkbutton(flags, text=text, variable=var).grid(
                row=i // 2, column=i % 2, sticky=tk.W, **pad
            )

        # Pause after load
        pause_frame = ttk.LabelFrame(parent, text="Pause After Load")
        pause_frame.pack(fill=tk.X, **pad)
        ttk.Label(pause_frame, text="Seconds (empty = no pause):").grid(
            row=0, column=0, sticky=tk.W, **pad
        )
        ttk.Entry(
            pause_frame, textvariable=self.app.var_pause_after_load, width=8
        ).grid(row=0, column=1, sticky=tk.W, **pad)

    # ── Post‑build tab ────────────────────────────────────────────────────

    def _build_post_tab(self, parent):
        pad = {"padx": 6, "pady": 3}

        emu_frame = ttk.LabelFrame(parent, text="Run Emulator After Compilation")
        emu_frame.pack(fill=tk.X, **pad)
        for val, label in [
            ("none", "Do nothing"),
            ("internal", "Internal (Zesarux in ./tools/zesarux/)"),
            ("default", "System default application"),
        ]:
            ttk.Radiobutton(
                emu_frame,
                text=label,
                variable=self.app.var_run_emulator,
                value=val,
            ).pack(anchor=tk.W, **pad)

        bkp_frame = ttk.LabelFrame(parent, text="Backup")
        bkp_frame.pack(fill=tk.X, **pad)
        ttk.Checkbutton(
            bkp_frame,
            text="Backup .cyd file after successful compilation (to ./BACKUP/)",
            variable=self.app.var_backup_cyd,
        ).pack(anchor=tk.W, **pad)

    # ── Browse helpers ─────────────────────────────────────────────────────

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
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
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
        self.var_show_bytecode = tk.BooleanVar()
        self.var_use_wyz = tk.BooleanVar()
        self.var_disk_720 = tk.BooleanVar()
        self.var_pause_after_load = tk.StringVar()
        self.var_run_emulator = tk.StringVar()
        self.var_backup_cyd = tk.BooleanVar()

        # Set defaults first, then override with saved settings
        self._set_defaults()
        self._load_settings()

        self._build_ui()
        self._set_window_icon()

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
        self.var_show_bytecode.set(False)
        self.var_use_wyz.set(False)
        self.var_disk_720.set(False)
        self.var_pause_after_load.set("")
        self.var_run_emulator.set("none")
        self.var_backup_cyd.set(False)

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

        tk.Label(
            title_frame,
            text="Choose Your Destiny",
            font=("Helvetica", 16, "bold"),
            fg="#e0e0e0",
            bg="#1a1a2e",
        ).pack(anchor=tk.W)
        tk.Label(
            title_frame,
            text=f"Adventure Compiler — {PROGRAM_TITLE}",
            font=("Helvetica", 9),
            fg="#8888aa",
            bg="#1a1a2e",
        ).pack(anchor=tk.W)

        # ── Main settings area ─────────────────────────────────────────────
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        pad = {"padx": 6, "pady": 4}
        project_frame = ttk.LabelFrame(main_frame, text="Project")
        project_frame.pack(fill=tk.X, **pad)

        # Game name
        r = 0
        ttk.Label(project_frame, text="Game name:").grid(
            row=r, column=0, sticky=tk.W, **pad
        )
        ttk.Entry(project_frame, textvariable=self.var_game_name, width=25).grid(
            row=r, column=1, sticky=tk.W, **pad
        )
        ttk.Label(
            project_frame,
            text="(the .cyd file must match this name)",
            foreground="gray",
        ).grid(row=r, column=2, sticky=tk.W, **pad)

        # Target
        r += 1
        ttk.Label(project_frame, text="Target:").grid(
            row=r, column=0, sticky=tk.W, **pad
        )
        target_frame = ttk.Frame(project_frame)
        target_frame.grid(row=r, column=1, columnspan=2, sticky=tk.W, **pad)
        for val, label in [
            ("48k", "48K (TAP)"),
            ("128k", "128K (TAP)"),
            ("plus3", "+3 (DSK)"),
        ]:
            ttk.Radiobutton(
                target_frame, text=label, variable=self.var_target, value=val
            ).pack(side=tk.LEFT, padx=(0, 14))

        # ── Buttons row: Configure + Compile ───────────────────────────────
        btn_area = ttk.Frame(self.root)
        btn_area.pack(fill=tk.X, padx=8, pady=(0, 4))

        ttk.Button(
            btn_area,
            text="⚙  Configure…",
            command=self._open_settings,
        ).pack(side=tk.LEFT, padx=(6, 4))

        self.btn_compile = ttk.Button(
            btn_area, text="▶  Compile", command=self._on_compile
        )
        self.btn_compile.pack(side=tk.LEFT, padx=(0, 4))

        self.btn_clear_log = ttk.Button(
            btn_area, text="Clear Log", command=self._clear_log
        )
        self.btn_clear_log.pack(side=tk.LEFT)

        self.progress = ttk.Progressbar(btn_area, mode="indeterminate", length=200)
        self.progress.pack(side=tk.RIGHT, padx=(4, 6))

        # ── Build output log ───────────────────────────────────────────────
        log_frame = ttk.LabelFrame(self.root, text="Build Output")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))

        self.log = scrolledtext.ScrolledText(
            log_frame,
            height=14,
            state=tk.DISABLED,
            wrap=tk.WORD,
            font=("Courier", 9),
        )
        self.log.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

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

    # ── Logging ────────────────────────────────────────────────────────────

    def _log(self, text):
        """Thread‑safe log append."""

        def _append():
            self.log.configure(state=tk.NORMAL)
            self.log.insert(tk.END, text + "\n")
            self.log.see(tk.END)
            self.log.configure(state=tk.DISABLED)

        self.root.after(0, _append)

    def _clear_log(self):
        self.log.configure(state=tk.NORMAL)
        self.log.delete("1.0", tk.END)
        self.log.configure(state=tk.DISABLED)

    # ── Compile logic ──────────────────────────────────────────────────────

    def _on_compile(self):
        """Validate inputs and start compilation in a background thread."""
        if self.compiling:
            return

        # Save settings before compiling (in case of crash)
        self._save_settings()

        # ── Validation ─────────────────────────────────────────────────────
        curr_path = self.paths["curr_path"]
        game_name = self.var_game_name.get().strip()
        if not game_name:
            messagebox.showerror("Error", "Game name cannot be empty.")
            return

        input_file = os.path.join(curr_path, f"{game_name}.cyd")
        if not os.path.isfile(input_file):
            messagebox.showerror(
                "Error", f"Input file does not exist:\n{input_file}"
            )
            return

        sjasmplus = self.var_sjasmplus.get().strip()
        if not os.path.isfile(sjasmplus):
            messagebox.showerror(
                "Error", f"SjASMPlus executable not found:\n{sjasmplus}"
            )
            return

        output_path = self.var_output_path.get().strip()
        if not os.path.isdir(output_path):
            messagebox.showerror(
                "Error", f"Output path does not exist:\n{output_path}"
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
                    "Error",
                    "Pause value must be a non‑negative integer (seconds) "
                    "such that value × 50 < 65536.",
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

        if self.var_verbose.get():
            cydc_params = ["-v"] + cydc_params
        if self.var_slice_texts.get():
            cydc_params = ["-S"] + cydc_params
        if self.var_trim_interpreter.get():
            cydc_params = ["-trim"] + cydc_params
        if self.var_show_bytecode.get():
            cydc_params = ["-code"] + cydc_params
        if pause_val:
            cydc_params = ["-pause", pause_val] + cydc_params
        if self.var_disk_720.get():
            cydc_params = ["-720"] + cydc_params
        if self.var_use_wyz.get():
            cydc_params = ["-wyz"] + cydc_params
        if self.var_image_lines.get():
            cydc_params = ["-il", str(self.var_image_lines.get())] + cydc_params

        cydc_path = self.paths["cydc_path"]
        python_path = self.paths["python_path"]
        model = self.var_target.get()

        cydc_params = [cydc_path] + cydc_params
        cydc_params += [model, input_file, sjasmplus, output_path]

        # ── Launch ─────────────────────────────────────────────────────────
        self.compiling = True
        self.btn_compile.configure(state=tk.DISABLED)
        self.progress.start(15)
        self._log(f"{'─' * 60}")
        self._log(f"Compiling '{game_name}' for {model}…")
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
            ),
            daemon=True,
        )
        thread.start()

    def _compile_thread(
        self, python_path, cydc_params, model, game_name, output_path, input_file
    ):
        """Run the compiler in a background thread."""
        success = False
        try:
            result = run_exec(python_path, cydc_params)
            if result.stdout:
                self._log(result.stdout)
            if result.stderr:
                self._log(result.stderr)
            if result.returncode != 0:
                self._log(f"ERROR: Compiler exited with code {result.returncode}")
            else:
                success = True
                self._log("─────────────────────")
                self._log("Compilation finished successfully!")
        except OSError as exc:
            self._log(f"ERROR running CYDC: {exc}")

        # Plus3 cleanup (mirrors make_adventure.py)
        if success and model == "plus3":
            self._log("Cleaning temporary files…")
            for fname in ["SCRIPT.DAT", "DISK", "CYD.BIN"]:
                p = os.path.join(output_path, fname)
                if os.path.isfile(p):
                    os.remove(p)
                    self._log(f"  Removed {fname}")

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
        self.compiling = False

    # ── Backup ─────────────────────────────────────────────────────────────

    def _do_backup(self, input_file, game_name):
        """Backup the .cyd file, mirroring make_adv.cmd logic."""
        backup_dir = os.path.join(self.paths["curr_path"], "BACKUP")
        os.makedirs(backup_dir, exist_ok=True)
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dst = os.path.join(backup_dir, f"{game_name}_{now}.cyd")
        try:
            shutil.copy2(input_file, dst)
            self._log(f"Backup saved to {dst}")
        except Exception as exc:
            self._log(f"Backup failed: {exc}")

    # ── Emulator launch ───────────────────────────────────────────────────

    def _run_emulator(self, model, game_name, output_path):
        """Launch the compiled file in an emulator, mirroring make_adv.cmd."""
        run_mode = self.var_run_emulator.get()
        if run_mode == "none":
            return

        ext = ".DSK" if model == "plus3" else ".TAP"
        compiled_file = os.path.join(output_path, f"{game_name}{ext}")

        if not os.path.isfile(compiled_file):
            self._log(f"Cannot run emulator – file not found: {compiled_file}")
            return

        if run_mode == "default":
            self._log(f"Opening {compiled_file} with default application…")
            try:
                if os.name == "nt":
                    os.startfile(compiled_file)
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", compiled_file])
                else:
                    subprocess.Popen(["xdg-open", compiled_file])
            except Exception as exc:
                self._log(f"Failed to open file: {exc}")

        elif run_mode == "internal":
            zesarux_dir = os.path.join(self.paths["tools_path"], "zesarux")
            if os.name == "nt":
                zesarux = os.path.join(zesarux_dir, "zesarux.exe")
            else:
                zesarux = os.path.join(zesarux_dir, "zesarux")
            if not os.path.isfile(zesarux):
                self._log(f"Zesarux not found at {zesarux}")
                return

            machine_map = {"plus3": "P341", "128k": "128k", "48k": "48k"}
            zparams = [
                "--noconfigfile",
                "--quickexit",
                "--zoom",
                "2",
                "--realvideo",
                "--nosplash",
                "--forcevisiblehotkeys",
                "--forceconfirmyes",
                "--nowelcomemessage",
                "--cpuspeed",
                "100",
                "--machine",
                machine_map[model],
                compiled_file,
            ]
            self._log(f"Launching Zesarux: {zesarux} {' '.join(zparams)}")
            try:
                subprocess.Popen([zesarux] + zparams, cwd=zesarux_dir)
            except Exception as exc:
                self._log(f"Failed to launch Zesarux: {exc}")


# ── Entry point ────────────────────────────────────────────────────────────────


def main():
    if sys.version_info[0] < 3:
        print("ERROR: Python 3 is required.")
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