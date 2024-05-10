#
# MIT License
#
# Copyright (c) 2024 Sergio Chico
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


import os
import sys
import re
import subprocess


from string import Template
from cydc_utils import bytes2str


class AsmTemplate(Template):
    delimiter = "@"


def get_unused_opcodes_defines(unused_opcodes=None):
    asm = "\n"
    if unused_opcodes is None:
        return asm
    for c in unused_opcodes:
        asm += f"    DEFINE UNUSED_OP_{c}\n"
    return asm


def get_game_id(name=None):
    if name is None or len(name) == 0:
        return "    DEFB 16,0"
    elif len(name) < 16:
        n = 16 - len(name)
        name = '"' + name + '"'
        for i in range(n):
            name += ", 0"
        return f"    DEFB {name}"
    else:
        name = '"' + name[0:15] + '"'
        return f"    DEFB {name}"


def get_asm_template(filename):
    filepath = os.path.join(os.path.dirname(__file__), "cyd", filename + ".asm")
    filepath = os.path.abspath(filepath)
    if not os.path.isfile(filepath):
        raise ValueError(f"{filename} file not found")
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    return AsmTemplate(text)


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
        t = get_asm_template("VTII10bG")
        includes += t.substitute(d)
    t = get_asm_template("screen_manager_tape")
    includes += t.substitute(d)
    t = get_asm_template("text_manager")
    includes += t.substitute(d)
    t = get_asm_template("interpreter")
    includes += t.substitute(d)
    if has_tracks:
        t = get_asm_template("VTII10bG_vars")
        includes += t.substitute(d)
    includes += sfx_asm

    d.update(INCLUDES=includes)
    t = get_asm_template("sysvars")
    asm = t.substitute(d)
    t = get_asm_template("vars")
    asm += t.substitute(d)
    if has_tracks:
        asm += "    DEFINE USE_VORTEX\n\n"

    asm += get_unused_opcodes_defines(unused_opcodes)

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

    d.update(INCLUDES=includes)
    t = get_asm_template("sysvars")
    asm = t.substitute(d)
    t = get_asm_template("vars")
    asm += t.substitute(d)

    asm += get_unused_opcodes_defines(unused_opcodes)

    t = get_asm_template("cyd_tape")
    asm += t.substitute(d)

    # Use the ROM KEYB routines to save memory...
    asm = "    DEFINE USE_ROM_KEYB\n" + asm

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


def do_asm_plus3(
    sjasmplus_path,
    output_path,
    verbose,
    sfx_asm,
    filename_script="SCRIPT.DAT",
    loading_scr=None,
    unused_opcodes=None,
    name="",
):

    if sfx_asm is None:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 0\n"
        sfx_asm += "BEEPFX              EQU $0\n"
        sfx_asm += "SFX_ID              EQU BEEPFX+1\n"
    else:
        sfx_asm = "BEEPFX_AVAILABLE      EQU 0\nBEEPFX:\n" + sfx_asm
        sfx_asm += "\nSFX_ID              EQU BEEPFX+1\n"

    loading_scr_def = ""
    if loading_scr is None:
        loading_scr = ""
    else:
        loading_scr = bytes2str(loading_scr, "")
        loading_scr_def = "DEFINE LOADING_SCREEN"

    d = dict(
        INIT_ADDR="$8000",
        STACK_ADDRESS="$8000",
        INTERPRETER_FILENAME=os.path.join(output_path, "CYD.BIN").replace(os.sep, "/"),
        INTERPRETER_FILENAME_BASE="CYD.BIN",
        LOADER_FILENAME=os.path.join(output_path, "DISK").replace(os.sep, "/"),
        FILENAME_SCRIPT=filename_script,
        DEFINE_LOADING_SCREEN=loading_scr_def,
        LOADSCR_DAT=loading_scr,
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
    t = get_asm_template("music_manager")
    includes += t.substitute(d)
    t = get_asm_template("VTII10bG")
    includes += t.substitute(d)
    t = get_asm_template("screen_manager")
    includes += t.substitute(d)
    t = get_asm_template("text_manager")
    includes += t.substitute(d)
    t = get_asm_template("interpreter")
    includes += t.substitute(d)
    t = get_asm_template("VTII10bG_vars")
    includes += t.substitute(d)
    includes += sfx_asm

    d.update(INCLUDES=includes)
    t = get_asm_template("sysvars")
    asm = t.substitute(d)
    t = get_asm_template("vars")
    asm += t.substitute(d)

    asm += get_unused_opcodes_defines(unused_opcodes)

    t = get_asm_template("cyd_plus3")
    asm += t.substitute(d)
    t = get_asm_template("loaderplus3")
    asm += t.substitute(d)

    run_assembler(
        asm_path=sjasmplus_path,
        asm=asm,
        filename=os.path.join(output_path, "cyd.asm"),
        listing=verbose,
    )


def run_assembler(asm_path, asm, filename, listing=True, capture_output=False):
    """_summary_

    Args:
        zx0_path (_type_): _description_
        chunk (_type_): _description_
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(asm)
    except OSError:
        sys.exit("ERROR: Can't write temp file.")
    asm_path = os.path.abspath(asm_path)  # Get the absolute path of the executable
    command_line = [asm_path, "--nologo", "-Wno-all"]
    if listing:
        command_line += ["--lst=" + (os.path.splitext(filename)[0] + ".lst")]
    command_line += [filename]
    try:
        stdout = None
        # stdout = subprocess.DEVNULL
        # stdout = subprocess.STDOUT
        stderr = None
        # stderr=subprocess.DEVNULL
        result = subprocess.run(
            args=command_line,
            check=False,
            stdout=subprocess.PIPE if capture_output else stdout,
            stderr=subprocess.PIPE if capture_output else stderr,
            universal_newlines=capture_output,
        )
    except subprocess.CalledProcessError as exc:
        raise OSError from exc
    finally:
        if os.path.isfile(filename):
            os.remove(filename)
    if result.returncode != 0:
        raise OSError(result.stderr)
    return result
    # try:
    #    with open(filename + ".zx0", "rb") as f:
    #        chunk = list(f.read())
    # except OSError:
    #    sys.exit("ERROR: Can't read temp file.")
    # finally:
    #    if os.path.isfile(filename + ".zx0"):
    #        os.remove(filename + ".zx0")
    # return chunk
