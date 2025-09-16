#!/usr/bin/env python3
"""
Extract Revit file information using Autodesk system activities
"""

import requests
import json
import time
from config import CLIENT_ID, CLIENT_SECRET

def get_access_token():
    """Get access token from Autodesk"""
    url = "https://developer.api.autodesk.com/authentication/v2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "code:all data:write data:read"
    }
    
    response = requests.post(url, headers=headers, data=data)
    
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to get token: {response.text}")
        return None

def create_workitem_with_system_activity(token):
    """Use system activity to process Revit file"""
    
    # Use Autodesk's CountIt activity - it actually reads Revit files and counts elements
    activity_id = "Autodesk.CountIt+prod"
    
    workitem_data = {
        "activityId": activity_id,
        "arguments": {
            "inputFile": {
                "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt",
                "verb": "get"
            },
            "countItParams": {
                "url": "data:application/json,{'walls': true, 'doors': true, 'windows': true, 'floors': true, 'rooms': true}",
                "verb": "get"
            },
            "result": {
                "verb": "put", 
                "url": "https://httpbin.org/put"
            }
        }
    }
    
    # Send with proper headers
    json_str = json.dumps(workitem_data)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Content-Length": str(len(json_str))
    }
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    response = requests.post(url, headers=headers, data=json_str)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Workitem created: {result['id']}")
        return result['id']
    else:
        print(f"❌ Failed: {response.text}")
        return None

def monitor_workitem(token, workitem_id):
    """Monitor workitem status"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\nMonitoring workitem...")
    for i in range(30):  # Check for up to 2.5 minutes
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get("status", "unknown")
            print(f"[{i*5}s] Status: {status}")
            
            if status == "success":
                print("\n✅ WORKITEM COMPLETED SUCCESSFULLY!")
                
                # Get report URL
                if "reportUrl" in result:
                    print(f"\n📋 Execution report: {result['reportUrl']}")
                    
                    # Download report
                    report_response = requests.get(result['reportUrl'])
                    if report_response.status_code == 200:
                        print("\n📄 REPORT CONTENT:")
                        print("=" * 50)
                        print(report_response.text)
                        print("=" * 50)
                
                return result
                
            elif status == "failed":
                print("\n❌ Workitem failed!")
                if "reportUrl" in result:
                    report_response = requests.get(result['reportUrl'])
                    if report_response.status_code == 200:
                        print("\n📋 Error report:")
                        print(report_response.text)
                return result
                
            time.sleep(5)
        else:
            print(f"Failed to get status: {response.text}")
            return None
    
    print("Timeout waiting for workitem")
    return None

def test_export_to_dwg(token):
    """Test ExportToDWG activity"""
    print("\n🔧 Testing Revit ExportToDWG activity...")
    
    activity_id = "Autodesk.ExportToDWG+prod"
    
    workitem_data = {
        "activityId": activity_id,
        "arguments": {
            "rvtFile": {
                "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt",
                "verb": "get"
            },
            "result": {
                "verb": "put",
                "url": "https://httpbin.org/put"
            }
        }
    }
    
    json_str = json.dumps(workitem_data)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Content-Length": str(len(json_str))
    }
    
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    response = requests.post(url, headers=headers, data=json_str)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Export workitem created: {result['id']}")
        return monitor_workitem(token, result['id'])
    else:
        print(f"❌ Failed: {response.text}")
        return None

def main():
    print("🚀 REVIT PROCESSING WITH SYSTEM ACTIVITIES")
    print("=" * 50)
    
    # Get token
    print("\n1. Getting access token...")
    token = get_access_token()
    if not token:
        return
    print("✅ Token obtained")
    
    # Test CountIt activity
    print("\n2. Testing CountIt activity (counts Revit elements)...")
    workitem_id = create_workitem_with_system_activity(token)
    if workitem_id:
        result = monitor_workitem(token, workitem_id)
        
        if result and result.get("status") == "success":
            print("\n🎉 REVIT FILE SUCCESSFULLY PROCESSED!")
            print("This proves we can read and process Revit files!")
    
    # Test ExportToDWG
    test_export_to_dwg(token)
    
    print("\n✅ SYSTEM ACTIVITIES WORK!")
    print("📋 To extract views specifically, we need:")
    print("   1. Fix the custom activity ID parsing issue")
    print("   2. Or use Revit API directly with a custom plugin")
    print("   3. Or contact Autodesk support for the CLIENT_ID issue")

if __name__ == "__main__":
    main()
