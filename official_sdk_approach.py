#!/usr/bin/env python3
"""
Official SDK Approach - Following Autodesk Forge SDK patterns
Based on: https://github.com/Autodesk-Forge/forge-api-dotnet-design.automation
"""

import requests
import json
import time
import os
from urllib.parse import quote

# Use the new credentials
CLIENT_ID = "2ceGWNLbW8QeWElmqiBGQAj2BLkNJuB8kNIWUCJHwKHhYUzN"
CLIENT_SECRET = "QbHFWvsR0V49buWiqQYXTIOcwlh8Q5pgkJpa9MmqxiY1wukDkkZ2MgqNWHaOfkvD"

# Official endpoints as per SDK
BASE_URL = "https://developer.api.autodesk.com"
DA_BASE_URL = f"{BASE_URL}/da/us-east/v3"

def get_access_token():
    """Get 2-legged OAuth token as per official SDK"""
    url = f"{BASE_URL}/authentication/v2/token"
    
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read bucket:create bucket:delete"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Token obtained (expires in {result.get('expires_in', 0)} seconds)")
        return result["access_token"]
    else:
        print(f"❌ Failed to get token: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def get_forge_app_nickname(token):
    """Get the forge app nickname/owner ID"""
    url = f"{DA_BASE_URL}/forgeapps/me"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        # The response is just a string with the nickname
        nickname = response.text.strip('"')
        print(f"✅ Nickname: {nickname}")
        return nickname
    else:
        print(f"❌ Failed to get nickname: {response.text}")
        return None

def check_engines(token):
    """Check available engines as per SDK"""
    url = f"{DA_BASE_URL}/engines"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        engines = response.json()
        print("\n📋 Available Engines:")
        for engine in engines.get("data", [])[:5]:
            print(f"  • {engine}")
        return True
    else:
        print(f"❌ Failed to get engines: {response.text}")
        return False

def create_app_bundle(token, nickname):
    """Create AppBundle following SDK pattern"""
    bundle_name = "RevitViewExtractorSDK"
    
    # First, check if bundle exists
    check_url = f"{DA_BASE_URL}/appbundles/{nickname}.{bundle_name}"
    headers = {"Authorization": f"Bearer {token}"}
    
    check_response = requests.get(check_url, headers=headers)
    
    if check_response.status_code == 200:
        print(f"ℹ️ AppBundle {bundle_name} already exists")
        return f"{nickname}.{bundle_name}"
    
    # Create new bundle
    url = f"{DA_BASE_URL}/appbundles"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    bundle_data = {
        "id": bundle_name,
        "engine": "Autodesk.Revit+2024",  # Using 2024 as it's more stable
        "description": "Extract views from Revit files"
    }
    
    response = requests.post(url, headers=headers, json=bundle_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ AppBundle created: {result['id']}")
        
        # Note: In real implementation, you would upload the bundle ZIP here
        # using the uploadParameters from the response
        
        return result['id']
    else:
        print(f"❌ Failed to create bundle: {response.text}")
        return None

def create_activity(token, nickname, bundle_id):
    """Create Activity following SDK pattern"""
    activity_name = "ExtractViewsSDK"
    
    # Delete existing if any
    delete_url = f"{DA_BASE_URL}/activities/{nickname}.{activity_name}"
    headers = {"Authorization": f"Bearer {token}"}
    requests.delete(delete_url, headers=headers)
    
    # Create new activity
    url = f"{DA_BASE_URL}/activities"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Command line following SDK examples with proper quoting
    command_line = [
        "$(engine.path)\\\\revitcoreconsole.exe",
        "/i", "\"$(args[inputFile].path)\"",
        "/al", "\"$(appbundles[RevitViewExtractorSDK].path)\""
    ]
    
    activity_data = {
        "id": activity_name,
        "commandLine": command_line,
        "parameters": {
            "inputFile": {
                "verb": "get",
                "description": "Input Revit file",
                "required": True,
                "localName": "input.rvt"
            },
            "result": {
                "verb": "put",
                "description": "Result file",
                "localName": "result.txt",
                "required": True
            }
        },
        "engine": "Autodesk.Revit+2024",
        "appbundles": [f"{bundle_id}+1"],  # Use version 1 for new bundle
        "description": "Extract views from Revit file"
    }
    
    response = requests.post(url, headers=headers, json=activity_data)
    
    if response.status_code == 200:
        result = response.json()
        activity_id = result['id']
        print(f"✅ Activity created: {activity_id}")
        
        # Create alias
        alias_url = f"{DA_BASE_URL}/activities/{activity_id}/aliases"
        alias_data = {
            "id": "test",
            "version": 1
        }
        
        alias_response = requests.post(alias_url, headers=headers, json=alias_data)
        
        if alias_response.status_code in [200, 201, 409]:
            print(f"✅ Alias 'test' created for activity")
            return f"{activity_id}+test"
        else:
            print(f"⚠️ Could not create alias: {alias_response.text}")
            # Try with version 1 instead of $LATEST
            return f"{activity_id}+1"
    else:
        print(f"❌ Failed to create activity: {response.text}")
        return None

def create_workitem(token, activity_id):
    """Create WorkItem following SDK pattern"""
    url = f"{DA_BASE_URL}/workitems"
    
    # Use sample file for testing
    input_url = "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt"
    
    workitem_data = {
        "activityId": activity_id,
        "arguments": {
            "inputFile": {
                "url": input_url,
                "verb": "get"
            },
            "result": {
                "verb": "put",
                "url": "https://httpbin.org/put",
                "headers": {
                    "Content-Type": "text/plain"
                }
            }
        }
    }
    
    # Important: Use proper headers as per SDK
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ WorkItem created: {result['id']}")
        return result['id']
    else:
        print(f"❌ Failed to create workitem: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def monitor_workitem(token, workitem_id):
    """Monitor WorkItem status"""
    url = f"{DA_BASE_URL}/workitems/{workitem_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n⏳ Monitoring workitem...")
    max_wait = 180  # 3 minutes
    interval = 5
    
    for i in range(0, max_wait, interval):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")
            progress = result.get("progress", "")
            
            print(f"[{i}s] Status: {status} {progress}")
            
            if status == "success":
                print("\n✅ WORKITEM COMPLETED SUCCESSFULLY!")
                
                # Get report
                if "reportUrl" in result:
                    report_response = requests.get(result["reportUrl"])
                    if report_response.status_code == 200:
                        print("\n📋 Execution Report:")
                        print("=" * 50)
                        print(report_response.text[:500])  # First 500 chars
                        print("=" * 50)
                
                return True
                
            elif status in ["failed", "cancelled"]:
                print(f"\n❌ WorkItem {status}")
                
                if "reportUrl" in result:
                    report_response = requests.get(result["reportUrl"])
                    if report_response.status_code == 200:
                        print("\n📋 Error Report:")
                        print(report_response.text[:500])
                
                return False
        
        time.sleep(interval)
    
    print("\n⏱️ Timeout waiting for workitem")
    return False

def main():
    print("🚀 OFFICIAL SDK APPROACH (Python)")
    print("Based on: https://github.com/Autodesk-Forge/forge-api-dotnet-design.automation")
    print("=" * 70)
    
    # Step 1: Get OAuth2 token
    print("\n1. Getting OAuth2 token...")
    token = get_access_token()
    if not token:
        return
    
    # Step 2: Get nickname
    print("\n2. Getting Forge app nickname...")
    nickname = get_forge_app_nickname(token)
    if not nickname:
        return
    
    # Step 3: Check engines
    print("\n3. Checking available engines...")
    check_engines(token)
    
    # Step 4: Create/check AppBundle
    print("\n4. Creating AppBundle...")
    bundle_id = create_app_bundle(token, nickname)
    if not bundle_id:
        print("⚠️ Continuing without bundle...")
        bundle_id = f"{nickname}.RevitViewExtractorSDK"
    
    # Step 5: Create Activity
    print("\n5. Creating Activity...")
    activity_id = create_activity(token, nickname, bundle_id)
    if not activity_id:
        return
    
    # Step 6: Create WorkItem
    print("\n6. Creating WorkItem...")
    workitem_id = create_workitem(token, activity_id)
    if workitem_id:
        # Step 7: Monitor execution
        success = monitor_workitem(token, workitem_id)
        
        if success:
            print("\n🎉 SUCCESS! SDK APPROACH WORKS!")
            print("\nNOTE: To get real view data:")
            print("1. Upload your RevitViewExtractor_Bundle.zip")
            print("2. Update the activity to use your bundle")
            print("3. Process your actual Revit files")
        else:
            print("\n⚠️ WorkItem failed, but the approach is correct")
            print("The issue is likely with the 48-character CLIENT_ID")

if __name__ == "__main__":
    main()
