@echo off  &SETLOCAL

REM ---- Configuration variables ----------

REM Name of the game
SET GAME=test
REM This name will be used as:
REM   - The file to compile will be test.cyd with this example
REM   - The name of the TAP file or +3 disk image

REM Target for the compiler (48k, 128k for TAP, plus3 for DSK)
SET TARGET=128k

REM Number of lines used on SCR files at compressing
SET IMGLINES=192

REM Loading screen
SET LOAD_SCR="./IMAGES/LOAD.scr"

REM Parameters for compiler
SET CYDC_EXTRA_PARAMS=-wyz -v

REM Run emulator after compilation (none/internal/default)
REM     -None: Do nothing
REM     -internal: run the compiled file with Zesarux (must be on the directory .\tools\zesarux\)
REM     -default: run the compiled file with the program set on Windows to run its extension
SET RUN_EMULATOR=none

REM Backup CYD file after compilation (yes/no) on ./BACKUP directory.
SET BACKUP_CYD=no

REM --------------------------------------
%~dp0\dist\python\python %~dp0\make_adventure.py -n %GAME% %CYDC_EXTRA_PARAMS% -il %IMGLINES% -scr %LOAD_SCR% %TARGET%
IF ERRORLEVEL 1 GOTO ERROR
ECHO ---------------------
ECHO Success!

if "%BACKUP_CYD%"=="yes" (
if not exist %~dp0\BACKUP\NUL mkdir %~dp0\BACKUP
COPY %~dp0\%GAME%.cyd "%~dp0\BACKUP\%GAME%_%DATE:~6,4%-%DATE:~3,2%-%DATE:~0,2%_%TIME:~0,2%-%TIME:~3,2%-%TIME:~6,2%.cyd" 1>NUL
)

REM DEFAULT EMULATOR (windows default)
if "%RUN_EMULATOR%"=="default" (
if "%TARGET%"=="plus3" (
%GAME%.DSK
)
if "%TARGET%"=="128k" (
%GAME%.TAP
)
if "%TARGET%"=="48k" (
%GAME%.TAP
)
GOTO END
)

REM INTERNAL EMULATOR (in Tools)
REM By default it expects Zesarux, but you can adapt this to your favorite emulator
if "%RUN_EMULATOR%"=="internal" (
if EXIST %~dp0\tools\zesarux\zesarux.exe (
cd %~dp0\tools\zesarux
SET ZESARUXPARAMS=--noconfigfile --quickexit --zoom 2 --realvideo --nosplash --forcevisiblehotkeys --forceconfirmyes  --nowelcomemessage  --cpuspeed 100
if "%TARGET%"=="plus3" (
zesarux %ZESARUXPARAMS% --machine P341 ..\..\%GAME%.DSK
)
if "%TARGET%"=="128k" (
zesarux %ZESARUXPARAMS% --machine 128k ..\..\%GAME%.TAP
)
if "%TARGET%"=="48k" (
zesarux %ZESARUXPARAMS% --machine 48k ..\..\%GAME%.TAP
)
SET ZESARUXPARAMS=
CD ..\..
)
GOTO END
)

GOTO END
:ERROR
ECHO ---------------------
ECHO Compile error, please check
PAUSE
:END
SET GAME=
SET TARGET=
SET IMGLINES=
SET LOAD_SCR=
SET CYDC_EXTRA_PARAMS=
SET RUN_EMULATOR=
SET BACKUP_CYD=
