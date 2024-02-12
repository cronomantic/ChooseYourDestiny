@echo off  &SETLOCAL

REM ---- Configuration variables 

REM Name of the game
SET GAME=test
REM This name will be used as:
REM   - The file to compile will be test.txt with this example
REM   - The +3 disk image file will be called test.dsk with this example

REM Number of lines used on SCR files at compressing
SET IMGLINES=192

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
CD IMAGES
for /L %%i in (0, 1, 9) do (CALL :CHECK_IF_COMPRESS 00%%i.SCR 00%%i.CSC && (..\DIST\CSC -l=%IMGLINES% -f -o=00%%i.CSC 00%%i.SCR  > nul 2>&1))
for /L %%i in (10, 1, 99) do (CALL :CHECK_IF_COMPRESS 0%%i.SCR 0%%i.CSC && (..\DIST\CSC -l=%IMGLINES% -f -o=0%%i.CSC 0%%i.SCR  > nul 2>&1))
for /L %%i in (100, 1, 256) do (CALL :CHECK_IF_COMPRESS %%i.SCR %%i.CSC && (..\DIST\CSC -l=%IMGLINES% -f -o=%%i.CSC %%i.SCR  > nul 2>&1))
CD ..

REM  ---- COMPILING ADVENTURE ----
ECHO ---------------------
ECHO Compiling the script...
IF NOT exist .\tokens.json (
  rem Token file does not exists, create a new one
  %~dp0\dist\python\python %~dp0\dist\cydc\cydc_cli.py -T tokens.json .\%GAME%.txt .\SCRIPT.DAT
  IF ERRORLEVEL 1 GOTO ERROR
) else (
  rem Token file exists, use it...
  %~dp0\dist\python\python %~dp0\dist\cydc\cydc_cli.py .\%GAME%.txt .\SCRIPT.DAT
  IF ERRORLEVEL 1 GOTO ERROR
)

REM  ---- Making DISK ----
ECHO ---------------------
ECHO Building the disk image...
IF NOT EXIST %~dp0\tools\mkp3fs.exe (
  echo mkp3fs.exe file not found!
  GOTO ERROR
)
SET LISTFILES=
IF NOT EXIST .\dist\DISK (
  echo DISK file not found!
  GOTO ERROR
) else (
  CALL SET LISTFILES=%LISTFILES% dist\DISK
)
IF NOT EXIST .\dist\CYD.BIN (
  echo CYD.BIN file not found!
  GOTO ERROR
) else (
  CALL SET LISTFILES=%LISTFILES% dist\CYD.BIN
)
IF NOT EXIST .\SCRIPT.DAT (
  echo SCRIPT.DAT file not found!
  GOTO ERROR
) else (
  CALL SET LISTFILES=%LISTFILES% SCRIPT.DAT
)
IF EXIST SFX.BIN (
  CALL SET LISTFILES=%LISTFILES% SFX.BIN
)
SET IMAGEFILES=
for /L %%i in (0, 1, 9) do IF exist IMAGES\00%%i.CSC (CALL SET "IMAGEFILES=%%IMAGEFILES%% IMAGES\00%%i.CSC")
for /L %%i in (10, 1, 99) do IF exist IMAGES\0%%i.CSC (CALL SET "IMAGEFILES=%%IMAGEFILES%% IMAGES\0%%i.CSC")
for /L %%i in (100, 1, 255) do IF exist IMAGES\%%i.CSC (CALL SET "IMAGEFILES=%%IMAGEFILES%% IMAGES\%%i.CSC")
SET LISTFILES=%LISTFILES%%IMAGEFILES%

SET TRACKFILES=
for /L %%i in (0, 1, 9) do IF exist TRACKS\00%%i.PT3 (CALL SET "TRACKFILES=%%TRACKFILES%% TRACKS\00%%i.PT3")
for /L %%i in (10, 1, 99) do IF exist TRACKS\0%%i.PT3 (CALL SET "TRACKFILES=%%TRACKFILES%% TRACKS\0%%i.PT3")
for /L %%i in (100, 1, 255) do IF exist TRACKS\%%i.PT3 (CALL SET "TRACKFILES=%%TRACKFILES%% TRACKS\%%i.PT3")
SET LISTFILES=%LISTFILES%%TRACKFILES%

IF EXIST %GAME%.DSK DEL %GAME%.DSK > nul 2>&1
%~dp0\tools\mkp3fs.exe -180 -label %GAME% %GAME%.DSK %LISTFILES% > nul 2>&1
IF ERRORLEVEL 1 GOTO ERROR
ECHO ---------------------
ECHO Success!
GOTO END

:ERROR
ECHO ---------------------
ECHO Compile error, please check
PAUSE
:END

REM ----  CLEANING ---- 
DEL .\SCRIPT.DAT > nul 2>&1
