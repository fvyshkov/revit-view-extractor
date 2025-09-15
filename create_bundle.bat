@echo off
echo === Creating Design Automation Bundle ===
echo.

REM Create bundle directory structure
if exist "Bundle" rmdir /s /q "Bundle"
mkdir "Bundle"
mkdir "Bundle\Contents"

echo Creating bundle structure...

REM Copy the main DLL
copy "RevitViewExtractor\bin\Release\net48\RevitViewExtractor.dll" "Bundle\Contents\"

REM Copy the addin file for Design Automation
copy "ViewExtractorCloud.addin" "Bundle\Contents\"

REM Create PackageContents.xml for the bundle
(
echo ^<?xml version="1.0" encoding="utf-8"?^>
echo ^<ApplicationPackage SchemaVersion="1.0" Version="1.0.0" ProductCode="{A1B2C3D4-E5F6-7890-ABCD-123456789013}" Name="RevitViewExtractor" Description="Extract views from Revit models" Author="RVEXT"^>
echo   ^<CompanyDetails Name="RVEXT" Url="" Email="" /^>
echo   ^<Components Description="Revit View Extractor Components"^>
echo     ^<RuntimeRequirements SeriesMin="R2024" SeriesMax="R2026" Platform="Any" OS="Win64" /^>
echo     ^<ComponentEntry AppName="RevitViewExtractor" ModuleName="./Contents/RevitViewExtractor.dll" AppDescription="Extract views from Revit models" LoadOnCommandInvocation="False" LoadOnRevitStartup="True"^>
echo       ^<Commands GroupName="RVEXT"^>
echo         ^<Command Global="ViewExtractorCloud" Local="ViewExtractorCloud" /^>
echo       ^</Commands^>
echo     ^</ComponentEntry^>
echo   ^</Components^>
echo ^</ApplicationPackage^>
) > "Bundle\PackageContents.xml"

echo.
echo Bundle structure created:
dir "Bundle" /s

echo.
echo === Bundle Contents ===
echo Bundle\
echo   PackageContents.xml
echo   Contents\
echo     RevitViewExtractor.dll
echo     ViewExtractorCloud.addin

echo.
echo === Next Steps ===
echo 1. Zip the Bundle folder contents (not the Bundle folder itself)
echo 2. Upload the ZIP file to Autodesk Design Automation
echo 3. Create an Activity that uses this AppBundle

echo.
echo Creating ZIP file...
powershell -Command "Compress-Archive -Path 'Bundle\*' -DestinationPath 'RevitViewExtractor_Bundle.zip' -Force"

if exist "RevitViewExtractor_Bundle.zip" (
    echo ✓ Bundle ZIP created: RevitViewExtractor_Bundle.zip
    echo File size:
    dir "RevitViewExtractor_Bundle.zip"
) else (
    echo ✗ Failed to create ZIP file
)

echo.
pause
