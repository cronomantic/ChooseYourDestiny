#!/usr/bin/env bash
#
# Distribution builder for ChooseYourDestiny (Unix/Linux/macOS)
# Extracts version from git and builds distribution packages
#

set -e  # Exit on error

echo "ChooseYourDestiny Distribution Builder"
echo "======================================"
echo

# Get version
echo "Extracting version information..."
python3 get_version.py

# Build distribution
python3 make_dist.py "$@"

echo
echo "Done!"
