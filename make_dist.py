#!/usr/bin/env python3

"""
Cross-platform distribution builder for ChooseYourDestiny
Creates redistributable ZIP files for Windows, Linux, and macOS.

MIT License - Copyright (c) 2024-2026 Sergio Chico
"""

import argparse
import os
import platform
import shutil
import struct
import sys
import zipfile
from pathlib import Path


def compile_po_to_mo(po_path, mo_path):
    """Compile a gettext .po file into a binary .mo file (pure Python).

    Produces a little-endian MO file (magic 0xDE120495) compatible with the
    GNU gettext runtime and Python's ``gettext`` module.
    """

    def _unescape(s):
        out = []
        i = 0
        while i < len(s):
            if s[i] == "\\" and i + 1 < len(s):
                c = s[i + 1]
                if c == "n":
                    out.append("\n")
                elif c == "t":
                    out.append("\t")
                elif c == "r":
                    out.append("\r")
                elif c == '"':
                    out.append('"')
                elif c == "\\":
                    out.append("\\")
                else:
                    out.append(s[i])
                    i += 1
                    continue
                i += 2
            else:
                out.append(s[i])
                i += 1
        return "".join(out)

    catalog = {}        # msgid (str) → msgstr (str)
    msgid = msgstr = ""
    in_id = in_str = False

    def _save():
        if in_str:
            catalog[msgid] = msgstr

    with open(po_path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                _save()
                in_id = in_str = False
                continue
            if line.startswith("msgid "):
                _save()
                in_id, in_str = True, False
                msgid = _unescape(line[6:].strip()[1:-1])
                msgstr = ""
            elif line.startswith("msgstr "):
                in_id, in_str = False, True
                msgstr = _unescape(line[7:].strip()[1:-1])
            elif line.startswith('"') and line.endswith('"'):
                s = _unescape(line[1:-1])
                if in_id:
                    msgid += s
                elif in_str:
                    msgstr += s
    _save()

    # Keep header (msgid == "") and entries that have a non-empty translation.
    entries = sorted(
        [
            (k.encode("utf-8"), v.encode("utf-8"))
            for k, v in catalog.items()
            if v or k == ""
        ],
        key=lambda e: e[0],
    )
    N = len(entries)

    # MO layout (all uint32, little-endian):
    #   header         28 bytes  (7 × uint32)
    #   orig table     N × 8 bytes
    #   trans table    N × 8 bytes
    #   orig strings   (NUL-terminated, packed)
    #   trans strings  (NUL-terminated, packed)
    O = 28           # offset of original-strings table
    T = O + N * 8    # offset of translated-strings table
    S = T + N * 8    # first byte of string data

    orig_blob = b"\x00".join(k for k, _ in entries) + (b"\x00" if N else b"")
    tran_blob = b"\x00".join(v for _, v in entries) + (b"\x00" if N else b"")

    orig_table = b""
    tran_table = b""
    orig_pos = S
    tran_pos = S + len(orig_blob)
    for k, v in entries:
        orig_table += struct.pack("<II", len(k), orig_pos)
        tran_table += struct.pack("<II", len(v), tran_pos)
        orig_pos += len(k) + 1
        tran_pos += len(v) + 1

    os.makedirs(os.path.dirname(mo_path), exist_ok=True)
    with open(mo_path, "wb") as fh:
        fh.write(struct.pack("<7I", 0x950412DE, 0, N, O, T, 0, T + N * 8))
        fh.write(orig_table)
        fh.write(tran_table)
        fh.write(orig_blob)
        fh.write(tran_blob)
    print(f"  Compiled {os.path.relpath(po_path)} -> {os.path.relpath(mo_path)}")


def compile_locale_dir(locale_dir):
    """Walk *locale_dir* and compile every .po file to its sibling .mo file."""
    for dirpath, _, filenames in os.walk(locale_dir):
        for fname in filenames:
            if fname.endswith(".po"):
                po = os.path.join(dirpath, fname)
                mo = os.path.splitext(po)[0] + ".mo"
                compile_po_to_mo(po, mo)


def get_source_files():
    """Return list of source files to include in distribution."""
    return [
        "cydc_cli.py",
        "cyd_chr_conv.py",
        "cydc/cydc.py",
        "cydc/cydc_codegen.py",
        "cydc/cydc_font.py",
        "cydc/cydc_lexer.py",
        "cydc/cydc_parser.py",
        "cydc/cydc_preprocessor.py",  # NEW: Added preprocessor
        "cydc/cydc_txt_compress.py",
        "cydc/cyd.py",
        "cydc/cydc_utils.py",
        "cydc/cydc_music.py",
        "cydc/cydc_csc.py",
        "cydc/plus3fs.py",
        "cydc/mkp3fs.py",
        "cydc/ply/lex.py",
        "cydc/ply/yacc.py",
        "cydc/pyZX0/compress.py",
        "cydc/pyZX0/optimize.py",
        "cydc/pyZX0/pyzx0.py",
        "cydc/pyZX0/README.md",
        "cydc/pyZX0/LICENSE",
        "cydc/cyd/bank_zx128.asm",
        "cydc/cyd/cyd_plus3.asm",
        "cydc/cyd/cyd_tape.asm",
        "cydc/cyd/dzx0_turbo.asm",
        "cydc/cyd/dzx0_turbo_plus3.asm",
        "cydc/cyd/interpreter.asm",
        "cydc/cyd/loaderplus3.asm",
        "cydc/cyd/loadertape.asm",
        "cydc/cyd/music_manager.asm",
        "cydc/cyd/music_manager_tape.asm",
        "cydc/cyd/plus3dos.asm",
        "cydc/cyd/screen_manager.asm",
        "cydc/cyd/screen_manager_tape.asm",
        "cydc/cyd/sysvars.asm",
        "cydc/cyd/text_manager.asm",
        "cydc/cyd/inkey.asm",
        "cydc/cyd/vars.asm",
        "cydc/cyd/VTII10bG.asm",
        "cydc/cyd/VTII10bG_vars.asm",
        "cydc/cyd/savegame_plus3.asm",
        "cydc/cyd/savegame_tape.asm",
        "cydc/cyd/wyz_player.asm",
    ]


def get_common_files():
    """Return list of files common to all platforms."""
    return [
        "make_adventure.py",
        "LICENSE",
        "version.txt",
        "test.cyd",
        "MANUAL_es.md",
        "MANUAL_en.md",
        "README.md",
        "dist/cyd_chr_conv.py",
        "dist/cydc_cli.py",
        "IMAGES/readme.txt",
        "TRACKS/readme.txt",
        "documentation/es/MANUAL_es.pdf",
        "documentation/en/MANUAL_en.pdf",
        "documentation/es/TUTORIAL_es.pdf",
        "documentation/en/TUTORIAL_en.pdf",
        "make_adventure_gui.py",
    ]


def get_common_dirs():
    """Return list of directories common to all platforms."""
    return ["assets", "examples", "dist/cydc", "locale", "dist/locale"]


def get_platform_specific_files(target_platform):
    """Return platform-specific files."""
    if target_platform == "windows":
        return [
            "make_adv.cmd",
            "tools/sjasmplus.exe",
            "dist/csc.exe",
            "dist/cyd_chr_conv.cmd",
            "dist/cydc.cmd",
            "make_adventure_gui.cmd",
        ]
    elif target_platform in ["linux", "macos"]:
        return [
            "make_adv.sh",
            "make_adventure_gui.sh",
            "dist/csc",
        ]
    return []


def get_platform_specific_dirs(target_platform):
    """Return platform-specific directories."""
    if target_platform == "windows":
        # Include Python runtime for Windows
        return ["dist/python"]
    return []


def copy_source_files(current_path, src_path, dst_path):
    """Copy source files to dist directory."""
    print("Copying source files...")
    for file in get_source_files():
        src_file = os.path.join(current_path, src_path, file)
        dst_file = os.path.join(current_path, dst_path, file)
        os.makedirs(os.path.dirname(dst_file), exist_ok=True)
        if os.path.exists(src_file):
            shutil.copy(src_file, dst_file)
        else:
            print(f"  Warning: Source file not found: {src_file}")


def compile_translations(current_path, src_path):
    """Compile all translations."""
    locale_dirs = [
        os.path.join(current_path, "locale"),
        os.path.join(current_path, src_path, "cydc", "locale"),
        os.path.join(current_path, src_path, "locale"),
    ]
    print("Compiling translations...")
    for locale_dir in locale_dirs:
        if os.path.exists(locale_dir):
            compile_locale_dir(locale_dir)


def copy_translations(current_path, src_path, dst_path):
    """Copy locale directories to dist."""
    print("Copying translations...")
    # Copy cydc locale
    src_locale = os.path.join(current_path, src_path, "cydc", "locale")
    dst_locale = os.path.join(current_path, dst_path, "cydc", "locale")
    if os.path.exists(src_locale):
        shutil.copytree(src_locale, dst_locale, dirs_exist_ok=True)
    
    # Copy main locale
    src_locale = os.path.join(current_path, src_path, "locale")
    dst_locale = os.path.join(current_path, dst_path, "locale")
    if os.path.exists(src_locale):
        shutil.copytree(src_locale, dst_locale, dirs_exist_ok=True)


def collect_files(current_path, dirs_list, files_list):
    """Collect all files from directories, excluding __pycache__."""
    all_files = list(files_list)
    for d in dirs_list:
        dir_path = os.path.join(current_path, d)
        if not os.path.exists(dir_path):
            print(f"  Warning: Directory not found: {d}")
            continue
        result = [os.path.join(x[0], t) for x in os.walk(dir_path) for t in x[2]]
        result = [x for x in result if "__pycache__" not in x]
        # Make paths relative
        result = [os.path.relpath(x, current_path) for x in result]
        all_files.extend(result)
    return all_files


def get_version_string(current_path):
    """Get version string from version.txt."""
    ver_file_path = os.path.join(current_path, "version.txt")
    version = ""
    if os.path.exists(ver_file_path):
        with open(ver_file_path, "r") as f:
            version = f.read().strip().replace("\n", "").replace("\r", "")
        if version:
            version = "_" + version
    return version


def create_distribution_zip(current_path, target_platform, version_string):
    """Create distribution ZIP for specified platform."""
    platform_names = {
        "windows": "Win_x64",
        "linux": "Linux_x64",
        "macos": "macOS_x64",
    }
    
    platform_name = platform_names.get(target_platform, target_platform)
    zip_filename = f"ChooseYourDestiny_{platform_name}{version_string}.zip"
    zip_path = os.path.join(current_path, zip_filename)
    
    print(f"\nCreating {target_platform} distribution: {zip_filename}")
    
    # Collect files
    common_files = get_common_files()
    platform_files = get_platform_specific_files(target_platform)
    common_dirs = get_common_dirs()
    platform_dirs = get_platform_specific_dirs(target_platform)
    
    all_dirs = common_dirs + platform_dirs
    all_files = collect_files(current_path, all_dirs, common_files + platform_files)
    
    # Create ZIP
    files_added = 0
    files_missing = 0
    
    with zipfile.ZipFile(
        zip_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as zf:
        for file_path in all_files:
            full_path = os.path.join(current_path, file_path)
            if os.path.exists(full_path):
                zf.write(full_path, arcname=file_path)
                files_added += 1
            else:
                print(f"  Warning: File not found: {file_path}")
                files_missing += 1
    
    file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"  [OK] Created: {zip_filename} ({file_size_mb:.2f} MB)")
    print(f"  Files: {files_added} added, {files_missing} missing")
    
    return zip_path


def detect_current_platform():
    """Detect current operating system platform."""
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "macos"
    elif system == "linux":
        return "linux"
    else:
        return "linux"  # Default to linux for other Unix-like systems


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Create redistributable packages for ChooseYourDestiny",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python make_dist.py --all              # Create packages for all platforms
  python make_dist.py --platform windows # Create Windows package only
  python make_dist.py --platform linux   # Create Linux package only
  python make_dist.py                    # Create package for current platform
        """,
    )
    
    parser.add_argument(
        "--platform",
        "-p",
        choices=["windows", "linux", "macos", "all"],
        help="Target platform (default: current platform)",
    )
    
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Create packages for all platforms",
    )
    
    parser.add_argument(
        "--skip-compile",
        action="store_true",
        help="Skip source file copying and translation compilation",
    )
    
    args = parser.parse_args()
    
    current_path = Path(__file__).parent
    src_path = "src/cydc"
    dst_path = "dist/"
    
    # Determine target platforms
    if args.all or args.platform == "all":
        platforms = ["windows", "linux", "macos"]
    elif args.platform:
        platforms = [args.platform]
    else:
        platforms = [detect_current_platform()]
    
    print(f"ChooseYourDestiny Distribution Builder")
    print(f"========================================")
    print(f"Target platform(s): {', '.join(platforms)}")
    print()
    
    # Prepare source files and translations (once for all platforms)
    if not args.skip_compile:
        copy_source_files(current_path, src_path, dst_path)
        compile_translations(current_path, src_path)
        copy_translations(current_path, src_path, dst_path)
    else:
        print("Skipping source file compilation (--skip-compile)")
    
    # Get version
    version_string = get_version_string(current_path)
    if version_string:
        print(f"Version: {version_string[1:]}")  # Remove leading underscore
    else:
        print("Version: (no version file)")
    print()
    
    # Create distribution packages
    for target_platform in platforms:
        try:
            create_distribution_zip(current_path, target_platform, version_string)
        except Exception as e:
            print(f"  [X] Error creating {target_platform} package: {e}")
            continue
    
    print("\n[OK] Distribution build complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
