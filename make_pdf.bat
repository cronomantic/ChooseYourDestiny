@echo off
REM ==============================================================================
REM  PDF Documentation Generator for ChooseYourDestiny (Windows)
REM ==============================================================================
REM  Generates PDF documentation from Markdown files using Pandoc.
REM  Requires: Pandoc with Tectonic (included in tools/pandoc/)
REM ==============================================================================

echo Generating PDF documentation...
echo.

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
"%~dp0tools\pandoc\pandoc" MANUAL_es.md -o "%~dp0documentation\es\MANUAL_es.pdf" -V geometry:margin=1in --pdf-engine="%~dp0tools\pandoc\tectonic" --toc

echo Generating TUTORIAL_es.pdf...
"%~dp0tools\pandoc\pandoc" TUTORIAL_es.md -o "%~dp0documentation\es\TUTORIAL_es.pdf" -V geometry:margin=1in --pdf-engine="%~dp0tools\pandoc\tectonic" --toc

REM Generate English PDFs
echo Generating MANUAL_en.pdf...
"%~dp0tools\pandoc\pandoc" MANUAL_en.md -o "%~dp0documentation\en\MANUAL_en.pdf" -V geometry:margin=1in --pdf-engine="%~dp0tools\pandoc\tectonic" --toc

echo Generating TUTORIAL_en.pdf...
"%~dp0tools\pandoc\pandoc" TUTORIAL_en.md -o "%~dp0documentation\en\TUTORIAL_en.pdf" -V geometry:margin=1in --pdf-engine="%~dp0tools\pandoc\tectonic" --toc

popd

echo.
echo PDF documentation generated successfully!
echo   - documentation\es\MANUAL_es.pdf
echo   - documentation\es\TUTORIAL_es.pdf
echo   - documentation\en\MANUAL_en.pdf
echo   - documentation\en\TUTORIAL_en.pdf
pause
