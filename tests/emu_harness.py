"""Headless emulator harness for automated runtime verification.

Compiles a ``.cyd`` source, runs the resulting program in **ZEsarUX** with no
window (``--vo null --ao null``) and reads the engine's ``FLAGS`` variable array
back over the **ZRCP** remote protocol. This lets tests check *runtime* behaviour
(not just that things compile) with no human loading the program by hand.

Why this exists: untested runtime changes are what silently broke the Dandanator
support. This closes that loop — anything that runs on the Spectrum can now be
asserted automatically.

Requirements (all under ``tools/``): ``sjasmplus`` and a ``ZEsarUX_*`` build.
``find_*`` return ``None`` when a tool is missing so callers can skip gracefully.

Typical use (put every test case in ONE program to amortise the ~5s emulator
start, storing each result in a distinct variable, then read them all at once):

    from emu_harness import run_cyd, emulator_available
    flags = run_cyd(SOURCE, n_bytes=16)   # bytes of FLAGS[0..15]
    assert flags[4] == 42
"""

import glob
import os
import re
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CYDC = REPO / "src" / "cydc" / "cydc" / "cydc.py"
_PROMPT = b"command> "


def find_sjasmplus():
    exe = "sjasmplus.exe" if os.name == "nt" else "sjasmplus"
    p = REPO / "tools" / exe
    if p.is_file():
        return str(p)
    from shutil import which
    return which("sjasmplus")


def find_zesarux():
    """Newest ZEsarUX build under tools/ (or on PATH)."""
    exe = "zesarux.exe" if os.name == "nt" else "zesarux"
    cands = sorted(glob.glob(str(REPO / "tools" / "ZEsarUX*" / exe)))
    if cands:
        return cands[-1]  # highest version dir sorts last
    from shutil import which
    return which("zesarux")


def emulator_available():
    return bool(find_sjasmplus() and find_zesarux())


def _parse_flags_addr(lst_path):
    """Extract the address of the FLAGS label from a sjasmplus listing."""
    with open(lst_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            # listing rows look like: "  307  5D00              FLAGS:"
            m = re.search(r"^\s*\d+\s+([0-9A-Fa-f]{4})\s+FLAGS:", line)
            if m:
                return int(m.group(1), 16)
    return None


def compile_cyd(source, model, workdir):
    """Compile ``source`` under ``workdir``; return (image_path, flags_addr).

    The image is a TAP for tape targets and a DSK for the +3 (disk) target;
    ZEsarUX ``smartload`` loads either.
    """
    sj = find_sjasmplus()
    if not sj:
        raise RuntimeError("sjasmplus not found under tools/")
    src = Path(workdir) / "test.cyd"
    src.write_text(source, encoding="utf-8")
    # -v makes run_assembler keep the .lst listing (we parse FLAGS from it).
    proc = subprocess.run(
        [sys.executable, str(CYDC), "-v", model, "test.cyd", sj, "."],
        cwd=workdir, capture_output=True, text=True, timeout=120,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"compilation failed:\n{proc.stdout[-1500:]}\n{proc.stderr[-1500:]}"
        )
    if model == "plus3":
        image = next(iter(Path(workdir).glob("*.DSK")), None)
        if image is None:
            raise RuntimeError("no DSK produced")
    else:
        image = Path(workdir) / "test.tap"
        if not image.is_file():
            raise RuntimeError("no TAP produced")
    lst = Path(workdir) / "cyd.lst"
    flags_addr = _parse_flags_addr(lst) if lst.is_file() else None
    if flags_addr is None:
        raise RuntimeError("could not determine FLAGS address from listing")
    return str(image), flags_addr


def _recv_until_prompt(s, timeout):
    s.settimeout(timeout)
    buf = b""
    try:
        while _PROMPT not in buf:
            chunk = s.recv(8192)
            if not chunk:
                break
            buf += chunk
    except socket.timeout:
        pass
    return buf


def _cmd(s, c, timeout=8.0):
    s.sendall(c.encode() + b"\n")
    return _recv_until_prompt(s, timeout)


def _read_mem(s, addr, length):
    r = _cmd(s, f"read-memory {addr} {length}", timeout=12.0)
    h = b"".join(ln.strip() for ln in r.split(b"\n") if _PROMPT not in ln)
    h = h.replace(b"command>", b"").strip()
    try:
        return bytes.fromhex(h.decode(errors="ignore"))
    except ValueError:
        return b""


def _pc(s):
    r = _cmd(s, "get-registers")
    i = r.find(b"PC=")
    if i < 0:
        return None
    try:
        return int(r[i + 3 : i + 7], 16)
    except ValueError:
        return None


def run_in_zesarux(tap_path, flags_addr, n_bytes=16, port=10000, max_wait=25.0,
                   machine="48k"):
    """Load+run the TAP headless, return FLAGS[0:n_bytes] once the run is stable.

    ``machine`` picks the ZEsarUX model ("48k", "128k", ...); use it to exercise
    the banked runtime paths.
    """
    zes = find_zesarux()
    if not zes:
        raise RuntimeError("ZEsarUX not found under tools/")
    proc = subprocess.Popen(
        [zes, "--noconfigfile", "--machine", machine, "--vo", "null", "--ao", "null",
         "--enable-remoteprotocol", "--remoteprotocol-port", str(port)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        s = None
        for _ in range(40):
            try:
                s = socket.create_connection(("127.0.0.1", port), timeout=1.0)
                break
            except OSError:
                time.sleep(0.25)
        if s is None:
            raise RuntimeError("ZRCP port never opened")
        _recv_until_prompt(s, 5.0)
        time.sleep(2.0)  # let the 48k ROM reach BASIC
        _cmd(s, f"smartload {os.path.abspath(tap_path)}", timeout=12.0)

        # Poll until the interpreter is running (PC in $8000+) and FLAGS is stable.
        prev = None
        deadline = time.time() + max_wait
        result = b"\x00" * n_bytes
        while time.time() < deadline:
            time.sleep(0.7)
            pc = _pc(s)
            cur = _read_mem(s, flags_addr, n_bytes)
            if pc is not None and pc >= 0x8000 and cur == prev and any(cur):
                result = cur
                break
            prev = cur
        else:
            result = prev or result
        try:
            _cmd(s, "quit", 2.0)
            s.close()
        except OSError:
            pass
        return result
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            proc.kill()


def run_cyd(source, model="48k", n_bytes=16, max_wait=25.0):
    """Compile ``source``, run it headless, and return the first ``n_bytes`` of FLAGS."""
    with tempfile.TemporaryDirectory(prefix="cyd_emu_") as wd:
        tap, flags_addr = compile_cyd(source, model, wd)
        return run_in_zesarux(tap, flags_addr, n_bytes=n_bytes, max_wait=max_wait)
