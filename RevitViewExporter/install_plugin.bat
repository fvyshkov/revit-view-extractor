@echo off
echo Installing Revit ViewExporter plugin...

REM Define paths
set ADDIN_FOLDER=%APPDATA%\Autodesk\Revit\Addins\2026
set PLUGIN_DLL=bin\Debug\RevitViewExporter.dll
set ADDIN_FILE=RevitViewExporter.addin

REM Create directory if it doesn't exist
if not exist "%ADDIN_FOLDER%" (
    echo Creating directory: %ADDIN_FOLDER%
    mkdir "%ADDIN_FOLDER%"
)

REM Copy files
echo Copying %ADDIN_FILE% to %ADDIN_FOLDER%
copy /Y "%~dp0%ADDIN_FILE%" "%ADDIN_FOLDER%\"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to copy %ADDIN_FILE%
    goto ERROR
)

echo Copying %PLUGIN_DLL% to %ADDIN_FOLDER%
copy /Y "%~dp0%PLUGIN_DLL%" "%ADDIN_FOLDER%\"
if %ERRORLEVEL% NEQ 0 (
    echo Failed to copy %PLUGIN_DLL%
    goto ERROR
)

echo.
echo Installation successful!
echo Files copied to: %ADDIN_FOLDER%
echo.
dir "%ADDIN_FOLDER%\RevitViewExporter.*"
goto END

:ERROR
echo.
echo Installation failed!
echo.

:END
pause

