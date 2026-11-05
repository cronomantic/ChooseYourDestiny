#!/usr/bin/env bash

# ===============================================================================
#  ChooseYourDestiny - Adventure Builder Script (Linux/macOS/BSD/Unix)
# ===============================================================================
#  This script compiles a project (a folder with a game, and its
#  cyd_project.ini) into a TAP, DSK, or MLD file for the ZX Spectrum 48k,
#  128k, +3, esxDOS (divMMC) or Dandanator MLD target.
#
#  Usage: ./make_adv.sh [PROJECT] [TARGET]
#
#  PROJECT is the folder of the game, or its main .cyd file; without it, the
#  PROJECT variable below. TARGET, if given, is used instead of the project's.
#  The game's settings (target, image lines, loading screen...) are in its
#  cyd_project.ini; the variables below are for this computer.
# ===============================================================================

set -e  # Exit on error

# ──────────────────────────────────────────────────────────────────────────────
#  CONFIGURATION SECTION - Edit these variables as needed
# ──────────────────────────────────────────────────────────────────────────────

# The project to compile when none is given: the folder of the game (or its
# main .cyd file). Relative to this script's folder, or absolute.
PROJECT=""

# Target platform, instead of the project's: 48k, 128k (for TAP), plus3 (for
# DSK), esxdos (TAP + DAT for the SD card), mld, or mld128 (for MLD). Empty:
# the project's.
TARGET=""

# Name of the game, instead of the project's (empty: the project's). The
# compiler cuts it to 10 characters on tape and to 8 on the other targets.
GAME=""

# Extra parameters for make_adventure.py (optional)
# Example: --verbose for more output
CYDC_EXTRA_PARAMS=""

# Run emulator after successful compilation
# Options:
#   none     - Do not run emulator
#   internal - Run with ZEsarUX (see ZESARUX_PATH below)
#   custom   - Run with custom command (edit CUSTOM_EMULATOR_CMD below)
RUN_EMULATOR="none"

# Custom emulator command (used when RUN_EMULATOR=custom)
# Available variables: ${OUTPUT_FILE}, ${TARGET}, ${GAME}
# Examples:
#   CUSTOM_EMULATOR_CMD="fuse ${OUTPUT_FILE}"
#   CUSTOM_EMULATOR_CMD="spectemu ${OUTPUT_FILE}"
CUSTOM_EMULATOR_CMD="fuse \${OUTPUT_FILE}"

# Path to ZEsarUX (used when RUN_EMULATOR=internal). Empty: look for it in
# ./tools/zesarux/, then in the newest ./tools/ZEsarUX-<version>/ (where
# tools/build_emu_tools.sh leaves it), then on the PATH.
ZESARUX_PATH=""

# Backup the main .cyd file after compilation, to the project's BACKUP folder
# (yes/no; empty: the project's "backup" setting)
BACKUP_CYD=""

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

# Arguments: the project and the target, in any order.
for ARG in "$@"; do
    case "${ARG,,}" in
        48k|128k|plus3|esxdos|mld|mld128) TARGET="${ARG,,}" ;;
        *) PROJECT="${ARG}" ;;
    esac
done

if [ -z "${PROJECT}" ]; then
    echo "ERROR: No project given."
    echo ""
    echo "Usage: ./make_adv.sh PROJECT [TARGET]  (the folder of the game, or its"
    echo "main .cyd file), or set the PROJECT variable in this script. To start a"
    echo "project: python3 make_adventure.py --new FOLDER"
    echo ""
    exit 1
fi
# A relative PROJECT variable is from this script's folder (an argument, from
# where the script is run).
if [ $# -eq 0 ] && [[ "${PROJECT}" != /* ]]; then
    PROJECT="${SCRIPT_DIR}/${PROJECT}"
fi

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

# The project as make_adventure.py sees it: ROOT, MAIN, NAME, TARGET, OUTPUT
# and BACKUP.
NAME_PARAMS=()
[ -n "${GAME}" ] && NAME_PARAMS=(-n "${GAME}")
DESCRIPTION="$("$PYTHON" "${SCRIPT_DIR}/make_adventure.py" --describe "${NAME_PARAMS[@]}" "${PROJECT}" ${TARGET})" || exit 1
while IFS='=' read -r KEY VALUE; do
    VALUE="${VALUE%$'\r'}"  # a Windows Python ends its lines with \r\n
    case "${KEY}" in
        ROOT|MAIN|NAME|TARGET|OUTPUT|BACKUP) printf -v "CYD_${KEY}" '%s' "${VALUE}" ;;
    esac
done <<< "${DESCRIPTION}"
GAME="${CYD_NAME}"
TARGET="${CYD_TARGET}"
[ -z "${BACKUP_CYD}" ] && BACKUP_CYD="${CYD_BACKUP}"

echo "==============================================================================="
echo " ChooseYourDestiny Adventure Builder"
echo "==============================================================================="
echo " Project: ${CYD_ROOT}"
echo " Game: ${GAME}"
echo " Target: ${TARGET}"
echo "==============================================================================="
echo ""

# Compile the adventure
echo "Compiling $(basename "${CYD_MAIN}")..."
echo ""

RETVAL=0  # set -e would leave before the message below
$PYTHON "${SCRIPT_DIR}/make_adventure.py" ${CYDC_EXTRA_PARAMS} "${NAME_PARAMS[@]}" "${PROJECT}" "${TARGET}" || RETVAL=$?

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

# Determine output file, in the output folder: the compiler cuts the name (10
# characters on tape, 8 on the other targets) and writes .tap in lowercase.
case "${TARGET}" in
    plus3)      EXT_GLOB="[dD][sS][kK]" ;;
    mld|mld128) EXT_GLOB="[mM][lL][dD]" ;;
    *)          EXT_GLOB="[tT][aA][pP]" ;;
esac
OUTPUT_FILE=""
for NAME in "${GAME}" "${GAME:0:10}" "${GAME:0:8}"; do
    for FILE in "${CYD_OUTPUT}/${NAME}".${EXT_GLOB}; do
        if [ -z "${OUTPUT_FILE}" ] && [ -f "${FILE}" ]; then
            OUTPUT_FILE="${FILE}"
        fi
    done
done

# Create backup if enabled
if [ "${BACKUP_CYD}" == "yes" ]; then
    echo ""
    echo "Creating backup..."

    BACKUP_DIR="${CYD_ROOT}/BACKUP"
    mkdir -p "${BACKUP_DIR}"

    # Generate timestamp for backup filename
    TIMESTAMP=$(date +"%Y-%m-%d_%H-%M-%S")
    BACKUP_FILE="${BACKUP_DIR}/${GAME}_${TIMESTAMP}.cyd"

    if cp "${CYD_MAIN}" "${BACKUP_FILE}"; then
        echo "Backup created: BACKUP/${GAME}_${TIMESTAMP}.cyd"
    else
        echo "Warning: Could not create backup."
    fi

    # Delete old backups if limit is set
    if [ ${BACKUP_MAX_FILES} -gt 0 ]; then
        BACKUP_COUNT=$(ls -1 "${BACKUP_DIR}/${GAME}_"*.cyd 2>/dev/null | wc -l)

        if [ ${BACKUP_COUNT} -gt ${BACKUP_MAX_FILES} ]; then
            echo "Rotating backups (keeping ${BACKUP_MAX_FILES} most recent)..."

            TO_DELETE=$((BACKUP_COUNT - BACKUP_MAX_FILES))
            ls -1t "${BACKUP_DIR}/${GAME}_"*.cyd | tail -n ${TO_DELETE} | xargs -d '\n' rm -f

            echo "Deleted ${TO_DELETE} old backup(s)."
        fi
    fi
fi

# The ZEsarUX to use: ZESARUX_PATH, else tools/zesarux/, else the highest
# version in tools/ZEsarUX*/ (by its numbers: 13.0 before 9.0), else the PATH.
find_zesarux() {
    if [ -n "${ZESARUX_PATH}" ]; then
        case "${ZESARUX_PATH}" in
            /*) echo "${ZESARUX_PATH}" ;;
            *)  echo "${SCRIPT_DIR}/${ZESARUX_PATH}" ;;
        esac
        return
    fi
    if [ -f "${SCRIPT_DIR}/tools/zesarux/zesarux" ]; then
        echo "${SCRIPT_DIR}/tools/zesarux/zesarux"
        return
    fi
    local dir best=""
    best=$(for dir in "${SCRIPT_DIR}"/tools/[zZ][eE][sS][aA][rR][uU][xX]*/; do
               if [ -f "${dir}zesarux" ]; then
                   printf '%s\t%s\n' "$(basename "${dir}" | sed 's/[^0-9][^0-9]*/ /g')" "${dir}zesarux"
               fi
           done | sort -t "$(printf '\t')" -k1,1V | tail -n 1 | cut -f 2)
    if [ -n "${best}" ]; then
        echo "${best}"
    else
        command -v zesarux || true
    fi
}

# Run emulator if configured
if [ "${RUN_EMULATOR}" == "internal" ]; then
    echo ""
    echo "Launching with ZEsarUX emulator..."
    ZESARUX="$(find_zesarux)"

    if [ "${TARGET}" == "mld" ] || [ "${TARGET}" == "mld128" ]; then
        echo "Warning: internal emulator launch is not configured for MLD cartridges."
        echo "         Use RUN_EMULATOR=custom or load ${OUTPUT_FILE} manually."
    elif [ -z "${ZESARUX}" ] || [ ! -f "${ZESARUX}" ]; then
        echo "Warning: ZEsarUX not found (${ZESARUX_PATH:-tools/zesarux/, tools/ZEsarUX-*/ or the PATH})"
        echo "Please download ZEsarUX from https://github.com/chernandezba/zesarux/releases,"
        echo "build it with tools/build_emu_tools.sh or set ZESARUX_PATH in this script."
    elif [ -z "${OUTPUT_FILE}" ]; then
        echo "Warning: compiled file not found for ${GAME} (${TARGET})."
    else
        case "${TARGET}" in
            plus3)       MACHINE="P341" ;;
            128k|esxdos) MACHINE="128k" ;;
            *)           MACHINE="48k" ;;
        esac
        ZESARUX_PARAMS=(--noconfigfile --quickexit --zoom 2 --realvideo --nosplash
                        --forcevisiblehotkeys --forceconfirmyes --nowelcomemessage
                        --cpuspeed 100 --machine "${MACHINE}")
        if [ "${TARGET}" == "esxdos" ]; then
            # The .tap bootstrap loads the .DAT from the SD card: the output folder.
            ZESARUX_PARAMS+=(--enable-divmmc --enable-esxdos-handler
                             --esxdos-root-dir "${CYD_OUTPUT}")
        fi
        echo "Launching ZEsarUX: ${ZESARUX} ${ZESARUX_PARAMS[*]} ${OUTPUT_FILE}"
        # From its own folder, where its ROMs are.
        (cd "$(dirname "${ZESARUX}")" && exec "${ZESARUX}" "${ZESARUX_PARAMS[@]}" "${OUTPUT_FILE}") &
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
