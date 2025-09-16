#!/usr/bin/env python3
"""
Test with new CLIENT_ID
"""

import requests
import json
import time

# New credentials
CLIENT_ID = "H3nGeDHGOZINPwBBltL0dAtUnJKG6jQrdShz1bOggsAswmzU"
CLIENT_SECRET = "ZW2ViZrysoHleclZRBR5PdgMO8KeWbwKMmtvGLL4OxGAwkuDICaSG8h3Np02fhUO"

def get_access_token():
    """Get access token"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read bucket:create bucket:delete"
    }
    response = requests.post(url, headers={"Content-Type": "application/x-www-form-urlencoded"}, data=data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get token: {response.text}")
        return None

def test_new_client():
    print("🚀 TESTING NEW CLIENT_ID")
    print("=" * 60)
    print(f"CLIENT_ID: {CLIENT_ID}")
    print(f"Length: {len(CLIENT_ID)} characters")
    
    # Get token
    print("\n1. Getting access token...")
    token = get_access_token()
    if not token:
        return
    print("✅ Token obtained")
    
    # Get nickname
    print("\n2. Getting nickname...")
    url = "https://developer.api.autodesk.com/da/us-east/v3/forgeapps/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        nickname = response.text.strip('"')
        print(f"✅ Nickname: {nickname}")
    else:
        print(f"❌ Failed to get nickname: {response.text}")
        return
    
    # Create simple activity
    print("\n3. Creating test activity...")
    activity_name = "TestActivity"
    
    activity_data = {
        "id": activity_name,
        "commandLine": ["echo 'Hello from new client' > \"$(args[result].path)\""],
        "engine": "Autodesk.Revit+2024",
        "parameters": {
            "result": {
                "verb": "put",
                "description": "Output",
                "localName": "result.txt",
                "required": True
            }
        },
        "description": "Test with new client"
    }
    
    # Delete if exists
    delete_url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{nickname}.{activity_name}"
    requests.delete(delete_url, headers=headers)
    
    # Create new
    create_url = "https://developer.api.autodesk.com/da/us-east/v3/activities"
    headers["Content-Type"] = "application/json"
    
    response = requests.post(create_url, headers=headers, json=activity_data)
    
    if response.status_code == 200:
        result = response.json()
        activity_id = result["id"]
        print(f"✅ Activity created: {activity_id}")
        
        # Try to create alias
        alias_url = f"https://developer.api.autodesk.com/da/us-east/v3/activities/{activity_id}/aliases"
        alias_data = {"id": "prod", "version": 1}
        
        alias_response = requests.post(alias_url, headers=headers, json=alias_data)
        
        if alias_response.status_code in [200, 201, 409]:
            print("✅ Alias created")
            test_activity = f"{activity_id}+prod"
        else:
            print(f"⚠️ Alias failed: {alias_response.text}")
            test_activity = f"{activity_id}+1"
        
        # Test workitem
        print(f"\n4. Testing workitem with: {test_activity}")
        
        workitem_data = {
            "activityId": test_activity,
            "arguments": {
                "result": {
                    "url": "https://httpbin.org/put",
                    "verb": "put"
                }
            }
        }
        
        json_str = json.dumps(workitem_data)
        headers["Content-Length"] = str(len(json_str))
        
        workitem_url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
        workitem_response = requests.post(workitem_url, headers=headers, data=json_str)
        
        if workitem_response.status_code == 200:
            workitem_id = workitem_response.json()["id"]
            print(f"✅ SUCCESS! Workitem created: {workitem_id}")
            print("\n🎉 NEW CLIENT_ID WORKS!")
            print("You can now use this client for your Revit view extraction!")
        else:
            print(f"❌ Workitem failed: {workitem_response.text}")
    else:
        print(f"❌ Activity creation failed: {response.text}")

if __name__ == "__main__":
    test_new_client()
