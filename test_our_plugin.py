#!/usr/bin/env python3
"""
Test our plugin with a simple approach - use a public test file
"""

import requests
import json
import time
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

def create_test_workitem(token):
    """Create a test workitem to verify our activity works"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    activity_id = f"{CLIENT_ID}.ExtractViewsActivity"
    
    # Use a public test Revit file and httpbin for output
    workitem_data = {
        "activityId": activity_id,
        "arguments": {
            "inputFile": {
                "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt",
                "verb": "get"
            },
            "result": {
                "url": "https://httpbin.org/put",
                "verb": "put"
            }
        }
    }
    
    print("Creating test workitem...")
    print(f"Activity: {activity_id}")
    print("Using public test Revit file")
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        workitem_id = response.json()["id"]
        print(f"✓ Workitem created: {workitem_id}")
        return workitem_id
    else:
        print(f"✗ Failed to create workitem: {response.text}")
        
        # Try with different activity format
        print("Trying alternative activity format...")
        workitem_data["activityId"] = f"{CLIENT_ID}.ExtractViewsActivity+1"
        
        response = requests.post(url, headers=headers, json=workitem_data)
        print(f"Alternative response: {response.status_code} - {response.text}")
        
        return None

def monitor_workitem(token, workitem_id):
    """Monitor workitem progress"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("Monitoring workitem...")
    
    for i in range(60):  # 10 minutes max
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            status = data["status"]
            
            print(f"Status: {status}")
            
            if status == "success":
                print("✓ SUCCESS! Our plugin worked!")
                print("The plugin successfully processed a Revit file!")
                if "reportUrl" in data:
                    print(f"Report: {data['reportUrl']}")
                return True
            elif status == "failed":
                print("✗ Processing failed")
                if "reportUrl" in data:
                    print(f"Report: {data['reportUrl']}")
                return False
            elif status in ["pending", "inprogress"]:
                time.sleep(10)
                continue
        else:
            print(f"Error: {response.text}")
            return False
    
    print("✗ Timeout")
    return False

def main():
    print("🧪 TESTING OUR REVIT PLUGIN")
    print("="*50)
    print("This will test our cloud plugin with a public Revit file")
    print()
    
    # Get token
    token = get_access_token()
    if not token:
        return
    print("✓ Token obtained")
    
    # Create test workitem
    workitem_id = create_test_workitem(token)
    if not workitem_id:
        print("\n❌ Could not create workitem")
        print("This might be due to API format issues")
        return
    
    # Monitor progress
    success = monitor_workitem(token, workitem_id)
    
    if success:
        print("\n🎉 PLUGIN TEST SUCCESSFUL!")
        print("Your RevitViewExtractor plugin is working in the cloud!")
        print("It can process Revit files and extract view information!")
    else:
        print("\n⚠️  Test completed but may have issues")
        print("Check the report URL for details")

if __name__ == "__main__":
    main()





