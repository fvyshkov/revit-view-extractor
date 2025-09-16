#!/usr/bin/env python3

import requests
import json
from config import *

def get_access_token():
    """Get access token for APS API"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()["access_token"] if response.status_code == 200 else None

def create_fresh_activity(token):
    """Create a completely new activity with timestamp"""
    import time
    timestamp = int(time.time())
    activity_id = f"FreshViewExtractor{timestamp}"
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Use our existing bundle
    our_bundle = f"{CLIENT_ID}.RevitViewExtractor4+prod"
    
    activity_data = {
        "id": activity_id,
        "commandLine": [
            "\"$(engine.path)\\\\revit.exe\" /i \"$(args[inputFile].path)\" /al \"$(appbundles[RevitViewExtractor4].path)\""
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
                "description": "Output result file with view information",
                "localName": "result.txt",
                "required": False
            }
        },
        "engine": "Autodesk.Revit+2026",
        "appbundles": [our_bundle],
        "description": f"Fresh view extractor activity created at {timestamp}"
    }
    
    print(f"Creating fresh activity: {activity_id}")
    print(f"Bundle: {our_bundle}")
    
    response = requests.post(url, headers=headers, json=activity_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        result = response.json()
        version = result.get("version", "1")
        full_id = f"{CLIENT_ID}.{activity_id}+{version}"
        print(f"SUCCESS: Activity created!")
        print(f"Activity ID: {CLIENT_ID}.{activity_id}")
        print(f"Version: {version}")
        print(f"Full ID: {full_id}")
        return full_id
    else:
        print(f"FAILED: {response.text}")
        return None

def test_fresh_activity(token, activity_id):
    """Test the fresh activity with a workitem"""
    # Попробуем без версии
    base_activity = activity_id.split('+')[0]
    print(f"\nTesting activity: {base_activity} (without version)")
    
    workitem_data = {
        "activityId": base_activity,
        "arguments": {
            "inputFile": {
                "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
            },
            "result": {
                "url": "https://httpbin.org/put"
            }
        }
    }
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    print(f"Workitem creation: {response.status_code}")
    if response.status_code == 200:
        workitem_id = response.json()["id"]
        print(f"SUCCESS: Workitem created: {workitem_id}")
        return workitem_id
    else:
        print(f"FAILED: {response.text}")
        return None

def main():
    print("=== Creating Fresh Activity ===")
    
    token = get_access_token()
    if not token:
        print("Failed to get access token")
        return
    
    # Create fresh activity
    activity_id = create_fresh_activity(token)
    if not activity_id:
        print("Failed to create activity")
        return
    
    # Test it immediately
    workitem_id = test_fresh_activity(token, activity_id)
    if workitem_id:
        print(f"\nSUCCESS! Fresh activity {activity_id} is working!")
        print(f"Workitem: {workitem_id}")
    else:
        print(f"\nActivity created but workitem failed")

if __name__ == "__main__":
    main()
