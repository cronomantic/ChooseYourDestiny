@echo off & SETLOCAL

REM ===============================================================================
REM  CYD Dandanator ROM Builder - GUI Launcher (Windows)
REM ===============================================================================
REM  Launches the standalone GUI that packs CYD .MLD games into a bootable
REM  Dandanator Mini ROM. Uses the embedded Python distribution shipped with CYD.
REM
REM  Usage: mld2rom_gui.cmd
REM ===============================================================================

IF NOT EXIST "%~dp0dist\python\python.exe" (
    ECHO ERROR: Embedded Python distribution not found.
    ECHO Expected: %~dp0dist\python\python.exe
    ECHO Please use the complete Windows distribution package.
    PAUSE
    EXIT /B 1
)

IF NOT EXIST "%~dp0mld2rom_gui.py" (
    ECHO ERROR: GUI script not found: mld2rom_gui.py
    PAUSE
    EXIT /B 1
)

"%~dp0dist\python\python.exe" "%~dp0mld2rom_gui.py" %*

IF ERRORLEVEL 1 (
    ECHO.
    ECHO ERROR: Failed to launch the Dandanator ROM Builder GUI.
    PAUSE
    EXIT /B 1
)

EXIT /B 0
