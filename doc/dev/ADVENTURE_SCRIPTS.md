# Adventure Building Scripts

This document describes the improved adventure building scripts for ChooseYourDestiny, now with consistent features across Windows, Linux, and macOS.

## Overview

ChooseYourDestiny provides two methods for building adventures:

1. **Command-line scripts** (`make_adv.*`) - For quick builds and automation
2. **GUI application** (`make_adventure_gui.*`) - For visual, user-friendly interface

Both methods are now **fully cross-platform** with feature parity.

Both build a **project**: the folder of a game, with its main `.cyd` file (and the
files it INCLUDEs), `IMAGES/`, `TRACKS/`, `SFX.ASM`, the loading screen,
`tokens.json`, `charset.json` and an optional `cyd_project.ini` with the game's
settings (main file, target, paths, image lines, compiler options...). CYD's own
folder can't be a project; its subfolders can (each example in `examples/` is
one). Both run `make_adventure.py`, which does the build.

## Files

### Command-Line Builder

- **`make_adv.cmd`** - Windows batch script
- **`make_adv.sh`** - Linux/macOS/BSD/Unix bash script

### GUI Builder

- **`make_adventure_gui.cmd`** - Windows GUI launcher
- **`make_adventure_gui.sh`** - Linux/macOS/BSD/Unix GUI launcher

## Command-Line Builder (`make_adv`)

### Features

✅ **Cross-platform** - Same features on Windows, Linux, and macOS
✅ **Configurable** - Edit variables at the top of the script
✅ **Automatic backup** - Optional timestamped backups with rotation
✅ **Emulator integration** - Launch your game after compilation
✅ **Error handling** - Clear error messages and status reporting

### Quick Start

```
make_adv.cmd [PROJECT] [TARGET]
./make_adv.sh [PROJECT] [TARGET]
```

`PROJECT` is the folder of the game, or its main `.cyd` file; `TARGET` (`48k`,
`128k`, `plus3`, `esxdos`, `mld`, `mld128`), if given, is used instead of the
project's. They can go in any order.

**Windows:**
```cmd
make_adv.cmd ..\my_game
make_adv.cmd examples\test 48k
```
The project's folder (or its `.cyd`) can also be **dragged onto `make_adv.cmd`**.

**Linux/macOS:**
```bash
chmod +x make_adv.sh  # First time only
./make_adv.sh ../my_game
./make_adv.sh examples/test 48k
```

To start a new project: `python make_adventure.py --new ../my_game` (on Windows,
`dist\python\python make_adventure.py --new ..\my_game`), or *New…* in the GUI.

### Configuration

The game's settings (main file, target, image lines, loading screen, compiler
options...) are in its `cyd_project.ini`. The variables at the top of the script
are for this computer:

```bash
# The project to compile when none is given: the folder of the game (or its
# main .cyd file). Relative to the script's folder, or absolute.
PROJECT=""

# Target platform, instead of the project's (empty: the project's)
TARGET=""

# Name of the game, instead of the project's (empty: the project's)
GAME=""

# Extra parameters for make_adventure.py (optional)
CYDC_EXTRA_PARAMS=""

# Run emulator after compilation
# Options: none, internal, default (Windows), custom (Linux/Mac)
RUN_EMULATOR="none"

# Path to ZEsarUX (empty: look for it, see below)
ZESARUX_PATH=""

# Backup settings (empty: the project's "backup" setting)
BACKUP_CYD=""
BACKUP_MAX_FILES=0  # 0 = unlimited
```

`IMGLINES` and `LOAD_SCR` are gone: they are now `image_lines` and `load_scr` in
the project's `cyd_project.ini`.

The script reads the project with `make_adventure.py --describe` (its folder,
main file, name, target, output folder and backup setting), builds it with
`make_adventure.py`, backs up the main `.cyd` and runs the emulator on the
compiled file.

### Emulator Integration

#### Windows

**Option 1: Default emulator** (uses Windows file association)
```cmd
SET RUN_EMULATOR=default
```
Launches TAP/DSK files with your default program.

**Option 2: Internal ZEsarUX**
```cmd
SET RUN_EMULATOR=internal
```
Looks for `zesarux.exe` in `ZESARUX_PATH` if set, else in `.\tools\zesarux\`, else in
the `.\tools\ZEsarUX*\` folder with the highest version (`ZEsarUX_win-13.0` before
`ZEsarUX_win-11.0`), else on the `PATH`. The +3 runs as `P341`, and esxdos as a 128K
with divMMC and the project's output folder as the SD card.

#### Linux/macOS

**Option 1: Custom command**
```bash
RUN_EMULATOR="custom"
CUSTOM_EMULATOR_CMD="fuse ${OUTPUT_FILE}"
```
Popular emulators:
- **Fuse**: `fuse ${OUTPUT_FILE}`
- **SpecEmu**: `spectemu ${OUTPUT_FILE}`
- **ZXSpin**: `zxspin ${OUTPUT_FILE}`

**Option 2: Internal ZEsarUX**
```bash
RUN_EMULATOR="internal"
ZESARUX_PATH=""   # empty: ./tools/zesarux/, the newest ./tools/ZEsarUX-*/ or the PATH
```
Same search and machines as on Windows; `tools/build_emu_tools.sh` builds it into
`./tools/ZEsarUX-<version>/`. `tests/test_make_adv.py` checks both scripts.

### Backup Feature

Enable automatic backups of the main `.cyd` file, for every project with
`backup = yes` in its `cyd_project.ini`, or for all of them in the script:

```bash
BACKUP_CYD="yes"
BACKUP_MAX_FILES=10  # Keep only 10 most recent backups
```

Backups are saved to the project's `BACKUP/` folder with timestamps:
```
my_game/BACKUP/
  my_game_2026-02-21_14-30-45.cyd
  my_game_2026-02-21_15-22-10.cyd
  ...
```

### Output Files

Everything the build delivers goes to the project's output folder (`OUTPUT/` by
default, `output` in `cyd_project.ini`), depending on the target platform:

- **48k / 128k**: `{GAME}.tap` (tape file)
- **plus3**: `{GAME}.DSK` (disk image)
- **mld / mld128**: `{GAME}.MLD` (Dandanator Mini)
- **esxdos**: the SD files (`{GAME}.tap`, `{GAME}.DAT`, `NNN.CSC`, `NNN.BIN`, and
  `AUTOBOOT.BAS` + `ESXDOS.CFG` with `-autoboot`)

The compiler cuts the name to 10 characters on tape and to 8 on the other
targets. Intermediate files go to `OUTPUT/cyd_tmp/` (removed when the build ends
well, kept if it fails or with `--keep-temp`), and the compressed images are
cached in `OUTPUT/cyd_cache/`.

## GUI Builder (`make_adventure_gui`)

### Features

✅ **User-friendly interface** - No need to edit scripts
✅ **Visual configuration** - Point-and-click settings
✅ **Real-time feedback** - See compilation progress
✅ **Cross-platform** - Works on Windows, Linux, and macOS

### Quick Start

**Windows:**
```cmd
make_adventure_gui.cmd
```

**Linux/macOS:**
```bash
chmod +x make_adventure_gui.sh  # First time only
./make_adventure_gui.sh
```

### Requirements

#### Windows
- No additional requirements!
- Uses embedded Python runtime included in distribution

#### Linux/macOS
- **Python 3.6+** (usually pre-installed)
- **tkinter** GUI library

**Install tkinter:**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**Arch Linux:**
```bash
sudo pacman -S tk
```

**macOS:**
```bash
brew install python-tk
# or
pip3 install tk
```

### Using the GUI

1. **Launch** the GUI using the appropriate script
2. **Open a project** in the "Project" frame: **New…** makes one, **Open…** opens
   the folder of a game, **Recent** lists the last ones (the GUI reopens the last
   project when it starts). Without a project open it shows a welcome text and a
   **How to migrate it** button, and Compile and Check are disabled.
3. **Configure** your adventure:
   - Main file and game name (empty: the main file's name)
   - Target platform (48k/128k/+3/esxdos/mld/mld128)
   - Configure → Paths: the project's paths (relative to its folder), loading
     screen, INCLUDE / INCLUDE LIB / IMPORT folders
   - Image compression and compiler settings
4. **Compile** by clicking the build button
5. **Test** your adventure with the integrated emulator launcher

The project's settings are saved in its `cyd_project.ini` (only what isn't a
default, keeping its comments). This computer's settings (SjASMPlus, emulator,
appearance, recent projects) are saved in `cyd_gui_settings.ini` in CYD's folder.
An old `cyd_gui_settings.json` is migrated once (and renamed `.json.old`); its
game options are applied to the first project made with New….

## Platform-Specific Notes

### Windows

- **Python included**: No need to install Python separately
- **Pre-compiled tools**: sjasmplus.exe and other tools are ready to use
- **Emulator options**: Default Windows association or internal ZEsarUX

### Linux

**First-time setup:**

1. **Install Python 3** (usually pre-installed):
   ```bash
   sudo apt install python3  # Debian/Ubuntu
   sudo dnf install python3  # Fedora
   sudo pacman -S python     # Arch
   ```

2. **Compile sjasmplus** (one-time):
   ```bash
   cd external/sjasmplus
   make clean
   make
   cd ../..
   ```

3. **Make scripts executable**:
   ```bash
   chmod +x make_adv.sh make_adventure_gui.sh
   ```

**Recommended emulators:**
- **Fuse**: `sudo apt install fuse-emulator-sdl`
- **SpecEmu**: Available from various sources
- **ZEsarUX**: Download from https://github.com/chernandezba/zesarux

### macOS

**First-time setup:**

1. **Install Homebrew** (if not already):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python and tkinter**:
   ```bash
   brew install python-tk
   ```

3. **Compile sjasmplus** (one-time):
   ```bash
   cd external/sjasmplus
   make clean
   make
   cd ../..
   ```

4. **Make scripts executable**:
   ```bash
   chmod +x make_adv.sh make_adventure_gui.sh
   ```

**Recommended emulators:**
- **Fuse**: `brew install fuse-emulator`
- **ZEsarUX**: Download from https://github.com/chernandezba/zesarux

## Advanced Usage

### Command-Line Options

The underlying Python script (`make_adventure.py`) supports additional options:

```bash
# Windows
dist\python\python make_adventure.py --help

# Linux/Mac
python3 make_adventure.py --help
```

You can add these to `CYDC_EXTRA_PARAMS` in the scripts:

```bash
CYDC_EXTRA_PARAMS="--verbose --debug-errors"
```

Options given on the command line win over the project's `cyd_project.ini`, which
wins over the defaults. For settings that belong to the game, prefer its key in
`cyd_project.ini`.

Direct usage:

```bash
python make_adventure.py [options] [TARGET] [PROJECT]   # in any order
python make_adventure.py --new ../my_game 48k           # make a project and exit
python make_adventure.py ../my_game                     # build it for its target
python make_adventure.py 128k examples/test             # another target
```

Without `TARGET`, the project's. `--describe` prints the project's `ROOT=`,
`MAIN=`, `NAME=`, `TARGET=`, `OUTPUT=` and `BACKUP=` (the make_adv scripts use it);
`--sjasmplus PATH` uses another assembler (default: the bundled one).

### Automation

The command-line scripts are perfect for automation:

**Continuous compilation (Linux/Mac):**
```bash
while true; do
  ./make_adv.sh
  sleep 60
done
```

**Batch processing multiple games:**
```bash
for game in ../game1 ../game2 ../game3; do
  ./make_adv.sh "$game"
done
```

## Troubleshooting

### "Python not found"

**Windows**: Check that `dist\python\` folder exists and contains `python.exe`
**Linux/Mac**: Install Python 3: `sudo apt install python3`

### "tkinter not available"

Install the tkinter package for your system (see Requirements section above).

### "sjasmplus not found" (Linux/Mac)

Compile sjasmplus from source:
```bash
cd external/sjasmplus
make
```

### "No project given" / main file not found

Give the project's folder (or its main `.cyd`) as an argument, or set the
`PROJECT` variable in the script. If the folder has several `.cyd` files, say
which is the main one with `main` (or `name`) in its `cyd_project.ini`. CYD's own
folder can't be a project: put the game in its own folder.

### Emulator doesn't launch (Linux/Mac)

1. Check emulator is installed: `which fuse`
2. Verify CUSTOM_EMULATOR_CMD is correct
3. Try absolute paths: `CUSTOM_EMULATOR_CMD="/usr/bin/fuse ${OUTPUT_FILE}"`

### Permission denied (Linux/Mac)

Make scripts executable:
```bash
chmod +x make_adv.sh make_adventure_gui.sh
```

## Migration from Old Scripts

The scripts **no longer build a game in CYD's own folder**: every game is a
project in its own folder (and upgrading CYD no longer means copying the game).
To move a game from an older version (see the manual, section *Migrating a game
from an older version* / *Migrar un juego de una versión anterior*):

1. Make the project's folder, outside CYD's folder: `make_adventure.py --new
   FOLDER`, *New…* in the GUI, or just a new folder.
2. Copy the game's `.cyd` and the files it INCLUDEs, `IMAGES/`, `TRACKS/`,
   `SFX.ASM`, `tokens.json`, `charset.json` and the loading screen.
3. Change `INCLUDE "lib/x.cyd"` / `INCLUDE "../../lib/x.cyd"` to
   `INCLUDE LIB "x.cyd"` (the compiler suggests it).
4. Move what the make_adv script had to `cyd_project.ini`: `GAME` → `name` (or
   `main`), `TARGET` → `target`, `IMGLINES` → `image_lines`, `LOAD_SCR` →
   `load_scr`, each option of `CYDC_EXTRA_PARAMS` → its key in `[options]`.
5. The GUI's settings migrate on their own.
6. The compiled files are now in the project's `OUTPUT/`, and the backups in its
   `BACKUP/`.

Then build it with `make_adv.cmd FOLDER` (or drag the folder onto it),
`./make_adv.sh FOLDER`, the GUI's *Open…*, or `make_adventure.py FOLDER`.

## Examples

### Example 1: Quick Compilation

Compile a game in the folder `mygame` (with `mygame.cyd`) for 128k:

**`mygame/cyd_project.ini`:**
```ini
[project]
main = mygame.cyd
target = 128k
```

**Run:**
```bash
./make_adv.sh ../mygame  # or make_adv.cmd ..\mygame on Windows
```

### Example 2: With Backups and Emulator

Build `../adventure` when no project is given, with backups and auto-launch:

```bash
PROJECT="../adventure"
BACKUP_CYD="yes"
BACKUP_MAX_FILES=5
RUN_EMULATOR="custom"
CUSTOM_EMULATOR_CMD="fuse ${OUTPUT_FILE}"
```

### Example 3: +3 Disk Image

Create a +3 disk image of a project, whatever its target:

```bash
./make_adv.sh ../diskgame plus3
```

Output: `../diskgame/OUTPUT/diskgame.DSK`

## Tips and Best Practices

1. **Use version control**: Keep your `.cyd` files in git/svn
2. **Enable backups**: Useful safety net during development
3. **Test on target**: Use emulators matching your target platform
4. **Start with 48k**: Smaller, faster, easier to debug
5. **Organize assets**: Keep screens in the project's `IMAGES/`, music in its `TRACKS/`
6. **Comment your code**: Use `/* comments */` in your `.cyd` files
7. **Version your builds**: Include version numbers in game names

## Getting Help

- **Manual**: See `MANUAL_en.md` or `MANUAL_es.md`
- **Tutorial**: See `TUTORIAL_en.md` or `TUTORIAL_es.md`
- **Wiki**: https://github.com/cronomantic/ChooseYourDestiny/wiki
- **Issues**: https://github.com/cronomantic/ChooseYourDestiny/issues
- **Discussions**: https://github.com/cronomantic/ChooseYourDestiny/discussions

## License

These scripts are part of ChooseYourDestiny and follow the same MIT License.
