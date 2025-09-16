@echo off
echo === Building Revit View Extractor for Revit 2026 ===
echo.

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0
echo Script directory: %SCRIPT_DIR%

REM Change to the script directory
cd /d "%SCRIPT_DIR%"
echo Current directory: %CD%
echo.

echo Checking project file...
if exist "RevitViewExtractor\RevitViewExtractor.csproj" (
    echo ✓ Project file found
) else (
    echo ✗ Project file NOT found
    echo Looking for project files in current directory:
    dir *.csproj /s /b 2>nul
    echo.
    echo Make sure the RevitViewExtractor folder exists with the .csproj file
    pause
    exit /b 1
)

echo.
echo Checking Revit 2026 installation...
if exist "C:\Program Files\Autodesk\Revit 2026\RevitAPI.dll" (
    echo ✓ Revit 2026 API found
) else (
    echo ✗ Revit 2026 API not found
    echo Please check Revit 2026 installation
    pause
    exit /b 1
)

echo.
echo Building project...
echo.

REM Try VS 2022 Community MSBuild first
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
    echo Using Visual Studio 2022 Community MSBuild...
    "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" RevitViewExtractor\RevitViewExtractor.csproj /p:Configuration=Release /p:Platform=AnyCPU /verbosity:minimal
    set BUILD_RESULT=%ERRORLEVEL%
) else if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe" (
    echo Using Visual Studio 2022 Professional MSBuild...
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe" RevitViewExtractor\RevitViewExtractor.csproj /p:Configuration=Release /p:Platform=AnyCPU /verbosity:minimal
    set BUILD_RESULT=%ERRORLEVEL%
) else (
    echo Visual Studio 2022 MSBuild not found, trying PATH...
    msbuild RevitViewExtractor\RevitViewExtractor.csproj /p:Configuration=Release /p:Platform=AnyCPU /verbosity:minimal
    set BUILD_RESULT=%ERRORLEVEL%
)

echo.
if %BUILD_RESULT%==0 (
    echo ✓ Build successful!
    echo.
    echo Output files:
    if exist "RevitViewExtractor\bin\Release\RevitViewExtractor.dll" (
        echo ✓ RevitViewExtractor.dll created
        echo File details:
        dir "RevitViewExtractor\bin\Release\RevitViewExtractor.*" 
        echo.
        echo ✓ Plugin ready for installation!
        echo Copy RevitViewExtractor.dll to your Revit Add-ins folder
    ) else (
        echo ✗ DLL not found in expected location
        echo Checking all output files:
        if exist "RevitViewExtractor\bin\" (
            dir "RevitViewExtractor\bin\" /s /b
        ) else (
            echo No bin folder found
        )
    )
) else (
    echo ✗ Build failed with error code %BUILD_RESULT%
    echo Check the error messages above for details.
)

echo.
echo Press any key to continue...
pause >nul

