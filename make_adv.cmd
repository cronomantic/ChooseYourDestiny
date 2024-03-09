@echo off  &SETLOCAL

REM ---- Configuration variables ----------

REM Name of the game
SET GAME=test
REM This name will be used as:
REM   - The file to compile will be test.cyd with this example
REM   - The name of the TAP file or +3 disk image

REM Target for the compiler (48k, 128k for TAP, plus3 for DSK)
SET TARGET=plus3

REM Number of lines used on SCR files at compressing
SET IMGLINES=192

REM Loading screen
SET LOAD_SCR="LOAD.scr"

REM Parameters for compiler
SET CYDC_EXTRA_PARAMS=

REM --------------------------------------
%~dp0\dist\python\python %~dp0\make_adventure.py -n %GAME% %CYDC_EXTRA_PARAMS% -l %IMGLINES% -scr %LOAD_SCR% %TARGET%
IF ERRORLEVEL 1 GOTO ERROR
SET GAME=
SET TARGET=
SET IMGLINES=
SET LOAD_SCR=
SET CYDC_EXTRA_PARAMS=
ECHO ---------------------
ECHO Success!

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

:ERROR
SET GAME=
SET TARGET=
SET IMGLINES=
SET LOAD_SCR=
SET CYDC_EXTRA_PARAMS=
ECHO ---------------------
ECHO Compile error, please check
PAUSE
:END

