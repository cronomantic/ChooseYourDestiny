@echo off
REM ==============================================================================
REM  PDF Documentation Generator for ChooseYourDestiny (Windows)
REM ==============================================================================
REM  Generates PDF documentation from Markdown files using Pandoc.
REM  Requires: Pandoc with Tectonic (included in tools/pandoc/)
REM ==============================================================================

echo Generating PDF documentation...
echo.

set "PANDOC=%~dp0tools\pandoc\pandoc"
set "TECTONIC=%~dp0tools\pandoc\tectonic"
set "HEADER=%~dp0documentation\pdf\pandoc-header.tex"

set "COMMON_ARGS=-f markdown-yaml_metadata_block --pdf-engine=""%TECTONIC%"" --include-in-header=""%HEADER%"" --number-sections --toc --toc-depth=3 --highlight-style=tango -V papersize:a4 -V geometry:margin=2.2cm -V fontsize=11pt -V linestretch=1.15 -V colorlinks=true -V linkcolor=CYDAccent -V urlcolor=CYDAccent -V toccolor=black -V monofont=""DejaVu Sans Mono"""

REM The MANUAL is canonical in this repo; the TUTORIAL lives in the wiki submodule.
REM Each is built from its own directory so its relative image paths (assets\) resolve.
set "WIKI_DIR=%~dp0external\ChooseYourDestiny.wiki"
if not exist "%WIKI_DIR%" (
    echo Error: wiki submodule not found at %WIKI_DIR%
    echo Initialize it with: git submodule update --init external/ChooseYourDestiny.wiki
    pause
    exit /b 1
)

REM Create output directories
if not exist "%~dp0documentation\es" mkdir "%~dp0documentation\es"
if not exist "%~dp0documentation\en" mkdir "%~dp0documentation\en"

REM Generate the MANUALs (from the repo root)
pushd "%~dp0"
echo Generating MANUAL_es.pdf...
"%PANDOC%" MANUAL_es.md -o "%~dp0documentation\es\MANUAL_es.pdf" %COMMON_ARGS%
echo Generating MANUAL_en.pdf...
"%PANDOC%" MANUAL_en.md -o "%~dp0documentation\en\MANUAL_en.pdf" %COMMON_ARGS%
popd

REM Generate the TUTORIALs (from the wiki submodule, where their images live)
pushd "%WIKI_DIR%"
echo Generating TUTORIAL_es.pdf...
"%PANDOC%" TUTORIAL_es.md -o "%~dp0documentation\es\TUTORIAL_es.pdf" %COMMON_ARGS%
echo Generating TUTORIAL_en.pdf...
"%PANDOC%" TUTORIAL_en.md -o "%~dp0documentation\en\TUTORIAL_en.pdf" %COMMON_ARGS%
popd

echo.
echo PDF documentation generated successfully!
echo   - documentation\es\MANUAL_es.pdf
echo   - documentation\es\TUTORIAL_es.pdf
echo   - documentation\en\MANUAL_en.pdf
echo   - documentation\en\TUTORIAL_en.pdf
pause
