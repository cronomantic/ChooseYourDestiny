# Distribution Build System

This document describes the improved distribution build system for ChooseYourDestiny.

## Overview

The distribution system has been **improved and streamlined** to support creating redistributable packages for **Windows, Linux, and macOS** from any platform.

### Key Improvements

1. **Cross-platform support**: Build packages for Windows, Linux, and macOS
2. **Auto-detection**: Automatically detects your current platform
3. **Modular design**: Clean separation of concerns, easier to maintain
4. **Better error handling**: Clear warnings for missing files
5. **Added preprocessor**: Includes the new `cydc_preprocessor.py` module
6. **Flexible usage**: Command-line options for different build scenarios

## Files

- **`get_version.py`**: Cross-platform version extraction (replaces `get_ver.sh`)
- **`make_dist.py`**: Main distribution builder (improved from original)
- **`make_dist.sh`**: Unix/Linux/macOS wrapper script
- **`make_dist.cmd`**: Windows wrapper script

## Quick Start

### Building for Your Current Platform

**Windows:**
```cmd
make_dist.cmd
```

**Linux/macOS:**
```bash
./make_dist.sh
```

**Using Python directly (all platforms):**
```bash
python get_version.py
python make_dist.py
```

### Building for All Platforms

To create distribution packages for all platforms at once:

**Windows:**
```cmd
python get_version.py
python make_dist.py --all
```

**Linux/macOS:**
```bash
python3 get_version.py
python3 make_dist.py --all
```

### Building for Specific Platforms

To create a package for a specific platform only:

```bash
# Windows package
python make_dist.py --platform windows

# Linux package
python make_dist.py --platform linux

# macOS package
python make_dist.py --platform macos
```

## Command-Line Options

```
usage: make_dist.py [-h] [--platform {windows,linux,macos,all}] [--all] [--skip-compile]

Create redistributable packages for ChooseYourDestiny

optional arguments:
  -h, --help            show this help message and exit
  --platform {windows,linux,macos,all}, -p {windows,linux,macos,all}
                        Target platform (default: current platform)
  --all, -a             Create packages for all platforms
  --skip-compile        Skip source file copying and translation compilation
```

## What Gets Packaged

### Common Files (All Platforms)

- Python source code (compiler, tools)
- Documentation (manuals, tutorials in PDF format)
- Example adventures
- Assets (images, fonts)
- License and README files
- Translation files (.mo compiled from .po)

### Platform-Specific

#### Windows
- `make_adv.cmd`, `make_adventure_gui.cmd`
- Pre-compiled tools: `sjasmplus.exe`, `csc.exe`
- Python runtime (embeddable Python in `dist/python/`)
- Batch script wrappers

#### Linux/macOS
- `make_adv.sh`, `make_adventure_gui.sh` (with execute permissions)
- Pre-compiled `csc` binary (platform-specific)
- Users must compile `sjasmplus` from `external/sjasmplus/`

## Output Files

The script creates ZIP files with the following naming convention:

- **Windows**: `ChooseYourDestiny_Win_x64_<version>_<date>.zip`
- **Linux**: `ChooseYourDestiny_Linux_x64_<version>_<date>.zip`
- **macOS**: `ChooseYourDestiny_macOS_x64_<version>_<date>.zip`

Where:
- `<version>` is extracted from git tags (e.g., `v0_8_0`)
- `<date>` is in format `YYYY_MM_DD`

Example: `ChooseYourDestiny_Win_x64_v0_8_0_2026_02_21.zip`

## Version Management

Version information is automatically extracted from git tags:

```bash
# The version comes from the most recent git tag
git describe --abbrev=0 --tags
```

If git is not available or no tags exist, it defaults to version `dev`.

The version is written to `version.txt` and used in the ZIP filename.

## Package Contents

### Windows Package
Users get a **fully standalone package** with:
- All Python scripts
- Embedded Python runtime (no installation needed)
- Pre-compiled tools (sjasmplus, csc)
- Complete documentation
- Example adventures

**No additional software installation required!**

### Linux/macOS Package
Users get:
- All Python scripts
- Pre-compiled csc binary
- Complete documentation
- Example adventures
- Source code for sjasmplus in `external/`

**Requirements:**
- Python 3.6+ (usually pre-installed)
- Compile sjasmplus from source (one-time setup)

## Building on Different Platforms

### On Windows

```cmd
REM Install Python 3 if not already installed
REM Open Command Prompt or PowerShell

cd path\to\ChooseYourDestiny
make_dist.cmd --all
```

### On Linux/macOS

```bash
# Ensure Python 3 is installed (usually is)
cd /path/to/ChooseYourDestiny

# Make scripts executable (first time only)
chmod +x make_dist.sh get_version.py make_dist.py

# Build all platforms
./make_dist.sh --all
```

## For Linux/macOS Users

When distributing to Linux/macOS users, they need to perform a one-time setup to compile sjasmplus:

```bash
# Navigate to the sjasmplus source
cd external/sjasmplus

# Clean and compile
make clean
make

# The binary 'sjasmplus' will be created in the same directory
# The system is already configured to use it from there
```

## Maintenance Notes

### Adding New Source Files

Edit `make_dist.py` and add file paths to the `get_source_files()` function:

```python
def get_source_files():
    """Return list of source files to include in distribution."""
    return [
        "cydc_cli.py",
        "cydc/new_module.py",  # Add new files here
        # ... rest of files
    ]
```

### Adding New Platform-Specific Files

Edit the `get_platform_specific_files()` function:

```python
def get_platform_specific_files(target_platform):
    """Return platform-specific files."""
    if target_platform == "windows":
        return [
            "tools/new_tool.exe",  # Add Windows-specific files
            # ...
        ]
    elif target_platform in ["linux", "macos"]:
        return [
            "tools/new_tool",  # Add Unix-specific files
            # ...
        ]
```

## Migration from Old System

The old distribution system files are:
- `get_ver.sh` - now replaced by `get_version.py`
- `make_dist.py` (old) - now replaced by the new `make_dist.py`
- `make_dist.sh` (old) - now replaced by the new `make_dist.sh`

**Key Differences:**

1. **Old system**: Only created Windows packages
2. **New system**: Creates packages for all platforms
3. **Old system**: Required bash for version extraction
4. **New system**: Pure Python, works on all platforms
5. **Old system**: Hardcoded file lists
6. **New system**: Modular functions, easier to maintain

## Troubleshooting

### "Git not found" Warning

If you see:
```
Warning: Could not get version from git. Using 'dev' version.
```

This means git is not in your PATH or no tags exist. The script will still work, using `dev` as the version.

**Solution**: Install git or ensure it's in your PATH.

### Missing Files Warnings

If you see warnings like:
```
Warning: File not found: some/file.ext
```

The file will be skipped from the ZIP. Check if:
1. The file path is correct
2. The file exists in your workspace
3. You compiled necessary dependencies (e.g., sjasmplus for Linux)

### Permission Errors (Linux/macOS)

If scripts aren't executable:
```bash
chmod +x make_dist.sh get_version.py make_dist.py
```

## Testing

After building, verify the ZIP file contents:

```bash
# List contents
unzip -l ChooseYourDestiny_*.zip

# Extract and test
unzip ChooseYourDestiny_*.zip -d test_dist
cd test_dist
# Try compiling the demo adventure
```

## Future Enhancements

Potential improvements for future versions:

1. **Code signing**: Sign executables and packages
2. **Checksums**: Generate SHA256 checksums for integrity verification
3. **ARM support**: Add ARM64 builds for Raspberry Pi and Apple Silicon
4. **Auto-upload**: Upload to GitHub releases automatically
5. **Delta patches**: Create update patches for minor version changes
6. **Installer**: Create installers (MSI for Windows, DEB/RPM for Linux)

## License

This distribution system is part of ChooseYourDestiny and follows the same MIT License.
