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
        # Entries that already name a full guard (e.g. "UNUSED_ARR_BROKER") are
        # emitted verbatim; plain opcode names get the UNUSED_OP_ prefix.
        if isinstance(c, str) and c.startswith("UNUSED_"):
            asm += f"    DEFINE {c}\n"
        else:
            asm += f"    DEFINE UNUSED_OP_{c}\n"
    return asm


# Resident memory-broker services (see interpreter.asm). If no native routine
# references any of them the whole broker is stripped (UNUSED_ARR_BROKER).
BROKER_SERVICES = ("CYD_PEEK", "CYD_POKE", "CYD_ARR_MAP", "CYD_ARR_FLUSH")

# Cross-block native call trampoline. Stripped (UNUSED_CYD_CALL) when unused.
CYD_CALL_SERVICE = "CYD_CALL"

# Numbered engine-service gateway. Stripped (UNUSED_SYSCALL) when unused.
CYD_SYSCALL_SERVICE = "CYD_SYSCALL"

# Engine services reachable through CYD_SYSCALL: (name, id). The ids are a stable
# contract and MUST match SVC_TABLE in interpreter.asm.
SYSCALL_SERVICES = (
    ("SVC_PRINT_CHAR", 0),
    ("SVC_WAIT_KEY", 1),
    ("SVC_INKEY", 2),
)

# Everything the unused-machinery probe looks for.
PROBE_SERVICES = BROKER_SERVICES + (CYD_CALL_SERVICE, CYD_SYSCALL_SERVICE)


def build_probe_abi(array_names):
    """A service-less ``cyd_abi.inc`` for the unused-broker probe: every ABI
    symbol a block may legitimately reference is defined as a dummy EXCEPT the
    broker services, so a block that calls one leaves an undefined-symbol trace
    ("Label not found: CYD_...") we can detect. Values are irrelevant (the probe
    only assembles to see which broker labels stay unresolved)."""
    lines = [
        "FLAGS EQU 0",
        "SCREEN_BUFFER_PXL EQU 0",
        "SCREEN_BUFFER_ATT EQU 0",
        "VIDEO_PXL EQU 0",
        "VIDEO_ATT EQU 0",
    ]
    for n in array_names:
        lines += [f"ARR_{n} EQU 0", f"ARR_{n}_LEN EQU 0", f"ARR_{n}_BANK EQU 0"]
    return "\n".join(lines) + "\n"


def probe_block_services(sjasmplus_path, output_path, name, source, base_dir, probe_abi):
    """Assemble a native block against a service-less ABI and return the set of
    broker services it references (via sjasmplus "Label not found" diagnostics).
    Author errors surface as other undefined labels and are ignored here; the
    real assembly pass reports them properly."""
    kind, payload = source
    src_path = os.path.join(output_path, f"__probe_{name}.asm").replace(os.sep, "/")
    if kind == "file":
        asm_file = payload
        if base_dir and not os.path.isabs(asm_file):
            asm_file = os.path.join(base_dir, asm_file)
        asm_file_abs = os.path.abspath(asm_file).replace(os.sep, "/")
        if not os.path.isfile(asm_file_abs):
            return set()  # missing file: the real pass will report it
        body = f'    INCLUDE "{asm_file_abs}"\n'
    else:
        body = payload if payload.endswith("\n") else payload + "\n"
    asm = "    DEVICE ZXSPECTRUM48\n" + probe_abi + "    ORG $C000\n" + body + "    END\n"
    try:
        run_assembler(
            asm_path=sjasmplus_path,
            asm=asm,
            filename=src_path,
            listing=False,
            capture_output=True,
        )
        text = ""  # assembled clean: references no undefined service
    except OSError as e:
        text = str(e)
    finally:
        if os.path.isfile(src_path):
            os.remove(src_path)
    missing = set(re.findall(r"Label not found:\s*([A-Za-z_]\w*)", text))
    return missing & set(PROBE_SERVICES)


def extern_probe_used(codegen, code, sjasmplus_path, output_path, base_dir):
    """Return the set of resident services (broker + CYD_CALL) that native
    routines actually reference, via the undefined-symbol probe. Empty when there
    are no externs (the whole machinery is already gone via UNUSED_OP_EXTERN).
    Used to strip unreferenced machinery: UNUSED_ARR_BROKER, UNUSED_CYD_CALL."""
    if len(codegen.externs) == 0:
        return set()
    array_names = [
        t[1] for t in code if isinstance(t, tuple) and t and t[0] == "ARRAY"
    ]
    probe_abi = build_probe_abi(array_names)
    used = set()
    for name, d in codegen.externs.items():
        used |= probe_block_services(
            sjasmplus_path, output_path, name, d["source"], base_dir, probe_abi
        )
    return used


def extern_live_blocks(codegen):
    """Native-block dead-code elimination.

    Returns ``(kept_block_names, sorted_kept_callables)``. A native block
    (IMPORT/ASM) is kept if any of its exported callables is referenced by a
    reachable ``CALL`` (``codegen.extern_calls`` is filled after the bytecode DCE,
    so it already lists only reachable calls) or, transitively, is a ``USES``
    callee of a kept block (a kept routine may ``CYD_CALL`` it). Blocks with no
    live export are not assembled/placed and get no dispatch-table slot.

    Exports cannot be pruned individually: a block is one indivisible assembly
    unit (its exports may share private helpers), so it is kept or dropped whole.
    Works with and without ``-dce``: ``extern_calls`` already reflects the chosen
    reachability, and an IMPORT/ASM that is never called is dropped either way."""
    externs = codegen.externs
    used = {name for (name, _chunk, _pos) in codegen.extern_calls}
    changed = True
    while changed:
        changed = False
        for d in externs.values():
            if any(c in used for c in d["exports"]):      # block is kept
                for callee in d["uses"]:                   # its CYD_CALL callees
                    if callee not in used:
                        used.add(callee)
                        changed = True
    kept = {
        name for name, d in externs.items() if any(c in used for c in d["exports"])
    }
    kept_callables = sorted(c for name in kept for c in externs[name]["exports"])
    return kept, kept_callables


def build_uses_inc(uses, route_index):
    """Inject ``RT_<name> EQU <index>`` for each routine the block declares in
    USES, so it can reach them with ``ld a, RT_<name> : call CYD_CALL``."""
    lines = [f"RT_{n} EQU {route_index[n]}" for n in (uses or []) if n in route_index]
    if not lines:
        return ""
    return "; --- CYD_CALL routine indices (from USES) ---\n" + "\n".join(lines) + "\n"


def build_dispatch_table(route_names, extern_addr):
    """The resident EXTERN_DISPATCH table: one ``[bank, addr_lo, addr_hi]`` row
    per callable, in RT_ index order (its position in ``route_names``). Rows are
    filled after placement; ``CYD_CALL`` indexes this table by RT_ index."""
    rows = []
    for name in route_names:
        bank_byte, addr = extern_addr[name]
        rows.append(
            f"    DEFB ${bank_byte:02X}, ${addr & 0xFF:02X}, ${(addr >> 8) & 0xFF:02X}"
        )
    return "\n".join(rows) + "\n" if rows else ""


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
    extern_dispatch="",
    data_len=0,
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
        EXTERN_DISPATCH=extern_dispatch,
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
    # +3 pages RAM banks at $C000 via $7FFD just like the 128k, so it uses the
    # same banked OP_EXTERN handler (routine paged in before the call).
    asm += "    DEFINE OP_EXTERN_BANKED\n\n"

    # PIC_BUFFER ($E000, 6.9 KB) is the disk image-staging buffer used ONLY by the
    # +3 disk image loader (screen_manager.asm). It is reserved (in vars.asm) only
    # when this marker is defined, so tape (48k/128k) and MLD do not waste that RAM.
    asm += "    DEFINE USE_PIC_BUFFER\n\n"

    if pause_start_value is not None:
        asm += f"    DEFINE PAUSE_AT_START_VAL {pause_start_value}\n\n"

    # Immutable DATA stream: length of the read-only blob (0 if no DATA). DATA_CHUNK
    # is always 0 (single TYPE_DATA block) -> its IFNDEF default suffices; only
    # DATA_LEN varies (used by DATAEND).
    asm += f"    DEFINE DATA_LEN {data_len}\n\n"

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
    extern_dispatch="",
    data_len=0,
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
        EXTERN_DISPATCH=extern_dispatch,
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

    # Immutable DATA stream: length of the read-only blob (0 if no DATA). DATA_CHUNK
    # is always 0 (single TYPE_DATA block) -> its IFNDEF default suffices; only
    # DATA_LEN varies (used by DATAEND).
    asm += f"    DEFINE DATA_LEN {data_len}\n\n"

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
    # $7FFD-banked OP_EXTERN handler (routine paged in at $C000 before the call).
    asm = "    DEFINE OP_EXTERN_BANKED\n" + asm

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
    extern_dispatch="",
    arr_init_table="",
    data_len=0,
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
        EXTERN_DISPATCH=extern_dispatch,
        ARR_INIT_TABLE=arr_init_table,
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

    # Immutable DATA stream: length of the read-only blob (0 if no DATA). DATA_CHUNK
    # is always 0 (single TYPE_DATA block) -> its IFNDEF default suffices; only
    # DATA_LEN varies (used by DATAEND).
    asm += f"    DEFINE DATA_LEN {data_len}\n\n"

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
    extern_dispatch="",
    arr_init_table="",
    data_len=0,
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
        EXTERN_DISPATCH=extern_dispatch,
        ARR_INIT_TABLE=arr_init_table,
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

    # Immutable DATA stream: length of the read-only blob (0 if no DATA). DATA_CHUNK
    # is always 0 (single TYPE_DATA block) -> its IFNDEF default suffices; only
    # DATA_LEN varies (used by DATAEND).
    asm += f"    DEFINE DATA_LEN {data_len}\n\n"

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
    # mld128 preloads code/data blocks to RAM banks at $C000 (see do_asm_mld's
    # mld_is_128 preload) and is a 128k machine, so native routines are reached
    # with the same $7FFD-banked OP_EXTERN handler as the 128k. (Bytecode itself
    # lives in Dandanator slots at $0000-$3FFF, independent of $C000.)
    asm = "    DEFINE OP_EXTERN_BANKED\n" + asm

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
    extern_dispatch="",
    data_len=0,
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
        EXTERN_DISPATCH=extern_dispatch,
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

    # Immutable DATA stream: length of the read-only blob (0 if no DATA). DATA_CHUNK
    # is always 0 (single TYPE_DATA block) -> its IFNDEF default suffices; only
    # DATA_LEN varies (used by DATAEND).
    asm += f"    DEFINE DATA_LEN {data_len}\n\n"

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
        sym=os.path.join(output_path, "cyd.sym"),
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
        sym=os.path.join(output_path, "cyd.sym"),
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
        sym=os.path.join(output_path, "cyd.sym"),
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
        sym=os.path.join(output_path, "cyd.sym"),
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


def build_abi_inc(sym_path):
    """Build the injected ``cyd_abi.inc`` text from the engine's ``--sym`` dump.

    Exposes to native routines, by name, the resident data structures they may
    touch: the FLAGS variable array, the engine's image buffer, and the hardware
    screen. Addresses come from the engine build (fixed by vars.asm); the screen
    base is a Spectrum hardware constant (target-dependent by design).

    The resident memory-broker services (CYD_PEEK / CYD_POKE / CYD_ARR_MAP /
    CYD_ARR_FLUSH) are engine labels too, so they ride the same ``--sym`` dump
    and become callable by name."""
    wanted = (
        "FLAGS",
        "SCREEN_BUFFER_PXL",
        "SCREEN_BUFFER_ATT",
        "CYD_PEEK",
        "CYD_POKE",
        "CYD_ARR_MAP",
        "CYD_ARR_FLUSH",
        "CYD_CALL",
        "CYD_SYSCALL",
    )
    found = {}
    if sym_path and os.path.exists(sym_path):
        with open(sym_path, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(
                    r"\s*([A-Za-z_][\w.]*):?\s+EQU\s+"
                    r"(0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+|\d+)",
                    line,
                )
                if m and m.group(1) in wanted:
                    found[m.group(1)] = int(m.group(2).replace("$", "0x"), 0)
    lines = ["; --- CYD ABI (injected by the compiler) ---"]
    for name in wanted:
        if name in found:
            lines.append(f"{name} EQU ${found[name]:04X}")
    lines.append("VIDEO_PXL EQU $4000")   # Spectrum screen bitmap (hardware)
    lines.append("VIDEO_ATT EQU $5800")   # Spectrum screen attributes (hardware)
    # Engine-service ids for CYD_SYSCALL. A stable numeric contract (must match
    # SVC_TABLE in interpreter.asm); injected as constants regardless of the build.
    for name, sid in SYSCALL_SERVICES:
        lines.append(f"{name} EQU {sid}")
    return "\n".join(lines) + "\n"


def build_arrays_inc(codegen, spectrum_banks):
    """Build the injected ``ARR_*`` constants that let a native routine reach the
    author's CYD arrays through the memory broker.

    For each array the compiler emits three EQUs:
      ``ARR_<name>``       address of element 0 (in the $C000 window on banked
                           targets; a resident low-RAM/``$8000``-window address
                           when the array lives in chunk 0),
      ``ARR_<name>_LEN``   element count,
      ``ARR_<name>_BANK``  the physical RAM bank holding it, or ``$FF`` when the
                           array is resident (always mapped, no paging needed).

    The address and bank are derived from ``codegen.symbols`` (filled by
    ``generate_code``): ``symbols[name] = (chunk, offset+1)`` points at the array
    header's length byte, so the data starts at ``offset+2``. ``_convert_address``
    turns the (chunk, offset) pair into the final load address exactly as the
    bytecode uses it. Chunk 0 is resident; every other chunk is a paged bank whose
    physical id is ``spectrum_banks[chunk]``.

    Exception — mld128 writable arrays: those are relocated to dedicated RAM banks,
    so ``symbols[name]`` already holds ``(physical_bank, $C000+addr)`` (not a
    logical chunk index). ``arr_init_table`` carries the authoritative destination,
    so use it directly — ``ARR_<n>_BANK`` is the real bank, ``ARR_<n>`` the paged
    ``$C000`` address of element 0."""
    # name -> (dest_bank, dest_addr) for arrays relocated to a RAM bank (mld128).
    # arr_init_table entries are 6-tuples there; strict mld uses 5-tuples (resident,
    # no native-routine support) which we leave to the generic path below.
    banked = {}
    for entry in getattr(codegen, "arr_init_table", None) or []:
        if len(entry) == 6:
            b_name, _c, _s, dest_bank, dest_addr, _n = entry
            banked[b_name] = (dest_bank, dest_addr)
    lines = []
    for name in sorted(codegen.array_lengths):
        length = codegen.array_lengths[name]
        if name in banked:
            dest_bank, dest_addr = banked[name]
            addr = (dest_addr + 1) & 0xFFFF  # element 0 (skip the len byte)
            bank_byte = dest_bank
        else:
            chunk, off1 = codegen.symbols[name]
            lo, hi = codegen._convert_address(off1 + 1, chunk)  # data addr (skip len)
            addr = lo | (hi << 8)
            if chunk == 0:
                bank_byte = 0xFF  # resident: always mapped, no paging
            elif chunk < len(spectrum_banks):
                bank_byte = spectrum_banks[chunk]
            else:
                bank_byte = spectrum_banks[-1]
        lines.append(f"ARR_{name} EQU ${addr:04X}")
        lines.append(f"ARR_{name}_LEN EQU {length}")
        lines.append(f"ARR_{name}_BANK EQU ${bank_byte:02X}")
    if not lines:
        return ""
    return "; --- CYD arrays (injected by the compiler) ---\n" + "\n".join(lines) + "\n"


def _parse_sym_addresses(sym_path, exports, name):
    """Parse sjasmplus ``--sym`` output (``label: EQU 0xADDR``) for ``exports``."""
    wanted = set(exports)
    found = {}
    with open(sym_path, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(
                r"\s*([A-Za-z_][\w.]*):?\s+EQU\s+(0[xX][0-9A-Fa-f]+|\$[0-9A-Fa-f]+|\d+)",
                line,
            )
            if m and m.group(1) in wanted:
                val = m.group(2)
                found[m.group(1)] = int(val.replace("$", "0x"), 0)
    missing = [e for e in exports if e not in found]
    if missing:
        raise OSError(
            f"ASM '{name}': exported label(s) not defined in the block: "
            + ", ".join(missing)
        )
    return found


def _attribute_extern_error(err, kind, name, src_path, cyd_line, framing_lines):
    """Attribute an assembly failure to the routine. For inline blocks, remap
    sjasmplus ``<tempfile>(<line>): ...`` numbers to the .cyd body line. The body
    begins at temp-file line ``framing_lines + 1`` (framing depends on how many
    header/ABI lines were injected)."""
    text = str(err)
    tag = "IMPORT" if kind == "file" else "ASM"
    if kind == "inline" and cyd_line is not None:
        pat = re.compile(
            r"[^\s(]*" + re.escape(f"__extern_{name}.asm") + r"\((\d+)\):"
        )

        def _remap(m):
            body_line = int(m.group(1)) - framing_lines
            return f"ASM '{name}' (.cyd line {cyd_line + max(body_line - 1, 0)}):"

        text = pat.sub(_remap, text)
    return f"{tag} '{name}': failed to assemble\n{text}"


# A line that DEFINES a symbol, which sjasmplus only recognises in column 0:
# "label:", "label: instr", or "name EQU/=/DEFL value".
_ASM_LABEL_RE = re.compile(
    r"^[ \t]+[A-Za-z_.@][\w.@]*"          # leading indent + identifier
    r"(:|[ \t]+(?:EQU|EQUAL|DEFL|=)\b)",  # then a colon, or an EQU-style keyword
    re.IGNORECASE,
)


def _dedent_asm_labels(body):
    """Move symbol-defining lines (labels / EQU) to column 0, leaving every other
    line exactly as written.

    sjasmplus reads the first token of a column-0 line as a label and the first
    token of an indented line as an instruction, so labels MUST start in column 0
    while instructions must stay indented. Authors, however, naturally indent the
    whole ASM block to line up with the surrounding ``[[ ]]``. Rather than dedent
    the block as a whole (which would also push instructions to column 0 and make
    sjasmplus mistake them for labels), only the label lines are un-indented; the
    line count is unchanged, so error remapping to the ``.cyd`` line stays exact."""
    out = []
    for line in body.splitlines(keepends=True):
        out.append(line.lstrip(" \t") if _ASM_LABEL_RE.match(line) else line)
    return "".join(out)


def assemble_extern_routine(
    sjasmplus_path,
    output_path,
    name,
    source,
    org,
    exports=None,
    base_dir=None,
    cyd_line=None,
    abi_inc=None,
    verbose=False,
):
    """Assemble a native routine in isolation at ``org``; return (data, addrs).

    ``source`` is ``("file", path)`` for an IMPORTed routine or ``("inline",
    body)`` for an inline ``ASM ... ENDASM`` block. The author writes only the
    routine body; this frames it with an ORG, a size measurement and a SAVEBIN,
    exactly like the WYZ player bank.

    ``exports`` is the list of label names whose final addresses to resolve (via
    sjasmplus ``--sym``); pass ``None``/empty for a single-entry block whose
    entry is the block start. Returns ``(data_bytes, {label: address})``; for a
    single-entry block the address dict is empty and the caller uses ``org``.

    A relative file ``source`` is resolved against ``base_dir`` (the .cyd's
    directory). Raises ``OSError`` attributed to the routine; for inline blocks
    sjasmplus line numbers are remapped to the ``.cyd`` source line ``cyd_line``.
    """
    kind, payload = source
    bin_path = os.path.join(output_path, f"__extern_{name}.bin").replace(os.sep, "/")
    src_path = os.path.join(output_path, f"__extern_{name}.asm").replace(os.sep, "/")
    sym_path = os.path.join(output_path, f"__extern_{name}.sym").replace(os.sep, "/")

    if kind == "file":
        asm_file = payload
        if base_dir and not os.path.isabs(asm_file):
            asm_file = os.path.join(base_dir, asm_file)
        asm_file_abs = os.path.abspath(asm_file).replace(os.sep, "/")
        if not os.path.isfile(asm_file_abs):
            raise OSError(f"IMPORT '{name}': assembler file not found: {payload}")
        body = f'    INCLUDE "{asm_file_abs}"\n'
    else:  # inline: embed the body (starts at framing_lines + 1)
        body = _dedent_asm_labels(payload)
        if not body.endswith("\n"):
            body += "\n"

    header = "    DEVICE ZXSPECTRUM48\n"
    if abi_inc:
        header += abi_inc  # injected cyd_abi.inc (FLAGS, buffers, video, ...)
    header += f"    ORG ${org:04X}\n"
    header += "__EXTERN_START:\n"
    framing_lines = header.count("\n")  # inline body begins at framing_lines + 1

    asm = header + body
    asm += "__EXTERN_END:\n"
    asm += "__EXTERN_LEN = __EXTERN_END - __EXTERN_START\n"
    asm += f'    SAVEBIN "{bin_path}", __EXTERN_START, __EXTERN_LEN\n'
    asm += "    END\n"

    try:
        run_assembler(
            asm_path=sjasmplus_path,
            asm=asm,
            filename=src_path,
            listing=verbose,
            capture_output=True,
            sym=(sym_path if exports else None),
        )
    except OSError as e:
        raise OSError(
            _attribute_extern_error(e, kind, name, src_path, cyd_line, framing_lines)
        )

    data = []
    if os.path.exists(bin_path):
        with open(bin_path, "rb") as f:
            data = list(f.read())
        os.remove(bin_path)

    addrs = {}
    if exports:
        if not os.path.exists(sym_path):
            raise OSError(f"ASM '{name}': could not read symbol file for EXPORTS")
        addrs = _parse_sym_addresses(sym_path, exports, name)
        os.remove(sym_path)
    return data, addrs


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
    extern_dispatch="",
    data_len=0,
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
        extern_dispatch=extern_dispatch,
        data_len=data_len,
    )

    # The interpreter image also carries the CYD_CALL dispatch table (3 bytes per
    # entry, right after the block index), so the loader must read those bytes too.
    dispatch_bytes = extern_dispatch.count("DEFB") * 3

    block_list = ""
    if loading_scr is not None:
        block_list += f"    DEFW LD_SCR_ADDR\n"
        block_list += f"    DEFW LD_SCR_SIZE\n"
    block_list += f"    DEFW $8000\n"
    block_list += f"    DEFW ${(size_interpreter + 5 * len(index) + dispatch_bytes):X}\n"
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
    extern_dispatch="",
    data_len=0,
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
        extern_dispatch=extern_dispatch,
        data_len=data_len,
    )

    # The interpreter image also carries the CYD_CALL dispatch table (3 bytes per
    # entry, right after the block index), so the loader must read those bytes too.
    dispatch_bytes = extern_dispatch.count("DEFB") * 3

    block_list = ""
    if loading_scr is not None:
        block_list += f"    DEFW LD_SCR_ADDR\n"
        block_list += f"    DEFW LD_SCR_SIZE\n"
        block_list += f"    DEFB $0\n"
    block_list += f"    DEFW $8000\n"
    block_list += f"    DEFW ${(size_interpreter + 5 * len(index) + dispatch_bytes):X}\n"
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
    extern_dispatch="",
    data_len=0,
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
        extern_dispatch=extern_dispatch,
        data_len=data_len,
    )

    # The interpreter image also carries the CYD_CALL dispatch table (3 bytes per
    # entry, right after the block index), so the loader must read those bytes too.
    dispatch_bytes = extern_dispatch.count("DEFB") * 3

    block_list = ""
    block_list += f"    DEFW $8000\n"
    block_list += f"    DEFW ${(size_interpreter + 5 * len(index) + dispatch_bytes):X}\n"
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
    extern_dispatch="",
    arr_init_table=None,
    data_len=0,
):
    # Array relocation table: DIM arrays live in read-only flash on MLD, so the
    # compiler relocates them to writable RAM. Emit the boot copy table ARR_INIT
    # reads (src is slot-relative, since MLD bank_offset_list=[0,0]), $FF-terminated:
    #  - strict mld (48K): 7-byte entries into the resident pool ARR_POOL
    #        DEFB chunk / DEFW src_off / DEFW pool_off / DEFW nbytes
    #  - mld128 (banked): 8-byte entries into a real RAM bank at $C000+offset
    #        DEFB chunk / DEFW src_off / DEFB dest_bank / DEFW dest_addr / DEFW nbytes
    arr_init_table_asm = ""
    if mld_is_128:
        for _name, chunk, src_off, dest_bank, dest_addr, nbytes in arr_init_table or []:
            arr_init_table_asm += (
                f"    DEFB ${chunk:02X}\n"
                f"    DEFW ${src_off:04X}\n"
                f"    DEFB ${dest_bank:02X}\n"
                f"    DEFW ${dest_addr:04X}\n"
                f"    DEFW ${nbytes:04X}\n"
            )
    else:
        for _name, chunk, src_off, pool_off, nbytes in arr_init_table or []:
            arr_init_table_asm += (
                f"    DEFB ${chunk:02X}\n"
                f"    DEFW ${src_off:04X}\n"
                f"    DEFW ${pool_off:04X}\n"
                f"    DEFW ${nbytes:04X}\n"
            )

    # Each aggregated code/data block is placed in one dedicated Dandanator slot.
    # Slot layout: 0=loader/footer, 1=interpreter, 2..N=aggregated blocks.
    slot_by_ram_bank = {}
    current_slot = 2
    for i, bank in enumerate(banks):
        if bank not in slot_by_ram_bank:
            slot_by_ram_bank[bank] = current_slot
            current_slot += 1

    # For MLD targets, TXT/SCR chunks must use Dandanator slot IDs in the index
    # and the offset must be slot-relative (0..0x3FFF), not the TAP-layout RAM
    # address that the compiler emits. Original offsets are:
    #   bank 0 chunks: position_in_bank + bank0_offset (start of bank 0 data)
    #   other banks:   position_in_bank + 0xC000 (paged window in 128K)
    # The Dandanator loader maps the slot at 0x0000-0x3FFF, so the in-slot
    # offset is just position_in_bank.
    # For mld128, music entries (TRK/WYZ) keep RAM-bank IDs and TAP offsets.
    first_bank = banks[0] if banks else 0
    remapped_index = []
    for entry_type, entry_idx, entry_bank, entry_offset in index:
        mapped_bank = entry_bank
        mapped_offset = entry_offset
        if entry_type in (0, 1, 4):  # TYPE_TXT, TYPE_SCR, TYPE_DATA
            # TYPE_DATA (immutable blob) is read from its Dandanator flash slot,
            # exactly like TXT/SCR -> slot ID + slot-relative offset.
            mapped_bank = slot_by_ram_bank.get(entry_bank, entry_bank)
            if entry_bank == first_bank:
                mapped_offset = (entry_offset - bank0_offset) & 0xFFFF
            else:
                mapped_offset = (entry_offset - 0xC000) & 0xFFFF
        remapped_index.append((entry_type, entry_idx, mapped_bank, mapped_offset))

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
        extern_dispatch=extern_dispatch,
        arr_init_table=arr_init_table_asm,
        data_len=data_len,
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

    # For mld128 keep RAM-bank preload entries (needed by the music managers, which
    # play from a RAM bank at $C000). TXT/SCR/bytecode are read from Dandanator
    # slots (IS_MLD_DAN), so blocks placed in "slot-only" banks (ids >= 8, not
    # valid 128K RAM banks) are NOT preloaded — that lets mld128 use far more slots
    # than the 6 available RAM banks. For strict mld nothing is preloaded.
    if mld_is_128:
        for i, block in enumerate(blocks):
            if banks[i] >= 8:  # slot-only bank: read from its Dandanator slot
                continue
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
