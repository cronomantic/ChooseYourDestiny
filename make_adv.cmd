@echo off & SETLOCAL ENABLEDELAYEDEXPANSION

REM ===============================================================================
REM  ChooseYourDestiny - Adventure Builder Script (Windows)
REM ===============================================================================
REM  This script compiles a .cyd adventure file into a TAP or DSK file
REM  for the ZX Spectrum 48k, 128k, or +3.
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
REM   - The output TAP or DSK file: %GAME%.TAP or %GAME%.DSK

REM Target platform: 48k, 128k (for TAP), or plus3 (for DSK)
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
REM   internal - Run with ZEsarUX (must be in .\tools\ZEsarUX_win-11.0\)
REM   default  - Run with Windows default program for .TAP/.DSK files
SET RUN_EMULATOR=none

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

REM Run emulator if configured
IF "%RUN_EMULATOR%"=="default" (
    ECHO.
    ECHO Launching with default program...
    IF "%TARGET%"=="plus3" (
        START "" "%GAME%.DSK"
    ) ELSE (
        START "" "%GAME%.TAP"
    )
    GOTO END
)

IF "%RUN_EMULATOR%"=="internal" (
    ECHO.
    ECHO Launching with ZEsarUX emulator...
    
    IF NOT EXIST "%~dp0tools\ZEsarUX_win-11.0\zesarux.exe" (
        ECHO Warning: ZEsarUX not found at tools\ZEsarUX_win-11.0\zesarux.exe
        ECHO Please download ZEsarUX from https://github.com/chernandezba/zesarux/releases
        GOTO END
    )
    
    PUSHD "%~dp0tools\ZEsarUX_win-11.0"
    
    SET ZESARUX_PARAMS=--noconfigfile --quickexit --zoom 2 --realvideo --nosplash --forcevisiblehotkeys --forceconfirmyes --nowelcomemessage --cpuspeed 100
    
    IF "%TARGET%"=="plus3" (
        START "ZEsarUX - %GAME%" zesarux.exe !ZESARUX_PARAMS! --machine P3SP41 "..\..\%GAME%.DSK"
    ) ELSE IF "%TARGET%"=="128k" (
        START "ZEsarUX - %GAME%" zesarux.exe !ZESARUX_PARAMS! --machine 128k "..\..\%GAME%.TAP"
    ) ELSE (
        START "ZEsarUX - %GAME%" zesarux.exe !ZESARUX_PARAMS! --machine 48k "..\..\%GAME%.TAP"
    )
    
    POPD
    GOTO END
)

GOTO END

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
SET BACKUP_CYD=
SET BACKUP_MAX_FILES=
SET DATESTAMP=
SET TIMESTAMP=
EXIT /B 0
