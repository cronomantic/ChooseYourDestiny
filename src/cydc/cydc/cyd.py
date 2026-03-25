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

import os
import re
from cydc_utils import bytes2str, run_assembler, get_asm_template
from pyZX7.compress import compress_data as zx7_compress_data


def get_unused_opcodes_defines(unused_opcodes=None):
    asm = "\n"
    if unused_opcodes is None:
        return asm
    for c in unused_opcodes:
        asm += f"    DEFINE UNUSED_OP_{c}\n"
    return asm


def get_game_id(name=None):
    if name is None or len(name) == 0:
        return "    DEFS 16,0"
    elif len(name) < 16:
        n = 16 - len(name)
        name = '"' + name + '"'
        for i in range(n):
            name += ", 0"
        return f"    DEFB {name}"
    else:
        name = '"' + name[0:15] + '"'
        return f"    DEFB {name}"


def get_asm_plus3(
    index,
    size_index,
    tokens,
    chars,
    charw,
    sfx_asm,
    has_tracks=False,
    dsk_path="",
    unused_opcodes=None,
    pause_start_value=None,
    use_wyz_tracker=False,
    name="",
):
    if sfx_asm is None:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 0\n"
        sfx_asm += "BEEPFX              EQU $0\n"
        sfx_asm += "SFX_ID              EQU BEEPFX+1\n"
    else:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 1\nBEEPFX:\n" + sfx_asm
        sfx_asm += "\nSFX_ID              EQU BEEPFX+1\n"
    d = dict(
        INIT_ADDR="$8000",
        TOKENS=bytes2str(tokens, ""),
        CHARS=bytes2str(chars, ""),
        CHARW=bytes2str(charw, ""),
        INDEX=index,
        SIZE_INDEX=str(size_index),
        SIZE_INDEX_ENTRY=str(5),
        DSK_PATH=dsk_path,
        GAMEID=get_game_id(name),
    )

    t = get_asm_template("inkey")
    includes = t.substitute(d)
    t = get_asm_template("bank_zx128")
    includes += t.substitute(d)
    t = get_asm_template("plus3dos")
    includes += t.substitute(d)
    t = get_asm_template("savegame_plus3")
    includes += t.substitute(d)
    t = get_asm_template("dzx0_turbo")
    includes += t.substitute(d)
    if has_tracks:
        t = get_asm_template("music_manager")
        includes += t.substitute(d)
        if not use_wyz_tracker:
            t = get_asm_template("VTII10bG")
            includes += t.substitute(d)
    t = get_asm_template("screen_manager")
    includes += t.substitute(d)
    t = get_asm_template("text_manager")
    includes += t.substitute(d)
    t = get_asm_template("interpreter")
    includes += t.substitute(d)
    if has_tracks and not use_wyz_tracker:
        t = get_asm_template("VTII10bG_vars")
        includes += t.substitute(d)
    includes += sfx_asm

    asm = "    DEVICE ZXSPECTRUM128\n"
    asm += "    SLOT 3\n"
    asm += "    PAGE 0\n"
    asm += "\n"

    if pause_start_value is not None:
        asm += f"    DEFINE PAUSE_AT_START_VAL {pause_start_value}\n\n"

    d.update(INCLUDES=includes)
    t = get_asm_template("sysvars")
    asm += t.substitute(d)
    t = get_asm_template("vars")
    asm += t.substitute(d)
    if has_tracks:
        if use_wyz_tracker:
            asm += "    DEFINE USE_WYZ\n\n"
        else:
            asm += "    DEFINE USE_VORTEX\n\n"

    asm += get_unused_opcodes_defines(unused_opcodes)

    t = get_asm_template("cyd_plus3")
    asm += t.substitute(d)

    return asm


def get_asm_128(
    index,
    size_index,
    tokens,
    chars,
    charw,
    sfx_asm,
    has_tracks=False,
    tap_path="",
    unused_opcodes=None,
    pause_start_value=None,
    use_wyz_tracker=False,
    name="",
):
    if sfx_asm is None:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 0\n"
        sfx_asm += "BEEPFX              EQU $0\n"
        sfx_asm += "SFX_ID              EQU BEEPFX+1\n"
    else:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 1\nBEEPFX:\n" + sfx_asm
        sfx_asm += "\nSFX_ID              EQU BEEPFX+1\n"

    d = dict(
        INIT_ADDR="$8000",
        TOKENS=bytes2str(tokens, ""),
        CHARS=bytes2str(chars, ""),
        CHARW=bytes2str(charw, ""),
        INDEX=index,
        SIZE_INDEX=str(size_index),
        SIZE_INDEX_ENTRY=str(5),
        TAP_PATH=tap_path,
        GAMEID=get_game_id(name),
    )

    t = get_asm_template("inkey")
    includes = t.substitute(d)
    t = get_asm_template("bank_zx128")
    includes += t.substitute(d)
    t = get_asm_template("dzx0_turbo")
    includes += t.substitute(d)
    t = get_asm_template("savegame_tape")
    includes += t.substitute(d)
    if has_tracks:
        t = get_asm_template("music_manager_tape")
        includes += t.substitute(d)
        if not use_wyz_tracker:
            t = get_asm_template("VTII10bG")
            includes += t.substitute(d)
    t = get_asm_template("screen_manager_tape")
    includes += t.substitute(d)
    t = get_asm_template("text_manager")
    includes += t.substitute(d)
    t = get_asm_template("interpreter")
    includes += t.substitute(d)
    if has_tracks and not use_wyz_tracker:
        t = get_asm_template("VTII10bG_vars")
        includes += t.substitute(d)
    includes += sfx_asm

    asm = "    DEVICE ZXSPECTRUM48\n\n"

    if pause_start_value is not None:
        asm += f"    DEFINE PAUSE_AT_START_VAL {pause_start_value}\n\n"

    d.update(INCLUDES=includes)
    t = get_asm_template("sysvars")
    asm += t.substitute(d)
    t = get_asm_template("vars")
    asm += t.substitute(d)
    if has_tracks:
        if use_wyz_tracker:
            asm += "    DEFINE USE_WYZ\n\n"
        else:
            asm += "    DEFINE USE_VORTEX\n\n"

    asm += get_unused_opcodes_defines(unused_opcodes)

    asm = "    DEFINE IS_128_TAPE\n" + asm

    t = get_asm_template("cyd_tape")
    asm += t.substitute(d)

    return asm


def get_asm_mld(
    index,
    size_index,
    tokens,
    chars,
    charw,
    sfx_asm,
    has_tracks=False,
    tap_path="",
    unused_opcodes=None,
    pause_start_value=None,
    use_wyz_tracker=False,
    name="",
    loading_scr=None,
):
    if sfx_asm is None:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 0\n"
        sfx_asm += "BEEPFX              EQU $0\n"
        sfx_asm += "SFX_ID              EQU BEEPFX+1\n"
    else:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 1\nBEEPFX:\n" + sfx_asm
        sfx_asm += "\nSFX_ID              EQU BEEPFX+1\n"

    intro_scr_bytes = ""
    if loading_scr is not None:
        intro_scr_bytes = bytes2str(zx7_compress_data(loading_scr), "")

    d = dict(
        INIT_ADDR="$8000",
        TOKENS=bytes2str(tokens, ""),
        CHARS=bytes2str(chars, ""),
        CHARW=bytes2str(charw, ""),
        INDEX=index,
        SIZE_INDEX=str(size_index),
        SIZE_INDEX_ENTRY=str(5),
        TAP_PATH=tap_path,
        GAMEID=get_game_id(name),
        MLD_INTRO_SCR_BYTES=intro_scr_bytes,
    )

    t = get_asm_template("inkey")
    includes = t.substitute(d)
    t = get_asm_template("bank_zx128")
    includes += t.substitute(d)
    t = get_asm_template("bank_dan")
    includes += t.substitute(d)
    t = get_asm_template("dzx0_turbo")
    includes += t.substitute(d)
    t = get_asm_template("savegame_mld")
    includes += t.substitute(d)
    t = get_asm_template("screen_manager_tape")
    includes += t.substitute(d)
    t = get_asm_template("text_manager")
    includes += t.substitute(d)
    t = get_asm_template("interpreter")
    includes += t.substitute(d)
    includes += sfx_asm

    asm = "    DEVICE ZXSPECTRUM48\n\n"
    # IS_MLD_DAN enables pure-Dandanator slot switching in LOAD_CHUNK and IMG_LOAD.
    asm += "    DEFINE IS_MLD_DAN\n\n"

    if loading_scr is not None:
        asm += "    DEFINE MLD_HAS_INTRO_SCR\n\n"

    if pause_start_value is not None:
        asm += f"    DEFINE PAUSE_AT_START_VAL {pause_start_value}\n\n"

    d.update(INCLUDES=includes)
    t = get_asm_template("sysvars")
    asm += t.substitute(d)
    t = get_asm_template("vars")
    asm += t.substitute(d)
    asm += get_unused_opcodes_defines(unused_opcodes)

    t = get_asm_template("cyd_mld")
    asm += t.substitute(d)

    return asm


def get_asm_mld128(
    index,
    size_index,
    tokens,
    chars,
    charw,
    sfx_asm,
    has_tracks=False,
    tap_path="",
    unused_opcodes=None,
    pause_start_value=None,
    use_wyz_tracker=False,
    name="",
    loading_scr=None,
):
    if sfx_asm is None:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 0\n"
        sfx_asm += "BEEPFX              EQU $0\n"
        sfx_asm += "SFX_ID              EQU BEEPFX+1\n"
    else:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 1\nBEEPFX:\n" + sfx_asm
        sfx_asm += "\nSFX_ID              EQU BEEPFX+1\n"

    intro_scr_bytes = ""
    if loading_scr is not None:
        intro_scr_bytes = bytes2str(zx7_compress_data(loading_scr), "")

    d = dict(
        INIT_ADDR="$8000",
        TOKENS=bytes2str(tokens, ""),
        CHARS=bytes2str(chars, ""),
        CHARW=bytes2str(charw, ""),
        INDEX=index,
        SIZE_INDEX=str(size_index),
        SIZE_INDEX_ENTRY=str(5),
        TAP_PATH=tap_path,
        GAMEID=get_game_id(name),
        MLD_INTRO_SCR_BYTES=intro_scr_bytes,
    )

    t = get_asm_template("inkey")
    includes = t.substitute(d)
    t = get_asm_template("bank_zx128")
    includes += t.substitute(d)
    t = get_asm_template("bank_dan")
    includes += t.substitute(d)
    t = get_asm_template("dzx0_turbo")
    includes += t.substitute(d)
    t = get_asm_template("savegame_mld")
    includes += t.substitute(d)
    if has_tracks:
        t = get_asm_template("music_manager_tape")
        includes += t.substitute(d)
        if not use_wyz_tracker:
            t = get_asm_template("VTII10bG")
            includes += t.substitute(d)
    t = get_asm_template("screen_manager_tape")
    includes += t.substitute(d)
    t = get_asm_template("text_manager")
    includes += t.substitute(d)
    t = get_asm_template("interpreter")
    includes += t.substitute(d)
    if has_tracks and not use_wyz_tracker:
        t = get_asm_template("VTII10bG_vars")
        includes += t.substitute(d)
    includes += sfx_asm

    asm = "    DEVICE ZXSPECTRUM48\n\n"
    # TXT/SCR data is read from Dandanator slots in both mld and mld128.
    # Music can still use RAM banks in mld128 through TYPE_TRK/TYPE_WYZ index entries.
    asm += "    DEFINE IS_MLD_DAN\n\n"

    if loading_scr is not None:
        asm += "    DEFINE MLD_HAS_INTRO_SCR\n\n"

    if pause_start_value is not None:
        asm += f"    DEFINE PAUSE_AT_START_VAL {pause_start_value}\n\n"

    d.update(INCLUDES=includes)
    t = get_asm_template("sysvars")
    asm += t.substitute(d)
    t = get_asm_template("vars")
    asm += t.substitute(d)
    if has_tracks:
        if use_wyz_tracker:
            asm += "    DEFINE USE_WYZ\n\n"
        else:
            asm += "    DEFINE USE_VORTEX\n\n"

    asm += get_unused_opcodes_defines(unused_opcodes)

    asm = "    DEFINE IS_128_TAPE\n" + asm

    t = get_asm_template("cyd_mld")
    asm += t.substitute(d)

    return asm


def get_asm_48(
    index,
    size_index,
    tokens,
    chars,
    charw,
    sfx_asm,
    tap_path="",
    unused_opcodes=None,
    pause_start_value=None,
    name="",
):
    if sfx_asm is None:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 0\n"
        sfx_asm += "BEEPFX              EQU $0\n"
        sfx_asm += "SFX_ID              EQU BEEPFX+1\n"
    else:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 1\nBEEPFX:\n" + sfx_asm
        sfx_asm += "\nSFX_ID              EQU BEEPFX+1\n"

    d = dict(
        INIT_ADDR="$8000",
        TOKENS=bytes2str(tokens, ""),
        CHARS=bytes2str(chars, ""),
        CHARW=bytes2str(charw, ""),
        INDEX=index,
        SIZE_INDEX=str(size_index),
        SIZE_INDEX_ENTRY=str(5),
        TAP_PATH=tap_path,
        GAMEID=get_game_id(name),
    )
    t = get_asm_template("inkey")
    includes = t.substitute(d)
    t = get_asm_template("bank_zx128")
    includes += t.substitute(d)
    t = get_asm_template("dzx0_turbo")
    includes += t.substitute(d)
    t = get_asm_template("savegame_tape")
    includes += t.substitute(d)
    t = get_asm_template("screen_manager_tape")
    includes += t.substitute(d)
    t = get_asm_template("text_manager")
    includes += t.substitute(d)
    t = get_asm_template("interpreter")
    includes += t.substitute(d)
    includes += sfx_asm

    asm = "    DEVICE ZXSPECTRUM48\n\n"

    if pause_start_value is not None:
        asm += f"    DEFINE PAUSE_AT_START_VAL {pause_start_value}\n\n"

    d.update(INCLUDES=includes)
    t = get_asm_template("sysvars")
    asm += t.substitute(d)
    t = get_asm_template("vars")
    asm += t.substitute(d)

    asm += get_unused_opcodes_defines(unused_opcodes)

    t = get_asm_template("cyd_tape")
    asm += t.substitute(d)

    return asm


def get_asm_128_size(
    sjasmplus_path,
    output_path,
    verbose,
    tokens,
    chars,
    charw,
    sfx_asm,
    has_tracks=False,
    unused_opcodes=None,
    pause_start_value=None,
    use_wyz_tracker=False,
):
    asm = get_asm_128(
        index="",
        size_index=0,
        tokens=tokens,
        chars=chars,
        charw=charw,
        sfx_asm=sfx_asm,
        has_tracks=has_tracks,
        tap_path="",
        unused_opcodes=unused_opcodes,
        pause_start_value=pause_start_value,
        use_wyz_tracker=use_wyz_tracker,
        name="",
    )
    asm = "    DEFINE SHOW_SIZE_INTERPRETER\n" + asm
    res = run_assembler(
        asm_path=sjasmplus_path,
        asm=asm,
        filename=os.path.join(output_path, "cyd.asm"),
        listing=verbose,
        capture_output=True,
    )
    m = re.search(r"> SIZE_INTERPRETER=\d{1,6} <", res.stderr)
    if m is None:
        raise ValueError("Size pattern not found")
    size = res.stderr[m.start() : m.end()]
    m = re.search(r"\d{1,6}", size)
    if m is None:
        raise ValueError("Size pattern not found")
    size = int(size[m.start() : m.end()])
    return size


def get_asm_48_size(
    sjasmplus_path,
    output_path,
    verbose,
    tokens,
    chars,
    charw,
    sfx_asm,
    unused_opcodes=None,
    pause_start_value=None,
):
    asm = get_asm_48(
        index="",
        size_index=0,
        tokens=tokens,
        chars=chars,
        charw=charw,
        sfx_asm=sfx_asm,
        tap_path="",
        unused_opcodes=unused_opcodes,
        pause_start_value=pause_start_value,
        name="",
    )
    asm = "    DEFINE SHOW_SIZE_INTERPRETER\n" + asm
    res = run_assembler(
        asm_path=sjasmplus_path,
        asm=asm,
        filename=os.path.join(output_path, "cyd.asm"),
        listing=verbose,
        capture_output=True,
    )
    m = re.search(r"> SIZE_INTERPRETER=\d{1,6} <", res.stderr)
    if m is None:
        raise ValueError("Size pattern not found")
    size = res.stderr[m.start() : m.end()]
    m = re.search(r"\d{1,6}", size)
    if m is None:
        raise ValueError("Size pattern not found")
    size = int(size[m.start() : m.end()])
    return size


def get_asm_plus3_size(
    sjasmplus_path,
    output_path,
    verbose,
    tokens,
    chars,
    charw,
    sfx_asm,
    has_tracks=False,
    unused_opcodes=None,
    pause_start_value=None,
    use_wyz_tracker=False,
):
    asm = get_asm_plus3(
        index="",
        size_index=0,
        tokens=tokens,
        chars=chars,
        charw=charw,
        sfx_asm=sfx_asm,
        has_tracks=has_tracks,
        dsk_path="",
        unused_opcodes=unused_opcodes,
        pause_start_value=pause_start_value,
        use_wyz_tracker=use_wyz_tracker,
        name="",
    )
    asm = "    DEFINE SHOW_SIZE_INTERPRETER\n" + asm
    res = run_assembler(
        asm_path=sjasmplus_path,
        asm=asm,
        filename=os.path.join(output_path, "cyd.asm"),
        listing=verbose,
        capture_output=True,
    )
    m = re.search(r"> SIZE_INTERPRETER=\d{1,6} <", res.stderr)
    if m is None:
        raise ValueError("Size pattern not found")
    size = res.stderr[m.start() : m.end()]
    m = re.search(r"\d{1,6}", size)
    if m is None:
        raise ValueError("Size pattern not found")
    size = int(size[m.start() : m.end()])
    return size


def get_asm_mld_size(
    sjasmplus_path,
    output_path,
    verbose,
    tokens,
    chars,
    charw,
    sfx_asm,
    has_tracks=False,
    unused_opcodes=None,
    pause_start_value=None,
    use_wyz_tracker=False,
    mld_is_128=False,
):
    asm_builder = get_asm_mld128 if mld_is_128 else get_asm_mld
    asm = asm_builder(
        index="",
        size_index=0,
        tokens=tokens,
        chars=chars,
        charw=charw,
        sfx_asm=sfx_asm,
        has_tracks=has_tracks,
        tap_path="",
        unused_opcodes=unused_opcodes,
        pause_start_value=pause_start_value,
        use_wyz_tracker=use_wyz_tracker,
        name="",
    )
    asm = "    DEFINE SHOW_SIZE_INTERPRETER\n" + asm
    res = run_assembler(
        asm_path=sjasmplus_path,
        asm=asm,
        filename=os.path.join(output_path, "cyd.asm"),
        listing=verbose,
        capture_output=True,
    )
    m = re.search(r"> SIZE_INTERPRETER=\d{1,6} <", res.stderr)
    if m is None:
        raise ValueError("Size pattern not found")
    size = res.stderr[m.start() : m.end()]
    m = re.search(r"\d{1,6}", size)
    if m is None:
        raise ValueError("Size pattern not found")
    size = int(size[m.start() : m.end()])
    return size


def do_asm_48(
    sjasmplus_path,
    output_path,
    verbose,
    tap_name,
    index,
    blocks,
    banks,
    size_interpreter,
    bank0_offset,
    tokens,
    chars,
    charw,
    sfx_asm,
    loading_scr=None,
    unused_opcodes=None,
    pause_start_value=None,
    name="",
):
    tap_path = os.path.join(output_path, tap_name + ".tap").replace(os.sep, "/")

    asm_ind = ""
    for i, v in enumerate(index):
        asm_ind += f"    DEFB ${v[0]:X}, ${v[1]:X}, ${v[2]:X}\n"
        asm_ind += f"    DEFW ${v[3]:X}\n"

    asm_int = get_asm_48(
        index=asm_ind,
        size_index=len(index),
        tokens=tokens,
        chars=chars,
        charw=charw,
        sfx_asm=sfx_asm,
        tap_path=tap_path,
        unused_opcodes=unused_opcodes,
        pause_start_value=pause_start_value,
        name=name,
    )

    block_list = ""
    if loading_scr is not None:
        block_list += f"    DEFW LD_SCR_ADDR\n"
        block_list += f"    DEFW LD_SCR_SIZE\n"
    block_list += f"    DEFW $8000\n"
    block_list += f"    DEFW ${(size_interpreter + 5 * len(index)):X}\n"
    for i, block in enumerate(blocks):
        bank = banks[i]
        if i == 0:
            offset = bank0_offset
        else:
            offset = 0xC000
        block_list += f"    DEFW ${offset:X}\n"
        block_list += f"    DEFW ${len(block):X}\n"
    block_list += "    DEFW $0\n"  # End mark

    d = dict(
        INIT_ADDR="$8000",
        STACK_ADDRESS="$8000",
        TAP_NAME=tap_path,
        TAP_LABEL=tap_name,
        BLOCK_LIST=block_list,
        DEFINE_IS_128="",
    )
    t = get_asm_template("loadertape")
    asm = t.substitute(d)

    if loading_scr is not None:
        asm += "    ORG 16384\n"
        asm += "START_LOADING_SCREEN:\n"
        asm += bytes2str(loading_scr)
        asm += "\nSIZE_LOADING_SCREEN = $ - START_LOADING_SCREEN\n"
        asm += f'    SAVETAP "{tap_path}",HEADLESS,START_LOADING_SCREEN,SIZE_LOADING_SCREEN\n\n'

    asm += asm_int

    for i, block in enumerate(blocks):
        if i == 0:
            blk_asm = f"    ORG ${bank0_offset:X}\n"
        else:
            blk_asm = "    ORG $C000\n"
        blk_asm += f"START_BLOCK_{i}:\n"
        blk_asm += bytes2str(block)
        blk_asm += f"\nSIZE_BLOCK_{i} = $ - START_BLOCK_{i}\n"
        blk_asm += (
            f'    SAVETAP "{tap_path}",HEADLESS,START_BLOCK_{i},SIZE_BLOCK_{i}\n\n'
        )
        asm += blk_asm

    res = run_assembler(
        asm_path=sjasmplus_path,
        asm=asm,
        filename=os.path.join(output_path, "cyd.asm"),
        listing=verbose,
        capture_output=False,
    )


def do_asm_128(
    sjasmplus_path,
    output_path,
    verbose,
    tap_name,
    index,
    blocks,
    banks,
    size_interpreter,
    bank0_offset,
    tokens,
    chars,
    charw,
    sfx_asm,
    loading_scr=None,
    has_tracks=False,
    unused_opcodes=None,
    pause_start_value=None,
    use_wyz_tracker=False,
    name="",
):

    tap_path = os.path.join(output_path, tap_name + ".tap").replace(os.sep, "/")

    asm_ind = ""
    for i, v in enumerate(index):
        asm_ind += f"    DEFB ${v[0]:X}, ${v[1]:X}, ${v[2]:X}\n"
        asm_ind += f"    DEFW ${v[3]:X}\n"

    asm_int = get_asm_128(
        index=asm_ind,
        size_index=len(index),
        tokens=tokens,
        chars=chars,
        charw=charw,
        sfx_asm=sfx_asm,
        has_tracks=has_tracks,
        tap_path=tap_path,
        unused_opcodes=unused_opcodes,
        pause_start_value=pause_start_value,
        use_wyz_tracker=use_wyz_tracker,
        name=name,
    )

    block_list = ""
    if loading_scr is not None:
        block_list += f"    DEFW LD_SCR_ADDR\n"
        block_list += f"    DEFW LD_SCR_SIZE\n"
        block_list += f"    DEFB $0\n"
    block_list += f"    DEFW $8000\n"
    block_list += f"    DEFW ${(size_interpreter + 5 * len(index)):X}\n"
    block_list += f"    DEFB $0\n"
    for i, block in enumerate(blocks):
        bank = banks[i]
        if i == 0:
            offset = bank0_offset
        else:
            offset = 0xC000
        block_list += f"    DEFW ${offset:X}\n"
        block_list += f"    DEFW ${len(block):X}\n"
        block_list += f"    DEFB ${bank:X}\n"
    block_list += "    DEFW $0\n"  # End mark

    d = dict(
        INIT_ADDR="$8000",
        STACK_ADDRESS="$8000",
        TAP_NAME=tap_path,
        TAP_LABEL=tap_name,
        BLOCK_LIST=block_list,
        DEFINE_IS_128="DEFINE IS_128",
    )
    t = get_asm_template("loadertape")
    asm = t.substitute(d)

    if loading_scr is not None:
        asm += "    ORG 16384\n"
        asm += "START_LOADING_SCREEN:\n"
        asm += bytes2str(loading_scr)
        asm += "\nSIZE_LOADING_SCREEN = $ - START_LOADING_SCREEN\n"
        asm += f'    SAVETAP "{tap_path}",HEADLESS,START_LOADING_SCREEN,SIZE_LOADING_SCREEN\n\n'

    asm += asm_int

    for i, block in enumerate(blocks):
        if i == 0:
            blk_asm = f"    ORG ${bank0_offset:X}\n"
        else:
            blk_asm = "    ORG $C000\n"
        blk_asm += f"START_BLOCK_{i}:\n"
        blk_asm += bytes2str(block)
        blk_asm += f"\nSIZE_BLOCK_{i} = $ - START_BLOCK_{i}\n"
        blk_asm += (
            f'    SAVETAP "{tap_path}",HEADLESS,START_BLOCK_{i},SIZE_BLOCK_{i}\n\n'
        )
        asm += blk_asm

    res = run_assembler(
        asm_path=sjasmplus_path,
        asm=asm,
        filename=os.path.join(output_path, "cyd.asm"),
        listing=verbose,
        capture_output=False,
    )


def do_asm_plus3(
    sjasmplus_path,
    output_path,
    verbose,
    dsk_name,
    index,
    blocks,
    banks,
    size_interpreter,
    bank0_offset,
    tokens,
    chars,
    charw,
    sfx_asm,
    loading_scr=None,
    has_tracks=False,
    unused_opcodes=None,
    pause_start_value=None,
    use_wyz_tracker=False,
    name="",
):

    dsk_path = os.path.join(output_path, dsk_name + ".BIN").replace(os.sep, "/")

    asm_ind = ""
    for i, v in enumerate(index):
        asm_ind += f"    DEFB ${v[0]:X}, ${v[1]:X}, ${v[2]:X}\n"
        asm_ind += f"    DEFW ${v[3]:X}\n"

    blk_asm = ""
    for i, block in enumerate(blocks):
        bank = banks[i]
        block_path = os.path.join(output_path, f"__BLOCK_{i}.BIN").replace(os.sep, "/")
        blk_asm += f"    PAGE {bank}\n"
        if i == 0:
            blk_asm += f"    ORG ${bank0_offset:X}\n"
        else:
            blk_asm += "    ORG $C000\n"
        blk_asm += f"START_BLOCK_{i}:\n"
        blk_asm += bytes2str(block)
        blk_asm += f"\nSIZE_BLOCK_{i} = $ - START_BLOCK_{i}\n"
        blk_asm += f'    SAVEBIN "{block_path}",START_BLOCK_{i},SIZE_BLOCK_{i}\n\n'

    asm_int = get_asm_plus3(
        index=asm_ind,
        size_index=len(index),
        tokens=tokens,
        chars=chars,
        charw=charw,
        sfx_asm=sfx_asm,
        has_tracks=has_tracks,
        dsk_path=dsk_path,
        unused_opcodes=unused_opcodes,
        pause_start_value=pause_start_value,
        use_wyz_tracker=use_wyz_tracker,
        name=name,
    )

    block_list = ""
    block_list += f"    DEFW $8000\n"
    block_list += f"    DEFW ${(size_interpreter + 5 * len(index)):X}\n"
    block_list += f"    DEFB $0\n"
    for i, block in enumerate(blocks):
        bank = banks[i]
        if i == 0:
            offset = bank0_offset
        else:
            offset = 0xC000
        block_list += f"    DEFW ${offset:X}\n"
        block_list += f"    DEFW ${len(block):X}\n"
        block_list += f"    DEFB ${bank:X}\n"
    block_list += "    DEFW $0\n"  # End mark

    loading_scr_def = ""
    if loading_scr is None:
        loading_scr = ""
    else:
        loading_scr = bytes2str(loading_scr, "")
        loading_scr_def = "DEFINE LOADING_SCREEN"

    d = dict(
        INIT_ADDR="$8000",
        STACK_ADDRESS="$8000",
        BLOCK_LIST=block_list,
        DSK_FILENAME_BASE=dsk_name + ".BIN",
        DSK_LOADER_FILENAME=os.path.join(output_path, "DISK").replace(os.sep, "/"),
        DEFINE_LOADING_SCREEN=loading_scr_def,
        LOADSCR_DAT=loading_scr,
        GAMEID=get_game_id(name),
    )

    t = get_asm_template("loaderplus3")
    asm = t.substitute(d)
    asm += asm_int + blk_asm

    res = run_assembler(
        asm_path=sjasmplus_path,
        asm=asm,
        filename=os.path.join(output_path, "cyd.asm"),
        listing=verbose,
        capture_output=False,
    )

    if res:
        for i, block in enumerate(blocks):
            block_path = os.path.join(output_path, f"__BLOCK_{i}.BIN").replace(
                os.sep, "/"
            )
            with open(dsk_path, "ab") as file_dsk, open(block_path, "rb") as file_block:
                file_dsk.write(file_block.read())
            if os.path.exists(block_path):
                os.remove(block_path)


def do_asm_mld(
    sjasmplus_path,
    output_path,
    verbose,
    mld_name,
    index,
    blocks,
    banks,
    size_interpreter,
    bank0_offset,
    tokens,
    chars,
    charw,
    sfx_asm,
    loading_scr=None,
    has_tracks=False,
    unused_opcodes=None,
    pause_start_value=None,
    use_wyz_tracker=False,
    mld_type="$83",
    mld_is_128=False,
    name="",
):
    # Each aggregated code/data block is placed in one dedicated Dandanator slot.
    # Slot layout: 0=loader/footer, 1=interpreter, 2..N=aggregated blocks.
    slot_by_ram_bank = {}
    current_slot = 2
    for i, bank in enumerate(banks):
        if bank not in slot_by_ram_bank:
            slot_by_ram_bank[bank] = current_slot
            current_slot += 1

    # For MLD targets, TXT/SCR chunks must use Dandanator slot IDs in index.
    # For mld128, music entries (TRK/WYZ) keep RAM-bank IDs.
    remapped_index = []
    for entry_type, entry_idx, entry_bank, entry_offset in index:
        mapped_bank = entry_bank
        if entry_type in (0, 1):  # TYPE_TXT, TYPE_SCR
            mapped_bank = slot_by_ram_bank.get(entry_bank, entry_bank)
        remapped_index.append((entry_type, entry_idx, mapped_bank, entry_offset))

    asm_ind = ""
    for _, v in enumerate(remapped_index):
        asm_ind += f"    DEFB ${v[0]:X}, ${v[1]:X}, ${v[2]:X}\n"
        asm_ind += f"    DEFW ${v[3]:X}\n"

    dummy_tap = os.path.join(output_path, "__mld_dummy.tap").replace(os.sep, "/")
    asm_builder = get_asm_mld128 if mld_is_128 else get_asm_mld
    asm_int = asm_builder(
        index=asm_ind,
        size_index=len(index),
        tokens=tokens,
        chars=chars,
        charw=charw,
        sfx_asm=sfx_asm,
        has_tracks=has_tracks,
        tap_path=dummy_tap,
        unused_opcodes=unused_opcodes,
        pause_start_value=pause_start_value,
        use_wyz_tracker=use_wyz_tracker,
        name=name,
        loading_scr=loading_scr,
    )

    int_bin_path = os.path.join(output_path, "__INTERP.BIN").replace(os.sep, "/")
    asm_int += (
        f'\n    SAVEBIN "{int_bin_path}", START_INTERPRETER, SIZE_INTERPRETER\n'
    )

    run_assembler(
        asm_path=sjasmplus_path,
        asm=asm_int,
        filename=os.path.join(output_path, "cyd.asm"),
        listing=verbose,
        capture_output=False,
    )

    with open(int_bin_path, "rb") as f:
        int_bytes = list(f.read())
    if os.path.exists(int_bin_path):
        os.remove(int_bin_path)
    if os.path.exists(dummy_tap):
        os.remove(dummy_tap)

    slots = {1: list(int_bytes)}
    for i, block in enumerate(blocks):
        slot_id = slot_by_ram_bank[banks[i]]
        slots[slot_id] = list(block)

    # Entries consumed by loadermld RAM routine.
    # Always copy interpreter to 0x8000 from slot 1.
    table_entries = [(1, 0, 0x8000, len(int_bytes), 0)]

    # For mld128 keep RAM-bank preload entries (needed by music managers).
    # For strict mld do not preload block data: TXT/SCR stays in Dandanator slots.
    if mld_is_128:
        for i, block in enumerate(blocks):
            if i == 0:
                dst_addr = bank0_offset
            else:
                dst_addr = 0xC000
            slot_id = slot_by_ram_bank[banks[i]]
            table_entries.append((slot_id, 0, dst_addr, len(block), banks[i]))

    max_slot_id = max(slots.keys())
    for slot_id in range(1, max_slot_id + 1):
        if slot_id not in slots:
            slots[slot_id] = []
        if len(slots[slot_id]) < 0x4000:
            slots[slot_id].extend([0xFF] * (0x4000 - len(slots[slot_id])))

    block_table = ""
    for slot_id, src_off, dst_addr, size, bank in table_entries:
        block_table += f"    DEFB ${slot_id:02X}\n"
        block_table += f"    DEFW ${src_off:04X}\n"
        block_table += f"    DEFW ${dst_addr:04X}\n"
        block_table += f"    DEFW ${size:04X}\n"
        block_table += f"    DEFB ${bank:02X}\n"
    block_table += "    DEFB $FF\n"

    preview_scr_data = ""
    preview_scr_addr = "0"
    preview_scr_size = "0"
    if loading_scr is not None:
        preview_scr_data = bytes2str(zx7_compress_data(loading_scr), "")
        preview_scr_addr = "PREVIEW_SCREEN"
        preview_scr_size = "PREVIEW_SCREEN_END-PREVIEW_SCREEN"

    slot0_bin = os.path.join(output_path, "__SLOT00.BIN").replace(os.sep, "/")
    d = dict(
        BLOCK_TABLE=block_table,
        SLOT0_BIN=slot0_bin,
        MLD_TYPE=mld_type,
        PREVIEW_SCR_DATA=preview_scr_data,
        PREVIEW_SCR_ADDR=preview_scr_addr,
        PREVIEW_SCR_SIZE=preview_scr_size,
    )
    t = get_asm_template("loadermld")
    asm_loader = t.substitute(d)
    run_assembler(
        asm_path=sjasmplus_path,
        asm=asm_loader,
        filename=os.path.join(output_path, "cyd_loader_mld.asm"),
        listing=verbose,
        capture_output=False,
    )

    mld_path = os.path.join(output_path, mld_name + ".MLD")
    with open(mld_path, "wb") as fout:
        with open(slot0_bin, "rb") as f0:
            fout.write(f0.read())
        for slot_id in range(1, max_slot_id + 1):
            fout.write(bytearray(slots[slot_id]))

    if os.path.exists(slot0_bin):
        os.remove(slot0_bin)
