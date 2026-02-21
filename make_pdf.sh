#!/usr/bin/env bash

# ==============================================================================
#  PDF Documentation Generator for ChooseYourDestiny (Linux/macOS)
# ==============================================================================
#  Generates PDF documentation from Markdown files using Pandoc.
#  Requires: pandoc and a LaTeX engine (preferably tectonic or pdflatex)
# ==============================================================================

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if pandoc is installed
if ! command -v pandoc &> /dev/null; then
    echo "Error: pandoc is not installed"
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install pandoc texlive-latex-base texlive-latex-extra"
    echo "  Fedora: sudo dnf install pandoc texlive-scheme-medium"
    echo "  macOS: brew install pandoc basictex"
    exit 1
fi

# Detect LaTeX engine
if command -v tectonic &> /dev/null; then
    PDF_ENGINE="tectonic"
    echo "Using Tectonic as PDF engine"
elif command -v pdflatex &> /dev/null; then
    PDF_ENGINE="pdflatex"
    echo "Using pdflatex as PDF engine"
else
    echo "Error: No LaTeX engine found"
    echo "Install tectonic or pdflatex"
    exit 1
fi

echo "Generating PDF documentation..."
echo ""

# Change to wiki directory
cd "$SCRIPT_DIR/../ChooseYourDestiny.wiki" || {
    echo "Error: Wiki directory not found at ../ChooseYourDestiny.wiki"
    echo "Make sure the wiki repository is cloned as a sibling directory"
    exit 1
}

# Generate Spanish PDFs
echo "Generating MANUAL_es.pdf..."
pandoc MANUAL_es.md -o "$SCRIPT_DIR/documentation/es/MANUAL_es.pdf" \
    -V geometry:margin=1in \
    --pdf-engine="$PDF_ENGINE" \
    --toc

echo "Generating TUTORIAL_es.pdf..."
pandoc TUTORIAL_es.md -o "$SCRIPT_DIR/documentation/es/TUTORIAL_es.pdf" \
    -V geometry:margin=1in \
    --pdf-engine="$PDF_ENGINE" \
    --toc

# Generate English PDFs
echo "Generating MANUAL_en.pdf..."
pandoc MANUAL_en.md -o "$SCRIPT_DIR/documentation/en/MANUAL_en.pdf" \
    -V geometry:margin=1in \
    --pdf-engine="$PDF_ENGINE" \
    --toc

echo "Generating TUTORIAL_en.pdf..."
pandoc TUTORIAL_en.md -o "$SCRIPT_DIR/documentation/en/TUTORIAL_en.pdf" \
    -V geometry:margin=1in \
    --pdf-engine="$PDF_ENGINE" \
    --toc

echo ""
echo "✓ PDF documentation generated successfully!"
echo "  - documentation/es/MANUAL_es.pdf"
echo "  - documentation/es/TUTORIAL_es.pdf"
echo "  - documentation/en/MANUAL_en.pdf"
echo "  - documentation/en/TUTORIAL_en.pdf"
