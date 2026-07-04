#!/usr/bin/env bash
# ===============================================================================
#  CYD Dandanator ROM Builder - GUI Launcher (Linux/macOS)
# ===============================================================================
#  Launches the standalone GUI that packs CYD .MLD games into a bootable
#  Dandanator Mini ROM. Uses the system Python 3 interpreter (needs tkinter).
#
#  Usage: ./mld2rom_gui.sh
# ===============================================================================
set -e

SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "ERROR: Python 3 is not installed (needs python3 with tkinter)."
    echo "  Ubuntu/Debian: sudo apt install python3 python3-tk"
    exit 1
fi

if ! "$PYTHON" -c "import tkinter" >/dev/null 2>&1; then
    echo "ERROR: tkinter is not available for $PYTHON."
    echo "  Ubuntu/Debian: sudo apt install python3-tk"
    exit 1
fi

if [ ! -f "${SCRIPT_DIR}/mld2rom_gui.py" ]; then
    echo "ERROR: GUI script not found: mld2rom_gui.py"
    exit 1
fi

cd "${SCRIPT_DIR}"
exec "$PYTHON" "${SCRIPT_DIR}/mld2rom_gui.py" "$@"
