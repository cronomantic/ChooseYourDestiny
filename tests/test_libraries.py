"""Emulator regression tests for the bundled CYD libraries (lib/).

Exercises the SHIPPED library files (`lib/math16_32.cyd`, `lib/strings.cyd`) by
INCLUDE-ing them and running the result headless in ZEsarUX, reading results back
from the FLAGS array. Gated on the emulator being available under tools/.

Run: python tests/run_tests.py   (or: python -m unittest tests.test_libraries)
"""

import os
import shutil
import socket
import tempfile
import time
import unittest
from pathlib import Path

import sys
sys.path.insert(0, os.path.dirname(__file__))
from emu_harness import (  # noqa: E402
    emulator_available, compile_cyd, run_in_zesarux,
    find_zesarux, _recv_until_prompt, _cmd, _read_mem,
)

REPO = Path(__file__).resolve().parent.parent
LIB = REPO / "lib"


def _compile_with_libs(source, wd):
    """Copy the libraries next to the test source so INCLUDE resolves, then compile."""
    shutil.copy(LIB / "math16_32.cyd", wd)
    shutil.copy(LIB / "strings.cyd", wd)
    return compile_cyd(source, "48k", wd)


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not found under tools/")
class TestMathLibrary(unittest.TestCase):
    def _run(self, driver, n_bytes):
        src = f'[[\nINCLUDE "math16_32.cyd"\n{driver}\nLABEL spin\nGOTO spin\n]]\n'
        with tempfile.TemporaryDirectory(prefix="cyd_lib_") as wd:
            tap, flags = _compile_with_libs(src, wd)
            return run_in_zesarux(tap, flags, n_bytes=n_bytes)

    @staticmethod
    def _u32(f, s):
        return f[s] | (f[s + 1] << 8) | (f[s + 2] << 16) | (f[s + 3] << 24)

    def test_32bit(self):
        driver = (
            "SET mlA0 TO {0,202,154,59}\nSET mlB0 TO {0,202,154,59}\nGOSUB add32\n"
            "SET 0 TO {@mlA0,@mlA1,@mlA2,@mlA3}\n"          # 1e9+1e9 = 2000000000
            "SET mlA0 TO {112,17,1,0}\nSET mlB0 TO {96,234,0,0}\nGOSUB mul32\n"
            "SET 4 TO {@mlC0,@mlC1,@mlC2,@mlC3}\n"          # 70000*60000 = 4200000000
            "SET mlA0 TO {232,3,0,0}\nSET mlB0 TO {7,0,0,0}\nGOSUB div32\n"
            "SET 8 TO {@mlA0,@mlA1,@mlA2,@mlA3}\n"          # 1000/7 quotient = 142
            "SET 12 TO @mlC0\n"                             # remainder = 6
            "SET mlA0 TO {9,0,0,0}\nSET mlB0 TO {7,0,0,0}\nGOSUB cmp32\nSET 13 TO @mlCmp\n"  # 2
        )
        f = self._run(driver, 16)
        self.assertEqual(self._u32(f, 0), 2000000000, "add32")
        self.assertEqual(self._u32(f, 4), 4200000000, "mul32")
        self.assertEqual(self._u32(f, 8), 142, "div32 quotient")
        self.assertEqual(f[12], 6, "div32 remainder")
        self.assertEqual(f[13], 2, "cmp32 greater")

    def test_16bit_and_widening(self):
        driver = (
            "SET mlA0 TO {64,156}\nSET mlB0 TO {32,78}\nGOSUB add16\n"
            "SET 0 TO @mlA0 : SET 1 TO @mlA1\n"             # 40000+20000 = 60000
            "SET mlA0 TO {80,195}\nSET mlB0 TO {80,195}\nGOSUB mul1632\n"
            "SET 2 TO {@mlC0,@mlC1,@mlC2,@mlC3}\n"          # 50000*50000 = 2500000000
        )
        f = self._run(driver, 8)
        self.assertEqual(f[0] | (f[1] << 8), 60000, "add16")
        self.assertEqual(self._u32(f, 2), 2500000000, "mul1632 widening")

    def test_print32_digits(self):
        # print32 fills the digit buffer at 224.. (LS first) before printing.
        driver = "SET mlA0 TO {135,214,18,0}\nGOSUB print32\n"   # 1234567
        f = self._run(driver, 231)
        digits = list(f[224:231])
        text = "".join(str(d) for d in digits if 0 <= d <= 9)
        # LS-first 7 digits of 1234567 -> reversed = "1234567"
        self.assertEqual("".join(str(d) for d in digits[:7][::-1]), "1234567")


@unittest.skipUnless(emulator_available(), "sjasmplus/ZEsarUX not found under tools/")
class TestStringsLibrary(unittest.TestCase):
    def _run(self, driver, n_bytes):
        src = f'[[\nINCLUDE "strings.cyd"\n{driver}\nLABEL spin\nGOTO spin\n]]\n'
        with tempfile.TemporaryDirectory(prefix="cyd_lib_") as wd:
            tap, flags = _compile_with_libs(src, wd)
            return run_in_zesarux(tap, flags, n_bytes=n_bytes)

    def test_data_routines(self):
        driver = (
            # strClear
            "SET 100 TO {1,2,3,4,5,6,7,8}\nSET stBase TO 100 : SET stLen TO 8\nGOSUB strClear\n"
            "SET 0 TO {@100,@101,@102,@103}\n"
            # strLen "HELLO" -> 5
            "SET 100 TO {72,69,76,76,79,0,0,0}\nGOSUB strLen\nSET 8 TO @stRes\n"
            # strCmp ABC<ABD -> 0 ; ABC=ABC -> 1
            "SET 100 TO {65,66,67,0,0,0,0,0}\nSET 120 TO {65,66,68,0,0,0,0,0}\n"
            "SET stBase TO 100 : SET stB2 TO 120 : SET stLen TO 8\nGOSUB strCmp\nSET 9 TO @stRes\n"
            "SET 120 TO {65,66,67,0,0,0,0,0}\nGOSUB strCmp\nSET 10 TO @stRes\n"
            # strCopy "HI" -> buf2
            "SET 100 TO {72,73,0,0,0,0,0,0}\nSET 120 TO {9,9,9,9,9,9,9,9}\n"
            "SET stBase TO 100 : SET stB2 TO 120 : SET stLen TO 8\nGOSUB strCopy\n"
            "SET 11 TO {@120,@121,@122}\n"
        )
        f = self._run(driver, 16)
        self.assertEqual(list(f[0:4]), [0, 0, 0, 0], "strClear")
        self.assertEqual(f[8], 5, "strLen")
        self.assertEqual(f[9], 0, "strCmp less")
        self.assertEqual(f[10], 1, "strCmp equal")
        self.assertEqual(list(f[11:14]), [72, 73, 0], "strCopy")

    def test_input_capture(self):
        """strInput stores typed characters; keys injected via ZRCP send-keys."""
        driver = "SET stBase TO 100 : SET stLen TO 8\nGOSUB strInput\n"
        src = f'[[\nINCLUDE "strings.cyd"\nPAPER 0 : INK 7 : CLEAR\n{driver}\nLABEL spin\nGOTO spin\n]]\n'
        with tempfile.TemporaryDirectory(prefix="cyd_lib_") as wd:
            tap, flags = _compile_with_libs(src, wd)
            zes = find_zesarux()
            import subprocess
            proc = subprocess.Popen(
                [zes, "--noconfigfile", "--machine", "48k", "--vo", "null", "--ao", "null",
                 "--enable-remoteprotocol", "--remoteprotocol-port", "10000"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            try:
                s = None
                for _ in range(40):
                    try:
                        s = socket.create_connection(("127.0.0.1", 10000), timeout=1.0)
                        break
                    except OSError:
                        time.sleep(0.25)
                self.assertIsNotNone(s, "ZRCP port never opened")
                _recv_until_prompt(s, 5.0)
                time.sleep(2.0)
                _cmd(s, f"smartload {os.path.abspath(tap)}", timeout=12.0)
                time.sleep(6.5)                      # let it load and reach strInput
                _cmd(s, "send-keys-string 150 hello", timeout=6.0)
                time.sleep(1.5)
                live = list(_read_mem(s, flags + 100, 8))
                _cmd(s, "quit", 2.0)
                s.close()
            finally:
                try:
                    proc.terminate(); proc.wait(timeout=5)
                except Exception:
                    proc.kill()
        self.assertEqual(live, [104, 101, 108, 108, 111, 0, 0, 0], "strInput captured 'hello'")


if __name__ == "__main__":
    unittest.main()
