#!/usr/bin/env python3
"""
Minimal workitem test - try the absolute simplest format
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

def test_minimal_workitem(token):
    """Test with absolute minimal workitem structure"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Try the most minimal structure possible
    minimal_data = {
        "activityId": f"{CLIENT_ID}.ExtractViewsActivity",
        "arguments": {}
    }
    
    print("🧪 Testing minimal workitem structure:")
    print(json.dumps(minimal_data, indent=2))
    
    response = requests.post(url, headers=headers, json=minimal_data)
    print(f"Minimal response: {response.status_code} - {response.text}")
    
    if response.status_code == 200:
        return response.json()["id"]
    
    # If that fails, try with just result
    result_only_data = {
        "activityId": f"{CLIENT_ID}.ExtractViewsActivity",
        "arguments": {
            "result": {
                "url": "https://httpbin.org/put"
            }
        }
    }
    
    print("\n🧪 Testing with result only:")
    print(json.dumps(result_only_data, indent=2))
    
    response = requests.post(url, headers=headers, json=result_only_data)
    print(f"Result-only response: {response.status_code} - {response.text}")
    
    if response.status_code == 200:
        return response.json()["id"]
    
    # Try with a working activity from the system
    system_activity_data = {
        "activityId": "Autodesk.Nop+Latest",
        "arguments": {}
    }
    
    print("\n🧪 Testing with system activity (Autodesk.Nop):")
    print(json.dumps(system_activity_data, indent=2))
    
    response = requests.post(url, headers=headers, json=system_activity_data)
    print(f"System activity response: {response.status_code} - {response.text}")
    
    if response.status_code == 200:
        workitem_id = response.json()["id"]
        print(f"✅ SUCCESS with system activity: {workitem_id}")
        print("This proves our API format is correct!")
        return workitem_id
    
    return None

def main():
    print("🔬 MINIMAL WORKITEM TEST")
    print("=" * 40)
    print("Testing the simplest possible workitem formats")
    print()
    
    token = get_access_token()
    if not token:
        print("❌ No token")
        return
    
    workitem_id = test_minimal_workitem(token)
    
    if workitem_id:
        print(f"\n🎉 SUCCESS! Workitem created: {workitem_id}")
        print("This means our API format works!")
        print("The issue is likely with our specific Activity reference")
    else:
        print("\n❌ All minimal tests failed")
        print("This indicates a fundamental API format issue")

if __name__ == "__main__":
    main()
