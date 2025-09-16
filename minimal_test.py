#!/usr/bin/env python3
"""
Minimal test - try to run a workitem directly with our bundle
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

def test_direct_workitem(token):
    """Try to create workitem without activity (this will likely fail but show us the error)"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    bundle_name = f"{CLIENT_ID}.RevitViewExtractor4+$LATEST"
    
    # Try using bundle as activity (this is not standard but let's see what happens)
    workitem_data = {
        "activityId": bundle_name,
        "arguments": {
            "result": {
                "verb": "put",
                "url": "https://httpbin.org/put"  # Test endpoint that accepts anything
            }
        }
    }
    
    print("Trying direct workitem...")
    print(f"Bundle: {bundle_name}")
    print(f"Data: {json.dumps(workitem_data, indent=2)}")
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    print(f"Response status: {response.status_code}")
    print(f"Response: {response.text}")
    
    return response.status_code == 200

def check_engines(token):
    """Check available engines"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/engines"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        engines = response.json()["data"]
        revit_engines = [e for e in engines if "Revit" in e]
        print("Available Revit engines:")
        for engine in revit_engines:
            print(f"  - {engine}")
        return revit_engines
    else:
        print(f"Failed to list engines: {response.text}")
        return []

def main():
    print("=== Minimal Test ===")
    
    # Get token
    token = get_access_token()
    if not token:
        return
    print("✓ Token obtained")
    
    # Check engines
    print("\nChecking available engines...")
    engines = check_engines(token)
    
    # Try direct workitem
    print("\nTrying direct workitem (will likely fail)...")
    test_direct_workitem(token)
    
    print("\n💡 Summary:")
    print("- Our bundle is uploaded and ready")
    print("- We need to create a proper Activity first")
    print("- The Activity creation API has specific format requirements")
    print("- Once Activity is created, we can run workitems")

if __name__ == "__main__":
    main()




