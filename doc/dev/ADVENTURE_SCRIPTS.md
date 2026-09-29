# Adventure Building Scripts

This document describes the improved adventure building scripts for ChooseYourDestiny, now with consistent features across Windows, Linux, and macOS.

## Overview

ChooseYourDestiny provides two methods for building adventures:

1. **Command-line scripts** (`make_adv.*`) - For quick builds and automation
2. **GUI application** (`make_adventure_gui.*`) - For visual, user-friendly interface

Both methods are now **fully cross-platform** with feature parity.

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

**Windows:**
```cmd
make_adv.cmd
```

**Linux/macOS:**
```bash
chmod +x make_adv.sh  # First time only
./make_adv.sh
```

### Configuration

Edit the variables at the top of the script:

```bash
# Name of your game (without .cyd extension)
GAME="test"

# Target platform: 48k, 128k, or plus3
TARGET="128k"

# Number of lines for screen compression (192 = full screen)
IMGLINES="192"

# Path to loading screen
LOAD_SCR="./IMAGES/LOAD.scr"

# Extra compiler parameters (optional)
CYDC_EXTRA_PARAMS=""

# Run emulator after compilation
# Options: none, internal, default (Windows), custom (Linux/Mac)
RUN_EMULATOR="none"

# Backup settings
BACKUP_CYD="no"
BACKUP_MAX_FILES=0  # 0 = unlimited
```

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
Requires ZEsarUX at `.\tools\ZEsarUX_win-11.0\zesarux.exe`

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
ZESARUX_PATH="./tools/ZEsarUX_linux/zesarux"
```

### Backup Feature

Enable automatic backups of your source files:

```bash
BACKUP_CYD="yes"
BACKUP_MAX_FILES=10  # Keep only 10 most recent backups
```

Backups are saved to `./BACKUP/` with timestamps:
```
BACKUP/
  test_2026-02-21_14-30-45.cyd
  test_2026-02-21_15-22-10.cyd
  ...
```

### Output Files

Depending on the target platform:

- **48k / 128k**: `{GAME}.TAP` (tape file)
- **plus3**: `{GAME}.DSK` (disk image)

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
2. **Configure** your adventure:
   - Game name
   - Target platform (48k/128k/+3)
   - Loading screen
   - Image compression settings
3. **Compile** by clicking the build button
4. **Test** your adventure with the integrated emulator launcher

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
CYDC_EXTRA_PARAMS="--verbose --debug"
```

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
for game in game1 game2 game3; do
  sed -i "s/GAME=.*/GAME=\"$game\"/" make_adv.sh
  ./make_adv.sh
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

### "Source file not found"

Make sure your `.cyd` file exists and the `GAME` variable matches the filename.

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

The new scripts are **backward compatible**. Your existing configuration will work, but you gain:

### New Features

1. ✨ **Better error messages** - Clear indication of what went wrong
2. ✨ **Backup system** - Automatic source file backups with rotation
3. ✨ **Improved emulator integration** - More options, better detection
4. ✨ **Cross-platform consistency** - Same features everywhere
5. ✨ **Enhanced documentation** - Inline comments and help text

### Changes

- **Windows**: ZEsarUX path updated to `tools\ZEsarUX_win-11.0\`
- **Linux/Mac**: New `custom` emulator mode with configurable command
- **All platforms**: Enhanced error checking and user feedback

Old scripts are backed up as:
- `make_adv_old.cmd` / `make_adv_old.sh`
- `make_adventure_gui_old.cmd` / `make_adventure_gui_old.sh`

## Examples

### Example 1: Quick Compilation

Compile a game called "mygame.cyd" for 128k:

**Edit make_adv script:**
```bash
GAME="mygame"
TARGET="128k"
```

**Run:**
```bash
./make_adv.sh  # or make_adv.cmd on Windows
```

### Example 2: With Backups and Emulator

Enable backups and auto-launch:

```bash
GAME="adventure"
TARGET="48k"
BACKUP_CYD="yes"
BACKUP_MAX_FILES=5
RUN_EMULATOR="custom"
CUSTOM_EMULATOR_CMD="fuse ${OUTPUT_FILE}"
```

### Example 3: +3 Disk Image

Create a +3 disk image:

```bash
GAME="diskgame"
TARGET="plus3"
```

Output: `diskgame.DSK`

## Tips and Best Practices

1. **Use version control**: Keep your `.cyd` files in git/svn
2. **Enable backups**: Useful safety net during development
3. **Test on target**: Use emulators matching your target platform
4. **Start with 48k**: Smaller, faster, easier to debug
5. **Organize assets**: Keep screens in `IMAGES/`, music in `TRACKS/`
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
