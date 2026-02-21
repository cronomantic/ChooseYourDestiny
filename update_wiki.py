#!/usr/bin/env python3

"""
Wiki updater for ChooseYourDestiny
Synchronizes documentation files to the GitHub Wiki repository.

This script:
1. Copies Markdown files from the main repository to the wiki
2. Commits and pushes changes to the wiki repository

MIT License - Copyright (c) 2024-2026 Sergio Chico
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(cmd, cwd=None, check=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr


def check_git_status(wiki_path):
    """Check if there are changes in the wiki repository."""
    success, stdout, stderr = run_command("git status --porcelain", cwd=wiki_path)
    return success and stdout.strip() != ""


def main():
    """Main entry point."""
    base_path = Path(__file__).parent
    wiki_path = base_path.parent / "ChooseYourDestiny.wiki"
    
    print("=" * 60)
    print("ChooseYourDestiny Wiki Updater")
    print("=" * 60)
    
    # Check if wiki repository exists
    if not wiki_path.exists():
        print(f"\n✗ Error: Wiki repository not found at {wiki_path}")
        print("\nTo clone the wiki:")
        print("  cd ..")
        print("  git clone https://github.com/cronomantic/ChooseYourDestiny.wiki.git")
        return 1
    
    print(f"\nWiki repository: {wiki_path}")
    
    # Files to sync
    files_to_sync = [
        "MANUAL_es.md",
        "MANUAL_en.md",
        "TUTORIAL_es.md",
        "TUTORIAL_en.md",
    ]
    
    print(f"\nSyncing documentation files to wiki...")
    
    copied_files = []
    for filename in files_to_sync:
        src = wiki_path / filename
        dst = wiki_path / filename
        
        if src.exists():
            # File is already in wiki, no need to copy
            print(f"  ✓ {filename} (already in wiki)")
            copied_files.append(filename)
        else:
            print(f"  ✗ {filename} not found in wiki")
    
    if not copied_files:
        print("\n✗ No files to sync")
        return 1
    
    # Check if there are changes
    print(f"\nChecking for changes...")
    if not check_git_status(wiki_path):
        print("  No changes detected in wiki repository")
        print("\n✓ Wiki is already up to date!")
        return 0
    
    # Show status
    success, stdout, stderr = run_command("git status --short", cwd=wiki_path)
    if success and stdout:
        print("\nChanges to commit:")
        for line in stdout.strip().split('\n'):
            print(f"  {line}")
    
    # Ask for confirmation
    print("\nDo you want to commit and push these changes to the wiki? (y/n): ", end="")
    response = input().strip().lower()
    
    if response != 'y':
        print("\n✗ Update cancelled by user")
        return 0
    
    # Commit changes
    print("\nCommitting changes...")
    success, stdout, stderr = run_command(
        'git add -A',
        cwd=wiki_path
    )
    
    if not success:
        print(f"  ✗ Error adding files: {stderr}")
        return 1
    
    success, stdout, stderr = run_command(
        'git commit -m "Update documentation"',
        cwd=wiki_path
    )
    
    if not success:
        print(f"  ✗ Error committing: {stderr}")
        return 1
    
    print("  ✓ Changes committed")
    
    # Push changes
    print("\nPushing to remote wiki repository...")
    success, stdout, stderr = run_command(
        'git push',
        cwd=wiki_path
    )
    
    if not success:
        print(f"  ✗ Error pushing: {stderr}")
        return 1
    
    print("  ✓ Changes pushed successfully")
    
    print("\n" + "=" * 60)
    print("✓ Wiki updated successfully!")
    print("=" * 60)
    print(f"\nView at: https://github.com/cronomantic/ChooseYourDestiny/wiki")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
