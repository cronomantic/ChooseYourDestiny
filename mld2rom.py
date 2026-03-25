#!/usr/bin/env python3
# ==============================================================================
# mld2rom.py  —  Pack CYD-generated MLD files into a Dandanator Mini ROM image
# ==============================================================================
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
# ==============================================================================
#
# SYNOPSIS
#   python mld2rom.py --base-rom dandanator.rom [OPTIONS] game.mld [game2.mld ...]
#
# PURPOSE
#   Embeds one or more .MLD files (produced by the CYD compiler for Dandanator
#   targets) into a Dandanator Mini ROM image that can be loaded directly in an
#   emulator such as ZEsarUX (--machine dandanator).
#
#   The tool patches each MLD file's "MLDoffset" byte in its slot-0 footer so
#   the Dandanator runtime can locate its own slots within the ROM, then writes
#   the updated game metadata to slot 0 of the output ROM.
#
# BASE ROM
#   A Dandanator ROM template is required.  Two formats are accepted:
#
#   • Full 512 KB ROM (524 288 bytes) — already fully initialised:
#       - Export from the dandanator-mini Java GUI with zero games loaded.
#       - Extract from the distributed JAR:
#           jar xf dandanator-mini-<version>.jar dandanator-mini/dandanator-mini.rom
#       - Download a release ROM from https://github.com/cronomantic/dandanator-mini
#
#   • Raw firmware file (3 584 bytes) — automatically zero-padded to 512 KB:
#       - Download dandanator-mini.rom directly from the GitHub source tree:
#           https://github.com/cronomantic/dandanator-mini/blob/master/src/main/resources/dandanator-mini/dandanator-mini.rom
#       This produces a valid empty-template ROM (0 games, empty slots).
#
# USAGE
#   mld2rom.py [-h] -b BASE_ROM [-o OUTPUT] [-a] [-v] game.mld [game2.mld ...]
#
# OPTIONS
#   -b / --base-rom FILE   512 KB Dandanator ROM template (required).
#   -o / --output FILE     Output ROM path (default: base ROM path stem + '.out.rom').
#   -n / --name TEXT       Game name override (for single-game invocations).
#   -a / --autoboot        Set the Dandanator autoboot flag so the first game
#                          starts immediately without the menu.
#   -v / --verbose         Print progress information.
#
# EXAMPLES
#   # Embed one MLD into a clean ROM template:
#   python mld2rom.py -b dandanator.rom -o test.rom my_adventure.mld
#
#   # Embed two MLD games and enable autoboot:
#   python mld2rom.py -b clean.rom -o cart.rom -a game1.mld game2.mld
#
# ==============================================================================

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Dandanator Mini ROM layout constants (firmware version 9/10)
# These must match the Java dandanator-mini constants exactly.
# ---------------------------------------------------------------------------

SLOT_SIZE = 0x4000          # 16 384 bytes per Dandanator slot
ROM_SLOTS = 32              # Total slots in a 512 KB ROM
ROM_SIZE = SLOT_SIZE * ROM_SLOTS  # 524 288 bytes

# Slot 0 structure (all offsets are byte positions within the ROM image):
BASEROM_SIZE = 3584         # Firmware code at the very start of slot 0
GAME_COUNT_OFFSET = 3584    # 1 byte: number of games currently in the ROM
GAME_STRUCT_BASE = 3585     # Game-struct array starts at 3585
GAME_STRUCT_SIZE = 131      # Bytes per game entry
MAX_GAMES = 25              # Hard limit: 25 games per cartridge

# Slot 31 = extra/test ROM (last 16 KB of the ROM image)
EXTRA_ROM_SLOT = 31
# Uncompressed games (MLD etc.) occupy slots just below slot 31, growing
# backwards as more games are added.
UNCOMPRESSED_TOP_SLOT = 30  # highest slot available for (uncompressed) game data

# Within each 131-byte game struct, field byte offsets:
_GS_SNA_HEADER   = 0        # 31 bytes (zeros for MLD)
_GS_GAMENAME     = 31       # 33 bytes, null-terminated
_GS_HW_MODE      = 64       # 1 byte  (0 for MLD)
_GS_COMPRESSED   = 65       # 1 byte  (0 = uncompressed)
_GS_TYPE_ID      = 66       # 1 byte  (0x83 = 48 K MLD, 0x88 = 128 K MLD)
_GS_SCREEN_HOLD  = 67       # 1 byte  (0)
_GS_ACTIVE_ROM   = 68       # 1 byte  (0 for MLD)
_GS_LAUNCH_CODE  = 69       # 18 bytes (zeros for MLD)
_GS_CHUNK_ADDR   = 87       # 2 bytes LE word
_GS_CHUNK_SIZE   = 89       # 2 bytes LE word
_GS_CBLOCKS      = 91       # 40 bytes: first 5 = MLD slot entry, rest 0xFF
GAMENAME_SIZE    = 33

# MLD footer (relative to the START of an MLD slot that carries the footer,
# i.e. MLD slot 0 in our CYD design).
MLD_HEADER_OFFSET    = 16362  # first byte of the footer within the slot
MLD_TYPE_OFFSET      = MLD_HEADER_OFFSET + 1
MLD_SIGNATURE_OFFSET = 16380
MLD_SIGNATURE        = b"MLD"

# MLD type IDs (must match GameType.java and our loadermld.asm $MLD_TYPE values)
MLD_TYPE_48K    = 0x83
MLD_TYPE_128K   = 0x88
MLD_TYPE_PLUS2A = 0xC8

# All GameType.java type IDs recognised by dandanator-mini.
KNOWN_MLD_TYPES: dict[int, str] = {
    0x83: "48K MLD",
    0x88: "128K MLD",
    0xC3: "DAN-SNAP",
    0xC8: "DAN-SNAP-128",
    0xC1: "DAN-SNAP-16",
    0x8B: "TAP",
}

# Slot 0 tail: these byte offsets are within slot 0 (= within the ROM image)
AUTOBOOT_OFFSET = 16381     # 1 byte: 0 = show menu, 1 = boot game 0 directly

# ---------------------------------------------------------------------------
# MLD footer field byte offsets (relative to MLD_HEADER_OFFSET inside a slot)
# Source: MLDInfo.fromGameSlotByteArray() in dandanator-mini
# ---------------------------------------------------------------------------
_FO_BASE_SLOT    =  0  # uint8  – original game base slot (MLDoffset)
_FO_MLD_TYPE     =  1  # uint8  – game type (0x83/0x88/…)
_FO_REQ_SECTORS  =  2  # uint8  – number of save-state sectors reserved
_FO_SECTOR_IDS   =  3  # 4 × uint8 – sector IDs (patched by dandanator-mini at ROM build)
_FO_TABLE_OFFSET =  7  # uint16 LE – byte offset of the slot-ID table within the MLD
_FO_TABLE_ROWSZ  =  9  # uint16 LE – bytes per table row
_FO_TABLE_ROWS   = 11  # uint16 LE – number of rows
_FO_ROW_SLOT_OFF = 13  # uint8  – byte offset of the slot-ID byte within each row
_FO_SCR_OFFSET   = 14  # uint16 LE – preview-screen offset within this slot
_FO_SCR_SIZE     = 16  # uint16 LE – preview-screen compressed size
_FO_SIGNATURE    = 18  # 3 bytes  – must be b"MLD"
_FO_NULL_TERM    = 21  # uint8  – must be 0x00

# Defect severity levels (aligned with dandanator-mini error categories)
SEV_CRITICAL = "CRITICAL"  # File cannot be loaded at all
SEV_ERROR    = "ERROR"     # Spec violation; runtime behaviour is undefined
SEV_WARNING  = "WARNING"   # Deviation from expected values; may still work
SEV_INFO     = "INFO"      # Informational note about a spec difference


# ---------------------------------------------------------------------------
# MLD parsing
# ---------------------------------------------------------------------------

class MLDParseError(Exception):
    pass


def _read_footer(data: bytes, header_slot: int) -> dict:
    """Read all 22 bytes of the MLD footer into a structured dict.

    Keys map 1-to-1 to MLDInfo fields in dandanator-mini's MLDInfo.java.
    """
    base = header_slot * SLOT_SIZE + MLD_HEADER_OFFSET
    return {
        "base_slot":      data[base + _FO_BASE_SLOT],
        "mld_type":       data[base + _FO_MLD_TYPE],
        "req_sectors":    data[base + _FO_REQ_SECTORS],
        "sector_ids":     list(data[base + _FO_SECTOR_IDS : base + _FO_SECTOR_IDS + 4]),
        "table_offset":   struct.unpack_from("<H", data, base + _FO_TABLE_OFFSET)[0],
        "table_row_size": struct.unpack_from("<H", data, base + _FO_TABLE_ROWSZ)[0],
        "table_rows":     struct.unpack_from("<H", data, base + _FO_TABLE_ROWS)[0],
        "row_slot_off":   data[base + _FO_ROW_SLOT_OFF],
        "screen_offset":  struct.unpack_from("<H", data, base + _FO_SCR_OFFSET)[0],
        "screen_size":    struct.unpack_from("<H", data, base + _FO_SCR_SIZE)[0],
        "signature":      data[base + _FO_SIGNATURE : base + _FO_SIGNATURE + 3],
        "null_term":      data[base + _FO_NULL_TERM],
    }


def validate_mld_file(data: bytes, path: str) -> list[tuple[str, str]]:
    """Validate an MLD binary against the dandanator-mini specification.

    Returns a list of (severity, message) tuples.  Severity is one of
    SEV_CRITICAL / SEV_ERROR / SEV_WARNING / SEV_INFO.

    The checks follow MLDInfo.fromGameSlotByteArray() and MLDGame.reallocate()
    from dandanator-mini, treating the CYD project output as the test subject.
    """
    issues: list[tuple[str, str]] = []

    def issue(sev: str, msg: str) -> None:
        issues.append((sev, msg))

    # ── 1. File size ─────────────────────────────────────────────────────────
    if len(data) == 0:
        issue(SEV_CRITICAL, "Empty file.")
        return issues

    num_slots, remainder = divmod(len(data), SLOT_SIZE)
    if remainder != 0:
        issue(
            SEV_CRITICAL,
            f"File size {len(data)} B is not a multiple of SLOT_SIZE ({SLOT_SIZE}). "
            f"The file is likely truncated or corrupted.",
        )
    num_slots = len(data) // SLOT_SIZE  # continue with what we have
    if num_slots == 0:
        issue(SEV_CRITICAL, "File is shorter than one 16 KB slot; cannot parse.")
        return issues

    # ── 2. MLD signature ─────────────────────────────────────────────────────
    header_slot = None
    for s in range(num_slots):
        base = s * SLOT_SIZE
        if data[base + MLD_SIGNATURE_OFFSET : base + MLD_SIGNATURE_OFFSET + 3] == MLD_SIGNATURE:
            header_slot = s
            break

    if header_slot is None:
        issue(
            SEV_CRITICAL,
            f'Signature "MLD" not found at offset {MLD_SIGNATURE_OFFSET} '
            f"in any of the {num_slots} slot(s). "
            f"dandanator-mini will reject this file (MLDInfo returns empty Optional).",
        )
        return issues  # cannot validate further without a footer

    footer = _read_footer(data, header_slot)

    # ── 3. Null terminator after signature ───────────────────────────────────
    if footer["null_term"] != 0x00:
        issue(
            SEV_ERROR,
            f"Footer byte at offset {MLD_HEADER_OFFSET + _FO_NULL_TERM} "
            f"(null-terminator after signature) is 0x{footer['null_term']:02X}, "
            f"expected 0x00. dandanator-mini checks type + signature but the extra "
            f"byte will be read garbage.",
        )

    # ── 4. Type byte ─────────────────────────────────────────────────────────
    mld_type = footer["mld_type"]
    if mld_type not in KNOWN_MLD_TYPES:
        known_str = ", ".join(
            f"0x{k:02X} ({v})" for k, v in KNOWN_MLD_TYPES.items()
        )
        issue(
            SEV_ERROR,
            f"Unknown MLD type byte 0x{mld_type:02X} at footer offset {_FO_MLD_TYPE}. "
            f"dandanator-mini GameType.byTypeId() will throw IllegalArgumentException. "
            f"Known types: {known_str}.",
        )
    else:
        type_name = KNOWN_MLD_TYPES[mld_type]
        issue(SEV_INFO, f"Type byte 0x{mld_type:02X} → {type_name}.")

    # ── 5. MLDoffset (baseSlot) should be 0 in a freshly-generated file ──────
    if footer["base_slot"] != 0:
        issue(
            SEV_WARNING,
            f"Footer byte 0 (MLDoffset / baseSlot) is {footer['base_slot']}, "
            f"expected 0 for a freshly-generated MLD. "
            f"dandanator-mini.MLDGame.reallocate() will overwrite it, but a non-zero "
            f"value suggests the file was previously embedded at slot "
            f"{footer['base_slot']} without resetting the source.",
        )

    # ── 6. Sector IDs should be zero in a freshly-generated file ─────────────
    if any(b != 0 for b in footer["sector_ids"]):
        issue(
            SEV_WARNING,
            f"Sector-ID bytes (footer offsets {_FO_SECTOR_IDS}–{_FO_SECTOR_IDS + 3}) "
            f"are not all zero: {footer['sector_ids']}. "
            f"dandanator-mini.MLDGame.allocateSaveSpace() will overwrite them at ROM "
            f"build time, but CYD (loadermld.asm) should emit four 0x00 bytes here.",
        )

    # ── 7. nsectors (requiredSectors) range ───────────────────────────────────
    req_sec = footer["req_sectors"]
    max_sectors = num_slots * 4  # 4 KB sectors per 16 KB slot
    if req_sec == 0:
        issue(
            SEV_WARNING,
            f"nsectors (requiredSectors) is 0. dandanator-mini will call "
            f"allocateSaveSpace() but the loop will not execute, so no save "
            f"space will be reserved. The standard CYD value is 4.",
        )
    elif req_sec > max_sectors:
        issue(
            SEV_ERROR,
            f"nsectors ({req_sec}) exceeds the maximum for {num_slots} slot(s) "
            f"({max_sectors} sectors of 4 KB each). dandanator-mini would allocate "
            f"sectors that overlap with other content.",
        )

    # ── 8. Slot-relocation table fields ──────────────────────────────────────
    table_offset   = footer["table_offset"]
    table_row_size = footer["table_row_size"]
    table_rows     = footer["table_rows"]
    row_slot_off   = footer["row_slot_off"]

    if table_rows == 0 and table_offset == 0 and table_row_size == 0:
        # CYD design: relative slot IDs computed at runtime from MLDoffset.
        # dandanator-mini.reallocate() loop will be skipped (tableRows == 0).
        # The only patch needed is MLDoffset itself – which mld2rom.py does.
        issue(
            SEV_INFO,
            "Relocation table fields are all zero (CYD relative-slot design). "
            "dandanator-mini.MLDGame.reallocate() will only patch MLDoffset; "
            "the loader computes absolute slot IDs at runtime using that cached value.",
        )
    else:
        # Non-zero table: dandanator-mini will walk the table and patch slot bytes.
        mld_size = num_slots * SLOT_SIZE
        table_end = table_offset + table_rows * table_row_size
        if table_end > mld_size:
            issue(
                SEV_ERROR,
                f"Relocation table extends beyond the MLD boundary: "
                f"tableOffset 0x{table_offset:04X} + tableRows {table_rows} × "
                f"tableRowSize {table_row_size} = {table_end} > {mld_size}.",
            )
        if table_row_size > 0 and row_slot_off >= table_row_size:
            issue(
                SEV_ERROR,
                f"rowSlotOffset ({row_slot_off}) ≥ tableRowSize ({table_row_size}); "
                f"dandanator-mini would read slot byte outside the row.",
            )
        if table_row_size == 0 and table_rows > 0:
            issue(
                SEV_ERROR,
                f"tableRows is {table_rows} but tableRowSize is 0; "
                f"dandanator-mini's relocation loop would loop forever.",
            )
        # mld2rom.py does NOT apply dandanator-mini-style table patching.
        # (It only patches MLDoffset and does not walk the table.)
        issue(
            SEV_WARNING,
            f"Non-zero relocation table detected (tableOffset=0x{table_offset:04X}, "
            f"tableRows={table_rows}, tableRowSize={table_row_size}). "
            f"mld2rom.py patches only MLDoffset, not the table entries. "
            f"Use the Java dandanator-mini tool for full relocation support.",
        )

    # ── 9. Preview screen bounds ──────────────────────────────────────────────
    scr_off  = footer["screen_offset"]
    scr_size = footer["screen_size"]
    if scr_off != 0:
        if scr_size == 0:
            issue(
                SEV_WARNING,
                f"Preview screen offset is 0x{scr_off:04X} but size is 0; "
                f"dandanator-mini will pass a zero-length stream to the ZX7 "
                f"decompressor and no preview will be shown.",
            )
        elif scr_off + scr_size > SLOT_SIZE:
            issue(
                SEV_ERROR,
                f"Preview screen data exceeds the slot boundary: "
                f"offset 0x{scr_off:04X} + size {scr_size} = "
                f"0x{scr_off + scr_size:04X} > 0x{SLOT_SIZE:04X}. "
                f"dandanator-mini.MLDGame.getScreenshot() would read out-of-bounds.",
            )
    elif scr_size != 0:
        issue(
            SEV_WARNING,
            f"Preview screen size is {scr_size} but offset is 0; "
            f"dandanator-mini uses offset=0 as 'no screen', so the preview "
            f"will not be displayed even though size > 0.",
        )

    # ── 10. Slot count sanity ──────────────────────────────────────────────────
    if num_slots > (ROM_SLOTS - 2):  # GAME_SLOTS = 30
        issue(
            SEV_ERROR,
            f"MLD occupies {num_slots} slot(s), but only {ROM_SLOTS - 2} game "
            f"slots are available in a {ROM_SLOTS}-slot Dandanator ROM "
            f"(slots 0 and {ROM_SLOTS - 1} are reserved for firmware / extra ROM).",
        )

    return issues


def parse_mld(data: bytes, path: str) -> dict:
    """Parse an MLD file and return a dict with relevant metadata.

    Returns keys:
        num_slots     : int  – total number of 16 KB slots in the MLD
        mld_type      : int  – type byte (0x83/0x88/0xC8 …)
        header_slot   : int  – index of the slot that contains the MLD footer
        screen_offset : int  – compressed preview-screen offset within that slot (0 if none)
        screen_size   : int  – compressed preview-screen size (0 if none)
        footer        : dict – full footer field dict (all MLDInfo fields)
    """
    num_slots, remainder = divmod(len(data), SLOT_SIZE)
    if remainder != 0 or num_slots == 0:
        raise MLDParseError(
            f"{path}: MLD file size ({len(data)}) is not a multiple of {SLOT_SIZE}."
        )

    # Locate the slot that carries the MLD footer signature.
    header_slot = None
    for s in range(num_slots):
        base = s * SLOT_SIZE
        sig = data[base + MLD_SIGNATURE_OFFSET : base + MLD_SIGNATURE_OFFSET + 3]
        if sig == MLD_SIGNATURE:
            header_slot = s
            break

    if header_slot is None:
        raise MLDParseError(
            f"{path}: No MLD signature found in any of the {num_slots} slots. "
            f"Is this a valid MLD file?"
        )

    footer = _read_footer(data, header_slot)

    return {
        "num_slots":     num_slots,
        "mld_type":      footer["mld_type"],
        "header_slot":   header_slot,
        "screen_offset": footer["screen_offset"],
        "screen_size":   footer["screen_size"],
        "footer":        footer,
    }


# ---------------------------------------------------------------------------
# ROM slot-allocation helpers
# ---------------------------------------------------------------------------

def read_existing_uncompressed_slots(rom: bytearray) -> list[tuple[int, int]]:
    """Scan the ROM's game-struct table and return (start_slot, num_slots)
    pairs for every *uncompressed* game already present.

    Uncompressed games have game_struct[_GS_COMPRESSED] == 0 and a valid
    CBlock first byte (not 0xFF).
    """
    game_count = rom[GAME_COUNT_OFFSET]
    used: list[tuple[int, int]] = []
    for i in range(game_count):
        gs_offset = GAME_STRUCT_BASE + i * GAME_STRUCT_SIZE
        if rom[gs_offset + _GS_COMPRESSED] == 0:          # uncompressed
            first_cblock = gs_offset + _GS_CBLOCKS
            slot_num = rom[first_cblock]
            if slot_num != 0xFF:                           # valid entry
                num_slots = struct.unpack_from("<H", rom, first_cblock + 3)[0]
                if num_slots > 0:
                    used.append((slot_num, num_slots))
    return used


def find_start_slot(rom: bytearray, needed_slots: int) -> int:
    """Return the lowest slot index where we can place a new *needed_slots*-slot
    uncompressed game, growing backwards from UNCOMPRESSED_TOP_SLOT.

    Raises ValueError if there is not enough room.
    """
    existing = read_existing_uncompressed_slots(rom)
    # Find the lowest slot currently occupied by any uncompressed game.
    if existing:
        min_used_slot = min(s for s, _ in existing)
        start_slot = min_used_slot - needed_slots
    else:
        start_slot = UNCOMPRESSED_TOP_SLOT - needed_slots + 1

    if start_slot < 2:  # Slot 0 = firmware, slot 1 = reserved
        raise ValueError(
            f"Not enough free ROM space: need {needed_slots} slot(s) but "
            f"only {start_slot + needed_slots - 2} free slot(s) remain."
        )
    return start_slot


# ---------------------------------------------------------------------------
# Game-struct builder
# ---------------------------------------------------------------------------

def _encode_name(index: int, name: str) -> bytes:
    """Encode a game name into the 33-byte null-terminated Dandanator format.

    Byte layout:  [slot digit] [space] [space] [name...] [0x00]

    The two 'space' bytes stand in for the extended-charset symbol pair that
    the Java GUI would use (we omit the extended graphics here because they are
    firmware-specific and unused in emulator testing).

    The slot digit follows the Java formula: (index + 1) % SLOT_COUNT(10).
    """
    slot_digit = str((index + 1) % 10)
    prefix = slot_digit + "  "          # 3 chars: digit + 2 spaces
    max_name_len = GAMENAME_SIZE - len(prefix) - 1   # -1 for NUL
    truncated = name[:max_name_len]
    combined = (prefix + truncated).encode("ascii", errors="replace")
    # Pad to exactly GAMENAME_SIZE bytes (including one NUL terminator)
    padded = combined[:GAMENAME_SIZE - 1].ljust(GAMENAME_SIZE - 1, b"\x00") + b"\x00"
    return padded


def build_game_struct(
    index: int,
    name: str,
    mld_type: int,
    start_slot: int,
    num_slots: int,
) -> bytes:
    """Build the 131-byte game struct for an uncompressed MLD game."""
    data = bytearray(GAME_STRUCT_SIZE)

    # SNA header (bytes 0..30): all zeros for MLD
    # Game name (bytes 31..63)
    name_bytes = _encode_name(index, name)
    data[_GS_GAMENAME : _GS_GAMENAME + GAMENAME_SIZE] = name_bytes

    data[_GS_HW_MODE]    = 0          # hardware mode (irrelevant for MLD)
    data[_GS_COMPRESSED] = 0          # 0 = uncompressed
    data[_GS_TYPE_ID]    = mld_type & 0xFF
    data[_GS_SCREEN_HOLD] = 0
    data[_GS_ACTIVE_ROM]  = 0
    # Launch code (bytes 69..86): zeros for MLD
    struct.pack_into("<H", data, _GS_CHUNK_ADDR, 0)
    struct.pack_into("<H", data, _GS_CHUNK_SIZE, 0)

    # CBlocks (bytes 91..130): first 5 bytes = MLD entry, rest = 0xFF
    cb = _GS_CBLOCKS
    data[cb] = start_slot & 0xFF                       # slot number
    struct.pack_into("<H", data, cb + 1, 0)            # in-slot offset = 0
    struct.pack_into("<H", data, cb + 3, num_slots)    # number of slots
    for i in range(5, 40):
        data[cb + i] = 0xFF

    return bytes(data)


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def mld2rom(
    base_rom_path: str,
    mld_paths: list[str],
    output_path: str,
    names: list[str],
    autoboot: bool,
    verbose: bool,
    validate: bool = True,
) -> None:
    # --- Read base ROM -------------------------------------------------------
    base_path = Path(base_rom_path)
    if not base_path.exists():
        sys.exit(f"ERROR: Base ROM not found: {base_rom_path}")

    rom_data = bytearray(base_path.read_bytes())
    if len(rom_data) == BASEROM_SIZE:
        # The raw dandanator-mini.rom resource file (as shipped in the JAR and
        # on GitHub) is only the firmware code (3 584 bytes).  Pad it to the
        # full 512 KB with zeros to produce a valid empty-template ROM.
        if verbose:
            print(
                f"Note: Base ROM is {BASEROM_SIZE} bytes (firmware only); "
                f"padding to {ROM_SIZE} bytes ({ROM_SIZE // 1024} KB) "
                f"with zeros to create an empty template."
            )
        rom_data = rom_data + bytearray(ROM_SIZE - BASEROM_SIZE)
    elif len(rom_data) != ROM_SIZE:
        sys.exit(
            f"ERROR: Base ROM must be exactly {ROM_SIZE} bytes "
            f"({ROM_SIZE // 1024} KB); got {len(rom_data)} bytes.\n"
            f"Tip: The raw dandanator-mini.rom from the JAR/GitHub is only "
            f"{BASEROM_SIZE} bytes and is also accepted (it will be "
            f"zero-padded to {ROM_SIZE // 1024} KB automatically)."
        )

    if verbose:
        current_game_count = rom_data[GAME_COUNT_OFFSET]
        print(f"Base ROM loaded: {base_rom_path!r} "
              f"({current_game_count} game(s) already present)")

    # --- Parse + optionally validate all MLD files ---------------------------
    mld_list: list[dict] = []
    has_errors = False
    for mld_path in mld_paths:
        if not Path(mld_path).exists():
            sys.exit(f"ERROR: MLD file not found: {mld_path}")
        raw = Path(mld_path).read_bytes()

        # Validation (always run so defects are visible; only fatal on CRITICAL)
        if validate:
            issues = validate_mld_file(raw, mld_path)
            if issues:
                print(f"\n[VALIDATE] {mld_path}")
                for sev, msg in issues:
                    prefix = {
                        SEV_CRITICAL: "  ✗ CRITICAL",
                        SEV_ERROR:    "  ✗ ERROR   ",
                        SEV_WARNING:  "  ! WARNING ",
                        SEV_INFO:     "  · INFO    ",
                    }.get(sev, f"  ? {sev:8}")
                    print(f"{prefix}: {msg}")
                critical = [i for i in issues if i[0] == SEV_CRITICAL]
                errors   = [i for i in issues if i[0] == SEV_ERROR]
                warnings = [i for i in issues if i[0] == SEV_WARNING]
                print(
                    f"  → {len(critical)} critical, {len(errors)} error(s), "
                    f"{len(warnings)} warning(s)."
                )
                if critical or errors:
                    has_errors = True
            elif verbose:
                print(f"[VALIDATE] {mld_path}: OK (no issues found)")

        try:
            info = parse_mld(raw, mld_path)
        except MLDParseError as exc:
            sys.exit(f"ERROR: {exc}")
        info["path"] = mld_path
        info["data"] = bytearray(raw)
        # Derive display name
        info["display_name"] = Path(mld_path).stem
        mld_list.append(info)
        if verbose:
            type_name = KNOWN_MLD_TYPES.get(info["mld_type"],
                                            f"0x{info['mld_type']:02X}")
            footer = info["footer"]
            print(
                f"  {mld_path!r}: {info['num_slots']} slot(s), "
                f"type {type_name}, footer in slot {info['header_slot']}, "
                f"nsectors={footer['req_sectors']}, "
                f"tableRows={footer['table_rows']}"
            )

    if has_errors:
        sys.exit(
            "\nAborting ROM build due to ERROR or CRITICAL validation issues above.\n"
            "Fix the MLD source or use --no-validate to skip checks."
        )

    # Apply name overrides
    for i, name_override in enumerate(names):
        if i < len(mld_list):
            mld_list[i]["display_name"] = name_override

    # --- Capacity check -------------------------------------------------------
    current_game_count = rom_data[GAME_COUNT_OFFSET]
    needed_game_slots = len(mld_list)
    if current_game_count + needed_game_slots > MAX_GAMES:
        sys.exit(
            f"ERROR: Base ROM already has {current_game_count} game(s); "
            f"adding {needed_game_slots} would exceed the maximum of {MAX_GAMES}."
        )

    # --- Allocate ROM slots and embed MLD data --------------------------------
    # Games are allocated backwards from slot UNCOMPRESSED_TOP_SLOT.
    # We do it in list order (same as Java's "first game → highest slots").
    working_rom = bytearray(rom_data)
    allocated: list[tuple[int, int, int]] = []  # (start_slot, num_slots, mld_index)

    for idx, mld in enumerate(mld_list):
        num_slots = mld["num_slots"]
        try:
            start_slot = find_start_slot(working_rom, num_slots)
        except ValueError as exc:
            sys.exit(f"ERROR: {exc}")

        # Patch MLDoffset byte in slot 0 of the MLD data
        footer_offset = mld["header_slot"] * SLOT_SIZE + MLD_HEADER_OFFSET
        mld["data"][footer_offset] = start_slot & 0xFF

        # Write MLD slots into ROM
        rom_byte_offset = start_slot * SLOT_SIZE
        working_rom[rom_byte_offset : rom_byte_offset + num_slots * SLOT_SIZE] = \
            mld["data"][: num_slots * SLOT_SIZE]

        # Build and write game struct
        game_index = current_game_count + idx
        gs_offset = GAME_STRUCT_BASE + game_index * GAME_STRUCT_SIZE
        gs = build_game_struct(
            game_index,
            mld["display_name"],
            mld["mld_type"],
            start_slot,
            num_slots,
        )
        working_rom[gs_offset : gs_offset + GAME_STRUCT_SIZE] = gs

        allocated.append((start_slot, num_slots, idx))

        if verbose:
            print(
                f"  Adding {mld['display_name']!r} at ROM slots "
                f"{start_slot}–{start_slot + num_slots - 1} "
                f"(MLDoffset={start_slot:#04x}, {num_slots} slot(s))"
            )

        # Mark slots as used so find_start_slot sees them on next iteration
        # by bumping the game count temporarily
        working_rom[GAME_COUNT_OFFSET] = (current_game_count + idx + 1) & 0xFF

    # Final game count
    final_count = current_game_count + len(mld_list)
    working_rom[GAME_COUNT_OFFSET] = final_count & 0xFF
    if verbose:
        print(f"Game count updated to {final_count}")

    # --- Autoboot ------------------------------------------------------------
    if autoboot:
        working_rom[AUTOBOOT_OFFSET] = 1
        if verbose:
            print("Autoboot enabled")

    # --- Write output ROM ----------------------------------------------------
    out_path = Path(output_path)
    out_path.write_bytes(bytes(working_rom))
    if verbose:
        print(f"ROM written to {output_path!r} ({ROM_SIZE} bytes)")


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mld2rom",
        description=(
            "Pack CYD-generated .MLD files into a Dandanator Mini 512 KB ROM "
            "image for testing in emulators."
        ),
        epilog=(
            "The Dandanator Mini base ROM (--base-rom) is required.  "
            "Obtain it from the dandanator-mini project: "
            "https://github.com/cronomantic/dandanator-mini"
        ),
    )
    parser.add_argument(
        "-b", "--base-rom",
        metavar="FILE",
        help=(
            "512 KB Dandanator Mini ROM template (required unless "
            "--validate-only is used)."
        ),
    )
    parser.add_argument(
        "mld_files",
        metavar="MLD",
        nargs="+",
        help="One or more .MLD files to embed (in order).",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="FILE",
        help=(
            "Output ROM path.  Defaults to the base ROM filename "
            "with '.out.rom' appended."
        ),
    )
    parser.add_argument(
        "-n", "--name",
        metavar="NAME",
        action="append",
        default=[],
        dest="names",
        help=(
            "Game name override (repeat for each MLD file; "
            "defaults to the MLD filename stem)."
        ),
    )
    parser.add_argument(
        "-a", "--autoboot",
        action="store_true",
        help="Set the Dandanator autoboot flag (first game starts immediately).",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print progress information.",
    )
    parser.add_argument(
        "--no-validate",
        action="store_true",
        help=(
            "Skip dandanator-mini spec validation. By default, each MLD file "
            "is checked against the spec and any defects are reported. Use "
            "--no-validate to suppress the check and embed the file regardless."
        ),
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help=(
            "Validate MLD file(s) and report defects without generating a ROM. "
            "No --base-rom is required in this mode."
        ),
    )

    args = parser.parse_args()

    # Validate-only mode: no ROM output, --base-rom not required.
    if args.validate_only:
        any_issues = False
        for mld_path in args.mld_files:
            if not Path(mld_path).exists():
                print(f"ERROR: MLD file not found: {mld_path}", file=sys.stderr)
                continue
            raw = Path(mld_path).read_bytes()
            issues = validate_mld_file(raw, mld_path)
            print(f"\n[VALIDATE] {mld_path}")
            if not issues:
                print("  OK – no issues found.")
            else:
                for sev, msg in issues:
                    prefix = {
                        SEV_CRITICAL: "  ✗ CRITICAL",
                        SEV_ERROR:    "  ✗ ERROR   ",
                        SEV_WARNING:  "  ! WARNING ",
                        SEV_INFO:     "  · INFO    ",
                    }.get(sev, f"  ? {sev:8}")
                    print(f"{prefix}: {msg}")
                n_crit = sum(1 for s, _ in issues if s == SEV_CRITICAL)
                n_err  = sum(1 for s, _ in issues if s == SEV_ERROR)
                n_warn = sum(1 for s, _ in issues if s == SEV_WARNING)
                print(f"  → {n_crit} critical, {n_err} error(s), {n_warn} warning(s).")
                if n_crit or n_err:
                    any_issues = True
        sys.exit(1 if any_issues else 0)

    if not args.base_rom:
        parser.error("--base-rom is required unless --validate-only is used.")

    if args.output:
        output_path = args.output
    else:
        base = Path(args.base_rom)
        output_path = str(base.with_suffix("").with_suffix(".out.rom"))

    mld2rom(
        base_rom_path=args.base_rom,
        mld_paths=args.mld_files,
        output_path=output_path,
        names=args.names,
        autoboot=args.autoboot,
        verbose=args.verbose,
        validate=not args.no_validate,
    )
    print(f"Done. Output: {output_path}")


if __name__ == "__main__":
    main()
