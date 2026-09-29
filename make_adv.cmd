@echo off & SETLOCAL ENABLEDELAYEDEXPANSION

REM ===============================================================================
REM  ChooseYourDestiny - Adventure Builder Script (Windows)
REM ===============================================================================
REM  This script compiles a .cyd adventure file into a TAP, DSK, or MLD file
REM  for the ZX Spectrum 48k, 128k, +3, esxDOS (divMMC) or Dandanator MLD target.
REM
REM  Usage: make_adv.cmd [options]
REM  
REM  Configuration is done by editing the variables below.
REM ===============================================================================

REM ──────────────────────────────────────────────────────────────────────────────
REM  CONFIGURATION SECTION - Edit these variables as needed
REM ──────────────────────────────────────────────────────────────────────────────

REM Name of the game (without .cyd extension)
SET GAME=test
REM This name will be used for:
REM   - The source file to compile: %GAME%.cyd
REM   - The output file: %GAME%.TAP, %GAME%.DSK, or %GAME%.MLD (the compiler
REM     cuts the name to 10 characters on tape and to 8 on the other targets)

REM Target platform: 48k, 128k (for TAP), plus3 (for DSK), esxdos (TAP + DAT for
REM the SD card), mld, or mld128 (for MLD)
SET TARGET=128k

REM Number of screen lines to use when compressing SCR files (default: 192)
REM Use 192 for full screen, or less for partial screen images
SET IMGLINES=192

REM Path to the loading screen SCR file
SET LOAD_SCR=./IMAGES/LOAD.scr

REM Extra parameters for the CYD compiler (optional)
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

REM Backup the .cyd source file after compilation (yes/no)
SET BACKUP_CYD=no

REM Maximum number of backup files to keep (0 = unlimited)
REM When this limit is reached, oldest backups are deleted
SET BACKUP_MAX_FILES=0

REM ──────────────────────────────────────────────────────────────────────────────
REM  END OF CONFIGURATION
REM ──────────────────────────────────────────────────────────────────────────────

ECHO ===============================================================================
ECHO  ChooseYourDestiny Adventure Builder
ECHO ===============================================================================
ECHO  Game: %GAME%
ECHO  Target: %TARGET%
ECHO  Loading screen: %LOAD_SCR%
ECHO ===============================================================================
ECHO.

REM Check if Python distribution exists
IF NOT EXIST "%~dp0dist\python\python.exe" (
    ECHO ERROR: Python distribution not found!
    ECHO Expected location: %~dp0dist\python\python.exe
    ECHO.
    ECHO Please ensure you have the complete ChooseYourDestiny distribution.
    ECHO Download it from: https://github.com/cronomantic/ChooseYourDestiny/releases
    GOTO ERROR
)

REM Check if source file exists
IF NOT EXIST "%~dp0%GAME%.cyd" (
    ECHO ERROR: Source file not found: %GAME%.cyd
    ECHO.
    ECHO Please create your adventure file or edit the GAME variable in this script.
    GOTO ERROR
)

REM Compile the adventure
ECHO Compiling %GAME%.cyd...
ECHO.
%~dp0dist\python\python "%~dp0make_adventure.py" -n %GAME% %CYDC_EXTRA_PARAMS% -il %IMGLINES% -scr %LOAD_SCR% %TARGET%

IF ERRORLEVEL 1 GOTO ERROR

ECHO.
ECHO ===============================================================================
ECHO  SUCCESS! Adventure compiled successfully.
ECHO ===============================================================================

REM Create backup if enabled
IF "%BACKUP_CYD%"=="yes" (
    ECHO.
    ECHO Creating backup...
    
    IF NOT EXIST "%~dp0BACKUP\" MKDIR "%~dp0BACKUP"
    
    REM Generate timestamp for backup filename
    SET DATESTAMP=%DATE:~6,4%-%DATE:~3,2%-%DATE:~0,2%
    SET TIMESTAMP=%TIME:~0,2%-%TIME:~3,2%-%TIME:~6,2%
    SET TIMESTAMP=!TIMESTAMP: =0!
    
    COPY /Y "%~dp0%GAME%.cyd" "%~dp0BACKUP\%GAME%_!DATESTAMP!_!TIMESTAMP!.cyd" >NUL
    
    IF ERRORLEVEL 1 (
        ECHO Warning: Could not create backup.
    ) ELSE (
        ECHO Backup created: BACKUP\%GAME%_!DATESTAMP!_!TIMESTAMP!.cyd
    )
    
    REM Delete old backups if limit is set
    IF %BACKUP_MAX_FILES% GTR 0 (
        SET count=0
        FOR /F "delims=" %%F IN ('DIR "%~dp0BACKUP\%GAME%_*.cyd" /B /O:D 2^>NUL') DO (
            SET /A count+=1
        )
        
        IF !count! GTR %BACKUP_MAX_FILES% (
            ECHO Rotating backups (keeping %BACKUP_MAX_FILES% most recent)...
            SET /A to_delete=!count!-%BACKUP_MAX_FILES%
            SET deleted=0
            FOR /F "delims=" %%F IN ('DIR "%~dp0BACKUP\%GAME%_*.cyd" /B /O:D 2^>NUL') DO (
                IF !deleted! LSS !to_delete! (
                    DEL /Q "%~dp0BACKUP\%%F" >NUL 2>&1
                    SET /A deleted+=1
                )
            )
            ECHO Deleted !deleted! old backup(s).
        )
    )
)

REM Run emulator if configured (the subroutines below use SCRIPT_DIR: inside a
REM CALL, %~dp0 is not always this script's folder)
SET "SCRIPT_DIR=%~dp0"
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
REM The .TAP bootstrap loads the .DAT from the SD card: this folder. (The "."
REM keeps the closing quote from being read as \".)
IF "%TARGET%"=="esxdos" SET ZESARUX_PARAMS=%ZESARUX_PARAMS% --enable-divmmc --enable-esxdos-handler --esxdos-root-dir "%SCRIPT_DIR%."

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

REM The compiled file: the compiler cuts the name to 10 characters on tape and
REM to 8 on the other targets.
:FIND_OUTPUT
SET OUTPUT_EXT=TAP
IF "%TARGET%"=="plus3" SET OUTPUT_EXT=DSK
IF "%TARGET%"=="mld" SET OUTPUT_EXT=MLD
IF "%TARGET%"=="mld128" SET OUTPUT_EXT=MLD
SET "OUTPUT_FILE="
SET "OUTPUT_NAME=%GAME%"
IF EXIST "%SCRIPT_DIR%%OUTPUT_NAME%.%OUTPUT_EXT%" SET "OUTPUT_FILE=%SCRIPT_DIR%%OUTPUT_NAME%.%OUTPUT_EXT%"
SET "OUTPUT_NAME=%GAME:~0,10%"
IF NOT DEFINED OUTPUT_FILE IF EXIST "%SCRIPT_DIR%%OUTPUT_NAME%.%OUTPUT_EXT%" SET "OUTPUT_FILE=%SCRIPT_DIR%%OUTPUT_NAME%.%OUTPUT_EXT%"
SET "OUTPUT_NAME=%GAME:~0,8%"
IF NOT DEFINED OUTPUT_FILE IF EXIST "%SCRIPT_DIR%%OUTPUT_NAME%.%OUTPUT_EXT%" SET "OUTPUT_FILE=%SCRIPT_DIR%%OUTPUT_NAME%.%OUTPUT_EXT%"
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
REM Clean up variables
SET GAME=
SET TARGET=
SET IMGLINES=
SET LOAD_SCR=
SET CYDC_EXTRA_PARAMS=
SET RUN_EMULATOR=
SET ZESARUX_PATH=
SET BACKUP_CYD=
SET BACKUP_MAX_FILES=
SET DATESTAMP=
SET TIMESTAMP=
EXIT /B 0
