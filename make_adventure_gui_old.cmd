@echo off &SETLOCAL

REM ──────────────────────────────────────────────────────────
REM  Launcher for Make Adventure GUI (Windows)
REM  Uses the embedded Python distribution in .\dist\python\
REM ──────────────────────────────────────────────────────────

"%~dp0\dist\python\pythonw.exe" "%~dp0make_adventure_gui.py" %*

IF ERRORLEVEL 1 (
    ECHO ---------------------
    ECHO Error launching the GUI, please check that dist\python\ exists.
    PAUSE
)