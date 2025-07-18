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
