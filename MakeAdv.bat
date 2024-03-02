@echo off  &SETLOCAL

REM ---- Configuration variables 

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
SET LOAD_SCR=%~dp0\IMAGES\000.scr

REM ---------------------------------


GOTO START
REM ---- Check if the file to compress is already compressed or is newer ----
:CHECK_IF_COMPRESS
  IF not exist %1 exit /b 1
  IF not exist %2 exit /b 0
  FOR %%i IN (%1) DO SET DATE1=%%~ti
  FOR %%i IN (%2) DO SET DATE2=%%~ti
  IF "%DATE1%"=="%DATE2%" exit /b 0
  FOR /F %%i IN ('DIR /B /O:D %1 %2') DO SET NEWEST=%%i
  IF "%2"=="%NEWEST%" exit /b 1
  exit /b 0
:START

IF NOT EXIST "%~dp0\%GAME%.cyd" (
  ECHO.
  echo %GAME%.cyd file not found!
  GOTO ERROR
)

REM  ---- PREPARE IMAGES ----
ECHO ---------------------
ECHO Preparing images (if any)...
CD "%~dp0\IMAGES"
for /L %%i in (0, 1, 9) do (CALL :CHECK_IF_COMPRESS 00%%i.SCR 00%%i.CSC && (..\DIST\CSC -l=%IMGLINES% -f -o=00%%i.CSC 00%%i.SCR  > nul 2>&1))
for /L %%i in (10, 1, 99) do (CALL :CHECK_IF_COMPRESS 0%%i.SCR 0%%i.CSC && (..\DIST\CSC -l=%IMGLINES% -f -o=0%%i.CSC 0%%i.SCR  > nul 2>&1))
for /L %%i in (100, 1, 256) do (CALL :CHECK_IF_COMPRESS %%i.SCR %%i.CSC && (..\DIST\CSC -l=%IMGLINES% -f -o=%%i.CSC %%i.SCR  > nul 2>&1))
CD ..

REM  ---- COMPILING ADVENTURE ----
ECHO ---------------------
ECHO Compiling the script...
IF NOT EXIST "%~dp0\tools\mkp3fs.exe" (
  echo mkp3fs.exe file not found!
  GOTO ERROR
)
IF NOT EXIST "%~dp0\tools\sjasmplus.exe" (
  echo sjasmplus.exe file not found!
  GOTO ERROR
)
SET CYDCPARAMS=
IF NOT EXIST "%~dp0\tokens.json" (
  SET CYDCPARAMS=%CYDCPARAMS% -T %~dp0\tokens.json
) else (
  SET CYDCPARAMS=%CYDCPARAMS% -t %~dp0\tokens.json
)
IF EXIST "%~dp0\SFX.ASM" (
  SET CYDCPARAMS=%CYDCPARAMS% -sfx %~dp0\SFX.ASM
)
IF EXIST "%LOAD_SCR%" (
  SET CYDCPARAMS=%CYDCPARAMS% -scr %LOAD_SCR%
)
IF EXIST "%~dp0\charset.json" (
  SET CYDCPARAMS=%CYDCPARAMS% -c %~dp0\charset.json
)
SET CYDCPARAMS=%CYDCPARAMS% -csc %~dp0\IMAGES -pt3 %~dp0\TRACKS
%~dp0\dist\python\python %~dp0\dist\cydc_cli.py %CYDCPARAMS% %TARGET% %~dp0\%GAME%.cyd %~dp0\tools\sjasmplus.exe %~dp0\tools\mkp3fs.exe %~dp0\.    
IF ERRORLEVEL 1 GOTO ERROR
SET CYDCPARAMS= 
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
SET CYDCPARAMS=
ECHO ---------------------
ECHO Compile error, please check
PAUSE
:END
REM ----  CLEANING ---- 
DEL %~dp0\SCRIPT.DAT > nul 2>&1
DEL %~dp0\DISK > nul 2>&1
DEL %~dp0\CYD.BIN > nul 2>&1
