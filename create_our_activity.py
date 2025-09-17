#!/usr/bin/env python3
"""
Create Activity for our RevitViewExtractor4 bundle using the correct format
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

def create_our_activity(token):
    """Create activity for our RevitViewExtractor4 bundle"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Our bundle (try with +prod instead of +$LATEST)
    our_bundle = f"{CLIENT_ID}.RevitViewExtractor4+prod"
    
    activity_data = {
        "id": "ExtractViewsActivity",
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
        "description": "Extract view information from Revit model"
    }
    
    print("Creating activity for our bundle...")
    print(f"Bundle: {our_bundle}")
    print(f"Activity ID: ExtractViewsActivity")
    
    response = requests.post(url, headers=headers, json=activity_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        activity_id = response.json()["id"]
        print(f"✓ Activity created successfully: {activity_id}")
        return activity_id
    else:
        print("✗ Failed to create activity")
        
        # If +prod doesn't work, try without version
        if "+prod" in our_bundle:
            print("Trying without version suffix...")
            our_bundle_no_version = f"{CLIENT_ID}.RevitViewExtractor4"
            activity_data["appbundles"] = [our_bundle_no_version]
            
            response = requests.post(url, headers=headers, json=activity_data)
            print(f"Second attempt status: {response.status_code}")
            print(f"Second attempt response: {response.text}")
            
            if response.status_code == 200:
                activity_id = response.json()["id"]
                print(f"✓ Activity created successfully: {activity_id}")
                return activity_id
        
        return None

def test_workitem(token, activity_id):
    """Test workitem creation (will fail without real file, but shows format works)"""
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
    
    print(f"\nTesting workitem with activity: {activity_id}")
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    print(f"Workitem status: {response.status_code}")
    print(f"Workitem response: {response.text}")
    
    if response.status_code == 200:
        workitem_id = response.json()["id"]
        print(f"✓ Workitem created: {workitem_id}")
        return workitem_id
    else:
        print("✗ Workitem creation failed (expected without input file)")
        return None

def main():
    print("=== Creating Activity for Our Bundle ===")
    
    token = get_access_token()
    if not token:
        return
    print("✓ Token obtained")
    
    # Create our activity
    activity_id = create_our_activity(token)
    
    if activity_id:
        print(f"\n🎉 SUCCESS! Activity created: {activity_id}")
        
        # Test workitem creation
        test_workitem(token, activity_id)
        
        print(f"\n✅ Ready to process files!")
        print(f"Activity ID: {activity_id}")
        print("Next step: Create workitem with real Revit file")
    else:
        print("\n❌ Failed to create activity")
        print("Check bundle name and version")

if __name__ == "__main__":
    main()





