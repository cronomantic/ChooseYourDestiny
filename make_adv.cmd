@echo off & SETLOCAL ENABLEDELAYEDEXPANSION

REM ===============================================================================
REM  ChooseYourDestiny - Adventure Builder Script (Windows)
REM ===============================================================================
REM  This script compiles a project (a folder with a game, and its
REM  cyd_project.ini) into a TAP, DSK, or MLD file for the ZX Spectrum 48k,
REM  128k, +3, esxDOS (divMMC) or Dandanator MLD target.
REM
REM  Usage: make_adv.cmd [PROJECT] [TARGET]
REM
REM  PROJECT is the folder of the game, or its main .cyd file (you can also drag
REM  it onto this script); without it, the PROJECT variable below. TARGET, if
REM  given, is used instead of the project's. The game's settings (target, image
REM  lines, loading screen...) are in its cyd_project.ini; the variables below
REM  are for this computer.
REM ===============================================================================

REM ──────────────────────────────────────────────────────────────────────────────
REM  CONFIGURATION SECTION - Edit these variables as needed
REM ──────────────────────────────────────────────────────────────────────────────

REM The project to compile when none is given: the folder of the game (or its
REM main .cyd file). Relative to this script's folder, or absolute.
SET PROJECT=

REM Target platform, instead of the project's: 48k, 128k (for TAP), plus3 (for
REM DSK), esxdos (TAP + DAT for the SD card), mld, or mld128 (for MLD). Empty:
REM the project's.
SET TARGET=

REM Name of the game, instead of the project's (empty: the project's). The
REM compiler cuts it to 10 characters on tape and to 8 on the other targets.
SET GAME=

REM Extra parameters for make_adventure.py (optional)
REM Example: --verbose for more output
SET CYDC_EXTRA_PARAMS=

REM Run emulator after successful compilation
REM Options:
REM   none     - Do not run emulator
REM   internal - Run with ZEsarUX (see ZESARUX_PATH below)
REM   default  - Run with Windows default program for .TAP/.DSK files
SET RUN_EMULATOR=none

REM Path to zesarux.exe (used when RUN_EMULATOR=internal). Empty: look for it in
REM .\tools\zesarux\, then in the newest .\tools\ZEsarUX*\ (for example
REM .\tools\ZEsarUX_win-13.0\), then on the PATH.
SET ZESARUX_PATH=

REM Backup the main .cyd file after compilation, to the project's BACKUP folder
REM (yes/no; empty: the project's "backup" setting)
SET BACKUP_CYD=

REM Maximum number of backup files to keep (0 = unlimited)
REM When this limit is reached, oldest backups are deleted
SET BACKUP_MAX_FILES=0

REM ──────────────────────────────────────────────────────────────────────────────
REM  END OF CONFIGURATION
REM ──────────────────────────────────────────────────────────────────────────────

REM The subroutines below use SCRIPT_DIR: inside a CALL, %~dp0 is not always
REM this script's folder.
SET "SCRIPT_DIR=%~dp0"
SET "PY=%SCRIPT_DIR%dist\python\python.exe"

REM Arguments: the project and the target, in any order. A relative PROJECT
REM variable is from this script's folder.
SET "ARG_PROJECT="
CALL :TAKE_ARG "%~1"
CALL :TAKE_ARG "%~2"
IF DEFINED ARG_PROJECT (
    SET "PROJECT=!ARG_PROJECT!"
) ELSE IF DEFINED PROJECT (
    PUSHD "%SCRIPT_DIR%"
    FOR %%F IN ("!PROJECT!") DO SET "PROJECT=%%~fF"
    POPD
)

IF NOT DEFINED PROJECT (
    ECHO ERROR: No project given.
    ECHO.
    ECHO Usage: make_adv.cmd PROJECT [TARGET]  ^(the folder of the game, or its main
    ECHO .cyd file; you can also drag it onto this script^), or set the PROJECT
    ECHO variable in this script. To start a project:
    ECHO   dist\python\python make_adventure.py --new FOLDER
    GOTO ERROR
)

REM Check if Python distribution exists
IF NOT EXIST "%PY%" (
    ECHO ERROR: Python distribution not found^^!
    ECHO Expected location: %PY%
    ECHO.
    ECHO Please ensure you have the complete ChooseYourDestiny distribution.
    ECHO Download it from: https://github.com/cronomantic/ChooseYourDestiny/releases
    GOTO ERROR
)

REM The project as make_adventure.py sees it: ROOT, MAIN, NAME, TARGET, OUTPUT
REM and BACKUP (as CYD_ROOT, CYD_MAIN...).
SET "NAME_PARAMS="
IF DEFINED GAME SET NAME_PARAMS=-n "%GAME%"
SET "CYD_ROOT="
FOR /F "usebackq tokens=1,* delims==" %%A IN (`CALL "%PY%" "%SCRIPT_DIR%make_adventure.py" --describe %NAME_PARAMS% "%PROJECT%" %TARGET%`) DO SET "CYD_%%A=%%B"
IF NOT DEFINED CYD_ROOT (
    REM Again, to show make_adventure.py's message.
    "%PY%" "%SCRIPT_DIR%make_adventure.py" --describe %NAME_PARAMS% "%PROJECT%" %TARGET% >NUL
    GOTO ERROR
)
SET "GAME=%CYD_NAME%"
SET "TARGET=%CYD_TARGET%"
IF NOT DEFINED BACKUP_CYD SET "BACKUP_CYD=%CYD_BACKUP%"

ECHO ===============================================================================
ECHO  ChooseYourDestiny Adventure Builder
ECHO ===============================================================================
ECHO  Project: %CYD_ROOT%
ECHO  Game: %GAME%
ECHO  Target: %TARGET%
ECHO ===============================================================================
ECHO.

REM Compile the adventure
FOR %%F IN ("%CYD_MAIN%") DO ECHO Compiling %%~nxF...
ECHO.
"%PY%" "%SCRIPT_DIR%make_adventure.py" %CYDC_EXTRA_PARAMS% %NAME_PARAMS% "%PROJECT%" %TARGET%

IF ERRORLEVEL 1 GOTO ERROR

ECHO.
ECHO ===============================================================================
ECHO  SUCCESS^^! Adventure compiled successfully.
ECHO ===============================================================================

REM Create backup if enabled
IF /I "%BACKUP_CYD%"=="yes" (
    ECHO.
    ECHO Creating backup...

    SET "BACKUP_DIR=%CYD_ROOT%\BACKUP"
    IF NOT EXIST "!BACKUP_DIR!\" MKDIR "!BACKUP_DIR!"

    REM Generate timestamp for backup filename
    SET DATESTAMP=%DATE:~6,4%-%DATE:~3,2%-%DATE:~0,2%
    SET TIMESTAMP=%TIME:~0,2%-%TIME:~3,2%-%TIME:~6,2%
    SET TIMESTAMP=!TIMESTAMP: =0!

    COPY /Y "%CYD_MAIN%" "!BACKUP_DIR!\%GAME%_!DATESTAMP!_!TIMESTAMP!.cyd" >NUL

    IF ERRORLEVEL 1 (
        ECHO Warning: Could not create backup.
    ) ELSE (
        ECHO Backup created: BACKUP\%GAME%_!DATESTAMP!_!TIMESTAMP!.cyd
    )

    REM Delete old backups if limit is set
    IF %BACKUP_MAX_FILES% GTR 0 (
        SET count=0
        FOR /F "delims=" %%F IN ('DIR "!BACKUP_DIR!\%GAME%_*.cyd" /B /O:D 2^>NUL') DO (
            SET /A count+=1
        )

        IF !count! GTR %BACKUP_MAX_FILES% (
            ECHO Rotating backups ^(keeping %BACKUP_MAX_FILES% most recent^)...
            SET /A to_delete=!count!-%BACKUP_MAX_FILES%
            SET deleted=0
            FOR /F "delims=" %%F IN ('DIR "!BACKUP_DIR!\%GAME%_*.cyd" /B /O:D 2^>NUL') DO (
                IF !deleted! LSS !to_delete! (
                    DEL /Q "!BACKUP_DIR!\%%F" >NUL 2>&1
                    SET /A deleted+=1
                )
            )
            ECHO Deleted !deleted! old backup^(s^).
        )
    )
)

REM Run emulator if configured
IF "%RUN_EMULATOR%"=="default" GOTO RUN_DEFAULT
IF "%RUN_EMULATOR%"=="internal" GOTO RUN_INTERNAL
GOTO END

:RUN_DEFAULT
ECHO.
ECHO Launching with default program...
CALL :FIND_OUTPUT
IF NOT DEFINED OUTPUT_FILE GOTO NO_OUTPUT
START "" "%OUTPUT_FILE%"
GOTO END

:RUN_INTERNAL
ECHO.
ECHO Launching with ZEsarUX emulator...
IF "%TARGET%"=="mld" GOTO NO_MLD
IF "%TARGET%"=="mld128" GOTO NO_MLD
CALL :FIND_OUTPUT
IF NOT DEFINED OUTPUT_FILE GOTO NO_OUTPUT
CALL :FIND_ZESARUX
IF NOT DEFINED ZESARUX GOTO NO_ZESARUX
IF NOT EXIST "%ZESARUX%" GOTO NO_ZESARUX

SET ZESARUX_MACHINE=48k
IF "%TARGET%"=="128k" SET ZESARUX_MACHINE=128k
IF "%TARGET%"=="esxdos" SET ZESARUX_MACHINE=128k
IF "%TARGET%"=="plus3" SET ZESARUX_MACHINE=P341
SET ZESARUX_PARAMS=--noconfigfile --quickexit --zoom 2 --realvideo --nosplash --forcevisiblehotkeys --forceconfirmyes --nowelcomemessage --cpuspeed 100 --machine %ZESARUX_MACHINE%
REM The .TAP bootstrap loads the .DAT from the SD card: the output folder. (The
REM "\." keeps the closing quote from being read as \".)
IF "%TARGET%"=="esxdos" SET ZESARUX_PARAMS=%ZESARUX_PARAMS% --enable-divmmc --enable-esxdos-handler --esxdos-root-dir "%CYD_OUTPUT%\."

ECHO Launching ZEsarUX: "%ZESARUX%" %ZESARUX_PARAMS% "%OUTPUT_FILE%"
REM From its own folder, where its ROMs are.
FOR %%F IN ("%ZESARUX%") DO PUSHD "%%~dpF"
START "ZEsarUX - %GAME%" "%ZESARUX%" %ZESARUX_PARAMS% "%OUTPUT_FILE%"
POPD
GOTO END

:NO_MLD
ECHO Warning: internal emulator launch is not configured for MLD cartridges.
ECHO          Use RUN_EMULATOR=default or load the .MLD file manually.
GOTO END

:NO_OUTPUT
ECHO Warning: compiled file not found for %GAME% (%TARGET%).
GOTO END

:NO_ZESARUX
ECHO Warning: ZEsarUX not found (ZESARUX_PATH, tools\zesarux\, tools\ZEsarUX*\ or the PATH).
ECHO Please download ZEsarUX from https://github.com/chernandezba/zesarux/releases
ECHO or set ZESARUX_PATH in this script.
GOTO END

REM %1: a target name goes to TARGET, anything else to ARG_PROJECT.
:TAKE_ARG
IF "%~1"=="" GOTO :EOF
FOR %%T IN (48k 128k plus3 esxdos mld mld128) DO IF /I "%~1"=="%%T" (
    SET "TARGET=%%T"
    GOTO :EOF
)
FOR %%F IN ("%~1") DO SET "ARG_PROJECT=%%~fF"
GOTO :EOF

REM The compiled file, in the output folder: the compiler cuts the name to 10
REM characters on tape and to 8 on the other targets.
:FIND_OUTPUT
SET OUTPUT_EXT=TAP
IF "%TARGET%"=="plus3" SET OUTPUT_EXT=DSK
IF "%TARGET%"=="mld" SET OUTPUT_EXT=MLD
IF "%TARGET%"=="mld128" SET OUTPUT_EXT=MLD
SET "OUTPUT_FILE="
SET "OUTPUT_NAME=%GAME%"
IF EXIST "%CYD_OUTPUT%\%OUTPUT_NAME%.%OUTPUT_EXT%" SET "OUTPUT_FILE=%CYD_OUTPUT%\%OUTPUT_NAME%.%OUTPUT_EXT%"
SET "OUTPUT_NAME=%GAME:~0,10%"
IF NOT DEFINED OUTPUT_FILE IF EXIST "%CYD_OUTPUT%\%OUTPUT_NAME%.%OUTPUT_EXT%" SET "OUTPUT_FILE=%CYD_OUTPUT%\%OUTPUT_NAME%.%OUTPUT_EXT%"
SET "OUTPUT_NAME=%GAME:~0,8%"
IF NOT DEFINED OUTPUT_FILE IF EXIST "%CYD_OUTPUT%\%OUTPUT_NAME%.%OUTPUT_EXT%" SET "OUTPUT_FILE=%CYD_OUTPUT%\%OUTPUT_NAME%.%OUTPUT_EXT%"
GOTO :EOF

REM The ZEsarUX to use: ZESARUX_PATH, else tools\zesarux\, else the highest
REM version in tools\ZEsarUX*\ (by its number: 13.0 before 9.0), else the PATH.
:FIND_ZESARUX
SET "ZESARUX="
IF NOT DEFINED ZESARUX_PATH GOTO FIND_ZESARUX_TOOLS
REM Relative to this folder, and absolute: it runs from its own folder.
PUSHD "%SCRIPT_DIR%"
FOR %%F IN ("%ZESARUX_PATH%") DO SET "ZESARUX=%%~fF"
POPD
GOTO :EOF
:FIND_ZESARUX_TOOLS
IF EXIST "%SCRIPT_DIR%tools\zesarux\zesarux.exe" SET "ZESARUX=%SCRIPT_DIR%tools\zesarux\zesarux.exe"
IF DEFINED ZESARUX GOTO :EOF
SET ZESARUX_BEST=-1
FOR /D %%D IN ("%SCRIPT_DIR%tools\ZEsarUX*") DO IF EXIST "%%~fD\zesarux.exe" CALL :ZESARUX_VERSION "%%~fD" "%%~nxD"
IF DEFINED ZESARUX GOTO :EOF
FOR /F "delims=" %%P IN ('WHERE zesarux.exe 2^>NUL') DO IF NOT DEFINED ZESARUX SET "ZESARUX=%%P"
GOTO :EOF

REM %1 the folder, %2 its name ("ZEsarUX_win-13.0"): its number is what goes
REM between the first "-" and the next ".".
:ZESARUX_VERSION
SET ZESARUX_VER=0
FOR /F "tokens=2 delims=-" %%V IN ("%~2") DO FOR /F "tokens=1 delims=." %%M IN ("%%V") DO SET ZESARUX_VER=%%M
IF %ZESARUX_VER% LEQ %ZESARUX_BEST% GOTO :EOF
SET ZESARUX_BEST=%ZESARUX_VER%
SET "ZESARUX=%~1\zesarux.exe"
GOTO :EOF

:ERROR
ECHO.
ECHO ===============================================================================
ECHO  COMPILATION FAILED
ECHO ===============================================================================
ECHO  Please check the error messages above.
ECHO ===============================================================================
PAUSE
EXIT /B 1

:END
ECHO.
EXIT /B 0
