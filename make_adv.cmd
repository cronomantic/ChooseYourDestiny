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
SET LOAD_SCR="LOAD.scr"

REM Parameters for compiler
SET CYDC_EXTRA_PARAMS=-pause 10

REM --------------------------------------
%~dp0\dist\python\python %~dp0\make_adventure.py -n %GAME% %CYDC_EXTRA_PARAMS% -il %IMGLINES% -scr %LOAD_SCR% %TARGET%
IF ERRORLEVEL 1 GOTO ERROR
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
GOTO END
)


if EXIST %~dp0\tools\jSpeccy\jSpeccy.jar (
cd %~dp0\tools\jSpeccy
SET JSPECCYPARAMS=-z 3 --fastload --no-confirm-actions
if "%TARGET%"=="plus3" (
jSpeccy.jar ..\..\%GAME%.TAP -m plus3 %JSPECCYPARAMS%
)
if "%TARGET%"=="128k" (
jSpeccy.jar ..\..\%GAME%.TAP -m sp128k %JSPECCYPARAMS%
)
if "%TARGET%"=="48k" (
jSpeccy.jar ..\..\%GAME%.TAP -m sp48k -%JSPECCYPARAMS%
)
SET JSPECCYPARAMS=
CD ..\..
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
