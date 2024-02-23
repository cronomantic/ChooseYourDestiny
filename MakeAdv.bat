@echo off  &SETLOCAL

REM ---- Configuration variables 

REM Name of the game
SET GAME=test
REM This name will be used as:
REM   - The file to compile will be test.txt with this example
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

IF NOT EXIST %~dp0\%GAME%.txt (
  ECHO.
  echo %GAME%.txt file not found!
  GOTO ERROR
)

REM  ---- PREPARE IMAGES ----
ECHO ---------------------
ECHO Preparing images (if any)...
CD %~dp0\IMAGES
for /L %%i in (0, 1, 9) do (CALL :CHECK_IF_COMPRESS 00%%i.SCR 00%%i.CSC && (..\DIST\CSC -l=%IMGLINES% -f -o=00%%i.CSC 00%%i.SCR  > nul 2>&1))
for /L %%i in (10, 1, 99) do (CALL :CHECK_IF_COMPRESS 0%%i.SCR 0%%i.CSC && (..\DIST\CSC -l=%IMGLINES% -f -o=0%%i.CSC 0%%i.SCR  > nul 2>&1))
for /L %%i in (100, 1, 256) do (CALL :CHECK_IF_COMPRESS %%i.SCR %%i.CSC && (..\DIST\CSC -l=%IMGLINES% -f -o=%%i.CSC %%i.SCR  > nul 2>&1))
CD ..

REM  ---- COMPILING ADVENTURE ----
ECHO ---------------------
ECHO Compiling the script...
IF NOT EXIST %~dp0\tools\mkp3fs.exe (
  echo mkp3fs.exe file not found!
  GOTO ERROR
)
IF NOT EXIST %~dp0\tools\sjasmplus.exe (
  echo sjasmplus.exe file not found!
  GOTO ERROR
)
IF NOT exist %~dp0\tokens.json (
  rem Token file does not exists, create a new one
  IF EXIST %~dp0\SFX.ASM (
  %~dp0\dist\python\python %~dp0\dist\cydc_cli.py -T %~dp0\tokens.json -sfx %~dp0\SFX.ASM -scr %LOAD_SCR% -csc %~dp0\IMAGES -pt3 %~dp0\TRACKS %TARGET% %~dp0\%GAME%.txt %~dp0\tools\sjasmplus.exe %~dp0\tools\mkp3fs.exe %~dp0\.
  IF ERRORLEVEL 1 GOTO ERROR
  ) else (
  %~dp0\dist\python\python %~dp0\dist\cydc_cli.py -T %~dp0\tokens.json -scr %LOAD_SCR% -csc %~dp0\IMAGES -pt3 %~dp0\TRACKS %TARGET% %~dp0\%GAME%.txt %~dp0\tools\sjasmplus.exe %~dp0\tools\mkp3fs.exe %~dp0\.    
  IF ERRORLEVEL 1 GOTO ERROR
  )
) else (
  rem Token file exists, use it...
  IF EXIST %~dp0\SFX.ASM (
  %~dp0\dist\python\python %~dp0\dist\cydc_cli.py -t %~dp0\tokens.json -sfx %~dp0\SFX.ASM -scr %LOAD_SCR% -csc %~dp0\IMAGES -pt3 %~dp0\TRACKS %TARGET% %~dp0\%GAME%.txt %~dp0\tools\sjasmplus.exe %~dp0\tools\mkp3fs.exe %~dp0\.
  IF ERRORLEVEL 1 GOTO ERROR
  ) else (
  %~dp0\dist\python\python %~dp0\dist\cydc_cli.py -t %~dp0\tokens.json -scr %LOAD_SCR% -csc %~dp0\IMAGES -pt3 %~dp0\TRACKS %TARGET% %~dp0\%GAME%.txt %~dp0\tools\sjasmplus.exe %~dp0\tools\mkp3fs.exe %~dp0\.
  IF ERRORLEVEL 1 GOTO ERROR
  )
)
ECHO ---------------------
ECHO Success!

if EXIST %~dp0\tools\zesarux\zesarux.exe (
cd %~dp0\tools\zesarux
if "%TARGET%"=="plus3" (
zesarux --noconfigfile --quickexit --zoom 2 --machine P341 --realvideo --nosplash --forcevisiblehotkeys --forceconfirmyes  --nowelcomemessage  --cpuspeed 100 "..\..\TEST.DSK"
)

if "%TARGET%"=="128k" (
zesarux --noconfigfile --quickexit --zoom 2 --machine 128k --realvideo --nosplash --forcevisiblehotkeys --forceconfirmyes  --nowelcomemessage  --cpuspeed 100 "..\..\TEST.TAP"
)

if "%TARGET%"=="48k" (
zesarux --noconfigfile --quickexit --zoom 2 --machine 48k --realvideo --nosplash --forcevisiblehotkeys --forceconfirmyes  --nowelcomemessage  --cpuspeed 100 "..\..\TEST.TAP"
)

CD ..\..
)

GOTO END

:ERROR
ECHO ---------------------
ECHO Compile error, please check
PAUSE
:END

REM ----  CLEANING ---- 
DEL %~dp0\SCRIPT.DAT > nul 2>&1
DEL %~dp0\DISK > nul 2>&1
DEL %~dp0\CYD.BIN > nul 2>&1
