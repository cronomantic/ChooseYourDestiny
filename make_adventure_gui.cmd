@echo off & SETLOCAL

REM ===============================================================================
REM  ChooseYourDestiny - GUI Launcher (Windows)
REM ===============================================================================
REM  This script launches the graphical user interface for building adventures.
REM  It uses the embedded Python distribution included with ChooseYourDestiny.
REM
REM  Usage: make_adventure_gui.cmd
REM
REM  The GUI provides an easy-to-use interface for:
REM    - Configuring game settings (name, target platform, etc.)
REM    - Compiling adventures
REM    - Managing assets and resources
REM    - Running emulators
REM ===============================================================================

ECHO ===============================================================================
ECHO  ChooseYourDestiny - GUI Launcher
ECHO ===============================================================================
ECHO.

REM Check if Python distribution exists
IF NOT EXIST "%~dp0dist\python\pythonw.exe" (
    ECHO ERROR: Python distribution not found!
    ECHO Expected location: %~dp0dist\python\pythonw.exe
    ECHO.
    ECHO The GUI requires the embedded Python runtime.
    ECHO Please ensure you have the complete Windows distribution package.
    ECHO.
    ECHO You can download it from:
    ECHO   https://github.com/cronomantic/ChooseYourDestiny/releases
    ECHO.
    PAUSE
    EXIT /B 1
)

REM Check if GUI script exists
IF NOT EXIST "%~dp0make_adventure_gui.py" (
    ECHO ERROR: GUI script not found: make_adventure_gui.py
    ECHO.
    ECHO Please ensure you have the complete ChooseYourDestiny distribution.
    ECHO.
    PAUSE
    EXIT /B 1
)

REM Launch GUI with pythonw (no console window)
ECHO Launching GUI...
START "" "%~dp0dist\python\pythonw.exe" "%~dp0make_adventure_gui.py" %*

REM Check if launch was successful
IF ERRORLEVEL 1 (
    ECHO.
    ECHO ===============================================================================
    ECHO  ERROR: Failed to launch the GUI
    ECHO ===============================================================================
    ECHO.
    ECHO Possible causes:
    ECHO   - Python distribution is corrupted or incomplete
    ECHO   - Required Python modules are missing
    ECHO   - tkinter GUI library is not available
    ECHO.
    ECHO Please try:
    ECHO   1. Re-download the complete Windows distribution package
    ECHO   2. Extract it to a new folder (avoid spaces in path)
    ECHO   3. Run this script again
    ECHO.
    ECHO If the problem persists, please report it at:
    ECHO   https://github.com/cronomantic/ChooseYourDestiny/issues
    ECHO.
    PAUSE
    EXIT /B 1
)

EXIT /B 0
