#!/usr/bin/env python3

"""
Cross-platform version extraction script for ChooseYourDestiny
Gets version from git tags and current date.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_version():
    """Get version from git tags"""
    try:
        # Try to get the latest tag
        result = subprocess.run(
            ["git", "describe", "--abbrev=0", "--tags"],
            capture_output=True,
            text=True,
            check=True,
        )
        version = result.stdout.strip()
        # Replace dots with underscores for filename compatibility
        version = version.replace(".", "_")
        return version
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git not available or no tags found
        print("Warning: Could not get version from git. Using 'dev' version.", file=sys.stderr)
        return "dev"


def get_date_string():
    """Get current date in YYYY_MM_DD format"""
    return datetime.now().strftime("%Y_%m_%d")


def main():
    """Main function"""
    version = get_git_version()
    date_str = get_date_string()
    version_string = f"{version}_{date_str}"
    
    # Write to version.txt
    version_file = Path(__file__).parent / "version.txt"
    version_file.write_text(version_string, encoding="utf-8")
    
    print(version_string)
    return 0


if __name__ == "__main__":
    sys.exit(main())
