#!/usr/bin/env python3
"""
Test the uploaded RevitViewExtractor4 bundle
"""

import requests
import json
from config import CLIENT_ID, CLIENT_SECRET

def get_access_token():
    """Get access token"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
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
        print(f"Failed to get token: {response.text}")
        return None

def list_app_bundles(token):
    """List all app bundles"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/appbundles"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        bundles = response.json()["data"]
        print("Available AppBundles:")
        for bundle in bundles:
            print(f"  - {bundle}")
        return bundles
    else:
        print(f"Failed to list bundles: {response.text}")
        return []

def create_simple_activity(token, bundle_name):
    """Create a simple activity for testing"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    activity_data = {
        "id": "TestExtractViews",
        "commandLine": [
            "$(engine.path)\\\\revit.exe /i $(args[inputFile].path) /al $(appbundles[{bundle_name}].path)"
        ],
        "parameters": {
            "inputFile": {
                "verb": "get",
                "description": "Input Revit file",
                "required": True
            },
            "result": {
                "verb": "put",
                "description": "Output result file",
                "localName": "result.txt"
            }
        },
        "engine": "Autodesk.Revit+2024",
        "appbundles": [f"{bundle_name}+$LATEST"],
        "description": "Test activity for view extraction"
    }
    
    response = requests.post(url, headers=headers, json=activity_data)
    if response.status_code == 200:
        print("✓ Activity created successfully")
        return True
    else:
        print(f"✗ Failed to create Activity: {response.text}")
        return False

def main():
    print("=== Testing RevitViewExtractor Bundle ===")
    print()
    
    # Get token
    print("Getting access token...")
    token = get_access_token()
    if not token:
        return
    print("✓ Token obtained")
    
    # List bundles
    print("\nListing app bundles...")
    bundles = list_app_bundles(token)
    
    # Check if our bundle exists
    target_bundle = f"{CLIENT_ID}.RevitViewExtractor4+$LATEST"
    if target_bundle in bundles:
        print(f"✓ Found our bundle: {target_bundle}")
        
        # Try to create activity
        print(f"\nCreating test activity...")
        create_simple_activity(token, target_bundle)
    else:
        print(f"✗ Bundle {target_bundle} not found")
        print("Available bundles:", bundles)

if __name__ == "__main__":
    main()
