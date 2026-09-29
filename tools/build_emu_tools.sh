#!/usr/bin/env bash
# Builds, under tools/ (git-ignored), the Linux tools the emulator tests use:
#
#   tools/sjasmplus              from the external/sjasmplus submodule
#   tools/ZEsarUX-<ver>/zesarux  a headless ZEsarUX (no video or audio backends)
#
# The CI runs it before the test suite; run it once on Linux to run the
# emulator tests locally too (tests/emu_harness.py finds both there).
# ZEsarUX looks for its ROMs next to the binary, so its whole build directory
# is kept. Needs git, make and a C/C++ compiler; takes under a minute.
set -euo pipefail

ZESARUX_VERSION="${ZESARUX_VERSION:-13.0}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS="$ROOT/tools"
JOBS="$(nproc 2>/dev/null || echo 2)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "== sjasmplus (external/sjasmplus)"
git -C "$ROOT" submodule update --init external/sjasmplus
git -C "$ROOT/external/sjasmplus" submodule update --init LuaBridge
# Built on a copy so the submodule's working tree stays clean.
cp -r "$ROOT/external/sjasmplus" "$WORK/sjasmplus"
make -C "$WORK/sjasmplus" -j"$JOBS" >"$WORK/sjasmplus.log" 2>&1 || {
    tail -40 "$WORK/sjasmplus.log"; exit 1; }
cp "$WORK/sjasmplus/sjasmplus" "$TOOLS/sjasmplus"
"$TOOLS/sjasmplus" --version

echo "== ZEsarUX $ZESARUX_VERSION"
git clone -q --depth 1 --branch "ZEsarUX-$ZESARUX_VERSION" \
    https://github.com/chernandezba/zesarux "$WORK/zesarux"
(
    cd "$WORK/zesarux/src"
    ./configure --disable-xwindows --disable-xext --disable-sdl --disable-fbdev \
        --disable-dsp --disable-alsa --disable-pulse --disable-caca --disable-aa \
        --disable-curses --disable-cursesw --disable-sndfile \
        --disable-linuxrealjoystick --disable-onebitspeaker
    make -j"$JOBS"
) >"$WORK/zesarux.log" 2>&1 || { tail -40 "$WORK/zesarux.log"; exit 1; }
find "$WORK/zesarux/src" -name '*.o' -delete
rm -rf "$TOOLS/ZEsarUX-$ZESARUX_VERSION"
mv "$WORK/zesarux/src" "$TOOLS/ZEsarUX-$ZESARUX_VERSION"
echo "ZEsarUX $ZESARUX_VERSION -> tools/ZEsarUX-$ZESARUX_VERSION/zesarux"
