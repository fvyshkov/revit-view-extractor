#!/usr/bin/env python3
"""
Test with existing working bundle to understand the format
"""

import requests
import json
from config import CLIENT_ID, CLIENT_SECRET

def get_access_token():
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    
    response = requests.post(url, headers=headers, data=data)
    return response.json()["access_token"] if response.status_code == 200 else None

def create_activity_with_existing_bundle(token):
    """Create activity using existing ExportSheetImage bundle"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use existing bundle that we know works
    existing_bundle = f"{CLIENT_ID}.ExportSheetImage+prod"
    
    activity_data = {
        "id": "TestExportSheet",
        "commandLine": [
            "\"$(engine.path)\\\\revit.exe\" /i \"$(args[inputFile].path)\" /al \"$(appbundles[ExportSheetImage].path)\""
        ],
        "parameters": {
            "inputFile": {
                "verb": "get",
                "description": "Input Revit file",
                "required": True,
                "localName": "input.rvt"
            },
            "result": {
                "verb": "put",
                "description": "Output result",
                "localName": "result.txt",
                "required": False
            }
        },
        "engine": "Autodesk.Revit+2026",
        "appbundles": [existing_bundle],
        "description": "Test activity with existing bundle"
    }
    
    print("Creating test activity with existing bundle...")
    print(f"Bundle: {existing_bundle}")
    
    response = requests.post(url, headers=headers, json=activity_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✓ Activity created successfully!")
        return response.json()["id"]
    else:
        print("✗ Failed to create activity")
        return None

def create_simple_workitem(token, activity_id):
    """Create a simple workitem to test"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    workitem_data = {
        "activityId": activity_id,
        "arguments": {
            "result": {
                "verb": "put",
                "url": "https://httpbin.org/put"
            }
        }
    }
    
    print(f"Creating workitem with activity: {activity_id}")
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    print(f"Workitem response status: {response.status_code}")
    print(f"Workitem response: {response.text}")
    
    return response.status_code == 200

def main():
    print("=== Testing with Existing Bundle ===")
    
    token = get_access_token()
    if not token:
        return
    print("✓ Token obtained")
    
    # Create activity with existing bundle
    activity_id = create_activity_with_existing_bundle(token)
    
    if activity_id:
        print(f"\n✓ Activity created: {activity_id}")
        print("Now we know the format works!")
        
        # Try to create workitem (will fail without input file, but shows format is correct)
        create_simple_workitem(token, activity_id)
    
    print("\n💡 Next step: Use the same format for our RevitViewExtractor4 bundle")

if __name__ == "__main__":
    main()
