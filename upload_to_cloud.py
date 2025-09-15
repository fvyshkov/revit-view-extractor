#!/usr/bin/env python3
"""
Upload Revit View Extractor to Autodesk Design Automation
"""

import os
import requests
import json
import zipfile
from pathlib import Path

# Configuration - import from config.py
try:
    from config import CLIENT_ID, CLIENT_SECRET
except ImportError:
    CLIENT_ID = "your_client_id_here"  # Replace with your APS app client ID
    CLIENT_SECRET = "your_client_secret_here"  # Replace with your APS app client secret
CLIENT_ID = "rfZQOaSWaILCGB3wRheGj994IH1qCoy9f0tZiPrGs117K48n"
CLIENT_SECRET = "FRAmVrbnXcyp72GUcgmwANOk3lnil0ELRJGmPCzgebvr8DVEnGaNmk1b2ed9Gatq"

BUNDLE_NAME = "RevitViewExtractor4"
BUNDLE_VERSION = "1.0.1"  # Increment version
ACTIVITY_NAME = "ExtractViews"

def get_access_token():
    """Get access token from Autodesk APS"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get access token: {response.text}")
        return None

def create_bundle_zip():
    """Use existing bundle ZIP file or create new one"""
    zip_path = Path("RevitViewExtractor_Bundle.zip")
    
    if zip_path.exists():
        print(f"✓ Using existing bundle ZIP: {zip_path}")
        return zip_path
    
    # If ZIP doesn't exist, try to create from Bundle folder
    bundle_path = Path("Bundle")
    if not bundle_path.exists():
        print("❌ Neither RevitViewExtractor_Bundle.zip nor Bundle folder found!")
        print("Please copy the ZIP file from Windows or run create_bundle.sh")
        return None
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add PackageContents.xml
        zipf.write(bundle_path / "PackageContents.xml", "PackageContents.xml")
        
        # Add Contents folder
        contents_path = bundle_path / "Contents"
        for file_path in contents_path.glob("*"):
            zipf.write(file_path, f"Contents/{file_path.name}")
    
    print(f"✓ Bundle ZIP created: {zip_path}")
    return zip_path

def upload_app_bundle(token, zip_path):
    """Upload AppBundle to Design Automation"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/appbundles"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create AppBundle
    bundle_data = {
        "id": BUNDLE_NAME,
        "engine": "Autodesk.Revit+2024",
        "description": "Extract views from Revit models"
    }
    
    response = requests.post(url, headers=headers, json=bundle_data)
    
    if response.status_code == 200:
        print("✓ AppBundle created successfully")
        upload_url = response.json()["uploadParameters"]["endpointURL"]
        form_data = response.json()["uploadParameters"]["formData"]
        
        # Upload ZIP file
        print(f"Uploading to: {upload_url}")
        print(f"ZIP file size: {zip_path.stat().st_size} bytes")
        
        with open(zip_path, 'rb') as f:
            files = {"file": f}
            upload_response = requests.post(upload_url, data=form_data, files=files)
            
        print(f"Upload response status: {upload_response.status_code}")
        print(f"Upload response headers: {dict(upload_response.headers)}")
        
        if upload_response.status_code in [200, 204]:
            print("✓ Bundle uploaded successfully")
            return True
        else:
            print(f"✗ Failed to upload bundle: {upload_response.text}")
            print(f"Response content: {upload_response.content}")
            return False
    else:
        print(f"✗ Failed to create AppBundle: {response.text}")
        return False

def create_activity(token):
    """Create Activity for the AppBundle"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/activities"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    activity_data = {
        "id": ACTIVITY_NAME,
        "commandLine": [
            "$(engine.path)\\\\revit.exe /i $(args[inputFile].path) /al $(appbundles[{BUNDLE_NAME}].path)"
        ],
        "parameters": {
            "inputFile": {
                "verb": "get",
                "description": "Input Revit file"
            },
            "outputFile": {
                "verb": "put",
                "description": "Output result file",
                "localName": "result.txt"
            }
        },
        "engine": "Autodesk.Revit+2024",
        "appbundles": [f"{BUNDLE_NAME}+{BUNDLE_VERSION}"],
        "description": "Extract views from Revit model"
    }
    
    response = requests.post(url, headers=headers, json=activity_data)
    
    if response.status_code == 200:
        print("✓ Activity created successfully")
        return True
    else:
        print(f"✗ Failed to create Activity: {response.text}")
        return False

def main():
    print("=== Uploading Revit View Extractor to Design Automation ===")
    print()
    
    # Check if credentials are set
    if CLIENT_ID == "your_client_id_here" or CLIENT_SECRET == "your_client_secret_here":
        print("❌ Please set your CLIENT_ID and CLIENT_SECRET in the script")
        print("Get them from: https://forge.autodesk.com/myapps/")
        return
    
    # Get access token
    print("Getting access token...")
    token = get_access_token()
    if not token:
        return
    print("✓ Access token obtained")
    
    # Create bundle ZIP
    print("Preparing bundle ZIP...")
    zip_path = create_bundle_zip()
    if not zip_path:
        return
    
    # Upload AppBundle
    print("Uploading AppBundle...")
    if upload_app_bundle(token, zip_path):
        print("Creating Activity...")
        create_activity(token)
    
    print()
    print("=== Upload Complete ===")
    print(f"AppBundle: {BUNDLE_NAME}")
    print(f"Activity: {ACTIVITY_NAME}")
    print()
    print("Next steps:")
    print("1. Test the activity with a sample Revit file")
    print("2. Check the result.txt output")

if __name__ == "__main__":
    main()
