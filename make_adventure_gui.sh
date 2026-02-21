#!/usr/bin/env bash

# ===============================================================================
#  ChooseYourDestiny - GUI Launcher (Linux/macOS/BSD/Unix)
# ===============================================================================
#  This script launches the graphical user interface for building adventures.
#  It uses the system Python 3 interpreter.
#
#  Usage: ./make_adventure_gui.sh
#
#  Requirements:
#    - Python 3.6 or higher
#    - tkinter (Python GUI library)
#
#  The GUI provides an easy-to-use interface for:
#    - Configuring game settings (name, target platform, etc.)
#    - Compiling adventures
#    - Managing assets and resources
#    - Running emulators
# ===============================================================================

set -e  # Exit on error

# Resolve script directory (follows symlinks)
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

echo "==============================================================================="
echo " ChooseYourDestiny - GUI Launcher"
echo "==============================================================================="
echo ""

# Try to find Python 3
PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON="python"
else
    echo "ERROR: Python 3 is not installed!"
    echo ""
    echo "Please install Python 3.6 or higher:"
    echo ""
    echo "  Ubuntu/Debian:"
    echo "    sudo apt update"
    echo "    sudo apt install python3 python3-tk"
    echo ""
    echo "  Fedora:"
    echo "    sudo dnf install python3 python3-tkinter"
    echo ""
    echo "  Arch Linux:"
    echo "    sudo pacman -S python tk"
    echo ""
    echo "  macOS (with Homebrew):"
    echo "    brew install python-tk"
    echo ""
    echo "  macOS (without Homebrew):"
    echo "    Python 3 should come with macOS. Install tkinter with:"
    echo "    pip3 install tk"
    echo ""
    exit 1
fi

# Verify it's Python 3
PY_MAJOR=$($PYTHON -c "import sys; print(sys.version_info[0])" 2>/dev/null)
if [ "$PY_MAJOR" != "3" ]; then
    echo "ERROR: Python 3 is required!"
    echo ""
    echo "Found: $PYTHON (Python $PY_MAJOR)"
    echo "Please install Python 3.6 or higher."
    echo ""
    exit 1
fi

# Check Python version
PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
echo "Using: $PYTHON (Python $PY_VERSION)"
echo ""

# Check if tkinter is available
$PYTHON -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "==============================================================================="
    echo " ERROR: tkinter is not available!"
    echo "==============================================================================="
    echo ""
    echo "The GUI requires tkinter, which is not installed for your Python."
    echo ""
    echo "Install it with your package manager:"
    echo ""
    echo "  Ubuntu/Debian:"
    echo "    sudo apt install python3-tk"
    echo ""
    echo "  Fedora:"
    echo "    sudo dnf install python3-tkinter"
    echo ""
    echo "  Arch Linux:"
    echo "    sudo pacman -S tk"
    echo ""
    echo "  macOS (with Homebrew):"
    echo "    brew install python-tk"
    echo ""
    echo "  macOS (pip):"
    echo "    pip3 install tk"
    echo ""
    echo "==============================================================================="
    exit 1
fi

# Check if GUI script exists
if [ ! -f "${SCRIPT_DIR}/make_adventure_gui.py" ]; then
    echo "ERROR: GUI script not found: make_adventure_gui.py"
    echo ""
    echo "Please ensure you have the complete ChooseYourDestiny distribution."
    echo ""
    exit 1
fi

# Launch the GUI
echo "Launching GUI..."
echo ""

cd "${SCRIPT_DIR}"
$PYTHON "${SCRIPT_DIR}/make_adventure_gui.py" "$@"
RETVAL=$?

if [ $RETVAL -ne 0 ]; then
    echo ""
    echo "==============================================================================="
    echo " ERROR: GUI exited with error code $RETVAL"
    echo "==============================================================================="
    echo ""
    echo "If you continue to have problems, please:"
    echo "  1. Check that all required Python packages are installed"
    echo "  2. Try running: $PYTHON make_adventure_gui.py"
    echo "  3. Report the issue at:"
    echo "     https://github.com/cronomantic/ChooseYourDestiny/issues"
    echo ""
    exit $RETVAL
fi

exit 0
