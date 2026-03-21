#!/usr/bin/env bash

# ==============================================================================
#  PDF Documentation Generator for ChooseYourDestiny (Linux/macOS)
# ==============================================================================
#  Generates PDF documentation from Markdown files using Pandoc.
#  Requires: pandoc and a LaTeX engine (preferably tectonic or pdflatex)
# ==============================================================================

set -e  # Exit on error

# Ensure UTF-8 encoding (important for WSL). Fallback if es_ES is unavailable.
if locale -a 2>/dev/null | grep -qi '^es_ES\.utf8$'; then
    export LANG=es_ES.UTF-8
    export LC_ALL=es_ES.UTF-8
elif locale -a 2>/dev/null | grep -qi '^C\.utf8$'; then
    export LANG=C.UTF-8
    export LC_ALL=C.UTF-8
fi

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

# Detect LaTeX engine (prefer xelatex for Unicode support)
if command -v tectonic &> /dev/null; then
    PDF_ENGINE="tectonic"
    echo "Using Tectonic as PDF engine"
elif command -v xelatex &> /dev/null; then
    PDF_ENGINE="xelatex"
    echo "Using xelatex as PDF engine (Unicode-aware)"
elif command -v lualatex &> /dev/null; then
    PDF_ENGINE="lualatex"
    echo "Using lualatex as PDF engine (Unicode-aware)"
elif command -v pdflatex &> /dev/null; then
    PDF_ENGINE="pdflatex"
    echo "Using pdflatex as PDF engine"
else
    echo "Error: No LaTeX engine found"
    echo "Install tectonic, xelatex, lualatex, or pdflatex"
    exit 1
fi

echo "Generating PDF documentation..."
echo ""

COMMON_PANDOC_ARGS=(
    -f markdown-yaml_metadata_block
    --pdf-engine="$PDF_ENGINE"
    --include-in-header="$SCRIPT_DIR/documentation/pdf/pandoc-header.tex"
    --number-sections
    --toc
    --toc-depth=3
    --highlight-style=tango
    -V papersize:a4
    -V geometry:margin=2.2cm
    -V fontsize=11pt
    -V linestretch=1.15
    -V colorlinks=true
    -V linkcolor=CYDAccent
    -V urlcolor=CYDAccent
    -V toccolor=black
    -V monofont="DejaVu Sans Mono"
)

# Change to wiki directory
cd "$SCRIPT_DIR/../ChooseYourDestiny.wiki" || {
    echo "Error: Wiki directory not found at ../ChooseYourDestiny.wiki"
    echo "Make sure the wiki repository is cloned as a sibling directory"
    exit 1
}

# Ensure output directories exist
mkdir -p "$SCRIPT_DIR/documentation/es" "$SCRIPT_DIR/documentation/en"

# Generate Spanish PDFs
echo "Generating MANUAL_es.pdf..."
pandoc MANUAL_es.md -o "$SCRIPT_DIR/documentation/es/MANUAL_es.pdf" "${COMMON_PANDOC_ARGS[@]}"

echo "Generating TUTORIAL_es.pdf..."
pandoc TUTORIAL_es.md -o "$SCRIPT_DIR/documentation/es/TUTORIAL_es.pdf" "${COMMON_PANDOC_ARGS[@]}"

# Generate English PDFs
echo "Generating MANUAL_en.pdf..."
pandoc MANUAL_en.md -o "$SCRIPT_DIR/documentation/en/MANUAL_en.pdf" "${COMMON_PANDOC_ARGS[@]}"

echo "Generating TUTORIAL_en.pdf..."
pandoc TUTORIAL_en.md -o "$SCRIPT_DIR/documentation/en/TUTORIAL_en.pdf" "${COMMON_PANDOC_ARGS[@]}"

echo ""
echo "✓ PDF documentation generated successfully!"
echo "  - documentation/es/MANUAL_es.pdf"
echo "  - documentation/es/TUTORIAL_es.pdf"
echo "  - documentation/en/MANUAL_en.pdf"
echo "  - documentation/en/TUTORIAL_en.pdf"
