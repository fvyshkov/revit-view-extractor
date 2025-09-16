#!/usr/bin/env python3
"""
Simple approach - use direct OSS upload and workitem with URLs
"""

import os
import json
import time
import requests
from config import CLIENT_ID, CLIENT_SECRET

def get_access_token():
    """Get access token"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "data:read data:write data:create bucket:create bucket:read code:all"
    }
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get token: {response.text}")
        return None

def create_simple_workitem(token):
    """Create workitem with public URLs (test approach)"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    activity_id = f"{CLIENT_ID}.ExtractViewsActivity"
    
    # Use test URLs for now
    workitem_data = {
        "activityId": activity_id,
        "arguments": {
            "result": {
                "verb": "put",
                "url": "https://httpbin.org/put"  # Test endpoint
            }
        }
    }
    
    print("Creating simple workitem...")
    print(f"Activity: {activity_id}")
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        workitem_id = response.json()["id"]
        print(f"✓ Workitem created: {workitem_id}")
        return workitem_id
    else:
        print("✗ Failed to create workitem")
        return None

def wait_for_completion(token, workitem_id):
    """Wait for workitem to complete"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Waiting for completion...")
    
    for i in range(60):  # Wait up to 10 minutes
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            status = data["status"]
            
            if i % 6 == 0:  # Print every minute
                print(f"Status: {status} (elapsed: {i*10}s)")
            
            if status == "success":
                print("✓ Workitem completed successfully!")
                print("Result:", data.get("reportUrl", "No report"))
                return True
            elif status == "failed":
                print("✗ Workitem failed!")
                print("Report:", data.get("reportUrl", "No report"))
                return False
            elif status in ["pending", "inprogress"]:
                time.sleep(10)
                continue
        else:
            print(f"Error checking status: {response.text}")
            return False
    
    print("✗ Timeout")
    return False

def main():
    print("=== Simple Workitem Test ===")
    
    # Get token
    token = get_access_token()
    if not token:
        return
    print("✓ Token obtained")
    
    # Create simple workitem (without input file first)
    workitem_id = create_simple_workitem(token)
    
    if workitem_id:
        print(f"\n✓ Workitem created: {workitem_id}")
        
        # Wait for completion
        success = wait_for_completion(token, workitem_id)
        
        if success:
            print("\n🎉 Test successful!")
            print("Our Activity is working!")
            print("Next step: Add real file input")
        else:
            print("\n⚠️  Test failed, but this might be expected without input file")
            print("The important thing is that the Activity exists and can be called")

if __name__ == "__main__":
    main()




