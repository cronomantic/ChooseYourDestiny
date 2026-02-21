#!/usr/bin/env python3

"""
Locale file updater for ChooseYourDestiny
Extracts translatable strings from Python source files and updates .po files.

This script:
1. Scans Python source files for translatable strings marked with _()
2. Generates/updates .po files for each supported language
3. Preserves existing translations while adding new strings

MIT License - Copyright (c) 2024-2026 Sergio Chico
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def find_python_files(base_path):
    """Find all Python files that may contain translatable strings."""
    files = []
    patterns = [
        "make_adventure.py",
        "make_adventure_gui.py",
        "src/cydc/cydc/cydc.py",
        "src/cydc/cydc/cydc_parser.py",
        "src/cydc/cydc/cydc_lexer.py",
        "src/cydc/cyd_chr_conv.py",
    ]
    
    for pattern in patterns:
        path = base_path / pattern
        if path.exists():
            files.append(path)
    
    return files


def extract_strings_manual(file_path):
    """
    Extract translatable strings from Python file manually.
    Looks for _("string") and _('string') patterns.
    Returns dict of {msgid: [locations]}
    """
    strings = {}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.splitlines()
    
    # Pattern to match _("...") or _('...')
    # This is a simple pattern; doesn't handle all edge cases
    pattern = r'_\(["\'](.+?)["\']\)'
    
    for line_num, line in enumerate(lines, 1):
        matches = re.finditer(pattern, line)
        for match in matches:
            msgid = match.group(1)
            # Unescape common escape sequences for storage
            msgid = msgid.replace(r'\"', '"').replace(r"\'", "'")
            
            location = f"{file_path.name}:{line_num}"
            if msgid not in strings:
                strings[msgid] = []
            strings[msgid].append(location)
    
    return strings


def update_po_file(po_path, strings, project_name):
    """
    Update or create a .po file with extracted strings.
    Preserves existing translations.
    """
    # Read existing translations
    existing_translations = {}
    if po_path.exists():
        print(f"  Reading existing translations from {po_path.name}")
        current_msgid = None
        current_msgstr = None
        
        with open(po_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('msgid "'):
                    if current_msgid and current_msgstr:
                        existing_translations[current_msgid] = current_msgstr
                    current_msgid = line[7:-1]  # Remove msgid " and "
                    current_msgstr = None
                elif line.startswith('msgstr "'):
                    current_msgstr = line[8:-1]  # Remove msgstr " and "
                elif line.startswith('"') and current_msgstr is not None:
                    # Continuation line for msgstr
                    current_msgstr += '\n' + line[1:-1]
            
            # Don't forget the last entry
            if current_msgid and current_msgstr:
                existing_translations[current_msgid] = current_msgstr
    else:
        print(f"  Creating new .po file: {po_path.name}")
    
    # Create .po file
    po_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(po_path, 'w', encoding='utf-8') as f:
        # Write header
        now = datetime.now().strftime("%Y-%m-%d %H:%M+0000")
        f.write(f"""# Spanish translations for {project_name} package.
# Copyright (C) {datetime.now().year} THE PACKAGE'S COPYRIGHT HOLDER
# This file is distributed under the same license as the PACKAGE package.
# Automatically generated, {datetime.now().year}.
#
msgid ""
msgstr ""
"Project-Id-Version: ChooseYourDestiny 1.0.0\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: {now}\\n"
"PO-Revision-Date: {now}\\n"
"Last-Translator: Automatically generated\\n"
"Language-Team: Spanish\\n"
"Language: es\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

""")
        
        # Write entries
        for msgid, locations in sorted(strings.items()):
            # Write location comments
            for location in locations:
                f.write(f"#: {location}\n")
            
            # Write msgid
            f.write(f'msgid "{msgid}"\n')
            
            # Write msgstr (use existing translation or empty)
            msgstr = existing_translations.get(msgid, "")
            f.write(f'msgstr "{msgstr}"\n\n')
    
    print(f"  ✓ Updated {po_path.name} with {len(strings)} strings")


def update_locale_for_project(base_path, project_name, source_files, locale_dir):
    """Update locale files for a specific project."""
    print(f"\nProcessing {project_name}:")
    
    # Extract strings from all source files
    all_strings = {}
    for source_file in source_files:
        if not source_file.exists():
            print(f"  Warning: {source_file} not found, skipping")
            continue
        
        print(f"  Scanning {source_file.name}")
        strings = extract_strings_manual(source_file)
        
        # Merge strings, combining location lists
        for msgid, locations in strings.items():
            if msgid not in all_strings:
                all_strings[msgid] = []
            all_strings[msgid].extend(locations)
    
    if not all_strings:
        print(f"  No translatable strings found")
        return
    
    # Update .po file for Spanish
    po_path = base_path / locale_dir / "es" / "LC_MESSAGES" / f"{project_name}.po"
    update_po_file(po_path, all_strings, project_name)


def main():
    """Main entry point."""
    base_path = Path(__file__).parent
    
    print("=" * 60)
    print("ChooseYourDestiny Locale Updater")
    print("=" * 60)
    print("Extracting translatable strings and updating .po files...")
    
    # Update locales for main scripts
    update_locale_for_project(
        base_path,
        "make_adventure",
        [base_path / "make_adventure.py"],
        Path("locale")
    )
    
    update_locale_for_project(
        base_path,
        "make_adventure_gui",
        [base_path / "make_adventure_gui.py"],
        Path("locale")
    )
    
    # Update locales for cydc compiler
    update_locale_for_project(
        base_path,
        "cydc",
        [
            base_path / "src/cydc/cydc/cydc.py",
            base_path / "src/cydc/cydc/cydc_parser.py",
            base_path / "src/cydc/cydc/cydc_lexer.py",
        ],
        Path("src/cydc/cydc/locale")
    )
    
    # Update locales for font converter
    update_locale_for_project(
        base_path,
        "cyd_font_conv",
        [base_path / "src/cydc/cyd_chr_conv.py"],
        Path("src/cydc/locale")
    )
    
    print("\n" + "=" * 60)
    print("✓ Locale files updated successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the updated .po files")
    print("2. Add/update Spanish translations for new strings")
    print("3. Run make_dist.py to compile .po to .mo files")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
