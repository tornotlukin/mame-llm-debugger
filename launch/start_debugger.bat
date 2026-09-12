@echo off
REM ===========================================================
REM  Launch MAME with the remote (LLM) debugger enabled.
REM  Edit the four variables below to match your setup.
REM ===========================================================

REM Folder containing your MAME executable
set MAME_DIR=C:\mame

REM MAME executable name (mame.exe, or a SUBTARGET build such as mytest.exe)
set MAME_EXE=mame.exe

REM Game / machine to launch
set GAME=pacman

REM Optional: extra ROM path. Leave empty to use MAME's configured rompath.
set EXTRA_ROMPATH=

REM TCP port the remote debugger listens on (must match your MCP config)
set DEBUG_PORT=12345

REM -----------------------------------------------------------
echo Starting %GAME% with the remote debugger on localhost:%DEBUG_PORT%
echo.

cd /d "%MAME_DIR%"

if "%EXTRA_ROMPATH%"=="" (
    "%MAME_EXE%" %GAME% -debug -debugger remote -debugger_port %DEBUG_PORT%
) else (
    "%MAME_EXE%" %GAME% -rompath "%EXTRA_ROMPATH%" -debug -debugger remote -debugger_port %DEBUG_PORT%
)

pause
