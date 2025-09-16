#!/usr/bin/env python3
"""
Create a working Activity that we can actually use
"""

import requests
import json
from config import CLIENT_ID, CLIENT_SECRET

def get_access_token():
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    return response.json()["access_token"] if response.status_code == 200 else None

def create_working_activity():
    token = get_access_token()
    
    activity_name = "WorkingViewExtractor"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Create activity with minimal structure
    activity_data = {
        "id": activity_name,
        "commandLine": [
            f"\"$(engine.path)\\\\revit.exe\" /i \"$(args[inputFile].path)\" /al \"$(appbundles[RevitViewExtractor4].path)\""
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
        "engine": "Autodesk.Revit+2026",
        "appbundles": [
            f"{CLIENT_ID}.RevitViewExtractor4+prod"
        ],
        "description": "Working View Extractor"
    }

    print("🔄 Creating working activity...")
    print(json.dumps(activity_data, indent=2))

    url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    response = requests.post(url, headers=headers, json=activity_data)

    print(f"\nResponse: {response.status_code}")
    print(response.text)
    
    if response.status_code in [200, 201]:
        print(f"✅ SUCCESS! Activity created: {CLIENT_ID}.{activity_name}")
        
        # Now create alias
        alias_url = f"{url}/{CLIENT_ID}.{activity_name}/aliases"
        alias_data = {"id": "v1", "version": 1}
        
        alias_response = requests.post(alias_url, headers=headers, json=alias_data)
        print(f"Alias creation: {alias_response.status_code}")
        
        if alias_response.status_code in [200, 201]:
            final_activity = f"{CLIENT_ID}.{activity_name}+v1"
            print(f"🎯 FINAL ACTIVITY ID: {final_activity}")
            return final_activity
        else:
            # Try without alias
            return f"{CLIENT_ID}.{activity_name}"
    
    return None

def test_working_activity(activity_id):
    """Test the working activity"""
    token = get_access_token()
    
    workitem_data = {
        "activityId": activity_id,
        "arguments": {
            "inputFile": {
                "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
            },
            "result": {
                "url": "https://httpbin.org/put"
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    response = requests.post(url, headers=headers, json=workitem_data)
    
    print(f"\n🧪 Testing workitem: {response.status_code}")
    
    if response.status_code == 200:
        workitem_id = response.json()["id"]
        print(f"🎉 SUCCESS! Workitem created: {workitem_id}")
        print("✅ Our activity is working!")
        return workitem_id
    else:
        print(f"❌ Failed: {response.text}")
        return None

def main():
    print("🚀 CREATING WORKING ACTIVITY")
    print("=" * 50)
    
    activity_id = create_working_activity()
    
    if activity_id:
        print(f"\n✅ Activity created: {activity_id}")
        
        # Test it
        workitem_id = test_working_activity(activity_id)
        
        if workitem_id:
            print(f"\n🎯 SUCCESS! Use this activity ID in scripts:")
            print(f"   {activity_id}")
        else:
            print(f"\n⚠️ Activity created but test failed")
    else:
        print("\n❌ Failed to create activity")

if __name__ == "__main__":
    main()



