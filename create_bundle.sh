#!/bin/bash
echo "=== Creating Design Automation Bundle ==="
echo

# Create bundle directory structure
if [ -d "Bundle" ]; then
    rm -rf "Bundle"
fi
mkdir -p "Bundle/Contents"

echo "Creating bundle structure..."

# Copy the main DLL (assuming it was built on Windows and copied to Mac)
cp "RevitViewExtractor/bin/Release/net48/RevitViewExtractor.dll" "Bundle/Contents/" 2>/dev/null || echo "⚠️  RevitViewExtractor.dll not found - copy it from Windows build"

# Copy the addin file for Design Automation
cp "ViewExtractorCloud.addin" "Bundle/Contents/" 2>/dev/null || echo "⚠️  ViewExtractorCloud.addin not found"

# Create PackageContents.xml for the bundle
cat > "Bundle/PackageContents.xml" << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<ApplicationPackage SchemaVersion="1.0" Version="1.0.0" ProductCode="{A1B2C3D4-E5F6-7890-ABCD-123456789013}" Name="RevitViewExtractor" Description="Extract views from Revit models" Author="RVEXT">
  <CompanyDetails Name="RVEXT" Url="" Email="" />
  <Components Description="Revit View Extractor Components">
    <RuntimeRequirements SeriesMin="R2024" SeriesMax="R2026" Platform="Any" OS="Win64" />
    <ComponentEntry AppName="RevitViewExtractor" ModuleName="./Contents/RevitViewExtractor.dll" AppDescription="Extract views from Revit models" LoadOnCommandInvocation="False" LoadOnRevitStartup="True">
      <Commands GroupName="RVEXT">
        <Command Global="ViewExtractorCloud" Local="ViewExtractorCloud" />
      </Commands>
    </ComponentEntry>
  </Components>
</ApplicationPackage>
EOF

echo
echo "Bundle structure created:"
find Bundle -type f

echo
echo "=== Bundle Contents ==="
echo "Bundle/"
echo "  PackageContents.xml"
echo "  Contents/"
echo "    RevitViewExtractor.dll"
echo "    ViewExtractorCloud.addin"

echo
echo "Creating ZIP file..."
cd Bundle
zip -r "../RevitViewExtractor_Bundle.zip" . -x "*.DS_Store"
cd ..

if [ -f "RevitViewExtractor_Bundle.zip" ]; then
    echo "✓ Bundle ZIP created: RevitViewExtractor_Bundle.zip"
    echo "File size:"
    ls -lh "RevitViewExtractor_Bundle.zip"
else
    echo "✗ Failed to create ZIP file"
fi

echo
echo "=== Next Steps ==="
echo "1. Upload RevitViewExtractor_Bundle.zip to Autodesk Design Automation"
echo "2. Use upload_to_cloud.py script to automate the upload"
echo "3. Test with a sample Revit file"
