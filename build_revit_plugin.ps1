# PowerShell script to build Revit View Extractor
Write-Host "=== Building Revit View Extractor for Revit 2026 ===" -ForegroundColor Green
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "Script directory: $ScriptDir"

# Change to script directory
Set-Location $ScriptDir
Write-Host "Current directory: $(Get-Location)"
Write-Host ""

# Check project file
$ProjectFile = "RevitViewExtractor\RevitViewExtractor.csproj"
if (Test-Path $ProjectFile) {
    Write-Host "✓ Project file found" -ForegroundColor Green
} else {
    Write-Host "✗ Project file NOT found" -ForegroundColor Red
    Write-Host "Looking for project files in current directory:"
    Get-ChildItem -Recurse -Filter "*.csproj" | ForEach-Object { Write-Host $_.FullName }
    Write-Host ""
    Write-Host "Make sure the RevitViewExtractor folder exists with the .csproj file"
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host ""

# Check Revit 2026
$RevitApiPath = "C:\Program Files\Autodesk\Revit 2026\RevitAPI.dll"
if (Test-Path $RevitApiPath) {
    Write-Host "✓ Revit 2026 API found" -ForegroundColor Green
} else {
    Write-Host "✗ Revit 2026 API not found" -ForegroundColor Red
    Write-Host "Please check Revit 2026 installation"
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host ""
Write-Host "Building project..." -ForegroundColor Yellow
Write-Host ""

# Find MSBuild
$MSBuildPaths = @(
    "C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\Professional\MSBuild\Current\Bin\MSBuild.exe",
    "C:\Program Files\Microsoft Visual Studio\2022\Enterprise\MSBuild\Current\Bin\MSBuild.exe"
)

$MSBuildPath = $null
foreach ($Path in $MSBuildPaths) {
    if (Test-Path $Path) {
        $MSBuildPath = $Path
        Write-Host "Using MSBuild: $Path" -ForegroundColor Cyan
        break
    }
}

if (-not $MSBuildPath) {
    Write-Host "Visual Studio 2022 MSBuild not found, trying PATH..." -ForegroundColor Yellow
    $MSBuildPath = "msbuild"
}

# Build project
try {
    $BuildArgs = @(
        $ProjectFile,
        "/p:Configuration=Release",
        "/p:Platform=AnyCPU",
        "/verbosity:minimal"
    )
    
    & $MSBuildPath $BuildArgs
    $BuildResult = $LASTEXITCODE
} catch {
    Write-Host "Error running MSBuild: $($_.Exception.Message)" -ForegroundColor Red
    $BuildResult = 1
}

Write-Host ""

if ($BuildResult -eq 0) {
    Write-Host "✓ Build successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Output files:" -ForegroundColor Cyan
    
    $DllPath = "RevitViewExtractor\bin\Release\RevitViewExtractor.dll"
    if (Test-Path $DllPath) {
        Write-Host "✓ RevitViewExtractor.dll created" -ForegroundColor Green
        Write-Host "File details:"
        Get-ChildItem "RevitViewExtractor\bin\Release\RevitViewExtractor.*" | Format-Table Name, Length, LastWriteTime
        Write-Host ""
        Write-Host "✓ Plugin ready for installation!" -ForegroundColor Green
        Write-Host "Copy RevitViewExtractor.dll to your Revit Add-ins folder"
    } else {
        Write-Host "✗ DLL not found in expected location" -ForegroundColor Red
        Write-Host "Checking all output files:"
        if (Test-Path "RevitViewExtractor\bin\") {
            Get-ChildItem "RevitViewExtractor\bin\" -Recurse | ForEach-Object { Write-Host $_.FullName }
        } else {
            Write-Host "No bin folder found"
        }
    }
} else {
    Write-Host "✗ Build failed with error code $BuildResult" -ForegroundColor Red
    Write-Host "Check the error messages above for details."
}

Write-Host ""
Read-Host "Press Enter to continue"
