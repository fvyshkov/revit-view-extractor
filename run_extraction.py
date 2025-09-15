#!/usr/bin/env python3
"""
Simple runner script for Revit view extraction
"""

import os
import sys
from aps_controller import main

if __name__ == "__main__":
    print("=== Revit View Extractor ===")
    print("This script will:")
    print("1. Upload the bundle to APS Design Automation")
    print("2. Create/update the activity")
    print("3. Process the Revit file in the cloud")
    print("4. Download the extracted view image")
    print()
    
    # Check prerequisites
    if not os.path.exists("RevitViewExtractor.zip"):
        print("❌ Bundle not found!")
        print("Please run the following steps on Windows:")
        print("1. Install Visual Studio 2022 with C# support")
        print("2. Run: build_bundle.bat")
        print("3. Copy RevitViewExtractor.zip to this directory")
        sys.exit(1)
    
    if not os.path.exists("100.rvt"):
        print("❌ Revit file '100.rvt' not found!")
        sys.exit(1)
    
    print("✅ Prerequisites check passed")
    print("Starting extraction process...\n")
    
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
