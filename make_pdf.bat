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

REM Check if wiki directory exists
if not exist "%~dp0..\ChooseYourDestiny.wiki" (
    echo Error: Wiki directory not found at ..\ChooseYourDestiny.wiki
    echo Make sure the wiki repository is cloned as a sibling directory
    pause
    exit /b 1
)

REM Change to wiki directory
pushd "%~dp0..\ChooseYourDestiny.wiki"

REM Create output directories
if not exist "%~dp0documentation\es" mkdir "%~dp0documentation\es"
if not exist "%~dp0documentation\en" mkdir "%~dp0documentation\en"

REM Generate Spanish PDFs
echo Generating MANUAL_es.pdf...
"%PANDOC%" MANUAL_es.md -o "%~dp0documentation\es\MANUAL_es.pdf" %COMMON_ARGS%

echo Generating TUTORIAL_es.pdf...
"%PANDOC%" TUTORIAL_es.md -o "%~dp0documentation\es\TUTORIAL_es.pdf" %COMMON_ARGS%

REM Generate English PDFs
echo Generating MANUAL_en.pdf...
"%PANDOC%" MANUAL_en.md -o "%~dp0documentation\en\MANUAL_en.pdf" %COMMON_ARGS%

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
