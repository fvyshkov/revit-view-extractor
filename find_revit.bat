@echo off
echo === Finding Revit Installation ===
echo.

set REVIT_FOUND=0
set REVIT_PATH=""
set REVIT_VERSION=""

REM Check for different Revit versions (from newest to oldest)
for %%v in (2026 2025 2024 2023 2022 2021 2020) do (
    if exist "C:\Program Files\Autodesk\Revit %%v\" (
        echo ✓ Found Revit %%v
        if exist "C:\Program Files\Autodesk\Revit %%v\RevitAPI.dll" (
            echo ✓ RevitAPI.dll found for version %%v
            set REVIT_FOUND=1
            set REVIT_PATH=C:\Program Files\Autodesk\Revit %%v
            set REVIT_VERSION=%%v
            goto :found
        ) else (
            echo ✗ RevitAPI.dll NOT found for version %%v
        )
    )
)

:found
if %REVIT_FOUND%==1 (
    echo.
    echo === Revit Found ===
    echo Version: %REVIT_VERSION%
    echo Path: %REVIT_PATH%
    echo.
    
    echo Updating project file...
    
    REM Create updated project file
    (
        echo ^<?xml version="1.0" encoding="utf-8"?^>
        echo ^<Project ToolsVersion="15.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003"^>
        echo   ^<Import Project="$(MSBuildExtensionsPath)\$(MSBuildToolsVersion)\Microsoft.Common.props" Condition="Exists('$(MSBuildExtensionsPath)\$(MSBuildToolsVersion)\Microsoft.Common.props')" /^>
        echo   ^<PropertyGroup^>
        echo     ^<Configuration Condition=" '$(Configuration)' == '' "^>Debug^</Configuration^>
        echo     ^<Platform Condition=" '$(Platform)' == '' "^>AnyCPU^</Platform^>
        echo     ^<ProjectGuid^>{12345678-1234-1234-1234-123456789012}^</ProjectGuid^>
        echo     ^<OutputType^>Library^</OutputType^>
        echo     ^<AppDesignerFolder^>Properties^</AppDesignerFolder^>
        echo     ^<RootNamespace^>RevitViewExtractor^</RootNamespace^>
        echo     ^<AssemblyName^>RevitViewExtractor^</AssemblyName^>
        echo     ^<TargetFrameworkVersion^>v4.8^</TargetFrameworkVersion^>
        echo     ^<FileAlignment^>512^</FileAlignment^>
        echo     ^<Deterministic^>true^</Deterministic^>
        echo   ^</PropertyGroup^>
        echo   ^<PropertyGroup Condition=" '$(Configuration)^|$(Platform)' == 'Debug^|AnyCPU' "^>
        echo     ^<DebugSymbols^>true^</DebugSymbols^>
        echo     ^<DebugType^>full^</DebugType^>
        echo     ^<Optimize^>false^</Optimize^>
        echo     ^<OutputPath^>bin\Debug\^</OutputPath^>
        echo     ^<DefineConstants^>DEBUG;TRACE^</DefineConstants^>
        echo     ^<ErrorReport^>prompt^</ErrorReport^>
        echo     ^<WarningLevel^>4^</WarningLevel^>
        echo   ^</PropertyGroup^>
        echo   ^<PropertyGroup Condition=" '$(Configuration)^|$(Platform)' == 'Release^|AnyCPU' "^>
        echo     ^<DebugType^>pdbonly^</DebugType^>
        echo     ^<Optimize^>true^</Optimize^>
        echo     ^<OutputPath^>bin\Release\^</OutputPath^>
        echo     ^<DefineConstants^>TRACE^</DefineConstants^>
        echo     ^<ErrorReport^>prompt^</ErrorReport^>
        echo     ^<WarningLevel^>4^</WarningLevel^>
        echo   ^</PropertyGroup^>
        echo   ^<ItemGroup^>
        echo     ^<Reference Include="RevitAPI"^>
        echo       ^<HintPath^>%REVIT_PATH%\RevitAPI.dll^</HintPath^>
        echo       ^<Private^>False^</Private^>
        echo     ^</Reference^>
        echo     ^<Reference Include="RevitAPIUI"^>
        echo       ^<HintPath^>%REVIT_PATH%\RevitAPIUI.dll^</HintPath^>
        echo       ^<Private^>False^</Private^>
        echo     ^</Reference^>
        echo     ^<Reference Include="System" /^>
        echo     ^<Reference Include="System.Core" /^>
        echo     ^<Reference Include="System.Drawing" /^>
        echo     ^<Reference Include="System.Windows.Forms" /^>
        echo     ^<Reference Include="System.Xml.Linq" /^>
        echo     ^<Reference Include="System.Data.DataSetExtensions" /^>
        echo     ^<Reference Include="Microsoft.CSharp" /^>
        echo     ^<Reference Include="System.Data" /^>
        echo     ^<Reference Include="System.Net.Http" /^>
        echo     ^<Reference Include="System.Xml" /^>
        echo   ^</ItemGroup^>
        echo   ^<ItemGroup^>
        echo     ^<Compile Include="ViewExtractorApp.cs" /^>
        echo     ^<Compile Include="Properties\AssemblyInfo.cs" /^>
        echo   ^</ItemGroup^>
        echo   ^<Import Project="$(MSBuildToolsPath)\Microsoft.CSharp.targets" /^>
        echo ^</Project^>
    ) > RevitViewExtractor\RevitViewExtractor.csproj
    
    echo ✓ Project file updated for Revit %REVIT_VERSION%
    echo.
    
    echo Now trying to build the project...
    echo.
    
    REM Try to build using the found MSBuild
    if exist "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" (
        echo Using VS 2022 Community MSBuild...
        "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe" RevitViewExtractor\RevitViewExtractor.csproj /p:Configuration=Release /p:Platform=AnyCPU
    ) else (
        echo Trying MSBuild from PATH...
        msbuild RevitViewExtractor\RevitViewExtractor.csproj /p:Configuration=Release /p:Platform=AnyCPU
    )
    
) else (
    echo.
    echo ✗ No Revit installation found!
    echo Please install Revit or check the installation path.
    echo.
)

echo.
pause
