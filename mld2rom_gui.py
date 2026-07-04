#!/usr/bin/env python3
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
"""Standalone GUI to build a bootable Dandanator Mini ROM from CYD .MLD files.

This is a small front-end over dan_romgen (pure-Python Dandanator ROM
assembler). It packs one or more CYD-generated .MLD games into a complete,
bootable 512 KB Dandanator Mini ROM, exposing the menu options that matter for
authoring: the game name(s), the menu font, the menu background screen, the
four menu texts, the border effect and autoboot.

It deliberately does NOT include the transfer/flashing features of the official
tool (serial port, etc.): it just writes the .rom/.bin file, which can then be
loaded in an emulator (ZEsarUX --dandanator-rom, EsPectrum) or flashed with the
user's own tool. Pure Python (tkinter), no external dependencies.
"""
from __future__ import annotations

import os
import sys
import threading

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

_HERE = os.path.abspath(os.path.dirname(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# Internationalisation (optional: fall back to identity if unavailable).
try:
    from cydc.cyd_i18n import setup_i18n, _
except ImportError:
    try:
        sys.path.insert(0, os.path.join(_HERE, "dist"))
        from cydc.cyd_i18n import setup_i18n, _
    except ImportError:
        def setup_i18n(*_a, **_k):
            pass

        def _(s):
            return s

setup_i18n("mld2rom_gui", locale_dir=os.path.join(_HERE, "locale"))

import dan_romgen  # noqa: E402  (pure-Python Dandanator ROM assembler)
import mld2rom      # noqa: E402  (MLD parsing + validation)

VERSION = "1.0.0"
TITLE = "CYD Dandanator ROM Builder " + VERSION

SLOT_SIZE = 0x4000
GAME_SLOTS = dan_romgen.GAME_SLOTS
SCR_SIZE = 6912


def _human_type(mld_type: int) -> str:
    return {0x83: "48K", 0x88: "128K", 0xC8: "+2A"}.get(mld_type, f"0x{mld_type:02X}")


class RomBuilderApp:
    """The main window: a game list plus menu/build options."""

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(TITLE)
        root.minsize(720, 620)

        # Model: one dict per game (path, data, num_slots, mld_type, header_slot, name)
        self.games: list[dict] = []
        self._building = False

        # Option variables
        self.var_charset = tk.StringVar()
        self.var_background = tk.StringVar()
        self.var_output = tk.StringVar()
        self.var_autoboot = tk.BooleanVar(value=False)
        self.var_disable_border = tk.BooleanVar(value=False)
        self.var_name = tk.StringVar()
        self.var_txt_extrarom = tk.StringVar(value=dan_romgen._TEXT_EXTRAROM)
        self.var_txt_toggle = tk.StringVar(value=dan_romgen._TEXT_TOGGLEPOKES)
        self.var_txt_launch = tk.StringVar(value=dan_romgen._TEXT_LAUNCHGAME)
        self.var_txt_select = tk.StringVar(value=dan_romgen._TEXT_SELECTPOKES)

        self._build_ui()

    # ---------------------------------------------------------------- UI ----
    def _build_ui(self):
        pad = dict(padx=6, pady=4)
        main = ttk.Frame(self.root)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # ---- Games list ----------------------------------------------------
        games_f = ttk.LabelFrame(main, text=_("Games (.MLD)"))
        games_f.pack(fill=tk.BOTH, expand=True, **pad)

        cols = ("name", "type", "slots")
        self.tree = ttk.Treeview(games_f, columns=cols, show="tree headings", height=6)
        self.tree.heading("#0", text=_("File"))
        self.tree.heading("name", text=_("Name"))
        self.tree.heading("type", text=_("Type"))
        self.tree.heading("slots", text=_("Slots"))
        self.tree.column("#0", width=280, anchor=tk.W)
        self.tree.column("name", width=180, anchor=tk.W)
        self.tree.column("type", width=60, anchor=tk.CENTER)
        self.tree.column("slots", width=50, anchor=tk.CENTER)
        self.tree.grid(row=0, column=0, rowspan=5, sticky=tk.NSEW, **pad)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_game)
        games_f.columnconfigure(0, weight=1)
        games_f.rowconfigure(4, weight=1)

        ttk.Button(games_f, text=_("Add…"), command=self._add_games).grid(
            row=0, column=1, sticky=tk.EW, **pad)
        ttk.Button(games_f, text=_("Remove"), command=self._remove_game).grid(
            row=1, column=1, sticky=tk.EW, **pad)
        ttk.Button(games_f, text=_("Up"), command=lambda: self._move(-1)).grid(
            row=2, column=1, sticky=tk.EW, **pad)
        ttk.Button(games_f, text=_("Down"), command=lambda: self._move(1)).grid(
            row=3, column=1, sticky=tk.EW, **pad)

        name_row = ttk.Frame(games_f)
        name_row.grid(row=5, column=0, columnspan=2, sticky=tk.EW, **pad)
        ttk.Label(name_row, text=_("Selected game name:")).pack(side=tk.LEFT)
        name_entry = ttk.Entry(name_row, textvariable=self.var_name)
        name_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        self.var_name.trace_add("write", self._on_name_edit)

        # ---- Menu options --------------------------------------------------
        opt_f = ttk.LabelFrame(main, text=_("Menu options"))
        opt_f.pack(fill=tk.X, **pad)
        opt_f.columnconfigure(1, weight=1)

        self._file_row(opt_f, 0, _("Font (charset, 768/896 B):"),
                       self.var_charset, self._browse_charset, _("default"))
        self._file_row(opt_f, 1, _("Menu background (.scr, 6912 B):"),
                       self.var_background, self._browse_background, _("default"))

        ttk.Label(opt_f, text=_("Extra-ROM text:")).grid(row=2, column=0, sticky=tk.W, **pad)
        ttk.Entry(opt_f, textvariable=self.var_txt_extrarom).grid(
            row=2, column=1, columnspan=2, sticky=tk.EW, **pad)
        ttk.Label(opt_f, text=_("Toggle-pokes text:")).grid(row=3, column=0, sticky=tk.W, **pad)
        ttk.Entry(opt_f, textvariable=self.var_txt_toggle).grid(
            row=3, column=1, columnspan=2, sticky=tk.EW, **pad)
        ttk.Label(opt_f, text=_("Launch-game text:")).grid(row=4, column=0, sticky=tk.W, **pad)
        ttk.Entry(opt_f, textvariable=self.var_txt_launch).grid(
            row=4, column=1, columnspan=2, sticky=tk.EW, **pad)
        ttk.Label(opt_f, text=_("Select-pokes text:")).grid(row=5, column=0, sticky=tk.W, **pad)
        ttk.Entry(opt_f, textvariable=self.var_txt_select).grid(
            row=5, column=1, columnspan=2, sticky=tk.EW, **pad)

        checks = ttk.Frame(opt_f)
        checks.grid(row=6, column=0, columnspan=3, sticky=tk.W, **pad)
        ttk.Checkbutton(checks, text=_("Autoboot (launch first game, skip menu)"),
                        variable=self.var_autoboot).pack(side=tk.LEFT, padx=(0, 16))
        ttk.Checkbutton(checks, text=_("Disable border effect"),
                        variable=self.var_disable_border).pack(side=tk.LEFT)

        # ---- Output --------------------------------------------------------
        out_f = ttk.LabelFrame(main, text=_("Output ROM"))
        out_f.pack(fill=tk.X, **pad)
        out_f.columnconfigure(1, weight=1)
        self._file_row(out_f, 0, _("ROM file:"), self.var_output,
                       self._browse_output, _("(required)"), save=True)

        # ---- Build + log ---------------------------------------------------
        act = ttk.Frame(main)
        act.pack(fill=tk.X, **pad)
        self.build_btn = ttk.Button(act, text=_("Generate ROM"), command=self._generate)
        self.build_btn.pack(side=tk.LEFT)
        self.status = ttk.Label(act, text="")
        self.status.pack(side=tk.LEFT, padx=12)

        self.log = scrolledtext.ScrolledText(main, height=8, state=tk.DISABLED, wrap=tk.WORD)
        self.log.pack(fill=tk.BOTH, expand=True, **pad)

    def _file_row(self, parent, row, label, var, browse, hint, save=False):
        pad = dict(padx=6, pady=4)
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W, **pad)
        e = ttk.Entry(parent, textvariable=var)
        e.grid(row=row, column=1, sticky=tk.EW, **pad)
        if hint:
            e.insert(0, "")
        ttk.Button(parent, text=_("Browse…"), command=browse).grid(
            row=row, column=2, sticky=tk.EW, **pad)

    # ------------------------------------------------------------ logging ---
    def _write_log(self, text):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.log.configure(state=tk.DISABLED)

    def _set_status(self, text):
        self.status.configure(text=text)

    # -------------------------------------------------------- game list ----
    def _add_games(self):
        paths = filedialog.askopenfilenames(
            title=_("Select MLD file(s)"),
            filetypes=[(_("Dandanator MLD"), "*.MLD *.mld"), (_("All files"), "*.*")],
        )
        for p in paths:
            self._add_one(p)

    def _add_one(self, path):
        try:
            raw = open(path, "rb").read()
            info = mld2rom.parse_mld(raw, path)
        except Exception as exc:  # parse/read error
            self._write_log(_("ERROR loading {}: {}").format(os.path.basename(path), exc))
            return
        # Surface validation issues (non-fatal for INFO/WARNING).
        issues = mld2rom.validate_mld_file(raw, path)
        blocking = [m for s, m in issues if s in (mld2rom.SEV_CRITICAL, mld2rom.SEV_ERROR)]
        for sev, msg in issues:
            if sev in (mld2rom.SEV_CRITICAL, mld2rom.SEV_ERROR):
                self._write_log(f"  [{sev}] {os.path.basename(path)}: {msg}")
        if blocking:
            self._write_log(_("Not added (validation errors): {}").format(os.path.basename(path)))
            return
        game = {
            "path": path,
            "data": bytes(raw),
            "num_slots": info["num_slots"],
            "mld_type": info["mld_type"],
            "header_slot": info["header_slot"],
            "name": os.path.splitext(os.path.basename(path))[0],
        }
        self.games.append(game)
        self._refresh_tree()
        if not self.var_output.get():
            self.var_output.set(os.path.splitext(path)[0] + ".rom")
        self._write_log(_("Added {} ({}, {} slot(s)).").format(
            os.path.basename(path), _human_type(game["mld_type"]), game["num_slots"]))

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        total = 0
        for i, g in enumerate(self.games):
            total += g["num_slots"]
            self.tree.insert("", tk.END, iid=str(i),
                             text=os.path.basename(g["path"]),
                             values=(g["name"], _human_type(g["mld_type"]), g["num_slots"]))
        self._set_status(_("{} game(s), {}/{} slots").format(len(self.games), total, GAME_SLOTS))

    def _selected_index(self):
        sel = self.tree.selection()
        return int(sel[0]) if sel else None

    def _on_select_game(self, _evt=None):
        idx = self._selected_index()
        if idx is not None:
            # Update the name entry without triggering an edit write-back loop.
            self._loading_name = True
            self.var_name.set(self.games[idx]["name"])
            self._loading_name = False

    def _on_name_edit(self, *_a):
        if getattr(self, "_loading_name", False):
            return
        idx = self._selected_index()
        if idx is not None:
            self.games[idx]["name"] = self.var_name.get()
            self.tree.set(str(idx), "name", self.var_name.get())

    def _remove_game(self):
        idx = self._selected_index()
        if idx is None:
            return
        del self.games[idx]
        self._refresh_tree()

    def _move(self, delta):
        idx = self._selected_index()
        if idx is None:
            return
        j = idx + delta
        if 0 <= j < len(self.games):
            self.games[idx], self.games[j] = self.games[j], self.games[idx]
            self._refresh_tree()
            self.tree.selection_set(str(j))

    # ------------------------------------------------------------ browse ---
    def _browse_charset(self):
        p = filedialog.askopenfilename(
            title=_("Select font / charset"),
            filetypes=[(_("Charset"), "*.bin *.ch8 *.rom *.chr"), (_("All files"), "*.*")])
        if p:
            self.var_charset.set(p)

    def _browse_background(self):
        p = filedialog.askopenfilename(
            title=_("Select menu background"),
            filetypes=[(_("ZX screen"), "*.scr"), (_("All files"), "*.*")])
        if p:
            self.var_background.set(p)

    def _browse_output(self):
        p = filedialog.asksaveasfilename(
            title=_("Save ROM as"), defaultextension=".rom",
            filetypes=[(_("Dandanator ROM"), "*.rom *.bin"), (_("All files"), "*.*")])
        if p:
            self.var_output.set(p)

    # ----------------------------------------------------------- build -----
    def _read_optional(self, path, expected_lens, label):
        """Read an optional resource file, validating its length. Returns bytes
        or None (no override). Raises ValueError on a bad length."""
        path = path.strip()
        if not path:
            return None
        data = open(path, "rb").read()
        if expected_lens and len(data) not in expected_lens:
            raise ValueError(_("{} must be {} bytes, got {}").format(
                label, " or ".join(str(x) for x in expected_lens), len(data)))
        return data

    def _generate(self):
        if self._building:
            return
        if not self.games:
            messagebox.showwarning(TITLE, _("Add at least one MLD game."))
            return
        out = self.var_output.get().strip()
        if not out:
            messagebox.showwarning(TITLE, _("Choose an output ROM file."))
            return
        total = sum(g["num_slots"] for g in self.games)
        if total > GAME_SLOTS:
            messagebox.showerror(TITLE, _("Games need {} slots; only {} available.").format(
                total, GAME_SLOTS))
            return
        try:
            charset = self._read_optional(self.var_charset.get(), (768, 896), _("Charset"))
            background = self._read_optional(self.var_background.get(), (SCR_SIZE,),
                                             _("Background"))
        except (OSError, ValueError) as exc:
            messagebox.showerror(TITLE, str(exc))
            return

        params = dict(
            games=[{
                "data": g["data"], "num_slots": g["num_slots"],
                "mld_type": g["mld_type"], "header_slot": g["header_slot"],
                "display_name": g["name"],
            } for g in self.games],
            names=[g["name"] for g in self.games],
            autoboot=self.var_autoboot.get(),
            charset=charset,
            background_scr=background,
            text_extrarom=self.var_txt_extrarom.get(),
            text_togglepokes=self.var_txt_toggle.get(),
            text_launchgame=self.var_txt_launch.get(),
            text_selectpokes=self.var_txt_select.get(),
            disable_border=self.var_disable_border.get(),
        )

        self._building = True
        self.build_btn.configure(state=tk.DISABLED)
        self._set_status(_("Generating… (this can take a while)"))
        self._write_log(_("Building ROM: {}").format(out))
        threading.Thread(target=self._build_worker, args=(params, out), daemon=True).start()

    def _build_worker(self, params, out):
        try:
            rom = dan_romgen.build_dandanator_rom(**params)
            with open(out, "wb") as fh:
                fh.write(rom)
            self.root.after(0, self._build_done, out, len(rom), None)
        except Exception as exc:  # keep the UI alive on any build error
            self.root.after(0, self._build_done, out, 0, exc)

    def _build_done(self, out, size, error):
        self._building = False
        self.build_btn.configure(state=tk.NORMAL)
        if error is not None:
            self._set_status(_("Failed."))
            self._write_log(_("ERROR: {}").format(error))
            messagebox.showerror(TITLE, _("Could not build the ROM:\n{}").format(error))
            return
        self._set_status(_("Done."))
        self._write_log(_("ROM written: {} ({} bytes).").format(out, size))
        messagebox.showinfo(TITLE, _("ROM generated:\n{}").format(out))


def main():
    root = tk.Tk()
    RomBuilderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
