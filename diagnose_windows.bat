@echo off
echo === Windows Build Environment Diagnostics ===
echo.

echo Current directory: %CD%
echo.

echo === Checking for Visual Studio installations ===
echo.

REM Check for VS 2022
echo Checking Visual Studio 2022...
if exist "C:\Program Files\Microsoft Visual Studio\2022\" (
    echo ✓ VS 2022 folder found
    dir "C:\Program Files\Microsoft Visual Studio\2022\" /b
    echo.
    
    REM Check specific editions
    if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\" (
        echo ✓ VS 2022 Professional found
        if exist "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe" (
            echo ✓ MSBuild found in Professional
        ) else (
            echo ✗ MSBuild NOT found in Professional
        )
    )
    
    if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\" (
        echo ✓ VS 2022 Community found
        if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
            echo ✓ MSBuild found in Community
        ) else (
            echo ✗ MSBuild NOT found in Community
        )
    )
    
    if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\" (
        echo ✓ VS 2022 Enterprise found
        if exist "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe" (
            echo ✓ MSBuild found in Enterprise
        ) else (
            echo ✗ MSBuild NOT found in Enterprise
        )
    )
) else (
    echo ✗ VS 2022 not found
)

echo.

REM Check for VS 2019
echo Checking Visual Studio 2019...
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\" (
    echo ✓ VS 2019 folder found
    dir "C:\Program Files (x86)\Microsoft Visual Studio\2019\" /b
    echo.
    
    if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\" (
        echo ✓ VS 2019 Professional found
        if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\MSBuild.exe" (
            echo ✓ MSBuild found in Professional
        ) else (
            echo ✗ MSBuild NOT found in Professional
        )
    )
    
    if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\" (
        echo ✓ VS 2019 Community found
        if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe" (
            echo ✓ MSBuild found in Community
        ) else (
            echo ✗ MSBuild NOT found in Community
        )
    )
) else (
    echo ✗ VS 2019 not found
)

echo.

REM Check for standalone MSBuild
echo Checking standalone MSBuild...
if exist "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\MSBuild\Current\Bin\MSBuild.exe" (
    echo ✓ Standalone MSBuild 2019 found
)
if exist "C:\Program Files\Microsoft Visual Studio\2022\BuildTools\MSBuild\Current\Bin\MSBuild.exe" (
    echo ✓ Standalone MSBuild 2022 found
)

echo.

REM Check for .NET Framework
echo === Checking .NET Framework ===
if exist "C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETFramework\v4.8\" (
    echo ✓ .NET Framework 4.8 found
) else (
    echo ✗ .NET Framework 4.8 NOT found
)

echo.

REM Check for Revit
echo === Checking Revit Installation ===
if exist "C:\Program Files\Autodesk\Revit 2024\" (
    echo ✓ Revit 2024 folder found
    if exist "C:\Program Files\Autodesk\Revit 2024\RevitAPI.dll" (
        echo ✓ RevitAPI.dll found
    ) else (
        echo ✗ RevitAPI.dll NOT found
    )
) else (
    echo ✗ Revit 2024 not found
)

if exist "C:\Program Files\Autodesk\Revit 2023\" (
    echo ✓ Revit 2023 folder found (alternative)
)

echo.

REM Check project files
echo === Checking Project Files ===
if exist "RevitViewExtractor\RevitViewExtractor.csproj" (
    echo ✓ Project file found
) else (
    echo ✗ Project file NOT found
    echo Current directory contents:
    dir /b
)

echo.

REM Try to find MSBuild in PATH
echo === Checking PATH for MSBuild ===
where msbuild 2>nul
if %ERRORLEVEL% equ 0 (
    echo ✓ MSBuild found in PATH
    msbuild -version
) else (
    echo ✗ MSBuild not in PATH
)

echo.
echo === Diagnostics Complete ===
echo.
echo If MSBuild was found, you can try building manually with:
echo msbuild RevitViewExtractor\RevitViewExtractor.csproj /p:Configuration=Release
echo.
pause
