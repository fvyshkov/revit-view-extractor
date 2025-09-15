#!/usr/bin/env python3
"""
Simple test - just create a workitem with our bundle to see what happens
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

def create_simple_activity(token):
    """Create a simple activity"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    bundle_name = f"{CLIENT_ID}.RevitViewExtractor4"
    
    activity_data = {
        "id": "SimpleExtractViews",
        "commandLine": [
            "$(engine.path)\\\\revit.exe /i $(args[inputFile].path) /al $(appbundles[RevitViewExtractor4].path)"
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
                "description": "Output result file",
                "localName": "result.txt",
                "required": False
            }
        },
        "engine": "Autodesk.Revit+2024",
        "appbundles": [bundle_name],
        "description": "Simple activity to extract views info"
    }
    
    print("Creating activity...")
    print(f"Bundle: {bundle_name}")
    print(f"Activity data: {json.dumps(activity_data, indent=2)}")
    
    response = requests.post(url, headers=headers, json=activity_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("✓ Activity created successfully")
        return True
    else:
        print(f"✗ Failed to create Activity")
        return False

def main():
    print("=== Creating Simple Activity ===")
    
    # Get token
    token = get_access_token()
    if not token:
        return
    print("✓ Token obtained")
    
    # Create activity
    create_simple_activity(token)

if __name__ == "__main__":
    main()
