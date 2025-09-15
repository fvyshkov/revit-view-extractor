#!/usr/bin/env python3
"""
Final working test based on documentation research
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

def create_workitem_correct_format(token):
    """Create workitem with the correct format based on documentation"""
    url = "https://developer.api.autodesk.com/da/us-east/v3/workitems"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Based on documentation research, the correct format should be:
    activity_id = f"{CLIENT_ID}.ExtractViewsActivity+1"  # Try with version number
    
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
    
    print(f"🚀 TESTING WITH CORRECT FORMAT")
    print(f"Activity: {activity_id}")
    print("Request JSON:")
    print(json.dumps(workitem_data, indent=2))
    
    response = requests.post(url, headers=headers, json=workitem_data)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code == 200:
        workitem_id = response.json()["id"]
        print(f"✅ SUCCESS! Workitem created: {workitem_id}")
        return workitem_id
    elif response.status_code == 400:
        # Try alternative formats
        print("\n🔄 Trying alternative formats...")
        
        # Format 1: Without version
        workitem_data["activityId"] = f"{CLIENT_ID}.ExtractViewsActivity"
        response = requests.post(url, headers=headers, json=workitem_data)
        print(f"Format 1 (no version): {response.status_code} - {response.text[:200]}")
        
        if response.status_code == 200:
            return response.json()["id"]
        
        # Format 2: With $LATEST
        workitem_data["activityId"] = f"{CLIENT_ID}.ExtractViewsActivity+$LATEST"
        response = requests.post(url, headers=headers, json=workitem_data)
        print(f"Format 2 ($LATEST): {response.status_code} - {response.text[:200]}")
        
        if response.status_code == 200:
            return response.json()["id"]
        
        # Format 3: Add verb explicitly
        workitem_data["activityId"] = f"{CLIENT_ID}.ExtractViewsActivity"
        workitem_data["arguments"]["inputFile"]["verb"] = "get"
        workitem_data["arguments"]["result"]["verb"] = "put"
        response = requests.post(url, headers=headers, json=workitem_data)
        print(f"Format 3 (with verbs): {response.status_code} - {response.text[:200]}")
        
        if response.status_code == 200:
            return response.json()["id"]
        
        # Format 4: Try with headers parameter
        workitem_data_headers = {
            "activityId": f"{CLIENT_ID}.ExtractViewsActivity",
            "arguments": {
                "inputFile": {
                    "url": "https://github.com/Developer-Autodesk/forge-tutorial-postman/raw/master/Collections/DA4R-Tutorial/SampleFiles/DeleteWalls.rvt",
                    "verb": "get",
                    "headers": {
                        "Authorization": f"Bearer {token}"
                    }
                },
                "result": {
                    "url": "https://httpbin.org/put",
                    "verb": "put"
                }
            }
        }
        response = requests.post(url, headers=headers, json=workitem_data_headers)
        print(f"Format 4 (with headers): {response.status_code} - {response.text[:200]}")
        
        if response.status_code == 200:
            return response.json()["id"]
    
    print("❌ All formats failed")
    return None

def monitor_workitem(token, workitem_id):
    """Monitor workitem execution"""
    url = f"https://developer.api.autodesk.com/da/us-east/v3/workitems/{workitem_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n📊 Monitoring workitem: {workitem_id}")
    
    for i in range(60):  # 10 minutes
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            status = data["status"]
            
            if i % 3 == 0:
                print(f"Status: {status} (elapsed: {i*10}s)")
            
            if status == "success":
                print("\n🎉 SUCCESS! OUR PLUGIN WORKED!")
                print("The RevitViewExtractor processed a Revit file in the cloud!")
                
                if "reportUrl" in data:
                    print(f"Report URL: {data['reportUrl']}")
                    
                    # Get the report
                    try:
                        report_response = requests.get(data['reportUrl'])
                        if report_response.status_code == 200:
                            print("\n📋 EXECUTION REPORT:")
                            print("=" * 50)
                            print(report_response.text)
                            print("=" * 50)
                    except Exception as e:
                        print(f"Could not fetch report: {e}")
                
                return True
                
            elif status == "failed":
                print(f"\n❌ FAILED")
                if "reportUrl" in data:
                    print(f"Report URL: {data['reportUrl']}")
                    
                    try:
                        report_response = requests.get(data['reportUrl'])
                        if report_response.status_code == 200:
                            print("\n📋 FAILURE REPORT:")
                            print("=" * 50)
                            print(report_response.text)
                            print("=" * 50)
                    except Exception as e:
                        print(f"Could not fetch report: {e}")
                
                return False
                
            elif status in ["pending", "inprogress"]:
                time.sleep(10)
                continue
            else:
                print(f"Unknown status: {status}")
                return False
        else:
            print(f"Error checking status: {response.text}")
            return False
    
    print("⏰ Timeout")
    return False

def main():
    print("🎯 FINAL TEST - CORRECT API FORMAT")
    print("=" * 60)
    print("Testing our RevitViewExtractor plugin in the cloud")
    print("Using research-based correct API format")
    print("=" * 60)
    
    # Get token
    token = get_access_token()
    if not token:
        return
    print("✅ Token obtained")
    
    # Create workitem with correct format
    workitem_id = create_workitem_correct_format(token)
    if not workitem_id:
        print("\n❌ Could not create workitem with any format")
        print("This indicates a deeper API issue that needs investigation")
        return
    
    # Monitor execution
    success = monitor_workitem(token, workitem_id)
    
    if success:
        print("\n🎉 COMPLETE SUCCESS!")
        print("Your RevitViewExtractor plugin is fully working in the cloud!")
        print("It can process Revit files and extract view information!")
        print("\n🚀 Ready for production use!")
    else:
        print("\n⚠️  Execution had issues")
        print("Check the report above for details")

if __name__ == "__main__":
    main()
