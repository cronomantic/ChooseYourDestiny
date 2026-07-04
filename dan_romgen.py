#!/usr/bin/env python3
# ==============================================================================
# dan_romgen.py  --  Build a complete, bootable Dandanator Mini (v9/v10) 512 KB
# ROM image from one or more CYD .MLD games, in pure Python.
#
# Copyright (c) 2025 Sergio Chico
# MIT License (see mld2rom.py header).
#
# This is a faithful, byte-for-byte port of the slot-0 assembly performed by the
# reference Java tool (grelobites/dandanator-mini, DandanatorMiniV9RomSetHandler
# .exportRomSet), so the output is identical to that produced by the official
# tool and therefore boots on real hardware and on emulators (EsPectrum, ...).
#
# The static firmware resources it needs (base ROM, extended charset, PIC
# firmware, slot-1 header, menu background, EEPROM loader, extra ROM) are
# vendored under external/dandanator-mini/. Text compression is ZX7, provided by
# CYD's own vendored pyZX7 (its optimal output is byte-identical to the Java Zx7).
# ==============================================================================
from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

# CYD's vendored pyZX7 (optimal ZX7, byte-identical to the reference Zx7). Its
# location differs between the repository (src/cydc/cydc) and the packaged
# distribution (cydc), so probe the known layouts.
for _cand in (_HERE / "src" / "cydc" / "cydc", _HERE / "cydc", _HERE / "dist" / "cydc"):
    if (_cand / "pyZX7").is_dir():
        sys.path.insert(0, str(_cand))
        break
from pyZX7 import compress as _zx7  # noqa: E402


def _find_res_dir() -> Path:
    """Locate the vendored Dandanator firmware resources.

    Order: the ``CYD_DANDANATOR_RES`` environment variable, then
    ``external/dandanator-mini`` (repository and distribution both ship the
    resources next to this script), then ``dandanator-mini`` as a fallback.
    """
    env = os.environ.get("CYD_DANDANATOR_RES")
    if env:
        return Path(env)
    for cand in (_HERE / "external" / "dandanator-mini", _HERE / "dandanator-mini"):
        if cand.is_dir():
            return cand
    return _HERE / "external" / "dandanator-mini"


RES_DIR = _find_res_dir()

# --- Dandanator v9/v10 layout constants (must match the Java tool) -----------
SLOT_SIZE       = 0x4000
ROM_SLOTS       = 32
ROM_SIZE        = SLOT_SIZE * ROM_SLOTS
GAME_SLOTS      = 30                 # 32 - loader(1) - extra ROM(1)
MAX_GAMES       = 25
GAME_STRUCT_SIZE = 131
GREY_ZONE_OFFSET = 6860              # 3585 + 25*131: start of compressed blocks
VERSION_OFFSET   = 16352
VERSION_SIZE     = 8
CBLOCKS_OFFSET   = 16360
GAMENAME_SIZE    = 33
SLOT1_RESERVED_SIZE = 300
POKE_TARGET_ADDRESS = 25259
MLD_HEADER_OFFSET = 16362            # MLDoffset byte within the footer slot
MLD_TYPE_OFFSET   = 16363
MLD_NSECTORS_OFFSET = 16364
MLD_SECTORS_OFFSET  = 16365          # MLD_HEADER_OFFSET + 3

# ExtendedCharSet symbol code for the game-name icon, keyed by MLD type byte,
# plus the hardware-mode byte written in the game header (HardwareMode.intValue).
_TYPE_INFO = {
    0x83: {"symbol": 130, "hwmode": 0},    # 48K  MLD  -> SYMBOL_48K
    0x88: {"symbol": 128, "hwmode": 4},    # 128K MLD  -> SYMBOL_128K
    0xC8: {"symbol": 136, "hwmode": 13},   # +2A  MLD  -> SYMBOL_PLUS2A
}

# Default menu texts (Spanish locale, matching the reference tool's default).
_TEXT_EXTRAROM     = "Test - ZX Diagnostics"
_TEXT_TOGGLEPOKES  = "Conmutar pokes"
_TEXT_LAUNCHGAME   = "Ejecutar juego"
_TEXT_SELECTPOKES  = "Seleccionar pokes"


def _res(name: str) -> bytes:
    return (RES_DIR / name).read_bytes()


def _zc(data: bytes) -> bytes:
    return bytes(_zx7.compress(bytes(data)))


def _w(v: int) -> bytes:
    return struct.pack("<H", v & 0xFFFF)


def _ntstr(s: str, size: int = GAMENAME_SIZE) -> bytes:
    b = bytearray(size)
    e = s.encode("latin-1", "replace")[: size - 1]
    b[0:len(e)] = e
    return bytes(b)


def _screen_third_section(full_scr: bytes) -> bytes:
    # First 2048 pixel bytes + first 256 attribute bytes, in a 6912-byte buffer.
    scr = bytearray(6912)
    scr[0:2048] = full_scr[0:2048]
    scr[6144:6144 + 256] = full_scr[6144:6144 + 256]
    return bytes(scr)


def build_dandanator_rom(games, names=None, autoboot=False):
    """Build a full 512 KB Dandanator Mini ROM from a list of MLD games.

    Each game is a dict with keys: 'data' (raw .MLD bytes), 'num_slots',
    'mld_type', 'header_slot', and optionally 'display_name'.
    Returns the 512 KB ROM as bytes.
    """
    names = names or []
    if not games:
        raise ValueError("No MLD games to pack.")
    total_slots = sum(g["num_slots"] for g in games)
    if len(games) > MAX_GAMES:
        raise ValueError(f"Too many games ({len(games)} > {MAX_GAMES}).")
    if total_slots > GAME_SLOTS:
        raise ValueError(f"Games need {total_slots} slots; only {GAME_SLOTS} available.")

    # ---- compressed slot-0 blocks (all config-default, game-independent) -----
    b_screen = _zc(_screen_third_section(_res("menu.scr")))
    b_texts = _zc(
        _ntstr(f"R. {_TEXT_EXTRAROM}") + _ntstr(f"P. {_TEXT_TOGGLEPOKES}")
        + _ntstr(f"0. {_TEXT_LAUNCHGAME}") + _ntstr(_TEXT_SELECTPOKES)
    )
    base_poke = POKE_TARGET_ADDRESS + MAX_GAMES * 3
    poke_data = bytearray()
    poke_data += bytes(len(games))                       # poke count per game (0 for MLD)
    poke_data += bytes(MAX_GAMES - len(games))
    for _ in games:
        poke_data += _w(base_poke)                       # base poke address (no pokes)
    poke_data += bytes((MAX_GAMES - len(games)) * 2)
    b_poke = _zc(bytes(poke_data))
    b_charfw = _zc(_res("extcharset.bin") + b"DNTRMFW-Up" + _res("pic-fw.bin"))
    b_ee_scr = _zc(_res("eeprom-screen.scr"))
    b_ee_code = _zc(_res("eeprom-loader.bin"))

    # ---- patch each MLD footer (reallocate + allocateSaveSpace) --------------
    # Games are laid out from the top (slot 30) downward, game[0] highest.
    game_slot = {}
    cursor = GAME_SLOTS + 1        # 31: slot index growing down
    for gi, g in enumerate(games):
        start_slot = cursor - g["num_slots"]
        game_slot[gi] = start_slot
        cursor = start_slot
    # Save sectors use a SINGLE global counter that starts at the lowest slot and
    # decrements as games are dumped in reverse order (matching the Java tool's
    # threaded lastMldSaveSector), NOT a per-game 4*slot-1.
    sector_counter = (4 * (GAME_SLOTS + 1 - total_slots)) - 1
    sector_base = {}
    for gi in reversed(range(len(games))):
        sector_base[gi] = sector_counter
        sector_counter -= games[gi]["data"][MLD_NSECTORS_OFFSET]
    for gi, g in enumerate(games):
        data = bytearray(g["data"])
        data[MLD_HEADER_OFFSET] = game_slot[gi] & 0xFF    # MLDoffset (reallocate)
        nsectors = data[MLD_NSECTORS_OFFSET]
        base = sector_base[gi]                            # allocateSaveSpace
        for i in range(nsectors):
            data[MLD_SECTORS_OFFSET + i] = (base - i) & 0xFF
        g["_patched"] = bytes(data)

    # ---- game headers --------------------------------------------------------
    def game_header(gi, g, chunk_addr):
        info = _TYPE_INFO.get(g["mld_type"], {"symbol": 32, "hwmode": 0})
        sym = info["symbol"]
        name = names[gi] if gi < len(names) else g.get("display_name", "GAME")
        h = bytearray()
        h += bytes(31)                                            # SNA header
        h += _ntstr("%1d%c%c%s" % ((gi + 1) % 10, sym, sym + 1, name))
        h += bytes([info["hwmode"]])                             # hw mode
        h += bytes([0])                                          # compressed = 0
        h += bytes([g["mld_type"]])                              # type id
        h += bytes([0])                                          # screen hold
        h += bytes([0])                                          # active rom slot
        h += bytes(18)                                           # launch code
        h += _w(chunk_addr) + _w(0)                              # game chunk addr/len (0 for MLD)
        # CBlocks: [startSlot][0000][reportedSlots] padded to 40 with 0xFF
        mcb = bytes([game_slot[gi]]) + _w(0) + _w(g["num_slots"])
        h += mcb + bytes([0xFF] * (40 - len(mcb)))
        return bytes(h)

    # compressed-block offsets within slot 0
    off = GREY_ZONE_OFFSET
    scr_o = off; off += len(b_screen)
    txt_o = off; off += len(b_texts)
    pk_o = off; off += len(b_poke)
    cf_o = off; off += len(b_charfw)
    chunk_addr = off        # game chunks (empty for MLD) start here

    # ---- slot 0 --------------------------------------------------------------
    s0 = bytearray()
    s0 += _res("baserom.bin")                                    # 3584
    s0 += bytes([len(games)])                                    # game count
    for gi, g in enumerate(games):
        s0 += game_header(gi, g, chunk_addr)
    s0 += bytes(GAME_STRUCT_SIZE * (MAX_GAMES - len(games)))     # fill to 25 games
    s0 += b_screen + b_texts + b_poke + b_charfw                 # compressed blocks
    # game chunks: MLD games have empty chunks -> nothing
    ee_scr_loc = len(s0); s0 += b_ee_scr
    ee_code_loc = len(s0); s0 += b_ee_code
    if len(s0) > VERSION_OFFSET:
        raise ValueError("Slot 0 overflow (too much data in the menu zone).")
    s0 += bytes(VERSION_OFFSET - len(s0))                        # fill to version
    s0 += _ntstr("v10.4.3", VERSION_SIZE)                        # version info
    s0 += (_w(scr_o) + _w(len(b_screen)) + _w(txt_o) + _w(len(b_texts))
           + _w(pk_o) + _w(len(b_poke)) + _w(cf_o) + _w(len(b_charfw))
           + _w(ee_scr_loc) + _w(ee_code_loc))                  # CBlocks table @16360
    s0 += bytes([0])                                            # border effect
    s0 += bytes([1 if autoboot else 0])                        # autoboot
    s0 += bytes([0xFF])                                         # dansnap MLD type (none)
    s0 += bytes([2])                                            # pause mark (MLD)
    assert len(s0) == SLOT_SIZE, f"slot0 length {len(s0)}"

    # ---- full ROM ------------------------------------------------------------
    rom = bytearray()
    rom += s0
    rom += _res("slot1.bin")                                     # slot 1 header (300)
    unc_off = SLOT_SIZE * (GAME_SLOTS + 1) - total_slots * SLOT_SIZE
    rom += bytes([0xFF] * (unc_off - len(rom)))                  # gap to game data
    # Game data is dumped in REVERSE order (game[n-1] lowest slot first), so that
    # game[0] ends up in the highest slots -- matching the Java tool.
    for gi in reversed(range(len(games))):
        rom += games[gi]["_patched"]
    rom += _res("extra.rom")                                     # extra ROM (slot 31)
    assert len(rom) == ROM_SIZE, f"rom length {len(rom)}"
    return bytes(rom)
