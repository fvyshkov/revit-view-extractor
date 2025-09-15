@echo off
echo Building Revit View Extractor Bundle...

REM Set paths
set MSBUILD_PATH="C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe"
set PROJECT_PATH=RevitViewExtractor\RevitViewExtractor.csproj
set OUTPUT_DIR=bundle
set CONTENTS_DIR=%OUTPUT_DIR%\Contents

REM Clean previous build
if exist %OUTPUT_DIR% rmdir /s /q %OUTPUT_DIR%
mkdir %OUTPUT_DIR%
mkdir %CONTENTS_DIR%

REM Build the project
echo Building C# project...
%MSBUILD_PATH% %PROJECT_PATH% /p:Configuration=Release /p:Platform="Any CPU"

if %ERRORLEVEL% neq 0 (
    echo Build failed!
    exit /b 1
)

REM Copy files to bundle structure
echo Copying files to bundle...
copy RevitViewExtractor\bin\Release\RevitViewExtractor.dll %CONTENTS_DIR%\
copy PackageContents.xml %OUTPUT_DIR%\

REM Create bundle zip
echo Creating bundle zip...
powershell -command "Compress-Archive -Path '%OUTPUT_DIR%\*' -DestinationPath 'RevitViewExtractor.zip' -Force"

echo Bundle created successfully: RevitViewExtractor.zip
pause
