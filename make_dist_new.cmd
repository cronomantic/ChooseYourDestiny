@echo off
REM Distribution builder for ChooseYourDestiny (Windows)
REM Extracts version from git and builds distribution packages

echo ChooseYourDestiny Distribution Builder
echo ======================================
echo.

REM Get version
echo Extracting version information...
python get_version.py

REM Build distribution
python make_dist.py %*

echo.
echo Done!
