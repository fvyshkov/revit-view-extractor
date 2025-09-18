@echo off
setlocal ENABLEDELAYEDEXPANSION

rem ===== RevitCoreConsole headless export runner =====
rem Usage:
rem   run_headless_export.bat "<RVT_PATH>" "<VIEW_NAME>" "<OUTPUT_DIR>" ["<JOURNAL_PATH>"]
rem Example:
rem   run_headless_export.bat "Z:\Documents\revit-2\100.rvt" "South" "Z:\Documents\revit-2\addin-results"

set "PROJECT_DIR=%~dp0"
set "REVIT_EXE=C:\Program Files\Autodesk\Revit 2026\RevitCoreConsole.exe"

rem ---- Arguments with sensible defaults ----
if "%~1"=="" (
  set "RVT=%PROJECT_DIR%100.rvt"
) else (
  set "RVT=%~1"
)

if "%~2"=="" (
  set "VIEW=South"
) else (
  set "VIEW=%~2"
)

if "%~3"=="" (
  set "OUT=%PROJECT_DIR%addin-results"
) else (
  set "OUT=%~3"
)

if "%~4"=="" (
  set "JOUR=%PROJECT_DIR%run_exporter.txt"
) else (
  set "JOUR=%~4"
)

echo === RevitCoreConsole Headless Export ===
echo RVT   : "%RVT%"
echo VIEW  : "%VIEW%"
echo OUT   : "%OUT%"
echo JOUR  : "%JOUR%"
echo EXE   : "%REVIT_EXE%"
echo.

rem ---- Sanity checks ----
if not exist "%REVIT_EXE%" (
  echo ERROR: RevitCoreConsole not found: "%REVIT_EXE%"
  echo Edit this script to point to your Revit 2026 installation.
  exit /b 1
)

if not exist "%RVT%" (
  echo ERROR: RVT file not found: "%RVT%"
  exit /b 1
)

if not exist "%OUT%" (
  mkdir "%OUT%" 2>nul
)

rem ---- Set environment for HeadlessApp ----
set "RVE_RVT=%RVT%"
set "RVE_VIEW=%VIEW%"
set "RVE_OUT=%OUT%"

rem ---- Prepare journal (create if missing) ----
if not exist "%JOUR%" (
  echo Creating journal: "%JOUR%"
  >"%JOUR%" echo Jrn.Directive "Version" , "26.0"
  >>"%JOUR%" echo Jrn.Data "File Name" , "Open" , "%RVT%"
  >>"%JOUR%" echo Jrn.Wait 1
  >>"%JOUR%" echo Jrn.Data "File Operation" , "Close", "%RVT%"
)

rem ---- Run RevitCoreConsole ----
echo Running RevitCoreConsole...
"%REVIT_EXE%" /language ENU /journal "%JOUR%"
set "RC=%ERRORLEVEL%"
echo RevitCoreConsole exited with code %RC%

if not "%RC%"=="0" (
  echo ERROR: RevitCoreConsole run failed.
  exit /b %RC%
)

echo Done. Outputs (if any) should be in: "%OUT%"
exit /b 0


