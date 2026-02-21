#!/usr/bin/env bash

# ──────────────────────────────────────────────────────────────
#  Launcher for Make Adventure GUI (Linux / macOS / BSD / Unix)
#  Uses the system Python 3 interpreter.
# ──────────────────────────────────────────────────────────────

# Resolve the directory where this script lives (follows symlinks)
SOURCE=${BASH_SOURCE[0]}
while [ -L "$SOURCE" ]; do
  DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )
  SOURCE=$(readlink "$SOURCE")
  [[ $SOURCE != /* ]] && SOURCE=$DIR/$SOURCE
done
DIR=$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )

# Try python3 first, then python
PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "====================================================="
    echo "ERROR: Python 3 is not installed!"
    echo ""
    echo "Please install Python 3.11 or higher."
    echo "====================================================="
    exit 1
fi

# Verify it is Python 3
PY_MAJOR=$($PYTHON -c "import sys; print(sys.version_info[0])" 2>/dev/null)
if [ "$PY_MAJOR" != "3" ]; then
    echo "====================================================="
    echo "ERROR: Python 3 is required, but '$PYTHON' is Python $PY_MAJOR."
    echo "====================================================="
    exit 1
fi

# Check that tkinter is available
$PYTHON -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "====================================================="
    echo "ERROR: tkinter is not available for '$PYTHON'."
    echo ""
    echo "Install it with your package manager:"
    echo "  Debian/Ubuntu:  sudo apt install python3-tk"
    echo "  Fedora:         sudo dnf install python3-tkinter"
    echo "  Arch:           sudo pacman -S tk"
    echo "  macOS:          brew install python-tk"
    echo "====================================================="
    exit 1
fi

$PYTHON "$DIR/make_adventure_gui.py" "$@"
RETVAL=$?
if [ $RETVAL -ne 0 ]; then
    echo "---------------------"
    echo "Error launching the GUI, please check."
    read -rsp $'Press enter to continue...\n'
fi
exit $RETVAL