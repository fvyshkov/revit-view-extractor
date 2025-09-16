@echo off
setlocal enableextensions

REM Build and install RevitViewExporter add-in for Revit 2026

set PROJECT_DIR=%~dp0
set CSProj=%PROJECT_DIR%RevitViewExporter.csproj
set CONFIG=Release
set PLATFORM=x64
set DEST=%APPDATA%\Autodesk\Revit\Addins\2026
set BUILD_DLL=%PROJECT_DIR%bin\%CONFIG%\RevitViewExporter.dll
set ADDIN_FILE=%PROJECT_DIR%RevitViewExporter.addin

echo === Detecting MSBuild ===
set MSBUILD=
for /f "usebackq tokens=*" %%i in (`"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe" -latest -products * -requires Microsoft.Component.MSBuild -property installationPath 2^>nul`) do set VSINSTALL=%%i
if defined VSINSTALL (
  if exist "%VSINSTALL%\MSBuild\Current\Bin\MSBuild.exe" set MSBUILD="%VSINSTALL%\MSBuild\Current\Bin\MSBuild.exe"
)
if not defined MSBUILD (
  for %%p in ("%ProgramFiles%\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" "C:\Windows\Microsoft.NET\Framework64\v4.0.30319\MSBuild.exe") do (
    if exist %%p set MSBUILD=%%p
  )
)
if not defined MSBUILD (
  echo ERROR: MSBuild not found. Please install Visual Studio Build Tools.
  exit /b 1
)
echo MSBuild: %MSBUILD%

echo === Building %CONFIG%/%PLATFORM% ===
call %MSBUILD% "%CSProj%" /t:Rebuild "/p:Configuration=%CONFIG%;Platform=%PLATFORM%" /m
if errorlevel 1 (
  echo ERROR: Build failed.
  exit /b 1
)

if not exist "%BUILD_DLL%" (
  echo ERROR: Built DLL not found: %BUILD_DLL%
  echo Tip: Ensure Platform is x64 and Configuration is %CONFIG%.
  exit /b 1
)

echo === Installing to: %DEST% ===
if not exist "%DEST%" mkdir "%DEST%"

REM Detect running Revit which can lock DLL
tasklist | find /I "Revit.exe" >nul 2>&1
if %errorlevel%==0 (
  echo WARNING: Revit.exe is running and may lock the DLL. Close Revit and press any key to continue...
  pause >nul
)

REM Check if destination DLL is locked by trying to open with PowerShell
powershell -NoProfile -Command "try{$s=[IO.File]::Open('%DEST%\RevitViewExporter.dll','Open','ReadWrite','None');$s.Close();exit 0}catch{exit 1}" >nul 2>&1
if %errorlevel% neq 0 (
  echo ERROR: Destination DLL is locked. Close Revit and try again.
  exit /b 1
)

echo Copying add-in manifest...
copy /Y "%ADDIN_FILE%" "%DEST%\" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy add-in file.
  exit /b 1
)

echo Copying DLL...
copy /Y "%BUILD_DLL%" "%DEST%\" >nul
if errorlevel 1 (
  echo ERROR: Failed to copy DLL (possibly locked).
  exit /b 1
)

REM Unblock potential zone identifier on copied files
powershell -NoProfile -Command "Get-Item '%DEST%\RevitViewExporter.dll','%DEST%\RevitViewExporter.addin' -ErrorAction SilentlyContinue | Unblock-File" >nul 2>&1

echo Done. Files in %DEST% :
dir /-C "%DEST%\RevitViewExporter.*"

endlocal
exit /b 0
