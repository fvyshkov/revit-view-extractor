@echo off
setlocal enableextensions

if "%~3"=="" (
  echo Usage: %~nx0 ^<RVT_FILE^> ^<VIEW_NAME^> ^<OUT_DIR^>
  exit /b 1
)

set RVT_FILE=%~1
set VIEW_NAME=%~2
set OUT_DIR=%~3

if not exist "%RVT_FILE%" (
  echo ERROR: RVT file not found: %RVT_FILE%
  exit /b 1
)
if not exist "%OUT_DIR%" mkdir "%OUT_DIR%"

set RVE_RVT=%RVT_FILE%
set RVE_VIEW=%VIEW_NAME%
set RVE_OUT=%OUT_DIR%

REM Adjust this path to your Revit 2026 installation
set REVIT_CORE_CONSOLE="C:\Program Files\Autodesk\Revit 2026\RevitCoreConsole.exe"

if not exist %REVIT_CORE_CONSOLE% (
  echo ERROR: RevitCoreConsole.exe not found at %REVIT_CORE_CONSOLE%
  exit /b 1
)

REM The DBApplication will be loaded from the Addins folder; ensure .addin is installed.
%REVIT_CORE_CONSOLE% /i "%RVT_FILE%" /al "RevitViewExporter.addin"

echo Done. Check output in: %OUT_DIR%
endlocal
exit /b 0
