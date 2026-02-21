#!/usr/bin/env bash

# ===============================================================================
#  ChooseYourDestiny - Adventure Builder Script (Linux/macOS/BSD/Unix)
# ===============================================================================
#  This script compiles a .cyd adventure file into a TAP or DSK file
#  for the ZX Spectrum 48k, 128k, or +3.
#
#  Usage: ./make_adv.sh [options]
#  
#  Configuration is done by editing the variables below.
# ===============================================================================

set -e  # Exit on error

# ──────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION SECTION - Edit these variables as needed
# ──────────────────────────────────────────────────────────────────────────────

# Name of the game (without .cyd extension)
GAME="test"
# This name will be used for:
#   - The source file to compile: ${GAME}.cyd
#   - The output TAP or DSK file: ${GAME}.TAP or ${GAME}.DSK

# Target platform: 48k, 128k (for TAP), or plus3 (for DSK)
TARGET="128k"

# Number of screen lines to use when compressing SCR files (default: 192)
# Use 192 for full screen, or less for partial screen images
IMGLINES="192"

# Path to the loading screen SCR file
LOAD_SCR="./IMAGES/LOAD.scr"

# Extra parameters for the CYD compiler (optional)
# Example: --verbose for more output
CYDC_EXTRA_PARAMS=""

# Run emulator after successful compilation
# Options:
#   none     - Do not run emulator
#   internal - Run with ZEsarUX (must be configured below)
#   custom   - Run with custom command (edit CUSTOM_EMULATOR_CMD below)
RUN_EMULATOR="none"

# Custom emulator command (used when RUN_EMULATOR=custom)
# Available variables: ${OUTPUT_FILE}, ${TARGET}, ${GAME}
# Examples:
#   CUSTOM_EMULATOR_CMD="fuse ${OUTPUT_FILE}"
#   CUSTOM_EMULATOR_CMD="spectemu ${OUTPUT_FILE}"
CUSTOM_EMULATOR_CMD="fuse \${OUTPUT_FILE}"

# Path to ZEsarUX (used when RUN_EMULATOR=internal)
ZESARUX_PATH="./tools/ZEsarUX_linux/zesarux"

# Backup the .cyd source file after compilation (yes/no)
BACKUP_CYD="no"

# Maximum number of backup files to keep (0 = unlimited)
# When this limit is reached, oldest backups are deleted
BACKUP_MAX_FILES=0

# ──────────────────────────────────────────────────────────────────────────────
#  END OF CONFIGURATION
# ──────────────────────────────────────────────────────────────────────────────

# Resolve script directory (follows symlinks)
SOURCE="${BASH_SOURCE[0]}"
while [ -L "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

echo "==============================================================================="
echo " ChooseYourDestiny Adventure Builder"
echo "==============================================================================="
echo " Game: ${GAME}"
echo " Target: ${TARGET}"
echo " Loading screen: ${LOAD_SCR}"
echo "==============================================================================="
echo ""

# Check if Python 3 is available
PYTHON=""
if command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
elif command -v python >/dev/null 2>&1; then
    # Check if it's Python 3
    if python -c "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)" 2>/dev/null; then
        PYTHON="python"
    fi
fi

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3 is not installed or not in PATH!"
    echo ""
    echo "Please install Python 3.6 or higher:"
    echo "  Ubuntu/Debian: sudo apt install python3"
    echo "  Fedora:        sudo dnf install python3"
    echo "  macOS:         brew install python3"
    echo ""
    exit 1
fi

# Check if source file exists
if [ ! -f "${SCRIPT_DIR}/${GAME}.cyd" ]; then
    echo "ERROR: Source file not found: ${GAME}.cyd"
    echo ""
    echo "Please create your adventure file or edit the GAME variable in this script."
    echo ""
    exit 1
fi

# Compile the adventure
echo "Compiling ${GAME}.cyd..."
echo ""

cd "${SCRIPT_DIR}"
$PYTHON "${SCRIPT_DIR}/make_adventure.py" -n "${GAME}" ${CYDC_EXTRA_PARAMS} -il "${IMGLINES}" -scr "${LOAD_SCR}" "${TARGET}"
RETVAL=$?

if [ $RETVAL -ne 0 ]; then
    echo ""
    echo "==============================================================================="
    echo " COMPILATION FAILED"
    echo "==============================================================================="
    echo " Please check the error messages above."
    echo "==============================================================================="
    exit $RETVAL
fi

echo ""
echo "==============================================================================="
echo " SUCCESS! Adventure compiled successfully."
echo "==============================================================================="

# Determine output file
if [ "${TARGET}" == "plus3" ]; then
    OUTPUT_FILE="${GAME}.DSK"
else
    OUTPUT_FILE="${GAME}.TAP"
fi

# Create backup if enabled
if [ "${BACKUP_CYD}" == "yes" ]; then
    echo ""
    echo "Creating backup..."
    
    mkdir -p "${SCRIPT_DIR}/BACKUP"
    
    # Generate timestamp for backup filename
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    BACKUP_FILE="${SCRIPT_DIR}/BACKUP/${GAME}_${TIMESTAMP}.cyd"
    
    cp "${SCRIPT_DIR}/${GAME}.cyd" "${BACKUP_FILE}"
    
    if [ $? -eq 0 ]; then
        echo "Backup created: BACKUP/${GAME}_${TIMESTAMP}.cyd"
    else
        echo "Warning: Could not create backup."
    fi
    
    # Delete old backups if limit is set
    if [ ${BACKUP_MAX_FILES} -gt 0 ]; then
        BACKUP_COUNT=$(ls -1 "${SCRIPT_DIR}/BACKUP/${GAME}_"*.cyd 2>/dev/null | wc -l)
        
        if [ ${BACKUP_COUNT} -gt ${BACKUP_MAX_FILES} ]; then
            echo "Rotating backups (keeping ${BACKUP_MAX_FILES} most recent)..."
            
            TO_DELETE=$((BACKUP_COUNT - BACKUP_MAX_FILES))
            ls -1t "${SCRIPT_DIR}/BACKUP/${GAME}_"*.cyd | tail -n ${TO_DELETE} | xargs rm -f
            
            echo "Deleted ${TO_DELETE} old backup(s)."
        fi
    fi
fi

# Run emulator if configured
if [ "${RUN_EMULATOR}" == "internal" ]; then
    echo ""
    echo "Launching with ZEsarUX emulator..."
    
    if [ ! -f "${SCRIPT_DIR}/${ZESARUX_PATH}" ]; then
        echo "Warning: ZEsarUX not found at ${ZESARUX_PATH}"
        echo "Please download ZEsarUX from https://github.com/chernandezba/zesarux/releases"
        echo "or edit ZESARUX_PATH in this script."
    else
        ZESARUX_PARAMS="--noconfigfile --quickexit --zoom 2 --realvideo --nosplash --forcevisiblehotkeys --forceconfirmyes --nowelcomemessage --cpuspeed 100"
        
        if [ "${TARGET}" == "plus3" ]; then
            "${SCRIPT_DIR}/${ZESARUX_PATH}" ${ZESARUX_PARAMS} --machine P3SP41 "${SCRIPT_DIR}/${OUTPUT_FILE}" &
        elif [ "${TARGET}" == "128k" ]; then
            "${SCRIPT_DIR}/${ZESARUX_PATH}" ${ZESARUX_PARAMS} --machine 128k "${SCRIPT_DIR}/${OUTPUT_FILE}" &
        else
            "${SCRIPT_DIR}/${ZESARUX_PATH}" ${ZESARUX_PARAMS} --machine 48k "${SCRIPT_DIR}/${OUTPUT_FILE}" &
        fi
    fi
elif [ "${RUN_EMULATOR}" == "custom" ]; then
    echo ""
    echo "Launching with custom emulator..."
    
    # Expand variables in custom command
    CMD=$(eval echo "${CUSTOM_EMULATOR_CMD}")
    
    if eval ${CMD}; then
        echo "Emulator launched successfully."
    else
        echo "Warning: Failed to launch emulator with command: ${CMD}"
    fi
fi

echo ""
exit 0
