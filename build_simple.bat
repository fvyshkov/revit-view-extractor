@echo off
echo === Building Revit View Extractor for Revit 2026 ===
echo.

echo Current directory: %CD%
echo.

echo Checking project file...
if exist "RevitViewExtractor\RevitViewExtractor.csproj" (
    echo ✓ Project file found
) else (
    echo ✗ Project file NOT found
    echo Make sure you're in the correct directory
    pause
    exit /b 1
)

echo.
echo Building project...
echo.

REM Try VS 2022 Community MSBuild first
if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
    echo Using Visual Studio 2022 Community MSBuild...
    "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" RevitViewExtractor\RevitViewExtractor.csproj /p:Configuration=Release /p:Platform=AnyCPU /verbosity:normal
    set BUILD_RESULT=%ERRORLEVEL%
) else (
    echo Visual Studio 2022 Community MSBuild not found, trying PATH...
    msbuild RevitViewExtractor\RevitViewExtractor.csproj /p:Configuration=Release /p:Platform=AnyCPU /verbosity:normal
    set BUILD_RESULT=%ERRORLEVEL%
)

echo.
if %BUILD_RESULT%==0 (
    echo ✓ Build successful!
    echo.
    echo Output files:
    if exist "RevitViewExtractor\bin\Release\RevitViewExtractor.dll" (
        echo ✓ RevitViewExtractor.dll created
        dir "RevitViewExtractor\bin\Release\RevitViewExtractor.*" /b
    ) else (
        echo ✗ DLL not found in expected location
        echo Checking all output files:
        dir "RevitViewExtractor\bin\" /s /b
    )
) else (
    echo ✗ Build failed with error code %BUILD_RESULT%
    echo Check the error messages above for details.
)

echo.
pause
