"""make_adv.sh and make_adv.cmd: the emulator they run the game with.

Each test builds a project in a temporary folder (the real make_adventure.py
and dist/, a game with a long name) and runs the script with
RUN_EMULATOR=internal:

- ZEsarUX is found where tools/build_emu_tools.sh leaves it: the highest
  version among tools/ZEsarUX*/ (13.0 before 11.0 and 9.0), and tools/zesarux/
  before any of them. The ZEsarUX there is a fake that only notes how it was
  run.
- The compiled file is found although the compiler cut its name (10
  characters on tape, 8 on the other targets) and wrote .tap in lowercase.
- The +3 runs as P341 (the scripts used to ask for P3SP41, which ZEsarUX
  doesn't know), and esxdos as a 128K with divMMC and this folder as the SD.
- On Linux, with ZEsarUX and sjasmplus under tools/, the real emulator boots
  the game the way make_adv.sh runs it.
- Running the script at all: make_adv.cmd used to stop after compiling with
  "... was unexpected at this time", because of a ")" in an ECHO inside the
  backup block, which cmd parses even when BACKUP_CYD=no.

make_adv.sh runs where bash is (not Windows); make_adv.cmd only on Windows.
"""

import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tests"))
from emu_harness import (  # noqa: E402
    _read_mem, _recv_until_prompt, compile_cyd, emulator_available, find_sjasmplus,
    find_zesarux,
)

GAME = "aventuralarga"  # 13 characters: "aventurala" on tape, "aventura" on disk
SOURCE = "[[ SET 0 TO 42 ]]Hola.[[ WAITKEY ]]"
WINDOWS = os.name == "nt"
SCRIPT = "make_adv.cmd" if WINDOWS else "make_adv.sh"
EXE = "zesarux.exe" if WINDOWS else "zesarux"
BASE_ARGS = ["--noconfigfile", "--quickexit", "--zoom", "2", "--realvideo", "--nosplash",
             "--forcevisiblehotkeys", "--forceconfirmyes", "--nowelcomemessage",
             "--cpuspeed", "100"]


def _link_dir(link, target):
    if WINDOWS:  # a junction needs no special rights
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                       check=True, capture_output=True)
    else:
        os.symlink(target, link)


def new_folder(test):
    """A temporary folder, by its real path (the script's own folder is, and
    macOS's /tmp is a link, Windows' temp may be a short 8.3 name). Its links
    to the repository go before the rest, so the clean-up can't go into them."""
    wd = Path(os.path.realpath(tempfile.mkdtemp()))

    def clean():
        for link in ("dist", "locale"):
            path = wd / link
            if os.path.islink(path) or (WINDOWS and path.is_dir()):
                (os.rmdir if WINDOWS else os.unlink)(path)  # a junction / symlink
        shutil.rmtree(wd, ignore_errors=True)

    test.addCleanup(clean)
    return wd


def make_project(wd, target, zesarux_path=None):
    """A project in wd that compiles GAME for target with RUN_EMULATOR=internal."""
    wd = Path(wd)
    shutil.copy(REPO / "make_adventure.py", wd)
    _link_dir(wd / "dist", REPO / "dist")
    _link_dir(wd / "locale", REPO / "locale")
    for folder in ("IMAGES", "TRACKS", "tools"):
        (wd / folder).mkdir()
    if WINDOWS:
        shutil.copy(REPO / "tools" / "sjasmplus.exe", wd / "tools")
    else:  # where make_adventure.py looks for it
        (wd / "external" / "sjasmplus").mkdir(parents=True)
        os.symlink(find_sjasmplus(), wd / "external" / "sjasmplus" / "sjasmplus")
    (wd / f"{GAME}.cyd").write_text(SOURCE, encoding="utf-8")

    config = {"GAME": GAME, "TARGET": target, "RUN_EMULATOR": "internal",
              "ZESARUX_PATH": zesarux_path or ""}
    text = (REPO / SCRIPT).read_text(encoding="utf-8")
    for name, value in config.items():
        if WINDOWS:
            text, n = re.subn(rf"(?m)^SET {name}=.*$", lambda _m: f"SET {name}={value}", text,
                              count=1)
        else:
            text, n = re.subn(rf'(?m)^{name}=.*$', lambda _m: f'{name}="{value}"', text,
                              count=1)
        assert n == 1, name
    newline = "\r\n" if WINDOWS else "\n"
    (wd / SCRIPT).write_bytes(text.replace("\r\n", "\n").replace("\n", newline).encode())
    return wd


def fake_zesarux(folder, record):
    """A ZEsarUX that notes its folder and arguments in record (on Windows, a
    program that just ends: the script's own "Launching ZEsarUX:" line says
    how it ran it)."""
    folder.mkdir(parents=True)
    exe = folder / EXE
    if WINDOWS:
        shutil.copy(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "hostname.exe",
                    exe)
    else:
        exe.write_text('#!/bin/sh\n{ pwd; for a in "$@"; do echo "$a"; done; } > "%s"\n'
                       % record)
        exe.chmod(0o755)
    return exe


def run_script(wd):
    """Run the script in wd: (exit code, output). The output goes through a
    file: the emulator it leaves running would keep a pipe open."""
    cmd = ["cmd", "/c", SCRIPT] if WINDOWS else ["bash", SCRIPT]
    with tempfile.TemporaryFile() as out:
        code = subprocess.run(cmd, cwd=wd, stdout=out, stderr=subprocess.STDOUT,
                              stdin=subprocess.DEVNULL,  # PAUSE after a failure
                              timeout=300,
                              env={**os.environ, "LANGUAGE": "en", "CYD_LANG": "en"}).returncode
        out.seek(0)
        return code, out.read().decode("utf-8", errors="replace")


def launch_line(output):
    lines = [ln for ln in output.splitlines() if ln.startswith("Launching ZEsarUX:")]
    return lines[-1] if lines else None


def recorded(record):
    """(folder, arguments) the fake ZEsarUX was run with; it runs in the
    background, so wait for it."""
    for _ in range(50):
        if record.exists() and record.read_text().endswith("\n"):
            lines = record.read_text().splitlines()
            return lines[0], lines[1:]
        time.sleep(0.1)
    raise AssertionError("the fake ZEsarUX was not run")


def same_path(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


@unittest.skipUnless(find_sjasmplus() if not WINDOWS else (REPO / "tools" / "sjasmplus.exe").is_file(),
                     "sjasmplus not available")
@unittest.skipIf(not WINDOWS and not shutil.which("bash"), "bash not available")
class TestInternalEmulator(unittest.TestCase):
    def run_target(self, target, folders=("ZEsarUX-9.0", "ZEsarUX-13.0", "ZEsarUX_win-11.0")):
        """Run the script for target with fake ZEsarUXes in folders; return
        (project, output, ZEsarUX run, its folder, its arguments)."""
        wd = new_folder(self)
        make_project(wd, target)
        record = wd / "zesarux_run.txt"
        for folder in folders:
            fake_zesarux(wd / "tools" / folder, record)
        code, output = run_script(wd)
        self.assertEqual(code, 0, output)
        line = launch_line(output)
        self.assertIsNotNone(line, output)
        if WINDOWS:
            exe = re.match(r'Launching ZEsarUX: "([^"]+)"', line).group(1)
            return wd, output, exe, None, line
        folder, args = recorded(record)
        return wd, output, line.split()[2], folder, args

    def test_plus3_newest_zesarux_and_the_cut_name(self):
        wd, output, exe, folder, args = self.run_target("plus3")
        self.assertTrue(same_path(exe, wd / "tools" / "ZEsarUX-13.0" / EXE), output)
        game = wd / "aventura.DSK"
        if WINDOWS:
            self.assertIn("--machine P341", args)
            self.assertTrue(same_path(re.findall(r'"([^"]+)"', args)[-1], game), args)
        else:
            self.assertTrue(same_path(folder, wd / "tools" / "ZEsarUX-13.0"))
            self.assertEqual(args, BASE_ARGS + ["--machine", "P341", str(game)])

    def test_esxdos_with_the_folder_as_its_sd(self):
        wd, output, exe, folder, args = self.run_target("esxdos")
        if WINDOWS:
            self.assertIn("--machine 128k --enable-divmmc --enable-esxdos-handler", args)
            sd, game = re.findall(r'"([^"]+)"', args)[-2:]
            self.assertTrue(same_path(sd, wd), args)
            self.assertTrue(same_path(game, wd / "aventura.TAP"), args)
        else:
            self.assertEqual(args, BASE_ARGS + [
                "--machine", "128k", "--enable-divmmc", "--enable-esxdos-handler",
                "--esxdos-root-dir", str(wd), str(wd / "aventura.tap")])

    def test_tools_zesarux_first(self):
        wd, output, exe, folder, args = self.run_target(
            "48k", folders=("ZEsarUX-13.0", "zesarux"))
        self.assertTrue(same_path(exe, wd / "tools" / "zesarux" / EXE), output)
        if not WINDOWS:
            self.assertEqual(args, BASE_ARGS + ["--machine", "48k", str(wd / "aventurala.tap")])

    def test_without_zesarux_it_warns(self):
        wd = new_folder(self)
        make_project(wd, "48k", zesarux_path=str(wd / "nowhere" / EXE))
        code, output = run_script(wd)
        self.assertEqual(code, 0, output)
        # The whole message: make_adv.cmd runs with delayed expansion, which
        # drops a lone "!".
        self.assertIn("SUCCESS! Adventure compiled successfully.", output)
        self.assertIn("Warning: ZEsarUX not found", output)
        self.assertIsNone(launch_line(output))


@unittest.skipIf(WINDOWS, "make_adv.sh")
@unittest.skipUnless(emulator_available() and shutil.which("bash"),
                     "sjasmplus/ZEsarUX not available under tools/")
class TestRealZesarux(unittest.TestCase):
    def test_the_game_boots(self):
        for port, target in enumerate(("48k", "128k", "plus3", "esxdos"), 10260):
            with self.subTest(target):
                wd = new_folder(self)
                with tempfile.TemporaryDirectory() as other:  # the same program: its FLAGS
                    _, flags = compile_cyd(SOURCE, target, other)
                # ZESARUX_PATH: the real one, headless and listening, noting its pid.
                wrapper = Path(wd) / "zesarux_wrapper.sh"
                wrapper.write_text(
                    '#!/bin/sh\necho $$ > "%s/zesarux.pid"\nexec "%s" --vo null --ao null '
                    '--enable-remoteprotocol --remoteprotocol-port %d "$@"\n'
                    % (wd, find_zesarux(), port))
                wrapper.chmod(0o755)
                make_project(wd, target, zesarux_path=str(wrapper))
                code, output = run_script(wd)
                self.assertEqual(code, 0, output)
                try:
                    for _ in range(60):
                        try:
                            s = socket.create_connection(("127.0.0.1", port), timeout=1)
                            break
                        except OSError:
                            time.sleep(0.25)
                    else:
                        self.fail("ZEsarUX did not start:\n" + output)
                    with s:
                        _recv_until_prompt(s, 5)
                        deadline, value = time.time() + 40, None
                        while time.time() < deadline and value != 42:
                            time.sleep(1)
                            value = (_read_mem(s, flags, 1) or b"\0")[0]
                    self.assertEqual(value, 42, output)
                finally:
                    pid = Path(wd) / "zesarux.pid"
                    if pid.exists():
                        try:
                            os.kill(int(pid.read_text()), 9)
                        except (OSError, ValueError):
                            pass


if __name__ == "__main__":
    unittest.main()
